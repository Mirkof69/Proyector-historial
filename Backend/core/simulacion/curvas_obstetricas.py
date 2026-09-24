"""Simulación de biometría fetal y peso al nacer, con las variables ligadas.

QUÉ ES Y QUÉ NO ES
==================
Esto **no son datos reales**. Es una simulación en la que cada variable se
deriva de las demás siguiendo curvas de crecimiento publicadas. Sirve para:

  - probar el sistema con volumen,
  - comprobar que un pipeline de aprendizaje automático corre de punta a punta,
  - enseñar el flujo completo en una defensa.

**No sirve** para medir cuánto acertaría un modelo en la población boliviana,
ni para publicar una métrica como si fuera un resultado clínico.

Cualquier error medio (MAE) obtenido sobre estos datos es una **cota
optimista**: el simulador genera el peso a partir de las mismas variables que
el modelo va a recibir como entrada, así que el modelo está reaprendiendo la
fórmula que lo generó. Un MAE de 100-150 g aquí no significa 100-150 g en una
clínica. Y si sale por debajo de 50 g, el simulador está filtrando la etiqueta:
el ruido residual es demasiado pequeño y hay que subirlo.

POR QUÉ HIZO FALTA ESCRIBIRLO
=============================
El generador anterior era inservible para aprendizaje automático, por
construcción y no por descuido:

  - `pacientes/management/commands/seed_carga.py:572`
    `peso_nacimiento=random.randint(1800, 4200)`, dentro de
    `_crear_parto(..., semanas)` — que **recibía las semanas de gestación como
    argumento y no las usaba**. La correlación peso↔edad gestacional, que en la
    realidad es de r≈0,8, valía exactamente cero.
  - `seed_carga.py:493-497` — biometría con `_rango(20, 95)`, `_rango(80, 350)`…
    desacoplada de `sem_eco`. Un feto de 12 semanas podía salir con un diámetro
    biparietal de 95 mm, el de uno a término.
  - `seed_carga.py:573-576` — talla, perímetro cefálico y los dos Apgar,
    independientes entre sí y del peso. Un bebé de 1.800 g podía medir 54 cm.
  - `ecografias/management/commands/seed_ecografias.py:76` — `eg_semanas` se
    guardaba en la ecografía y **no se volvía a usar** para nada.

Un modelo entrenado sobre eso aprende ruido, y su métrica es un número sin
significado.

LA IDEA QUE HACE QUE ESTO FUNCIONE
==================================
Un solo **factor latente de tamaño fetal** (`z_tamano`) compartido por todas
las medidas del mismo feto. Ese es el punto: si cada medida se sortea por su
cuenta, no hay un feto, hay cuatro números sueltos. Encima de `z_tamano` se
añade ruido de medición independiente por medida (±2%, que es el error
inter-observador típico de un ecógrafo), y ahí sí cada una se mueve sola.

REFERENCIAS
===========
- Hadlock FP, Harrist RB, Martinez-Poyer J. «In utero analysis of fetal growth:
  a sonographic weight standard». Radiology. 1991;181(1):129-133.
  → percentiles de peso fetal estimado, en `ecografias.peso_fetal`.
- Los valores medios de biometría por semana se conservan de la tabla que ya
  existía en `seeders/management/commands/seed_all.py:1260-1277`, ampliados de
  cada dos semanas a cada semana por interpolación. **Se documenta con
  honestidad: son valores aproximados de referencia, del orden de magnitud
  correcto, no una tabla clínica certificada.** Para un uso clínico real habría
  que cargar las tablas de INTERGROWTH-21st.
"""
from __future__ import annotations

import random
from decimal import Decimal

from ecografias.peso_fetal import TABLA_HADLOCK_1991

