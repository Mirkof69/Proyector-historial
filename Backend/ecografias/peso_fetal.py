"""Estimación del peso fetal a partir de la biometría. Fuente única.

Por qué existe este módulo
--------------------------
Había DOS implementaciones de Hadlock en el proyecto y la que se usaba estaba
rota:

  - `ecografias/models.py:434`  (4 parámetros) — la que corre en producción
  - `calculadoras/utils.py:462` (3 parámetros) — correcta, pero nadie la llamaba

Los coeficientes de Hadlock 1985 están calibrados en **centímetros**. La base
de datos guarda **milímetros** (`verbose_name="DBP (mm)"`,
`ecografias/models.py:295`; la pantalla pinta `suffix="mm"` en
`DetalleEcoTabs.tsx:33`). Nadie convertía.

Medido contra las 280 biometrías reales del tenant `clinica_demo` el 23 de
septiembre de 2026:

    calcular_peso_fetal_hadlock() devolvía 0 g en 174 de 280 (62%)

Y en el 38% restante devolvía disparates. Estos son valores que estaban
guardados en la base y se mostraban en pantalla:

    | guardado  | biometría real          | lo correcto |
    |-----------|-------------------------|-------------|
    | 13.118 g  | DBP 20,6 mm (~12 sem)   |      93 g   |
    |    382 g  | DBP 35,0 mm             |     183 g   |
    |      0 g  | DBP 77,8 mm (~31 sem)   |   1.569 g   |

Un feto de doce semanas registrado con trece kilos.

El patrón no es aleatorio y conviene entenderlo: el término `-0,00386·CA·LF`
crece con el cuadrado de las medidas. Con un feto grande en milímetros
(CA=330, LF=70) ese término vale -89 y el exponente se va a -41, así que
`int(10**-41)` es 0. Con un feto pequeño (CA=73, LF=16) vale solo -4,6 y no
alcanza a compensar los términos lineales, de modo que sale una sobreestimación
enorme. **Es decir: fallaba al revés de como haría falta** — daba cero
precisamente en el tercer trimestre, que es cuando el peso importa para decidir
la vía de parto.

Y fallaba en silencio: `BiometriaFetal.save()` hacía `if peso_calculado:`, y 0
es falso en Python, así que en el 62% de los casos el campo se quedaba vacío
sin que nadie viera un error. En el otro 38% se guardaba el disparate.

La conversión mm→cm se hace **aquí, una vez**. Las medidas se siguen guardando
en milímetros porque es lo que escribe el ecógrafo y lo que ve la usuaria.

Referencia
----------
Hadlock FP, Harrist RB, Sharman RS, Deter RL, Park SK. «Estimation of fetal
weight with the use of head, body, and femur measurements — a prospective
study». Am J Obstet Gynecol. 1985;151(3):333-337.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: Límites fisiológicos del peso fetal estimado, en gramos.
#:
#: Sirven de red de seguridad: si el resultado cae fuera, la entrada está mal
#: (casi siempre, unidades equivocadas) y es mejor no dar número que dar uno
#: absurdo. Esto convierte la confusión mm/cm en un fallo **ruidoso**: quien
#: pase centímetros creyendo que son milímetros obtiene un peso de ~4 g, que
#: queda fuera de rango, se registra en el log y se devuelve None.
#:
#: El mínimo es 50 g y no 300 g (el validador de `RecienNacido`) a propósito:
#: aquí se estima el peso de un feto *in utero*, que a las 20 semanas pesa unos
#: 300 g y antes, menos. El validador de 300 g es para el peso *al nacer*.
PESO_FETAL_MINIMO_G = 50
PESO_FETAL_MAXIMO_G = 6500


def _a_centimetros(valor) -> float | None:
    """Convierte una medida en milímetros a centímetros.

    Acepta `Decimal`, `float`, `int` o `None`, porque los campos de
    `BiometriaFetal` son `DecimalField` que pueden venir nulos.
    """
    if valor is None:
        return None
    return float(valor) / 10.0


def _validar_resultado(peso_g: float, medidas: dict) -> int | None:
    """Devuelve el peso redondeado, o None si no es fisiológicamente posible.

    `medidas` solo se usa para el mensaje del log: cuando esto salta, lo que
    hace falta saber es con qué números se llamó.
    """
    if not (PESO_FETAL_MINIMO_G <= peso_g <= PESO_FETAL_MAXIMO_G):
        logger.warning(
            "Peso fetal fuera de rango fisiológico: %.1f g (límites %s-%s). "
            "Medidas recibidas (deben estar en MILÍMETROS): %s. "
            "Un resultado muy pequeño suele significar que se pasaron "
            "centímetros; uno de cero, milímetros a una fórmula de centímetros.",
            peso_g, PESO_FETAL_MINIMO_G, PESO_FETAL_MAXIMO_G, medidas,
        )
        return None
    return int(round(peso_g))


def hadlock_1985_4p(dbp_mm, cc_mm, ca_mm, lf_mm) -> int | None:
    """Peso fetal estimado en gramos, por Hadlock 1985 de cuatro parámetros.

    Las cuatro medidas se reciben en **milímetros** y se convierten dentro.

        log10(peso) = 1,3596 - 0,00386·CA·LF + 0,0064·CC
                      + 0,00061·DBP·CA + 0,0425·CA + 0,174·LF

    con todas las medidas en centímetros.

    Devuelve `None` —nunca 0— si falta alguna medida o si el resultado no es
    fisiológico. Es la variante más precisa y la que se debe usar siempre que
    estén las cuatro medidas; el error declarado es de ±15%.
    """
    dbp, cc, ca, lf = (_a_centimetros(v) for v in (dbp_mm, cc_mm, ca_mm, lf_mm))
    if None in (dbp, cc, ca, lf):
        return None

    log_peso = (
        1.3596
        - 0.00386 * ca * lf
        + 0.0064 * cc
        + 0.00061 * dbp * ca
        + 0.0425 * ca
        + 0.174 * lf
    )
    return _validar_resultado(
        10**log_peso,
        {"dbp_mm": dbp_mm, "cc_mm": cc_mm, "ca_mm": ca_mm, "lf_mm": lf_mm},
    )


def hadlock_1985_3p(dbp_mm, ca_mm, lf_mm) -> int | None:
    """Peso fetal estimado en gramos, sin la circunferencia cefálica.

        log10(peso) = 1,335 - 0,0034·CA·LF + 0,0316·DBP
                      + 0,0457·CA + 0,1623·LF

    Existe porque la circunferencia cefálica no siempre se puede medir: con el
    feto encajado o con mala ventana acústica, la cabeza queda fuera de plano.
    En esas ecografías, esta variante da un número donde la de cuatro
    parámetros no daría ninguno.
    """
    dbp, ca, lf = (_a_centimetros(v) for v in (dbp_mm, ca_mm, lf_mm))
    if None in (dbp, ca, lf):
        return None

    log_peso = (
        1.335
        - 0.0034 * ca * lf
        + 0.0316 * dbp
        + 0.0457 * ca
        + 0.1623 * lf
    )
    return _validar_resultado(
        10**log_peso, {"dbp_mm": dbp_mm, "ca_mm": ca_mm, "lf_mm": lf_mm},
    )


def estimar_peso_fetal(dbp_mm, cc_mm, ca_mm, lf_mm) -> int | None:
    """Mejor estimación disponible con las medidas que haya.

    Usa la fórmula de cuatro parámetros si está la circunferencia cefálica, y
    la de tres si no. Es el punto de entrada que deberían usar los llamadores
    que no quieran decidir entre variantes.
    """
    peso = hadlock_1985_4p(dbp_mm, cc_mm, ca_mm, lf_mm)
    if peso is not None:
        return peso
    return hadlock_1985_3p(dbp_mm, ca_mm, lf_mm)


#: Percentiles 10, 50 y 90 del peso fetal estimado *in utero*, en gramos, por
#: semana completa de gestación.
#:
#: Hadlock FP, Harrist RB, Martinez-Poyer J. «In utero analysis of fetal growth:
#: a sonographic weight standard». Radiology. 1991;181(1):129-133.
#:
#: Ojo con la diferencia, que se confunde a menudo: esto es peso fetal
#: ESTIMADO POR ECOGRAFÍA, no peso al nacer. Las curvas de peso al nacer
#: (Lubchenco, Fenton) están sesgadas hacia abajo en los prematuros, porque un
#: bebé que nace a las 32 semanas suele nacer antes precisamente por algún
#: problema que también frenó su crecimiento. Para juzgar a un feto que sigue
#: dentro, la referencia correcta es ésta.
TABLA_HADLOCK_1991: dict[int, tuple[int, int, int]] = {
    # semana: (p10, p50, p90)
    10: (26, 35, 44),
    11: (34, 45, 56),
    12: (43, 58, 73),
    13: (55, 73, 91),
    14: (70, 93, 116),
    15: (88, 117, 146),
    16: (110, 146, 183),
    17: (136, 181, 226),
    18: (167, 223, 279),
    19: (205, 273, 341),
    20: (248, 331, 414),
    21: (299, 399, 499),
    22: (359, 478, 598),
    23: (426, 568, 710),
    24: (503, 670, 838),
    25: (589, 785, 981),
    26: (685, 913, 1141),
    27: (791, 1055, 1319),
    28: (908, 1210, 1513),
    29: (1034, 1379, 1724),
    30: (1169, 1559, 1949),
    31: (1313, 1751, 2189),
    32: (1465, 1953, 2441),
    33: (1622, 2162, 2703),
    34: (1783, 2377, 2971),
    35: (1946, 2595, 3244),
    36: (2110, 2813, 3516),
    37: (2271, 3028, 3785),
    38: (2427, 3236, 4045),
    39: (2576, 3435, 4294),
    40: (2714, 3619, 4524),
    41: (2839, 3787, 4734),
    42: (2948, 3931, 4914),
}

#: Cortes de peso al nacer, en gramos. Son los mismos que usa
#: `RecienNacido.get_clasificacion_peso()` (`partos/models.py:1191`), y hay un
#: test que compara las dos funciones corte a corte para que no se separen.
CORTE_BAJO_PESO_G = 2500
CORTE_MACROSOMIA_G = 4000


def percentil_peso_fetal(peso_g: int | None, semanas: float | None) -> int | None:
    """Percentil aproximado del peso fetal para esa edad gestacional.

    Interpola entre los percentiles 10, 50 y 90 de la tabla de Hadlock 1991.
    Devuelve un entero de 1 a 99; fuera de p10-p90 se satura en 3 y 97, porque
    con tres puntos de anclaje no hay información para afinar las colas y dar
    un «percentil 1,4» sería inventar precisión.

    Devuelve `None` si falta el peso, falta la edad gestacional, o la edad cae
    fuera del rango validado de la tabla (10-42 semanas).
    """
    if peso_g is None or semanas is None:
        return None

    semana = int(round(float(semanas)))
    if semana not in TABLA_HADLOCK_1991:
        return None

    p10, p50, p90 = TABLA_HADLOCK_1991[semana]

    if peso_g <= p10:
        return 3
    if peso_g >= p90:
        return 97
    if peso_g < p50:
        # Entre p10 y p50: interpolación lineal en el tramo 10-50.
        return int(round(10 + 40 * (peso_g - p10) / (p50 - p10)))
    # Entre p50 y p90.
    return int(round(50 + 40 * (peso_g - p50) / (p90 - p50)))


def clasificar_crecimiento(percentil: int | None) -> tuple[str, str]:
    """Clasificación del crecimiento fetal a partir del percentil.

    Devuelve `(codigo, texto)`. El código es para la lógica y las gráficas; el
    texto, para la pantalla.

    Los cortes en p10 y p90 son los que usa la práctica obstétrica para
    sospechar restricción del crecimiento y macrosomía. No son diagnósticos:
    un feto constitucionalmente pequeño y uno con restricción real pueden
    tener el mismo percentil, y distinguirlos exige Doppler y seguimiento.
    """
    if percentil is None:
        return ("desconocido", "Sin datos suficientes")
    if percentil < 10:
        return ("pequeno", "Pequeño para la edad gestacional (< p10)")
    if percentil > 90:
        return ("grande", "Grande para la edad gestacional (> p90)")
    return ("adecuado", "Crecimiento adecuado para la edad gestacional")
