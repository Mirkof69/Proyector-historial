"""Conversión de unidades al importar resultados de laboratorio (Excel o CSV).

Por qué existe
--------------
Muchos laboratorios informan las plaquetas como «250000» (por µL) y el
catálogo las mide en 10³/µL: sin convertir, 250000 se guardaba como 250
millones de plaquetas y salía «RESULTADO CRÍTICO». Igual con leucocitos
(«7500»), o con una hemoglobina en g/L.

Reglas (prudentes, porque es un dato clínico):
- Si el archivo trae la unidad, solo se convierte entre unidades del mismo
  tipo, donde el factor es exacto: conteos (/µL, 10³/µL, 10⁹/L…), masa por
  volumen (g/L, g/dL, mg/dL…), actividad (U/L, mUI/mL…) y molares entre sí.
  Masa ↔ molar (mg/dL ↔ mmol/L) depende del analito: no se adivina, se rechaza.
- Si no trae unidad, solo se corrige un conteo cuyo valor es imposible en la
  unidad del catálogo (≥ 1000 y ≥ 10 veces su límite alto en 10³/µL): se
  interpreta como /µL. Un valor dudoso no se toca: se avisa.
- Toda conversión deja el valor original en las observaciones del resultado.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal

_MASA = {"g": Decimal(1), "mg": Decimal("1e-3"), "ug": Decimal("1e-6"), "ng": Decimal("1e-9"),
         "pg": Decimal("1e-12")}
_MOL = {"mol": Decimal(1), "mmol": Decimal("1e-3"), "umol": Decimal("1e-6"), "nmol": Decimal("1e-9"),
        "pmol": Decimal("1e-12")}
_ACTIVIDAD = {"u": Decimal(1), "ui": Decimal(1), "mu": Decimal("1e-3"), "mui": Decimal("1e-3"),
              "uu": Decimal("1e-6"), "uui": Decimal("1e-6")}
_VOLUMEN = {"l": Decimal(1), "dl": Decimal("0.1"), "ml": Decimal("1e-3"), "ul": Decimal("1e-6")}
_CONTEO = {"": Decimal(1), "10^3": Decimal("1e3"), "10^6": Decimal("1e6"), "10^9": Decimal("1e9"),
           "10^12": Decimal("1e12"), "k": Decimal("1e3"), "mil": Decimal("1e3"), "millones": Decimal("1e6")}
_PALABRAS = re.compile(r"(celulas|celula|cel|plaquetas|leucocitos|eritrocitos|globulos)")


class UnidadIncompatible(ValueError):
    """La unidad del archivo no se puede convertir con seguridad a la del catálogo."""


def normalizar(unidad: str) -> str:
    u = (unidad or "").strip().lower()
    for a, b in (("μ", "u"), ("µ", "u"), ("mcg", "ug"), ("³", "^3"), ("⁶", "^6"), ("⁹", "^9"),
                 ("¹²", "^12"), ("×", "x"), ("mm^3", "ul"), ("mm3", "ul"), ("cc", "ml")):
        u = u.replace(a, b)
    # Las tildes al final: NFKD antes convertiría «10³» en «103».
    u = "".join(c for c in unicodedata.normalize("NFKD", u) if not unicodedata.combining(c))
    u = _PALABRAS.sub("", u.replace(" ", ""))
    u = re.sub(r"x?10e?\^?(3|6|9|12)", r"10^\1", u).lstrip("x")
    return u


def _analizar(unidad: str) -> tuple[str, Decimal] | None:
    """(familia, factor a la unidad base de su familia) o None si no se reconoce."""
    u = normalizar(unidad)
    if "/" not in u:
        return None
    arriba, abajo = u.split("/", 1)
    if abajo not in _VOLUMEN:
        return None
    volumen = _VOLUMEN[abajo]
    for familia, tabla in (("masa", _MASA), ("molar", _MOL), ("actividad", _ACTIVIDAD), ("conteo", _CONTEO)):
        if arriba in tabla:
            return familia, tabla[arriba] / volumen
    return None


def convertir(valor: Decimal, desde: str, hacia: str) -> Decimal:
    """`valor` en `desde` expresado en `hacia`. UnidadIncompatible si no hay factor exacto."""
    if normalizar(desde) == normalizar(hacia):
        return valor
    origen, destino = _analizar(desde), _analizar(hacia)
    if origen is None or destino is None or origen[0] != destino[0]:
        raise UnidadIncompatible(
            f"La unidad «{desde}» no se puede convertir a «{hacia}» (la del catálogo). "
            f"Convierta el valor o informe en {hacia}.",
        )
    return _redondear(valor * origen[1] / destino[1])


def corregir_conteo_sin_unidad(valor: Decimal, rango) -> tuple[Decimal, str]:
    """Para un archivo sin unidad: (valor a guardar, aviso o '')."""
    destino = _analizar(rango.unidad or "")
    if destino is None or destino[0] != "conteo" or destino[1] <= _CONTEO[""] / _VOLUMEN["ul"]:
        return valor, ""
    multiplo = destino[1] * _VOLUMEN["ul"]  # 10³/µL → 1000; 10⁶/µL → 1 000 000
    tope = rango.es_critico_alto if rango.es_critico_alto is not None else rango.valor_maximo
    umbral = max(Decimal(1000), Decimal(10) * Decimal(tope or 0))
    if valor >= umbral:
        nuevo = _redondear(valor / multiplo)
        return nuevo, f"Se tomó {valor} como /µL: se guarda {nuevo} {rango.unidad}"
    if tope is not None and valor > Decimal(tope):
        return valor, f"Valor muy alto para {rango.unidad}: verifique que no venga en /µL"
    return valor, ""


def _redondear(valor: Decimal) -> Decimal:
    # format «f»: normalize() sola deja 250 como «2.5E+2».
    return Decimal(format(valor.quantize(Decimal("0.0001")).normalize(), "f"))