#: Medias de biometría fetal por semana de gestación, en milímetros.
#: DBP = diámetro biparietal, CC = circunferencia cefálica,
#: CA = circunferencia abdominal, LF = longitud del fémur.
#:
#: Origen: la tabla de `seed_all.py:1260-1277`, que venía cada dos semanas.
#: Aquí se interpola a cada semana en `biometria_esperada()`.
BIOMETRIA_MEDIA_MM: dict[int, dict[str, float]] = {
    10: {"dbp": 15, "cc": 55, "ca": 45, "lf": 7},
    12: {"dbp": 21, "cc": 75, "ca": 58, "lf": 10},
    14: {"dbp": 28, "cc": 100, "ca": 78, "lf": 15},
    16: {"dbp": 35, "cc": 125, "ca": 100, "lf": 21},
    18: {"dbp": 42, "cc": 150, "ca": 125, "lf": 27},
    20: {"dbp": 49, "cc": 175, "ca": 150, "lf": 33},
    22: {"dbp": 55, "cc": 200, "ca": 175, "lf": 39},
    24: {"dbp": 61, "cc": 220, "ca": 198, "lf": 44},
    26: {"dbp": 67, "cc": 240, "ca": 220, "lf": 49},
    28: {"dbp": 72, "cc": 260, "ca": 240, "lf": 54},
    30: {"dbp": 77, "cc": 278, "ca": 260, "lf": 58},
    32: {"dbp": 82, "cc": 295, "ca": 280, "lf": 62},
    34: {"dbp": 86, "cc": 310, "ca": 300, "lf": 66},
    36: {"dbp": 90, "cc": 325, "ca": 320, "lf": 70},
    38: {"dbp": 93, "cc": 338, "ca": 340, "lf": 73},
    40: {"dbp": 96, "cc": 350, "ca": 358, "lf": 76},
    42: {"dbp": 98, "cc": 356, "ca": 370, "lf": 78},
}

#: Coeficiente de variación del peso fetal alrededor de su mediana.
#: 11% reproduce aproximadamente la distancia entre el p10 y el p90 de la tabla
#: de Hadlock 1991 (que está en torno al ±25% de la mediana ≈ 1,28 sigma).
DISPERSION_PESO = 0.11

#: Factor que convierte «peso fetal estimado por ecografía» en «peso al nacer».
#:
#: La tabla de Hadlock 1991 da peso fetal ESTIMADO IN UTERO, que corre algo por
#: encima del peso real al nacer: su p50 a las 40 semanas son 3.619 g, mientras
#: que la mediana real del peso al nacer a término está en torno a 3.400 g.
#: Usar la tabla sin corregir infla la cola alta — medido: **17,2% de
#: macrosomía** en el primer intento, cuando lo real es entre el 5% y el 10%.
FACTOR_PESO_AL_NACER = 0.945

#: Error de medición del ecógrafo, por medida e independiente entre ellas.
#: Es el error inter-observador típico al medir sobre la imagen.
ERROR_MEDICION = 0.02

#: Desviación del ruido residual del peso al nacer, en gramos.
#: Es la variabilidad que NINGÚN modelo puede explicar a partir de la
#: biometría. Fija el suelo del MAE alcanzable y evita que el dataset sea un
#: problema ya resuelto: sin este término, un modelo bien entrenado daría un
#: MAE cercano a cero y la métrica no significaría nada.
RUIDO_PESO_G = 180


def _limitar(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(maximo, valor))


def biometria_esperada(semanas: float) -> dict[str, float]:
    """Biometría media para esa edad gestacional, en milímetros.

    Interpola linealmente entre las semanas de `BIOMETRIA_MEDIA_MM`, que viene
    cada dos. Por debajo de 10 o por encima de 42 semanas se satura en el
    extremo: extrapolar una curva de crecimiento fuera de su rango produce
    números sin sentido.
    """
    semanas_tabla = sorted(BIOMETRIA_MEDIA_MM)
    s = _limitar(float(semanas), semanas_tabla[0], semanas_tabla[-1])

    if s in BIOMETRIA_MEDIA_MM:
        return dict(BIOMETRIA_MEDIA_MM[int(s)])

    inferior = max(w for w in semanas_tabla if w <= s)
    superior = min(w for w in semanas_tabla if w >= s)
    if inferior == superior:
        return dict(BIOMETRIA_MEDIA_MM[inferior])

    peso_sup = (s - inferior) / (superior - inferior)
    a, b = BIOMETRIA_MEDIA_MM[inferior], BIOMETRIA_MEDIA_MM[superior]
    return {k: a[k] + (b[k] - a[k]) * peso_sup for k in a}


