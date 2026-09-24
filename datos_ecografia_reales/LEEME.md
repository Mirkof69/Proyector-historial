# Modelos supervisados de Fetal Medical Bolivia

Todo en una carpeta: el notebook, las muestras, el documento para el docente
y el código de entrenamiento. Los cuatro modelos ya están conectados al sistema.

| Modelo | Qué hace | Tipo | Datos | Resultado |
|---|---|---|---|---|
| 1. Peso al nacer | Gramos al nacer, sin ecografía | Regresión | 1.000 nacimientos **reales** (CDC 2014) | R² 0,322 (el techo sin ecografía) |
| 1b. Peso al nacer con ecografía de ingreso | Gramos al nacer, con la ecografía de los 7 días previos | Regresión | 513 partos **simulados** del sistema | R² 0,836 (estudio real de Lima: 0,847–0,873) |
| 2. Bajo peso | Alerta si nacerá con < 2.500 g | Clasificación | 1.000 nacimientos reales | 73 de 85 detectados, 296 falsas alarmas |
| 3. Red: cabeza | Mide la cabeza en mm y da las semanas (Hadlock 1984) | Regresión con red neuronal | 999 ecografías reales (HC18) | **R² 0,978** · 7,0 mm de error |
| 4. Red: plano | Abdomen, cerebro, fémur, tórax, cuello uterino u otro | Clasificación con red neuronal | 12.400 ecografías reales | **92,7 %** · AUC 0,992 |

Ninguna madre está a la vez en entrenamiento y en prueba.

## Qué hay

| Archivo | Qué es |
|---|---|
| `redes_ecografia_real.ipynb` | **El notebook completo**, 7 pasos, ejecutado: los 4 modelos, 17 gráficas con una tabla que explica cada una, comparación con un modelo no supervisado (K-means), revisión automática de errores y el R² con ecografía (paso 7.8). |
| `Guia_notebook_modelos.docx` | El documento para el docente: dónde está cada tema en el notebook, qué predice cada modelo y los resultados. |
| `datos/nacimientos_reales_2014.xlsx` | Muestra de 1.000 nacimientos reales, en español (hojas Nacimientos, Diccionario, Fuente). |
| `datos/births14.csv` | Los mismos nacimientos, tal como se descargaron de OpenIntro. |
| `datos/partos_ecografia_ingreso_simulados.csv` | Muestra de 513 partos simulados del sistema con ecografía de ingreso. Es una copia de `Backend/datasets/peso_nacimiento_ingreso.csv`. |
| `catalogo_imagenes.xlsx` | Muestra de imágenes: una fila por imagen (hojas HC18, Planos, Diccionario, Fuentes). |
| `preparar_nacimientos.py` | Vuelve a descargar los nacimientos y a construir su Excel. |
| `preparar_imagenes.py` | Descomprime los zips de imágenes y construye el catálogo y `imagenes/`. |
| `cnn_ecografia.py` | Carga, aumento de datos, EfficientNet-B0 y entrenamiento de las dos redes. |
| `modelos/*.json` | La ficha de cada red. Los `.pth` (16 MB cada uno) no se suben a git: se regeneran con el notebook. |
| `imagenes/` | 13.399 imágenes, 2,1 GB. No se sube a git: se regenera con `preparar_imagenes.py`. |

## De dónde salen los datos

- **Nacimientos**: registros de natalidad de EE. UU. 2014 (CDC), muestra `births14` de OpenIntro, libre para docencia.
- **HC18**: 999 ecografías de cabeza de 779 madres, medidas por ecografistas del Radboud UMC. Zenodo 1327317, CC BY 4.0.
- **FETAL_PLANES_DB**: 12.400 ecografías de 1.792 madres de Barcelona, con el plano anotado. Zenodo 3904280, CC BY 4.0.
- **Partos con ecografía de ingreso**: generados por el simulador del sistema (`seed_carga`), calibrado con curvas publicadas. No es una medición clínica.

Los zips de imágenes van en `../nuveos data seeds/`.

## Cómo reconstruirlo

Con el Python que tiene PyTorch y la GPU (kernel «Python 3.12 (GPU · Fetal Medical)»):

```
python preparar_nacimientos.py
python preparar_imagenes.py
jupyter notebook redes_ecografia_real.ipynb
copy modelos\*.pth ..\Backend\Microservicio_IA\trained_models\
copy modelos\*.json ..\Backend\Microservicio_IA\trained_models\
```

El modelo de peso del sistema se entrena desde `Backend/`:

```
python manage.py construir_dataset_peso --max-dias 7 --salida datasets/peso_nacimiento_ingreso.csv
python manage.py entrenar_modelo_peso --dataset datasets/peso_nacimiento_ingreso.csv --version-modelo 1.1.0
```

## Dónde está en el sistema (producción)

| Modelo | Servicio | Pantalla |
|---|---|---|
| Peso al nacer | `POST /api/ia/prediccion-peso/` (`Backend/ia_medica/ml/servicio_peso.py`), modelo en `Backend/ml_modelos/peso_nacimiento/<versión>/` | Ecografías → detalle → pestaña **Biometría Fetal** → «Peso al nacer previsto» (médicos) |
| Red: cabeza | Microservicio `POST /api/biometria/circunferencia-cefalica` → Django `/api/ecografias/circunferencia-cefalica/` | **IA Médica → Análisis CNN** |
| Red: plano | Microservicio `POST /api/plano-anatomico` → Django `/api/ecografias/plano-anatomico/` | **IA Médica → Análisis CNN** |

Comprobado en vivo: la API de peso da exactamente lo mismo que el modelo sobre la
fila con la que se entrenó (5 de 5), y la API de la cabeza reproduce el error del
notebook (6,98 mm). Los modelos (`ml_modelos/`, `trained_models/`) no se suben a
git: al desplegar hay que copiarlos o volver a entrenarlos.

## Límites, dichos claramente

- El peso al nacer con ecografía está entrenado con partos **simulados**. La
  pantalla lo avisa. Para uso clínico hay que reentrenarlo con partos reales,
  que el sistema ya registra.
- Para medir la cabeza hace falta el **tamaño de píxel** en mm (ecógrafo o DICOM).
- El clasificador de planos reconoce el 93 % de las cabezas de otro hospital, y
  solo el 59 % antes de la semana 14. La pantalla lo avisa.
- Datos de EE. UU. y Europa: antes de usarlos con pacientes en Bolivia hay que
  comprobarlos con datos de aquí. Es apoyo a la decisión, no un diagnóstico.
