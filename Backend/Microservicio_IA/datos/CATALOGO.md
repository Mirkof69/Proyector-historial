# Catálogo de datos de IA — Microservicio_IA/datos

Todo lo que usa (o usó) la IA de imágenes vive aquí. Las imágenes y los zips
no van a git (pesan GB); este catálogo sí.

```
datos/
├── crudos/      tal como se descargaron (zips, xlsx). No se tocan.
├── extraidos/   descomprimidos, listos para leer.
├── extraidos/segmentacion/   imágenes y máscaras preparadas por entrenamiento/segmentacion/preparar.py
└── legado_b4/   base de la EfficientNet-B4 RETIRADA. Etiquetas NO fiables (ver abajo).
```

Los scripts de entrenamiento están en `../entrenamiento/`.

## Datasets con imágenes reales y etiquetas verificables

| Dataset | Dónde | Imágenes | Qué etiqueta | Uso | Licencia / cita |
|---|---|---|---|---|---|
| FETAL_PLANES_DB | `crudos/FETAL_PLANES_ZENODO.zip` · `extraidos/fetal_planes_db` | 12.400 de 1.792 pacientes | Plano anatómico (experto) | Red de plano anatómico (92,7 %) | Burgos-Artizzu et al., Sci Rep 2020 · Zenodo 3904280 · CC BY 4.0 |
| HC18 | `crudos/cráneos fetales, 999 imágenes.zip` · `extraidos/hc18` | 999 + 335 | Circunferencia cefálica (ecografista) | Red de circunferencia cefálica (R² 0,978) | van den Heuvel et al., PLoS ONE 2018 · Zenodo 1327317 · CC BY 4.0 |
| Fetal Brain Abnormalities | `crudos/Fetal Brain Abnormalities Ultrasound.v1i.multiclass.zip` · `extraidos/fetal_brain_abnormalities` | 1.768 archivos de **solo 212 imágenes originales** (copias aumentadas ×3–8) | 16 anomalías cerebrales + normal. **Ojo:** las 102 «normales» son cortes de FETAL_PLANES_DB de 31 pacientes (`Patient00738_Plane3_…`) y las anomalías vienen de otras compilaciones, así que normal y anomalía difieren también en el aspecto de la imagen | Red de anomalías cerebrales (`entrenamiento/patologias_cerebrales/`, ver su INFORME.md) | Roboflow Universe, CC BY 4.0 |
| Fetal ultrasound brain | `crudos/fetal-ultrasound-brain.zip` · `extraidos/fetal_ultrasound_brain` | 3.092 | Subplano cerebral | Subconjunto de FETAL_PLANES_DB (cerebros normales) | Igual que FETAL_PLANES_DB |
| Fetal Abdominal Structures | `crudos/Fetal Abdominal Structures Segmentation Dataset.zip` · `extraidos/segmentacion/abdomen` | 1.588 de 169 pacientes | Máscaras de hígado, estómago, vena umbilical y aorta | **Segmentación abdominal** (Dice 0,69–0,84) | Mendeley Data, CC BY 4.0 |
| Large-Scale Fetal Head Biometry | `crudos/Large-Scale Annotation Dataset ... Head Biometry ....zip` · `extraidos/segmentacion/cabeza` | 2.833 de FETAL_PLANES (1.038 pacientes) + 999 que son HC18 reescaladas | Máscaras de cráneo, cavum y ventrículo lateral + tamaño de píxel | **Segmentación de cabeza** (Dice cráneo 0,968; HC en HC18 ±4,4 mm). Las 999 de HC18 NO se usan para entrenar: son la prueba externa | Alzubaidi et al., Sci Data 2023 · Zenodo 8265464 · CC BY 4.0 |
| IUGC MICCAI 2024 | `crudos/IUGC MICCAI 2024.zip` | 5.490 imágenes + 774 vídeos | Ecografía intraparto (sínfisis del pubis, cabeza fetal, ángulo de progresión) | **Segmentación intraparto y ángulo de progresión** (`entrenamiento/intraparto/`): error medio 6,7° en la prueba oficial | MICCAI 2024 challenge (uso para investigación; no se versionan sus imágenes) |
| FOCUS | `crudos/FOCUS-dataset.zip` · `extraidos/segmentacion/torax` | 300 | Máscaras de tórax y corazón (todos **normales**) | **Segmentación de tórax** (Dice 0,93; índice cardiotorácico ±0,02). Mide; no puede validar la detección de cardiomegalia | Zenodo 14597550 · CC BY 4.0 |
| HC18 variante Kaggle | `crudos/training_set.zip`, `crudos/test_set.zip` | 999 + 335 | Duplicado de HC18 renombrado y re-codificado | No se usa (se usa la oficial) | — |

