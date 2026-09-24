"""Datación del embarazo: FUM frente a la primera ecografía.

Regla del ACOG (Committee Opinion 700, 2017): la FPP se corrige con la
ecografía más temprana cuando la edad gestacional que da difiere de la de la
FUM más que el umbral de su periodo. Cuanto más tarde la ecografía, mayor su
margen de error y mayor el umbral.

No cambia nada guardado: devuelve la propuesta y el médico decide.
"""
from datetime import timedelta

#: (edad gestacional ecográfica máxima en días, diferencia que obliga a redatar)
UMBRALES_ACOG = (
    (8 * 7 + 6, 5),
    (13 * 7 + 6, 7),
    (15 * 7 + 6, 7),
    (21 * 7 + 6, 10),
    (27 * 7 + 6, 14),
)
UMBRAL_TERCER_TRIMESTRE = 21


def umbral_redatacion(eg_eco_dias: int) -> int:
    for maximo, umbral in UMBRALES_ACOG:
        if eg_eco_dias <= maximo:
            return umbral
    return UMBRAL_TERCER_TRIMESTRE


def primera_ecografia_con_eg(embarazo):
    """La ecografía más temprana con edad gestacional registrada."""
    ecos = [
        e for e in embarazo.ecografias.all()
        if e.fecha_ecografia and e.edad_gestacional_semanas is not None
    ]
    return min(ecos, key=lambda e: e.fecha_ecografia) if ecos else None


def datacion(embarazo):
    """Compara FUM y primera ecografía. None si falta alguno de los dos."""
    fum = embarazo.fecha_ultima_menstruacion
    eco = primera_ecografia_con_eg(embarazo)
    if not fum or eco is None:
        return None
    eg_eco = eco.edad_gestacional_semanas * 7 + (eco.edad_gestacional_dias or 0)
    eg_fum = (eco.fecha_ecografia - fum).days
    diferencia = eg_eco - eg_fum
    umbral = umbral_redatacion(eg_eco)
    redatar = abs(diferencia) > umbral
    fpp_fum = fum + timedelta(days=280)
    fpp_eco = eco.fecha_ecografia - timedelta(days=eg_eco) + timedelta(days=280)
    return {
        "ecografia_id": eco.pk,
        "fecha_ecografia": eco.fecha_ecografia,
        "eg_por_fum_dias": eg_fum,
        "eg_por_ecografia_dias": eg_eco,
        "diferencia_dias": diferencia,
        "umbral_dias": umbral,
        "redatar": redatar,
        "fpp_por_fum": fpp_fum,
        "fpp_corregida": fpp_eco if redatar else fpp_fum,
        "criterio": "ACOG Committee Opinion 700 (2017)",
    }
