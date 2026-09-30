# Catálogo de datos de IA — Microservicio_IA/datos

Todo lo que usa (o usó) la IA de imágenes vive aquí. Las imágenes y los zips
no van a git (pesan GB); este catálogo sí.

```
datos/
├── crudos/      tal como se descargaron (zips, xlsx). No se tocan.
├── extraidos/   descomprimidos, listos para leer.
└── legado_b4/   base de la red EfficientNet-B4 anterior. Etiquetas NO fiables (ver abajo).
```

Los scripts de entrenamiento están en `../entrenamiento/`.

## Datasets con imágenes reales y etiquetas verificables

| Dataset | Dónde | Imágenes | Qué etiqueta | Uso | Licencia / cita |
|---|---|---|---|---|---|
| FETAL_PLANES_DB | `crudos/FETAL_PLANES_ZENODO.zip` · `extraidos/fetal_planes_db` | 12.400 de 1.792 pacientes | Plano anatómico (experto) | Red de plano anatómico (92,7 %) | Burgos-Artizzu et al., Sci Rep 2020 · Zenodo 3904280 · CC BY 4.0 |
| HC18 | `crudos/cráneos fetales, 999 imágenes.zip` · `extraidos/hc18` | 999 + 335 | Circunferencia cefálica (ecografista) | Red de circunferencia cefálica (R² 0,978) | van den Heuvel et al., PLoS ONE 2018 · Zenodo 1327317 · CC BY 4.0 |
| Fetal Brain Abnormalities | `crudos/Fetal Brain Abnormalities Ultrasound.v1i.multiclass.zip` · `extraidos/fetal_brain_abnormalities` | 1.768 archivos de **solo 212 imágenes originales** (copias aumentadas ×3–8) | 16 anomalías cerebrales + normal. **Ojo:** las 102 «normales» son cortes de FETAL_PLANES_DB de 31 pacientes (`Patient00738_Plane3_…`) y las anomalías vienen de otras compilaciones, así que normal y anomalía difieren también en el aspecto de la imagen | Red de anomalías cerebrales (`entrenamiento/patologias_cerebrales/`, ver su INFORME.md) | Roboflow Universe, CC BY 4.0 |
| Fetal ultrasound brain | `crudos/fetal-ultrasound-brain.zip` · `extraidos/fetal_ultrasound_brain` | 3.092 | Subplano cerebral | Subconjunto de FETAL_PLANES_DB (cerebros normales) | Igual que FETAL_PLANES_DB |
| Fetal Abdominal Structures | `crudos/Fetal Abdominal Structures Segmentation Dataset.zip` · `extraidos/fetal_abdominal` | 1.588 | Máscaras de estructuras abdominales | Sin usar aún (segmentación) | Mendeley Data, CC BY 4.0 |
| Large-Scale Fetal Head Biometry | `crudos/Large-Scale Annotation Dataset ... Head Biometry ....zip` | 3.832 | Biometría de cabeza | Sin usar aún | Alzubaidi et al., Sci Data 2023 · Zenodo 8265464 · CC BY 4.0 |
| IUGC MICCAI 2024 | `crudos/IUGC MICCAI 2024.zip` | 5.490 imágenes + 774 vídeos | Ecografía intraparto (ángulo de progresión) | Sin usar aún | MICCAI 2024 challenge |
| FOCUS | `crudos/FOCUS-dataset.zip` | 300 | Biometría cardiotorácica de corazones **normales** | Sin usar (no tiene cardiopatías) | Zenodo 14597550 · CC BY 4.0 |
| HC18 variante Kaggle | `crudos/training_set.zip`, `crudos/test_set.zip` | 999 + 335 | Igual que HC18 pero renombrada y re-codificada | Sin usar (se usa la oficial) | — |

Datos tabulares (no son imágenes): `Fetal Health Classification.zip` (cardiotocografía),
`Maternal Health and High-Risk Pregnancy Dataset..zip`, `Idiopathic Polyhydramnios data.1.xlsx`.
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
diagnóstica. Se conserva solo porque la red experimental aún la usa.

## Duplicados eliminados (30/09/2026, a la papelera, verificados por contenido)

`FETAL_PLANES_ZENODO1.zip` (idéntico, anidado), `Datasets.rar` (mismo CRC que el
rar dentro de Ultrasound Fetus), `Fetal Abdominal ... Using Ultrasonic Images.zip`
(subconjunto), `fetal-head-ultrasound-dataset-for-image-segment.zip` (HC18 sin
sus CSV) y `Fetal Brain Abnormalities ....folder.zip` (mismas 1.768 imágenes
que la versión multiclass). Checkpoints del modelo viejo (2,5 GB, 34 épocas):
a la papelera a pedido del usuario.