Datos tabulares (no son imágenes):

| Dataset | Registros | Uso |
|---|---|---|
| `Fetal Health Classification.zip` (cardiotocografía SisPorto, consenso de 3 obstetras) | 2.126 | **Clasificador de CTG** en el backend (`ia_medica/ml/cardiotocografia.py`): exactitud 96,0 % en 423 registros no vistos |
| `Maternal Health and High-Risk Pregnancy Dataset..zip` (registro ANC de Bangladés) | 999 | No se usa: trae **nombres reales** de pacientes, encabezados en bengalí y una etiqueta «alto riesgo» sin criterio documentado |
| `Idiopathic Polyhydramnios data.1.xlsx` | 103 | No se usa: estudio de casos y controles demasiado pequeño para entrenar |
El modelo supervisado de peso al nacer usa sus propios datos en
`../entrenamiento/redes_ecografia_real/datos/`.

## Datos NO fiables — no usar para entrenar ni para medir

`crudos/imagenes_web_sin_verificar/`: imágenes sueltas de la web (Radiopaedia y
similares) sin paciente ni etiqueta verificada. La carpeta «Oligohydramnios»
contiene sobre todo anomalías renales; «placenta previa» mezcla vasa previa,
placenta percreta y lóbulo succenturiado.

`crudos/Ultrasound Fetus Dataset ....zip` (Kaggle, un .rar de 910 MB): sus
carpetas «benign», «malignant» y «normal» son **imágenes de HC18** (cabezas
fetales normales del Radboud): 2.668 de 2.966 idénticas byte a byte, con los
mismos nombres (`100_HC.png`, `_Annotation.png`). Las etiquetas son inventadas.
Revisado el 30/09/2026; no usar.

`legado_b4/` (datasets_pathology y _v2), base de la EfficientNet-B4 anterior.
Auditoría del 30/09/2026 sobre `_v2/_inventario.csv`:

| Clase | Problema |
|---|---|
| atresia duodenal, labio leporino, macrosomía, muerte fetal, polihidramnios | 100 % imágenes **sintéticas** |
| espina bífida, anencefalia, oligohidramnios, restricción de crecimiento | mayoría sintéticas o aumentadas |
| **signos de preeclampsia** (1.469) | son **cortes normales de FETAL_PLANES_DB** etiquetados como patología |
| **cardiopatía congénita** (298) | incluye cortes normales de FETAL_PLANES_DB y 171 de FOCUS (corazones normales) |
| placenta previa | mezcla vasa previa, percreta y lóbulo succenturiado |
| hidrocefalia, anencefalia, espina bífida | copias de Roboflow con el **45 %** de las imágenes de prueba presentes también en entrenamiento |

Por eso las métricas históricas de la B4 (AUC 0,96–1,00) no miden capacidad
diagnóstica. La red se retiró el 01/10/2026; esta carpeta queda solo como
registro y se puede borrar (6,7 GB).

## Duplicados eliminados (30/09/2026, a la papelera, verificados por contenido)

`FETAL_PLANES_ZENODO1.zip` (idéntico, anidado), `Datasets.rar` (mismo CRC que el
rar dentro de Ultrasound Fetus), `Fetal Abdominal ... Using Ultrasonic Images.zip`
(subconjunto), `fetal-head-ultrasound-dataset-for-image-segment.zip` (HC18 sin
sus CSV) y `Fetal Brain Abnormalities ....folder.zip` (mismas 1.768 imágenes
que la versión multiclass). Checkpoints del modelo viejo (2,5 GB, 34 épocas):
a la papelera a pedido del usuario.
