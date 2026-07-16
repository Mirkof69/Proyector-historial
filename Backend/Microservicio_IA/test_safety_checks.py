"""Test de regresión: _apply_safety_checks no debe rechazar ecografías reales
con señal por debajo del umbral clínico de confirmación (bug reportado: caso
embarazo_multiple al 92.9%, marcado falsamente como "no es una ecografía").

Ejecutar: .venv_gpu/Scripts/python.exe -m pytest test_safety_checks.py -v
"""
from app.routes import _apply_safety_checks


def test_senal_real_bajo_umbral_no_se_rechaza_por_color():
    result = {
        "pathology_detection": {
            "pathologies": [{"pathology": "baja_confianza", "confidence": 0.0324}],
            "all_probabilities": {"embarazo_multiple": 0.929, "normal": 0.032},
        },
    }
    quality = {"resolucion_baja": False}
    color_check = {"parece_ecografia": False, "saturacion_media": 0.4}

    _apply_safety_checks(result, quality, color_check)

    validation = result["ultrasound_validation"]
    assert validation.get("es_ecografia_obstetrica_valida") is not False, (
        "Una ecografia real con 92.9% de senal (embarazo_multiple) no debe "
        "marcarse como invalida solo por no alcanzar el umbral clinico de "
        "confirmacion (0.95)."
    )


def test_sin_senal_real_si_se_rechaza_por_color():
    result = {
        "pathology_detection": {
            "pathologies": [{"pathology": "baja_confianza", "confidence": 0.02}],
            "all_probabilities": {"normal": 0.02},
        },
    }
    quality = {"resolucion_baja": False}
    color_check = {"parece_ecografia": False, "saturacion_media": 0.6}

    _apply_safety_checks(result, quality, color_check)

    validation = result["ultrasound_validation"]
    assert validation["es_ecografia_obstetrica_valida"] is False, (
        "Una imagen sin ninguna senal real de anatomia y con colores de "
        "fotografia SI debe seguir rechazandose (el fix no debe volver "
        "inutil la heuristica)."
    )


def test_resolucion_baja_no_se_mezcla_con_motivo_de_validez():
    result = {
        "pathology_detection": {
            "pathologies": [{"pathology": "normal", "confidence": 0.9}],
            "all_probabilities": {"normal": 0.9},
        },
    }
    quality = {"resolucion_baja": True, "ancho_px": 200, "alto_px": 150, "resolucion_minima_recomendada_px": 256}
    color_check = {"parece_ecografia": True, "saturacion_media": 0.05}

    _apply_safety_checks(result, quality, color_check)

    validation = result["ultrasound_validation"]
    assert validation.get("motivo_calidad")
    assert not validation.get("motivo_validez")
    assert validation.get("es_ecografia_obstetrica_valida") is not False
