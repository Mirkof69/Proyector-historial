# Optimización de la red neuronal — lo que se midió

Documento de resultados, no de intenciones. Cada línea de aquí salió de correr
el modelo contra `datasets_pathology_v2` (2.911 imágenes de test, 2.893 de
validación) en una RTX 3090, con el mismo preprocesado que usa el
microservicio en producción.

Fecha de la medición: **4 de septiembre de 2026.**

---

## 1. Dónde se va el tiempo

| Etapa | ms | % |
|---|---|---|
| Leer y decodificar la imagen | 0,9 | 4% |
| Preprocesado (frost, CLAHE, normalización) | 0,9 | 4% |
| **Paso hacia adelante de la red** | **23,3** | **93%** |
| **Total por ecografía** | **25,1** | |

**Consecuencia:** optimizar el preprocesado no sirve de nada. El 93% está en
la red, y ahí las opciones son las de abajo.

---

## 2. Optimizaciones de velocidad probadas y **descartadas**

Todas se midieron; ninguna se aplicó, y por qué:

| Optimización | Resultado medido | Decisión |
|---|---|---|
| `cudnn.benchmark = True` | 22,7 → **24,1 ms** (más lento) | Descartada |
| `torch.inference_mode()` en vez de `no_grad()` | 22,7 → 23,3 ms (igual) | Descartada |
| AMP fp16 (tensor cores) | 24,6 → **33,7 ms** (37% más lento) | Descartada |
| `channels_last` + fp16 | 24,6 → **33,3 ms** | Descartada |
| Lote de 8-16 imágenes | 24,6 → **4,6-10,7 ms/imagen** | Ver abajo |

**Sobre fp16:** es la optimización "obvia" y es la equivocada aquí. Con lote
de 1, el coste de convertir los pesos a media precisión supera la ganancia de
los tensor cores. Solo compensa con lotes grandes.

**Sobre el lote:** es la única que da una mejora real (2,2× a 5,3×), pero solo
sirve para análisis masivo o retrospectivo. El uso clínico es una ecografía
por consulta: no hay nada que agrupar.

**Conclusión de velocidad:** el modelo ya está en su punto. 25 ms por
ecografía, con un objetivo de 3.000 ms en el estudio de investigación de
operaciones del proyecto. Está **120 veces por debajo del objetivo**, y de
punta a punta por HTTP responde en ~200 ms. La red no es el cuello de botella
de nada.

---

## 3. Precisión: lo que sí mejoró

### Recalibración de umbrales (aplicada)

Dos clases tenían el umbral mal puesto. Se calibró en `valid/` y se midió en
`test/`, para no ajustar y medir sobre las mismas imágenes:

| Clase | Umbral | F1 |
|---|---|---|
| `polihidramnios` | 0,18 → **0,49** | 0,268 → **0,430** |
| `macrosomia_fetal` | 0,22 → **0,37** | 0,305 → **0,429** |

Las otras doce no se tocaron: ya rendían bien (AP ≥ 0,80) y moverlas solo
podía empeorarlas.

**Resultado global — las cuatro métricas mejoran:**

| Métrica | Antes | Después |
|---|---|---|
| Precisión macro | 0,814 | **0,848** |
| F1 macro | 0,822 | **0,842** |
| Precisión ponderada | 0,933 | **0,940** |
| F1 ponderada | 0,926 | **0,931** |

### Una calibración que se probó y se descartó

El primer intento calibró las 14 clases con el criterio «máximo recall con
precisión ≥ 0,70». **Empeoró el sistema:** empujó `polihidramnios` y
`macrosomia_fetal` a umbrales de 0,91 y 0,88, con precisión 1,000 y recall
0,02 — detectores que no detectan. La F1 ponderada bajaba de 0,926 a 0,860.

### Aumento en tiempo de inferencia (TTA) — probado y **descartado**

Promediar la predicción sobre la imagen y su espejo horizontal. Una ecografía
no cambia de diagnóstico al reflejarla, así que en teoría promediar reduce el
ruido.

| Métrica | Sin TTA | Con TTA | Con TTA + umbrales recalibrados |
|---|---|---|---|
| AUC macro | 0,9824 | **0,9864** | — |
| AP macro | 0,8627 | **0,8729** | — |
| Precisión macro | **0,8477** | 0,8465 | 0,8363 |
| F1 macro | **0,8420** | 0,8410 | 0,8394 |

**TTA mejora la separación pero no las decisiones.** Sube el AUC y el AP —el
modelo ordena mejor— pero en el punto de operación, con cualquier umbral, la
precisión y la F1 no mejoran. Cuesta el doble de tiempo por nada, así que no
se aplicó.

Es una distinción que conviene tener clara: **AUC no es precisión.** El AUC
mide si el modelo sabe ordenar de más a menos probable; la precisión mide
cuántas de las alertas que emite son ciertas. Se puede mejorar la primera sin
tocar la segunda, y eso es exactamente lo que hace el TTA aquí.

---

## 4. El límite real, y no es de configuración

| Clase | AUC | AP | Diagnóstico |
|---|---|---|---|
| `macrosomia_fetal` | **0,838** | 0,343 | El modelo no separa bien esta clase |
| `polihidramnios` | 0,959 | 0,331 | Era el umbral — ya corregido |
| Las otras 12 | 0,985 – 1,000 | 0,80 – 1,00 | Bien |

`macrosomia_fetal` tiene el AUC más bajo de las catorce. El AUC no depende del
umbral, así que ningún ajuste lo mejora: recalibrar la llevó de F1 0,305 a
0,429 y ahí se acaba. Subirla de verdad necesita **más y mejores imágenes de
entrenamiento**, no configuración.

Es honesto decirlo así en la defensa: el sistema reconoce trece de catorce
patologías con separación casi perfecta, y en la catorce se sabe exactamente
por qué falla y qué haría falta.

---

## 5. Cómo reproducir estas cifras

Los scripts de medición no se versionan (son de análisis, no de producción),
pero el procedimiento es:

1. Cargar `HybridEfficientNetB4` con los pesos de `MODEL_PATHS`.
2. Recorrer `datasets_pathology_v2/test` con `_numpy_to_tensor`, que es el
   mismo preprocesado del microservicio. **Sin esto las cifras serían de otro
   sistema.**
3. Aplicar `sigmoid(logits / INFERENCE_TEMPERATURE)` y los umbrales de
   `CLASS_THRESHOLDS`.
4. Para calibrar: buscar el umbral de mejor F1 sobre `valid/` y reportar sobre
   `test/`. Nunca calibrar y medir sobre el mismo conjunto.

Los umbrales calibrados están fijados por `test_umbrales_calibrados.py`: si
alguien los cambia sin volver a medir, la suite falla.
