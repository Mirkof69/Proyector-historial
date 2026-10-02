# Microservicio de IA — Fetal Medical Bolivia

Servicio **FastAPI + PyTorch** que analiza ecografías fetales con redes
neuronales convolucionales **entrenadas con ecografías reales y medidas en
pacientes que no vieron**. Cada respuesta lleva la métrica de la red que la
produjo y la huella (sha256) de sus pesos.

> **Uso clínico:** apoyo al diagnóstico. Toda medida y toda alarma la confirma
> el médico (Ley 3131).

## Redes en servicio

| Red | Arquitectura | Datos | Resultado medido en datos no vistos |
|---|---|---|---|
| Plano anatómico (6 planos) | EfficientNet-B0 | FETAL_PLANES_DB, 12.400 imágenes de 1.792 madres | Exactitud 92,7 % en 5.271 imágenes de 896 madres |
| Segmentación de cabeza | U-Net (codificador EfficientNet-B2) | Large-Scale Fetal Head Biometry, 2.833 imágenes de 1.038 pacientes | Dice cráneo 0,968. **Otro hospital (HC18, 999 imágenes):** circunferencia cefálica con error medio 4,4 mm (3,7 %), 92 % dentro del 5 %, R² 0,982 |
| Segmentación de tórax y corazón | U-Net | FOCUS, 300 imágenes | Dice 0,93; índice cardiotorácico ±0,02 |
| Segmentación abdominal | U-Net | Fetal Abdominal Structures, 1.588 imágenes de 169 pacientes | Dice hígado 0,84, vena umbilical 0,77, estómago 0,71, aorta 0,69; estómago visto en el 92 %, vena en el 98 % |
| Segmentación intraparto | U-Net | IUGC MICCAI 2024 (ecografía transperineal), 2.218 imágenes de 48 exámenes | Ángulo de progresión con error medio 6,7° en 300 imágenes de 240 exámenes de otros años (piso del método 3,4°). AoP ≥ 120°: sensibilidad 65 %, especificidad 96 % → se informa como medida |
| Cribado de anomalías cerebrales | EfficientNet-B0 | Fetal Brain Abnormalities + normales de FETAL_PLANES | Falsas alarmas en otro hospital: 1 de 1.866. **Sensibilidad real no medible** con datos públicos |
| Circunferencia cefálica (regresión) | EfficientNet-B0 | HC18 | R² 0,978; error medio 7,0 mm (superada por la segmentación) |

**Ginecología** (02/10/2026, `app/ginecologia.py`, `entrenamiento/ginecologia/`):

| Red | Arquitectura | Datos | Resultado medido en pacientes no vistas |
|---|---|---|---|
| Lesión ovárica (contorno) | U-Net (EfficientNet-B2) | MMOTU, 1.469 imágenes con anatomía patológica | Dice 0,85; lesión encontrada en el 88 % de 436 imágenes |
| Tipo de lesión ovárica (8 clases) | Ensamble de 2 EfficientNet-B0 (recorte de la lesión + imagen entera) | MMOTU | 68,6 % (IC 64–73), AUC 0,91. Va de 80 % (quiste endometriósico, ovario normal) a 43 % (tumor de la teca) |
| Alarma de carcinoma seroso de alto grado | La misma, P ≥ 0,25 fijado de antemano | MMOTU | AUC 0,87; detecta 7 de 13 (54 %), especificidad 97,6 %. **Sin alarma no descarta** |
| Mioma uterino (ubicación) | U-Net (EfficientNet-B2) | Mendeley, 862 imágenes de 788 pacientes | Encontrado en el 96,9 % (IoU de la caja 0,78). Solo úteros con mioma: no descarta |
| Ovario normal / folículo dominante / poliquístico | EfficientNet-B0 | Borna et al. 2025, 295 pacientes | 80,0 % (IC 75–84), 5 pliegues; poliquístico detectado en el 83 % |

Modelos en tabla evaluados y descartados (cáncer cervicouterino por factores de
riesgo, riesgo materno): ver `datos/CATALOGO.md`.

