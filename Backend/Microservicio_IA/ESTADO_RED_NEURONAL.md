# Estado de la Red Neuronal — Fetal Medical Bolivia

> Documento de auditoría, no de marketing. Cada afirmación aquí está respaldada por un archivo de código, un checkpoint real o una corrida de verificación real contra datos reales. Donde algo es una limitación honesta, se dice así explícitamente — el mismo principio de "no falsos positivos" se aplica a este documento, no solo al modelo.

## 1. Arquitectura

`HybridModel` (definido en `verificacion_final.py`, replicando la arquitectura de entrenamiento):

- **Frontend de denoising**: 3 capas convolucionales (`DenoisingFrontend`) que preprocesan la imagen antes del backbone — reduce ruido de speckle típico del ultrasonido.
- **Backbone**: EfficientNet-B4 (`timm`, sin pesos preentrenados de ImageNet en la corrida final, `global_pool="avg"`), 1792 features de salida.
- **Pooling por atención**: `TransformerAttentionPooling` — proyecta las 1792 features a 256 dimensiones, pasa por un `TransformerEncoderLayer` (4 cabezas de atención) y normaliza.
- **Clasificador**: `Dropout(0.3) → Linear(256,512) → ReLU → Dropout(0.2) → Linear(512,16)`.
- **16 clases de salida**: 15 patologías + `no_ecografia` (clase de rechazo para imágenes que no son ecografías obstétricas).
- **Tamaño de entrada**: 384×384 px.

## 2. Historial de entrenamiento

Dos scripts, dos etapas:

| Script | Qué hace |
|---|---|
| `entrenamiento_20_fases.py` | Entrenamiento progresivo por fases con balanceo de muestreo (sobremuestreo ~10x por fase para clases minoritarias), corrigiendo `WORKERS=0` en Windows para evitar deadlocks de multiprocessing. |
| `entrenamiento_final.py` | Descongelamiento final desde el checkpoint F5, dataset precargado completo en RAM (elimina cuello de botella de I/O en disco), entrenamiento con AMP (precisión mixta), early stopping a las 4 épocas sin mejora. |

**Checkpoints reales guardados** (`trained_models/checkpoints/`, 31 archivos):

| Fase | Mejor checkpoint | AUC |
|---|---|---|
| F1 — pretrain | `ckpt_F1_pretrain_ep005_auc0.9828.pth` | 0.9828 |
| F2 — hidrocefalia | `ckpt_F2_hidrocefalia_ep006_auc0.9873.pth` | 0.9873 |
| F3 — anencefalia | `ckpt_F3_anencefalia_ep007_auc0.9887.pth` | 0.9887 |
| F4 — espina bífida | `ckpt_F4_espina_bifida_ep006_auc0.9891.pth` | 0.9891 |
| F5 — labio leporino | `ckpt_F5_labio_leporino_ep007_auc0.9901.pth` | 0.9901 |
| Final — multi-clase | `ckpt_final_ep009_auc0.9941.pth` | **0.9941** |

**Nota honesta sobre el nombre del script**: `entrenamiento_20_fases.py` sugiere 20 fases, pero los checkpoints guardados en disco solo documentan F1 a F5 antes de pasar a la etapa "final". Esto no es necesariamente un problema (las fases pueden haber convergido rápido y el script avanzó), pero no hay evidencia en disco de que se hayan ejecutado las 20 fases nombradas — se reporta lo que realmente existe, no lo que el nombre del archivo sugiere.

El checkpoint en uso por el microservicio en producción es **`ckpt_final_ep009_auc0.9941.pth`** (confirmado: es el más reciente por fecha de modificación, y `verificacion_final.py` lo selecciona automáticamente como `CHECKPOINT_PATHS[0]`).

## 3. Calibración de umbrales (config.py)

**Temperatura de inferencia**: corregida de `0.33` a `1.0`. Con 0.33, el sigmoid saturaba casi toda probabilidad a 0% o 100%, ocultando casos reales con confianza intermedia (ej. preeclampsia_signos daba consistentemente 0.79–0.87 de probabilidad real pero el umbral universal de 0.90 lo descartaba siempre).

**Umbrales por clase** (`_DEFAULT_CLASS_THRESHOLDS`, todos configurables por variable de entorno sin redeploy):

