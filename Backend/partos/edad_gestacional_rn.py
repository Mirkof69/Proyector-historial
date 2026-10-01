"""Edad gestacional del recién nacido por examen físico: Capurro somático y Ballard.

Capurro somático (Capurro H. et al., J Pediatr 1978;93:120-2; el que usa la
Historia Clínica Perinatal CLAP/SMR-OPS): cinco signos físicos, cada uno con
sus puntos. Edad gestacional en días = 204 + suma de puntos.

Nuevo Ballard (Ballard JL. et al., J Pediatr 1991;119:417-23): seis signos
neuromusculares y seis físicos, puntaje total de −10 a 50.
Edad gestacional en semanas = (2 × puntaje + 120) / 5  (−10 → 20 s; 50 → 44 s).

Las mismas tablas viajan al frontend por la API (`GET /api/partos/capurro/`),
para que el formulario y el cálculo no puedan diferir.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CAPURRO_CONSTANTE_DIAS = 204

#: signo → [(puntos, descripción)]
CAPURRO_SOMATICO: dict[str, dict] = {
    "textura_piel": {"etiqueta": "Textura de la piel", "opciones": [
        (0, "Muy fina, gelatinosa"),
        (5, "Fina y lisa"),
        (10, "Algo más gruesa, discreta descamación superficial"),
        (15, "Gruesa, grietas superficiales, descamación de manos y pies"),
        (20, "Gruesa, grietas profundas apergaminadas"),
    ]},
    "forma_oreja": {"etiqueta": "Forma de la oreja", "opciones": [
        (0, "Chata, deforme, pabellón no incurvado"),
        (8, "Pabellón parcialmente incurvado en el borde superior"),
        (16, "Pabellón incurvado en todo el borde superior"),
        (24, "Pabellón totalmente incurvado"),
    ]},
    "glandula_mamaria": {"etiqueta": "Tamaño de la glándula mamaria", "opciones": [
        (0, "No palpable"),
        (5, "Palpable, menor de 5 mm"),
        (10, "Entre 5 y 10 mm"),
        (15, "Mayor de 10 mm"),
    ]},
    "formacion_pezon": {"etiqueta": "Formación del pezón", "opciones": [
        (0, "Apenas visible, sin areola"),
        (5, "Diámetro menor de 7,5 mm, areola lisa y chata"),
        (10, "Diámetro menor de 7,5 mm, areola punteada, borde no levantado"),
        (15, "Diámetro mayor de 7,5 mm, areola punteada, borde levantado"),
    ]},
    "pliegues_plantares": {"etiqueta": "Pliegues plantares", "opciones": [
        (0, "Sin pliegues"),
        (5, "Marcas mal definidas en la mitad anterior"),
        (10, "Marcas bien definidas en la mitad anterior y surcos en el tercio anterior"),
        (15, "Surcos en la mitad anterior"),
        (20, "Surcos en más de la mitad anterior"),
    ]},
}

BALLARD_MINIMO, BALLARD_MAXIMO = -10, 50


def validar_capurro(items: dict) -> dict[str, str]:
    """Errores por signo; vacío si los cinco están y con puntos válidos."""
    errores = {}
    for clave, signo in CAPURRO_SOMATICO.items():
        validos = {p for p, _ in signo["opciones"]}
        valor = (items or {}).get(clave)
        if valor is None:
            errores[clave] = f"Falta «{signo['etiqueta']}»."
        elif not isinstance(valor, int) or isinstance(valor, bool) or valor not in validos:
            errores[clave] = f"«{signo['etiqueta']}» admite {sorted(validos)} puntos, no {valor!r}."
    sobrantes = set(items or {}) - set(CAPURRO_SOMATICO)
    if sobrantes:
        errores["capurro_items"] = f"Signos desconocidos: {', '.join(sorted(sobrantes))}."
    return errores


def semanas_capurro(items: dict) -> Decimal:
    """Semanas (una decimal) a partir de los cinco signos ya validados."""
    dias = CAPURRO_CONSTANTE_DIAS + sum(int(items[c]) for c in CAPURRO_SOMATICO)
    return (Decimal(dias) / 7).quantize(Decimal("0.1"), ROUND_HALF_UP)


def semanas_ballard(puntaje: int) -> Decimal:
    return (Decimal(2 * int(puntaje) + 120) / 5).quantize(Decimal("0.1"), ROUND_HALF_UP)


def clasificar_por_edad(semanas: Decimal | float | None) -> str | None:
    """Pretérmino (< 37), a término (37 a < 42) o postérmino (≥ 42), en semanas cumplidas."""
    if semanas is None:
        return None
    s = float(semanas)
    if s < 37:
        return "pretermino"
    if s < 42:
        return "termino"
    return "postermino"


def tablas() -> dict:
    """Lo que necesita el formulario: signos, opciones y fórmulas."""
    return {
        "capurro": {c: {"etiqueta": s["etiqueta"],
                        "opciones": [{"puntos": p, "descripcion": d} for p, d in s["opciones"]]}
                    for c, s in CAPURRO_SOMATICO.items()},
        "capurro_constante_dias": CAPURRO_CONSTANTE_DIAS,
        "ballard": {"minimo": BALLARD_MINIMO, "maximo": BALLARD_MAXIMO,
                    "formula": "(2 × puntaje + 120) / 5 semanas"},
    }
