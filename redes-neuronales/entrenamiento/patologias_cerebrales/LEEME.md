# Red de anomalías cerebrales fetales

Cribado sobre un corte axial de la cabeza fetal: **normal** o una de cuatro
familias de anomalía. Sustituye, para el cerebro, a las clases de la
EfficientNet-B4 anterior, cuyas etiquetas no eran verificables (ver
`../../datos/CATALOGO.md`).

| Familia | Anomalías que agrupa |
|---|---|
| Ventriculomegalia / hidrocefalia | leve, moderada, severa, hidranencefalia, colpocefalia |
| Fosa posterior | hipoplasia cerebelosa, Arnold-Chiari, megacisterna magna |
| Encefalocele | encefalocele |
| Lesión quística, hemorrágica o vascular | quiste aracnoideo, porencefalia, hemorragia, tumor, vena de Galeno, holoprosencefalia |

Se agrupan porque hay entre 1 y 21 imágenes por anomalía: con tan pocas no se
puede medir cada una por separado sin inventar precisión.

## Cómo se entrena (en orden)

```bash
# Python con torch + timm + GPU (en este equipo: Python312 del sistema)
python preparar.py    # salidas/manifiesto.csv: pliegues por imagen original
python entrenar.py    # 5 pliegues (80/20) + modelo final, ~35 min en una RTX 3090
python prueba_otro_hospital.py   # falsas alarmas en las 999 cabezas normales de HC18
python prueba_estilo.py          # ¿mira el cerebro o el aspecto de la imagen?
python evaluar.py     # salidas/metricas.json + INFORME.md (se genera, no se edita)
python exportar.py    # ../../../modelos-ia/redes/anomalias_cerebrales_fetales.pth + .json
```

Después, en el microservicio:
`python -m pytest test_anomalias_cerebrales.py -v`: comprueba que la API da
las mismas probabilidades que el entrenamiento.

## Reglas que evitan resultados inflados

1. **Partición por imagen original.** El dataset de Roboflow trae cada imagen
   copiada de 3 a 8 veces con aumentos, y sus particiones train/test comparten
   copias de la misma imagen en el 45 % de los casos. Aquí las copias van
   siempre juntas, y se evalúa por imagen original, no por archivo.
2. **80/20 rotando.** Validación cruzada de 5 pliegues: cada imagen se prueba
   una vez con una red que no la vio, y todas se usan para entrenar.
3. **Nada se ajusta mirando la prueba.** Arquitectura, épocas, aumentos y
   umbral (0,5) se fijaron antes. La época se elige con un 15 % de validación
   interna de cada pliegue.
4. **Pruebas fuera del entrenamiento.** Cortes normales de pacientes de
   FETAL_PLANES_DB que nunca se usaron, y las 999 cabezas de HC18 (otro
   hospital, otros ecógrafos), para contar falsas alarmas.
5. **Desconfiar de lo perfecto.** Las «normales» del dataset de Roboflow son
   imágenes de FETAL_PLANES y las anomalías vienen de otras compilaciones: la
   red puede acertar por el aspecto de la imagen. `prueba_estilo.py` lo mide
   poniendo ese aspecto a cabezas normales; la v1 daba alarma en el 46 % y por
   eso la v2 entrena con aumento de estilo en todas las clases. Los 31
   pacientes que estaban en los dos datasets se excluyen.
6. **Si no es una cabeza, no se clasifica.** En el microservicio, el
   clasificador de planos filtra antes: una imagen de fémur o abdomen no puede
   dar una alarma de anomalía cerebral.

## Resultados

En [INFORME.md](INFORME.md), generado por `evaluar.py` a partir de las
predicciones guardadas en `salidas/`.

## Dónde se usa

| Pieza | Dónde |
|---|---|
| Microservicio | `app/ecografia_real.py` → `POST /api/anomalias-cerebrales` |
| Django | `POST /api/ecografias/anomalias-cerebrales/` (`ecografias/ai_views.py`) |
| Pantalla | IA Médica y ficha de ecografía → pestaña «IA medida» (`RedesEcografiaReal.tsx`) |

Datos: Fetal Brain Abnormalities (Roboflow Universe, CC BY 4.0) y
FETAL_PLANES_DB (Burgos-Artizzu et al., Sci Rep 2020; Zenodo 3904280; CC BY 4.0).