def peso_mediano_por_semana(semanas: float) -> float:
    """Mediana del peso fetal estimado a esa edad gestacional, en gramos.

    Sale del percentil 50 de la tabla de Hadlock 1991, interpolando entre
    semanas completas.
    """
    semanas_tabla = sorted(TABLA_HADLOCK_1991)
    s = _limitar(float(semanas), semanas_tabla[0], semanas_tabla[-1])
    inferior, superior = int(s), min(int(s) + 1, semanas_tabla[-1])
    p50_inf = TABLA_HADLOCK_1991[inferior][1]
    p50_sup = TABLA_HADLOCK_1991[superior][1]
    return p50_inf + (p50_sup - p50_inf) * (s - inferior)


def sortear_z_tamano(rng: random.Random | None = None) -> float:
    """Factor latente de tamaño de un feto, N(0,1) recortado a ±2,5.

    Se sortea **una vez por embarazo** y se reutiliza en todas las ecografías y
    en el peso al nacer. Es lo que hace que las medidas del mismo feto se
    parezcan entre sí y al peso final. El recorte a ±2,5 evita generar fetos
    imposibles en las colas.
    """
    rng = rng or random
    return _limitar(rng.gauss(0, 1), -2.5, 2.5)


def simular_biometria(
    semanas: float, *, z_tamano: float, rng: random.Random | None = None,
) -> dict[str, Decimal]:
    """Biometría fetal en milímetros, coherente con la edad gestacional.

    Cada medida es `media(semanas) * (1 + dispersion*z) * (1 + error)`, donde
    `z` es el mismo para las cuatro (el feto es grande o pequeño en su
    conjunto) y `error` es independiente (el ecografista mide cada plano por
    separado).

    Devuelve `Decimal` porque los campos de `BiometriaFetal` son
    `DecimalField` y pasarles float acarrea avisos de precisión.
    """
    rng = rng or random
    esperada = biometria_esperada(semanas)
    factor_tamano = 1 + DISPERSION_PESO * z_tamano

    resultado: dict[str, Decimal] = {}
    for clave, media in esperada.items():
        error = rng.gauss(0, ERROR_MEDICION)
        valor = media * factor_tamano * (1 + error)
        # Las medidas biométricas no pueden ser negativas ni absurdas; el
        # recorte inferior a 1 mm es una guarda, no una regla clínica.
        resultado[clave] = Decimal(str(round(max(1.0, valor), 1)))
    return resultado


def simular_peso_nacimiento(
    *,
    semanas_parto: float,
    z_tamano: float,
    imc_materno: float = 24.0,
    paridad: int = 0,
    diabetes: bool = False,
    hipertension: bool = False,
    gemelar: bool = False,
    sexo: str = "femenino",
    rng: random.Random | None = None,
) -> int:
    """Peso al nacer en gramos, derivado de la misma `z_tamano` que la biometría.

    Modelo:
        peso = p50(semanas) * (1 + 0,11·z) * modificadores + ruido

    Los modificadores llevan la dirección y el orden de magnitud descritos en
    la literatura obstétrica. No pretenden ser coeficientes de un estudio
    concreto; pretenden que las variables del dataset tengan un efecto
    aprendible y clínicamente sensato:

      - IMC pregestacional > 30      +120 g
      - multípara (paridad ≥ 1)      +100 g
      - diabetes (previa o gestac.)  +230 g
      - hipertensión / preeclampsia  −200 g
      - gemelar                      −700 g
      - sexo masculino               +120 g

    La mediana de partida se corrige por `FACTOR_PESO_AL_NACER`, porque la
    tabla de Hadlock da peso estimado *in utero* y no peso al nacer.

    El resultado se recorta a [300, 6000] g para respetar el validador de
    `RecienNacido.peso_nacimiento` (`partos/models.py:1082`).
    """
    rng = rng or random

    peso = (
        peso_mediano_por_semana(semanas_parto)
        * FACTOR_PESO_AL_NACER
        * (1 + DISPERSION_PESO * z_tamano)
    )

    if imc_materno > 30:
        peso += 120
    if paridad >= 1:
        peso += 100
    if diabetes:
        peso += 230
    if hipertension:
        peso -= 200
    if gemelar:
        peso -= 700
    if sexo == "masculino":
        peso += 120

    peso += rng.gauss(0, RUIDO_PESO_G)
    return int(_limitar(round(peso), 300, 6000))