La **EfficientNet-B4 de «14 patologías» se retiró** (01/10/2026): se entrenó
con etiquetas no verificables (ver [datos/CATALOGO.md](datos/CATALOGO.md)) y
no tenía ninguna métrica válida. Su historia queda en
[entrenamiento/b4_retirada/](entrenamiento/b4_retirada/).

Los modelos supervisados tabulares (cardiotocografía y peso al nacer) viven en
el backend Django (`ia_medica/ml/`).

## Flujo del análisis completo

```
imagen → plano anatómico
       ├─ cerebro → segmentación de cabeza (HC, DBP, edad gestacional) + cribado cerebral
       ├─ tórax   → segmentación de tórax y corazón (índice cardiotorácico)
       ├─ abdomen → segmentación abdominal (¿corte adecuado para medir la CA?)
       └─ fémur, cuello uterino, otro → solo el plano: no hay red de medida validada
```

Respuesta: informe en JSON con plano, medidas con su margen, estructuras vistas,
hallazgos, avisos, imagen con las estructuras dibujadas (`superposicion_png`),
redes usadas con sus métricas e `informe_texto`. Ver
[app/analisis_ecografia.py](app/analisis_ecografia.py).

## Endpoints (`/api`)

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/analyze` · `/analisis-ecografia` | Análisis completo (con `tamano_pixel_mm` da milímetros) |
| POST | `/plano-anatomico` | Solo el plano |
| POST | `/segmentacion/{cabeza\|torax\|abdomen\|intraparto}` | Segmentar y medir (intraparto: ángulo de progresión) |
| POST | `/ginecologia/{ovario\|mioma\|ovario-pco}` | Lesión ovárica (contorno, tipo, alarma) · mioma · ovario poliquístico |
| POST | `/biometria/circunferencia-cefalica` | HC por regresión |
| POST | `/anomalias-cerebrales` | Cribado cerebral |
| GET | `/modelos` | Redes disponibles y sus métricas |
| POST | `/quality-check` · `/consultar` | Calidad de imagen · chatbot obstétrico |
| GET | `/health` | 503 si falta la red de plano; informa las redes precargadas al arrancar |

## Instalar y ejecutar

```bash
pip install -r requirements.txt            # servir
pip install -r requirements-entrenamiento.txt   # entrenar y probar
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Al arrancar se precargan las 11 redes en la GPU (≈ 7 s): sin eso la primera
consulta tras cada reinicio superaba los 30 s.

Versiones exactas probadas: [requirements.lock.txt](requirements.lock.txt). Con
mTLS: [start_mtls.sh](start_mtls.sh). Los pesos van en `trained_models/` (fuera
de git).

## Entrenar y medir

| Red | Scripts | Métricas |
|---|---|---|
| Segmentación | `entrenamiento/segmentacion/preparar.py` y `entrenar.py <tarea>` | `entrenamiento/segmentacion/salidas/<tarea>/metricas.json` |
| Intraparto | `entrenamiento/intraparto/preparar.py`, `segmentacion/entrenar.py intraparto`, `intraparto/evaluar.py` | `salidas/intraparto/metricas.json` |
| Plano y HC | `entrenamiento/redes_ecografia_real/` | `LEEME.md` |
| Anomalías cerebrales | `entrenamiento/patologias_cerebrales/` | `INFORME.md` |
| Ginecología | `entrenamiento/ginecologia/`: `auditar.py`, `preparar.py`, `segmentacion/entrenar.py ovario\|mioma`, `clasificar.py`, `mejorar_ovario.py`, `tablas.py`, `exportar.py` | `entrenamiento/ginecologia/salidas/*/metricas.json` |

Reglas: partición por paciente; la época se elige con validación, nunca con la
prueba; prueba externa en otro hospital cuando existe; las pruebas comprueban
que la API reproduce lo medido al entrenar.

## Pruebas

```bash
python -m pytest -q        # 37 pruebas
```
