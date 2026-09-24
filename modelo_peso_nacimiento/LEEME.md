# Modelo de peso al nacer — con datos reales

Carpeta aparte del sistema, para estudiar y presentar el modelo de aprendizaje
supervisado de Fetal Medical Bolivia.

## Qué hay

| Archivo | Qué es |
|---|---|
| `modelo_peso_nacimiento.ipynb` | El notebook: qué es Hadlock y los 7 pasos. Ya ejecutado, con las 10 gráficas dentro. |
| `datos/nacimientos_reales_2014.xlsx` | 1.000 nacimientos **reales** en español: hojas Nacimientos, Diccionario y Fuente. |
| `datos/births14.csv` | Los mismos datos, tal como se descargaron. |
| `datos/muestra_simulada_5000.xlsx` | Copia de la muestra **simulada** del sistema, con medidas de ecografía. |
| `preparar_datos.py` | Vuelve a descargar los datos y a construir el Excel. |

## De dónde salen los datos

Nacimientos reales elegidos al azar de los registros de natalidad de Estados
Unidos de 2014 (CDC), publicados por OpenIntro como `births14`, de uso libre
para docencia: <https://www.openintro.org/data/index.php?data=births14>

No tienen medidas de ecografía. Por eso el notebook usa la **curva** de Hadlock
(peso por semana) como referencia, y no la fórmula de cuatro medidas.

## Cómo abrirlo

En VS Code, clic en `modelo_peso_nacimiento.ipynb`. O desde esta carpeta:

```
..\Backend\.venv\Scripts\python.exe -m jupyter notebook modelo_peso_nacimiento.ipynb
```

## Resultados

| | |
|---|---|
| Bebés de bajo peso detectados | **73 de 85 (86%)** |
| Se escaparon | 12 |
| Falsas alarmas | 296 de 915 bebés sanos |
| Error medio del peso | 374 g (curva de Hadlock: 395 g) |

La mayoría de los bebés de bajo peso son **verdaderos positivos**. Se consigue
con el umbral de alerta, y se paga con falsas alarmas: de cada 100 alertas,
unas 20 son bebés de bajo peso. Las semanas de embarazo explican casi todo; los
datos de la madre añaden poco.

Son datos de Estados Unidos. Para usarlo con pacientes en Bolivia hay que
entrenarlo con partos bolivianos: el sistema ya tiene los comandos para eso.
