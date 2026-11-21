# Red de anomalías cerebrales fetales — informe de resultados

Generado por `evaluar.py` a partir de `salidas/`. No editar a mano.

## Resumen en cuatro frases

1. Falsas alarmas sobre cabezas **normales** de hospitales que la red no vio:
   0,2 % en 999 cabezas de HC18 (Países Bajos) y
   0,1 % en 1.866 cortes de FETAL_PLANES (Barcelona).
2. Detecta 109 de 110 anomalías
   que no vio, **pero esa cifra no es la sensibilidad real**: en el dataset
   público todas las normales vienen de un hospital y todas las anomalías de
   otras fuentes. La prueba de estilo indica que la v2 no se guía por el
   aspecto de la imagen, pero sin normales y anomalías del mismo hospital no se
   puede medir cuánto acertaría en la práctica.
3. Con las anomalías de fuentes clínicas reales (p. ej. un hospital boliviano)
   la sensibilidad es **desconocida**: no existe un dataset público que permita medirla.
4. Uso posible hoy: **cribado de apoyo** que avisa para que el especialista
   mire otra vez. Nunca descarta una anomalía ni la diagnostica.

## Cómo se midió

- **Datos reales**: 110 imágenes originales con anomalía y 102
  normales (Fetal Brain Abnormalities, Roboflow), más 1.120 cortes
  cerebrales normales de FETAL_PLANES_DB.
- **80 / 20 rotando (5 pliegues)**: cada imagen se prueba una vez con una red
  que no la vio; las copias aumentadas de una misma imagen van siempre juntas.
- Se excluyeron los 31 pacientes de FETAL_PLANES cuyas
  imágenes estaban también en Roboflow con otro nombre.
- Umbral de alarma fijo en 0,5, decidido antes de entrenar. IC95 por bootstrap.

## Normal frente a anomalía (validación cruzada)

| Conjunto | AUC | Sensibilidad | Especificidad | Anomalías detectadas | Falsas alarmas |
|---|---|---|---|---|---|
| Solo Roboflow (normales y anomalías del mismo dataset) | 1,000 (IC95 1,000–1,000) | 99,1 % (IC95 97,0–100,0) | 100,0 % (IC95 100,0–100,0) | 109/110 | 0/102 |
| Todas (con las normales de FETAL_PLANES) | 1,000 (IC95 1,000–1,000) | 99,1 % (IC95 96,8–100,0) | 100,0 % (IC95 100,0–100,0) | 109/110 | 0/1222 |

**Por qué no hay que tomar esto como la sensibilidad real.** Las 102 «normales» de
Roboflow son cortes de FETAL_PLANES_DB (se llaman `Patient00738_Plane3_…`); las
anomalías vienen de compilaciones con otro aspecto. Seis estadísticas del
píxel, sin mirar el cerebro, ya separan las dos clases con AUC 0,84. Una
separación perfecta aquí no demuestra que la red vea las anomalías.

## Falsas alarmas en cabezas normales que la red no vio

| Conjunto | Falsas alarmas |
|---|---|
| HC18 — Radboud UMC, Países Bajos (otro hospital, otros ecógrafos) | **0,2 % (IC95 0,0–0,5)** · 2/999 |
| FETAL_PLANES — pacientes no usados al entrenar | 0,1 % (IC95 0,0–0,2) · 1/1.866 |

HC18 por trimestre (la red se entrenó sobre todo con segundo y tercero):

| Trimestre | Falsas alarmas |
|---|---|
| primero | 1/153 |
| segundo | 1/701 |
| tercero | 0/145 |

## Prueba de estilo: ¿mira el cerebro o el aspecto de la imagen?

A 300 cabezas **normales** de HC18 se les cambia el aspecto sin tocar la
anatomía. Una red que mira el cerebro no debería alarmarse. La v1 se entrenó
sin aumento de estilo; la v2 (la que se usa) con él. «Foto de pantalla» (JPEG
fuerte, gamma, speckle) no se usó en ningún entrenamiento.

| Aspecto | v1: falsas alarmas | v2: falsas alarmas |
|---|---|---|
| original | 0/300 | 0/300 |
| lavada | 1/300 | 0/300 |
| fondo gris | 1/300 | 0/300 |
| reescalada | 1/300 | 0/300 |
| borrosa | 2/300 | 0/300 |
| todo junto | 139/300 | 0/300 |
| foto de pantalla | 6/300 | 6/300 |

## Qué familia de anomalía (entre las anomalías)

Aquí las dos partes vienen de la misma fuente, así que la cifra es más fiable:
exactitud 67,3 % (IC95 58,2–75,5) con 4 familias.

| Familia | Acertadas |
|---|---|
| Ventriculomegalia / hidrocefalia | 47/56 |
| Fosa posterior | 7/15 |
| Encefalocele | 6/12 |
| Lesión quística, hemorrágica o vascular | 14/27 |

## Detección por anomalía concreta (con la misma reserva que la sensibilidad)

| Anomalía | Detectadas |
|---|---|
| Ventriculomegalia leve | 21/21 |
| Ventriculomegalia moderada | 19/19 |
| Encefalocele | 12/12 |
| Quiste aracnoideo | 9/9 |
| Hipoplasia cerebelosa | 8/8 |
| Porencefalia | 8/8 |
| Ventriculomegalia severa | 8/8 |
| Colpocefalia | 5/6 |
| Hemorragia intracraneal | 5/5 |
| Malformación de Arnold-Chiari | 4/4 |
| Megacisterna magna | 3/3 |
| Aneurisma de la vena de Galeno | 3/3 |
| Hidranencefalia | 2/2 |
| Holoprosencefalia | 1/1 |
| Tumor intracraneal | 1/1 |

## Límites

- 212 imágenes originales, una sola compilación pública de anomalías, sin
  datos de pacientes ni de ecógrafo. Varias anomalías tienen 1–5 imágenes.
- Ninguna ecografía boliviana. Antes de uso clínico: validación local
  prospectiva con anomalías confirmadas.
- Solo cortes axiales de cabeza; el microservicio rechaza otros planos.