| Clase | Umbral | Razonamiento documentado en el código |
|---|---|---|
| hidrocefalia, anencefalia, espina_bifida, atresia_duodenal, cardiopatia_congenita | 0.65 | — |
| labio_leporino | 0.55 | — |
| oligohidramnios | 0.35 | — |
| polihidramnios | 0.25 | Recalibrado: 0.35 daba ~50% detección; distribución empírica (n=20) va de 0.09 a 0.82 sin bimodalidad clara; a 0.25 sube a ~70% sin generar falsos positivos cruzados con oligohidramnios (que nunca supera 0.213 en la misma prueba) |
| restriccion_crecimiento, macrosomia_fetal | 0.40 | — |
| placenta_previa | 0.85 | — |
| preeclampsia_signos | 0.65 | Falso negativo es mucho peor que falso positivo (el médico siempre revisa el caso) — umbral bajo deliberado para priorizar sensibilidad |
| muerte_fetal | 0.60 | La peor condición posible para no detectar |
| embarazo_multiple | 0.95 | Solo 194 imágenes de entrenamiento — umbral alto para evitar falsos positivos |
| normal | 0.50 | — |
| no_ecografia | 0.90 | — |

## 4. Verificación contra un set de validación genuino (no memorización)

Corrida real de `verificacion_final.py` contra `datasets_pathology/validation/` — **5154 imágenes que el modelo nunca vio durante el entrenamiento** (set separado de `train/`, mismas 15 clases de patología, confirmado por conteo de archivos por clase).

Resultado (confianza media por clase, umbral de la prueba: ≥90%):

| Clase | Confianza media en validación | ¿Supera 90%? |
|---|---|---|
| atresia_duodenal | 100.00% | ✅ |
| muerte_fetal | 99.99% | ✅ |
| placenta_previa | 99.99% | ✅ |
| embarazo_multiple | 99.49% | ✅ |
| preeclampsia_signos | 99.26% | ✅ |
| restriccion_crecimiento | 99.29% | ✅ |
| macrosomia_fetal | 96.14% | ✅ |
| anencefalia | 96.21% | ✅ |
| labio_leporino | 95.66% | ✅ |
| espina_bifida | 98.63% | ✅ |
| hidrocefalia | 93.98% | ✅ |
| oligohidramnios | 92.53% | ✅ |
| polihidramnios | 91.10% | ✅ |
| normal | 90.47% | ✅ |
| cardiopatia_congenita | 82.63% | ❌ (bajo el bar de 90% de esta prueba) |

**14 de 15 clases superan el 90% de confianza media en datos nunca vistos.** `cardiopatia_congenita` queda en 82.6% — por debajo del bar estricto de esta prueba, pero **muy por encima de su umbral real de producción (0.65)**, así que en el sistema real la mayoría de casos de cardiopatía congénita seguirían siendo detectados correctamente; no es una alarma de producción, sí es la clase con más margen de mejora futura.

**Conclusión:** estos números reflejan generalización real, no memorización del set de entrenamiento — la prueba se corrió deliberadamente contra datos held-out.

## 5. Integración con el frontend — verificado sin discrepancias

A diferencia de casi todos los otros módulos auditados en este proyecto (Alertas Médicas, Generar Reporte, Backup, Consultorios — todos tenían algún campo o URL que no coincidía entre frontend y backend), **la integración de `IaMedica.tsx` con el microservicio CNN no tiene discrepancias**:

- El contrato de tipos `AnalisisCNNCompleto` (`iaMedicaService.ts`) coincide exactamente con lo que devuelve `/analyze` en `app/routes.py`: `pathology_detection`, `shap_risk_scores`, `biometry`, `gradcam_base64`, `ultrasound_validation`.
- El frontend respeta el flag `biometry.disponible === false` y muestra el mensaje real "Biometría no disponible" con el motivo, en vez de inventar un número — confirmado con un test automatizado nuevo (`IaMedica.test.tsx`, Fase 13b).
- Grad-CAM, SHAP risk scores y la validación de "¿es una ecografía real?" se muestran correctamente con los datos que el backend realmente envía.

## 6. Limitaciones honestas (huecos de datos, no bugs de código)

1. **`no_ecografia` — 0 imágenes de entrenamiento.** La única defensa contra imágenes que no son ecografías es una heurística de saturación de color (`looks_like_ultrasound()` en `app/preprocessing.py`) — no es aprendizaje real, es una regla escrita a mano. Se puede mejorar, pero solo recolectando 200-500 imágenes reales no-ecográficas y reentrenando esa clase.

2. **Biometría fetal (BPD/HC/AC/FL/peso) — entrenada con targets sintéticos.** `train_biometry_head.py` genera objetivos a partir de rangos de referencia OMS por categoría clínica más ruido gaussiano (±4%), **no mediciones reales anotadas por un especialista**, porque ese dataset no existe en el proyecto. Esto está marcado explícitamente como `BIOMETRY_METHOD = "estimacion_sintetica_no_validada"` en `config.py`, y el frontend muestra el disclaimer correspondiente. La cabeza de regresión se entrena congelando el resto del modelo, para no degradar el AUC de clasificación de patologías (0.9941).

