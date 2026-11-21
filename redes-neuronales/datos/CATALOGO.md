# Catálogo de datos de IA — Microservicio_IA/datos

Todo lo que usa (o usó) la IA de imágenes vive aquí. Las imágenes y los zips
no van a git (pesan GB); este catálogo sí.

```
datos/
├── crudos/      tal como se descargaron (zips, xlsx). No se tocan.
├── extraidos/   descomprimidos, listos para leer.
├── extraidos/segmentacion/   imágenes y máscaras preparadas por entrenamiento/segmentacion/preparar.py
├── crudos/ginecologia/ · extraidos/ginecologia/   MMOTU, miomas, ovario poliquístico, tablas UCI
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

## Obstetricia, segunda tanda (añadido el 02/10/2026)

En `crudos/obstetricia/` (zips originales con checksum verificado) y `extraidos/obstetricia/`.

| Dataset | Registros | Qué etiqueta | Uso y resultado en pacientes no vistas | Licencia / cita |
|---|---|---|---|---|
| Multicentre Fetal Biometry 2026 | 4.513 imágenes de 1.904 pacientes, 4 hospitales, 7 ecógrafos | Extremos de DBP, DOF, diámetros abdominales y fémur marcados por expertos, con mm por píxel | **Longitud del fémur**: error medio 1,3 mm, 92 % dentro del 5 % (353 imágenes, 271 pacientes). **Circunferencia abdominal**: 2,9 % de error relativo, 89 % dentro del 5 % | UCL RDR 10.5522/04/30819911 · **CC BY-NC-SA 4.0 (uso no comercial)** |
| CTU-UHB Intrapartum CTG | 552 monitoreos (Brno) con gasometría umbilical | pH, déficit de base, Apgar | Evaluado y **descartado**: acidemia (pH < 7,15) AUC 0,73 (IC 0,60–0,84), especificidad 33 % para 90 % de sensibilidad; grave (< 7,05) AUC 0,64, peor que 3 rasgos clásicos | PhysioNet · ODC-By 1.0 |
| Term-Preterm EHG Database | 300 electrohisterogramas (Ljubljana), 38 prematuros | Semana del parto | Evaluado y **descartado**: sin sobremuestreo antes de partir, AUC 0,42–0,45 en validación cruzada y 0,61 (IC 0,32–0,87) en prueba: no predice | PhysioNet · ODC-By 1.0 |

Lo que encontró la revisión:
- **Biometría**: el README promete partición por paciente, pero 4 pacientes de
  UCLH (fémur) y 5 (abdomen) aparecen en entrenamiento y prueba: sus 9 y 21
  imágenes de prueba se quitan. Las coordenadas se verificaron dibujándolas.
- **Parto prematuro**: los trabajos que informan 95–99 % con TPEHG sobremuestrean
  (SMOTE/ADASYN) antes de partir; las copias sintéticas de un mismo caso quedan
  a ambos lados. Medido sin esa fuga, no hay señal.

Tercera tanda (02/10/2026, con los enlaces y archivos que trajo el usuario):

| Dataset | Registros | Resultado medido | Decisión |
|---|---|---|---|
| Dataset for Fetus Framework (Shenzhen; Mendeley n2rbrb9t4f, CC BY 4.0) | 1.684 cortes sagitales de 11–13+6 semanas; prueba externa de otra sede (Longhua) | ¿El corte sirve para medir la TN? Ronda 1: 92,3 % en el mismo hospital y **58,3 % en la otra sede**. Ronda 2 (zoom y estilo fijados de antemano): **94,8 %** (AUC 0,99) y **68,6 %** (AUC 0,73) | **No se pone en servicio**: no generaliza a otro centro; habría que afinarla con cortes del propio hospital |
| CARDIUM, tablas clínicas (repositorio BCV-Uniandes, CC BY-NC 4.0) | 1.104 gestantes, 74 con cardiopatía | Solo variables maternas: AUC 0,52–0,65 en validación cruzada; 0,70 en prueba con especificidad 17–34 % a sensibilidad 87 % (VPP 7–9 %) | **Descartado**: sin imágenes no sirve |
| Term-Preterm EHG DataSet with Tocogram (PhysioNet) | 26 registros de 18 embarazos | Demasiado pequeño para cambiar la conclusión de TPEHG | Guardado, no usado |

La biometría propia coincide con lo que publica el artículo del dataset (Di Vece
et al., Sci Rep 2026): su modelo multicéntrico (BiometryNet) tiene una mediana de
error en fémur de alrededor de 1 mm en la prueba M-C; el nuestro, 0,6 mm (media
1,3 mm). El artículo también documenta que entrenar en un centro y probar en otro
dispara el error (fémur NME 0,03 → 0,90): la misma lección que la translucencia nucal.

Pedidos que necesitan un formulario de la institución (no se pueden descargar libremente):

| Dataset | Para qué serviría | Cómo pedirlo |
|---|---|---|
| Heartbeat (1.475 pacientes, ecocardiografía fetal) | Cardiopatías congénitas | Formulario https://forms.gle/QTTn1S7kKxkepVB18 |
| CARDIUM, imágenes (6.558) | Cardiopatías congénitas | Formulario https://docs.google.com/forms/d/e/1FAIpQLSeW3EKB54HnfSVmyOf8yD9swB7DUiaEr0_pSMl6z_zTwdJR-Q/viewform |
| Fetal Ultrasound Grand Challenge ISBI 2025 (cuello uterino) | Longitud cervical → riesgo de parto prematuro | Acuerdo de uso de datos en Zenodo 14305302 (el GitHub maskoffs/Fetal-Ultrasound-Grand-Challenge trae solo el código) |

## Ginecología (añadido el 02/10/2026)

En `crudos/ginecologia/` (zips originales, ver `crudos/LEEME_ZIPS.md`) y
`extraidos/ginecologia/`. Auditoría de copias y fugas antes de entrenar:
`../entrenamiento/ginecologia/auditar.py` → `salidas/auditoria.json`.

| Dataset | Imágenes | Qué etiqueta | Uso y resultado en pacientes no vistas | Licencia / cita |
|---|---|---|---|---|
| MMOTU OTU_2d | 1.469 de 247 pacientes (Beijing Shijitan Hospital) | Contorno de la lesión y tipo en 8 clases, con informe de anatomía patológica (27 especialistas) | **U-Net de lesión ovárica**: Dice 0,85, lesión encontrada en el 88 %. **Clasificador** (ensamble de 2 EfficientNet-B0): 68,6 % en 8 clases (IC 64–73), AUC 0,91; carcinoma seroso de alto grado: AUC 0,87, detecta 7 de 13 (54 %) con 97,6 % de especificidad | Zhao et al., arXiv 2207.06799 · Zenodo 21128657 / Figshare 25058690 · CC BY 4.0 |
| Uterine fibroid ultrasound images | 862 con caja de 788 pacientes | Caja del mioma | **Ubicación del mioma**: encontrado en el 96,9 % (IoU de la caja 0,78). Solo hay úteros CON mioma: no sirve para descartarlo | Mendeley Data n2zcmcypgb v2 · CC BY 4.0 |
| Ovarian ultrasound (Borna et al. 2025) | 295 únicas de pacientes distintas | Normal / folículo dominante / poliquístico (una ginecobstetra) | **Clasificador**: 80,0 % (IC 75–84) con 5 pliegues; poliquístico detectado en el 83 % | Frontiers in Physiology 2025 · GitHub HananSaadat · CC BY 4.0 |

Lo que encontró la auditoría:
- **MMOTU** promete una partición por paciente, pero 37 pares de casi copias la
  cruzan (p. ej. 1290–1291–1292 en entrenamiento y prueba) y 5 pares de casi
  copias tienen **diagnósticos distintos** (716 teratoma / 718 quiste
  endometriósico; 85 quiste / 88 ovario normal): las 10 contradictorias se
  excluyen y de la prueba se quitan 30 casi copias de entrenamiento. La versión
  de Figshare trae solo 1.202 imágenes y máscaras sin tipo: se usa la de Zenodo
  con las etiquetas oficiales del Google Drive de los autores.
- **Miomas**: el XML de cada imagen trae en `<folder>` el **nombre de la
  paciente** (en chino). Se usa solo para agrupar, convertido a un código
  (sha256 truncado); el texto no se guarda en ningún archivo del proyecto.
- **Ovario poliquístico**: 2 copias exactas y 4 casi copias dentro de la misma
  clase; se deja una de cada grupo.

Modelos en tabla evaluados y **descartados** (`../entrenamiento/ginecologia/tablas.py`):

| Dataset | Resultado | Por qué no se usa |
|---|---|---|
| UCI 383 Cáncer cervicouterino (858 pacientes, Caracas) | Solo factores de riesgo: AUC 0,60 (IC 0,38–0,81). Con colposcopía, Schiller y citología: AUC 0,87 | El primero no distingue; el segundo pierde contra la regla «alguna prueba positiva» (sensibilidad 91 %, especificidad 92 %) |
| UCI 863 Riesgo materno (Bangladés) | 1.014 filas, 562 duplicadas y 71 contradictorias; 71 % de exactitud balanceada | Etiqueta sin criterio documentado y riesgo medio mal separado |

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