def simular_talla_y_perimetro(
    peso_g: int, rng: random.Random | None = None,
) -> tuple[Decimal, Decimal]:
    """Talla en cm y perímetro cefálico en cm, derivados del peso.

    Antes eran `_rango(42, 54)` y `_rango(30, 38)`, independientes del peso y
    entre sí: un recién nacido de 1.800 g podía medir 54 cm.

    Las relaciones son aproximadamente lineales en este rango:
    un bebé de 3.000 g mide unos 49 cm y tiene un perímetro de unos 34 cm.

    El ruido no es decorativo: con una desviación demasiado pequeña la
    correlación peso↔talla sale casi perfecta (medido: r = 0,976), y eso no
    ocurre en la realidad, donde ronda 0,8. Dos bebés del mismo peso pueden
    tener complexiones distintas. Con σ = 2,0 cm la correlación queda en su
    orden de magnitud correcto.

    Se recortan a los validadores del modelo: talla [20, 60], perímetro
    [20, 50] (`partos/models.py:1087,1094`).
    """
    rng = rng or random

    talla = 32.0 + peso_g * 0.0056 + rng.gauss(0, 2.0)
    perimetro = 24.5 + peso_g * 0.0032 + rng.gauss(0, 1.5)

    return (
        Decimal(str(round(_limitar(talla, 20.0, 60.0), 1))),
        Decimal(str(round(_limitar(perimetro, 20.0, 50.0), 1))),
    )


def simular_apgar(
    *, semanas_parto: float, peso_g: int, rng: random.Random | None = None,
) -> tuple[int, int]:
    """Apgar al minuto y a los cinco minutos.

    El de cinco minutos **se deriva** del de un minuto: recupera uno o dos
    puntos y nunca es menor. Antes se sorteaban por separado y salían
    combinaciones fisiológicamente extrañas, como 9 al minuto y 7 a los cinco.

    Los dos bajan con la prematuridad y con el bajo peso, que es lo que ocurre
    de verdad.
    """
    rng = rng or random

    base = 9.0
    if semanas_parto < 32:
        base -= 2.5
    elif semanas_parto < 37:
        base -= 1.0
    if peso_g < 1500:
        base -= 1.5
    elif peso_g < 2500:
        base -= 0.7

    apgar_1 = int(_limitar(round(base + rng.gauss(0, 0.9)), 0, 10))
    # A los cinco minutos casi todos recuperan; los que no, es que algo va mal.
    recuperacion = rng.choices([0, 1, 2], weights=[15, 55, 30])[0]
    apgar_5 = int(_limitar(apgar_1 + recuperacion, apgar_1, 10))

    return apgar_1, apgar_5


def clasificar_peso_nacimiento(peso_g: int) -> str:
    """`'bajo_peso'` (<2500), `'normal'` [2500, 4000], `'macrosomia'` (>4000).

    Los cortes son los mismos que usa `RecienNacido.get_clasificacion_peso()`
    (`partos/models.py:1191`) y los de `ecografias.peso_fetal`. Hay un test que
    compara las tres para que no se separen en silencio.
    """
    from ecografias.peso_fetal import CORTE_BAJO_PESO_G, CORTE_MACROSOMIA_G

    if peso_g < CORTE_BAJO_PESO_G:
        return "bajo_peso"
    if peso_g > CORTE_MACROSOMIA_G:
        return "macrosomia"
    return "normal"


def sortear_semanas_al_parto(rng: random.Random | None = None) -> int:
    """Edad gestacional al parto, con una distribución realista.

    Antes, `seed_carga.py:537` solo creaba partos con `semanas_actuales >= 37`:
    **todos a término**. Sin variación de edad gestacional no hay nada que
    aprender sobre su efecto en el peso, que es precisamente la relación más
    fuerte del problema.

    Proporciones aproximadas a las de Bolivia y la región:
      - pretérmino (32-36):  ~9%
      - muy pretérmino (28-31): ~1%
      - término (37-41):     ~85%
      - postérmino (42):     ~5%
    """
    rng = rng or random
    tramo = rng.choices(
        ["muy_pretermino", "pretermino", "termino", "postermino"],
        weights=[1, 9, 85, 5],
    )[0]
    if tramo == "muy_pretermino":
        return rng.randint(28, 31)
    if tramo == "pretermino":
        return rng.randint(32, 36)
    if tramo == "postermino":
        return 42
    return rng.randint(37, 41)