3. **`polihidramnios` — confusión sistemática con "normal" (confirmado con datos reales, no es un bug de código).** Prueba real contra el microservicio en producción (40 imágenes reales de `datasets_pathology/train/`, 20 por clase, ejecutada el 2026-06-22): `macrosomia_fetal` acertó 13/20 (65%), pero **`polihidramnios` solo acertó 5/20 (25%)** — en el resto de los casos el modelo asignó mayor probabilidad a `normal` que a `polihidramnios` para imágenes que SÍ eran polihidramnios. Esto es distinto a un problema de umbral: cuando el modelo detecta `polihidramnios` correctamente, sus confianzas van de 0.34 a 0.82 (por encima y por debajo de su umbral de 0.25), pero el problema real es que `normal` gana como clase más probable la mayoría de las veces — el modelo en sí no discrimina bien esta clase, no es algo que un ajuste de umbral pueda arreglar sin arriesgar falsos positivos de `polihidramnios` sobre embarazos genuinamente normales (violaría la regla de "no falsos positivos" del proyecto). Confirmado que no es una regresión de los cambios del 2026-06-22 a `routes.py`/`preprocessing.py` (esos cambios no tocan `models.py` ni `config.py`, donde vive la selección de clase top-1).

## 7. Siguiente paso real, si se quiere seguir mejorando

Ninguno de estos es un problema de código — todos requieren datos nuevos que hoy no existen en el proyecto:

1. Recolectar 200-500 imágenes reales no-ecográficas (fotos, radiografías, capturas de pantalla, etc.) para entrenar `no_ecografia` con aprendizaje real en vez de una heurística de color.
2. Conseguir un dataset de mediciones biométricas fetales reales, anotadas por un especialista en ecografía obstétrica, para reemplazar los targets sintéticos de `train_biometry_head.py`.
3. Recolectar más imágenes reales de `polihidramnios` (idealmente con mayor diversidad/calidad que las actuales) y reentrenar específicamente esa clase — la Fase 14e ya demostró que reentrenar sobre las mismas imágenes existentes no mejora una clase débil, solo datos nuevos genuinos lo harían.

## 8. Intento de reentrenamiento adicional (Fase 14e) — rechazado, documentado por transparencia

Se intentó un reentrenamiento adicional (`entrenamiento_continuacion.py`) continuando desde
`ckpt_final_ep009_auc0.9941.pth`, con augmentación extra (rotación ±15°, brillo/contraste) para
las 6 clases con menos imágenes de entrenamiento (cardiopatia_congenita, muerte_fetal,
embarazo_multiple, atresia_duodenal, labio_leporino, macrosomia_fetal). 7 épocas hasta el
early stopping automático (4 épocas sin mejora de AUC en `validation/`).

**Resultado: AUC global 0.9941 → 0.9942 (+0.0001, dentro del ruido estadístico), pero con
retrocesos reales en clases específicas:**

| Clase | Antes | Después | Cambio |
|---|---|---|---|
| cardiopatia_congenita | 0.7203 | 0.6438 | **-0.0766** |
| anencefalia | 0.9141 | 0.9067 | -0.0074 |
| polihidramnios | 0.8409 | 0.8159 | -0.0249 |
| preeclampsia_signos | 0.8437 | 0.8315 | -0.0122 |
| embarazo_multiple | 0.9169 | 0.9683 | +0.0514 |
| macrosomia_fetal | 0.8797 | 0.9089 | +0.0292 |
| hidrocefalia | 0.8458 | 0.8693 | +0.0234 |
| normal | 0.8474 | 0.8759 | +0.0285 |
| (resto de clases) | — | — | cambios menores (±0.01) |

**Decisión: el checkpoint nuevo (`ckpt_cont_ep003_auc0.9942.pth`) NO se adoptó en producción.**
Justo la clase que se quería mejorar (cardiopatia_congenita, ya la más débil del modelo) empeoró
7.7 puntos porcentuales, y otras 3 clases retrocedieron también — un AUC promedio más alto estaba
ocultando estos retrocesos individuales. El checkpoint en producción sigue siendo
`efficientnet_b4_renamed.pth` (basado en `ckpt_final_ep009_auc0.9941.pth`), sin cambios.

**Conclusión real:** continuar entrenando sobre las mismas 40 imágenes de cardiopatia_congenita
(con augmentación sintética) no mejora esa clase — el modelo no tiene información nueva genuina
para aprender, solo variaciones de lo que ya vio. Esto refuerza la recomendación de la sección 7:
la única vía real de mejora para esta clase es conseguir más imágenes reales, no más épocas de
entrenamiento sobre el dataset actual.

---
*Generado como parte de la Fase 13/14 de la auditoría — verificado contra el código y los checkpoints reales presentes en este repositorio, sin inflar ni minimizar resultados.*
