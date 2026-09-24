# Redes neuronales con ecografías reales

Dos redes convolucionales entrenadas con ecografías **reales**, cada una con la
anotación de un experto, y ya conectadas al sistema.

| Red | Qué hace | Tipo | Resultado en madres que no vio |
|---|---|---|---|
| Circunferencia cefálica | Mide la cabeza en mm y da la edad gestacional (Hadlock 1984) | Regresión | **R² 0,978** · error medio 7,0 mm · 0,62 semanas (146 imágenes, 117 madres) |
| Plano anatómico | Dice si la imagen es abdomen, cerebro, fémur, tórax, cuello uterino u otro | Clasificación, 6 clases | **92,7 % de aciertos** · AUC 0,992 · 4.887 de 5.271 bien (896 madres) |

Ninguna madre está a la vez en entrenamiento y en prueba: el reparto se hizo
por paciente, no por imagen.

## Qué hay

| Archivo | Qué es |
|---|---|
| `redes_ecografia_real.ipynb` | El notebook completo en 7 pasos, ejecutado: los **4 modelos** (regresión y clasificación del peso al nacer con 1.000 nacimientos reales, y las dos redes), 16 gráficas con una tabla que explica cada una, comparación con un modelo no supervisado (K-means) y revisión automática de errores y falsos positivos. |
| `catalogo_imagenes.xlsx` | Una fila por imagen: hojas HC18, Planos, Diccionario y Fuentes. |
| `preparar_imagenes.py` | Descomprime los zips y construye el catálogo y la carpeta `imagenes/`. |
| `cnn_ecografia.py` | Carga, aumento de datos, EfficientNet-B0 y entrenamiento de las dos redes. |
| `modelos/*.json` | La ficha de cada red. Los `.pth` (16 MB cada uno) no se suben a git: se regeneran con el notebook. |
| `imagenes/` | 13.399 imágenes, 2,1 GB. No se sube a git: se regenera con `preparar_imagenes.py`. |

## De dónde salen las imágenes

- **HC18** — 999 ecografías de cabeza fetal de 779 madres, con la circunferencia
  medida por ecografistas del Radboud UMC (Países Bajos). Zenodo 1327317,
  licencia CC BY 4.0.
- **FETAL_PLANES_DB** — 12.400 ecografías de 1.792 madres de dos hospitales de
  Barcelona, con el plano anotado por un médico. Zenodo 3904280, CC BY 4.0.

Los zips van en `../nuveos data seeds/`.

## Cómo reconstruirlo

Con el Python que tiene PyTorch y la GPU:

```
python preparar_imagenes.py
jupyter notebook redes_ecografia_real.ipynb      # kernel «fetal-gpu»
copy modelos\*.pth ..\Backend\Microservicio_IA\trained_models\
copy modelos\*.json ..\Backend\Microservicio_IA\trained_models\
```

## Dónde está en el sistema

- Microservicio (puerto 8001): `POST /api/plano-anatomico` y
  `POST /api/biometria/circunferencia-cefalica` — código en
  `Backend/Microservicio_IA/app/ecografia_real.py`.
- Django: `POST /api/ecografias/plano-anatomico/` y
  `/api/ecografias/circunferencia-cefalica/`.
- Pantalla: **IA Médica → Análisis CNN**, tarjeta «Redes entrenadas con
  ecografías reales».
- Tests: `Backend/Microservicio_IA/test_ecografia_real.py` pasa el conjunto de
  prueba entero por la API y exige el mismo error que el notebook (da 6,98 mm).

## Límites, dichos claramente

- Para medir la cabeza hace falta el **tamaño de píxel** en mm. Lo da el
  ecógrafo o la cabecera DICOM; una foto de la pantalla no lo trae.
- La medida solo vale sobre el **corte transtalámico** de la cabeza.
- El clasificador de planos se entrenó con imágenes de Barcelona de 18 a 40
  semanas. Sobre las 999 cabezas de HC18 (otro hospital, otros ecógrafos)
  reconoce la cabeza en el 93 % de los casos, pero antes de la semana 14 solo
  en el 59 %. La pantalla lo avisa.
- Las imágenes son de Europa. Antes de usarlo con pacientes en Bolivia hay
  que comprobarlo con ecografías de aquí.
- Es apoyo a la decisión, no un diagnóstico.
