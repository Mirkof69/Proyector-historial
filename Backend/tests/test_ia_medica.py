"""Tests para el mapeo de resultados del microservicio de IA.

Regresion de la Fase 14: dos vistas de Django (ia_medica/views.py y
ecografias/ai_views.py) reimplementaban su propia logica de veredicto con
un umbral plano de 0.50 y mezclaban la probabilidad de "normal" con
score_global para la "confianza" mostrada al usuario, dando resultados
incoherentes entre los dos botones de analisis para la misma imagen.
Estos tests fijan el comportamiento correcto de la funcion centralizada
que reemplaza esa logica duplicada.
"""
from ia_medica.services.result_mapping import mapear_resultado_microservicio


def _ai_result(pathologies, score_global=0.0):
    return {
        "pathology_detection": {
            "pathologies": pathologies,
            "all_probabilities": {},
        },
        "score_global": score_global,
    }


class TestMapearResultadoMicroservicio:
    def test_normal_con_confianza_baja_no_es_requiere_revision(self):
        """Un caso normal con score_global=0.43 (bajo el viejo umbral plano
        de "score_global <= 0.3 => normal") debe seguir siendo "normal",
        porque el microservicio ya determino que "normal" es la clase
        ganadora con los umbrales calibrados."""
        ai_result = _ai_result(
            [{"pathology": "normal", "confidence": 0.43, "severity": "ninguna"}],
            score_global=0.43,
        )
        resultado = mapear_resultado_microservicio(ai_result)
        assert resultado["resultado"] == "normal"
        assert resultado["confianza"] == 0.43

    def test_baja_confianza_es_requiere_revision(self):
        """Cuando el microservicio determina honestamente que no hay
        suficiente señal (ni patologia ni normal superan su umbral),
        devuelve "baja_confianza" — debe traducirse a "requiere_revision",
        no a un veredicto fabricado con alta confianza."""
        ai_result = _ai_result(
            [{"pathology": "baja_confianza", "confidence": 0.03, "severity": "media"}],
            score_global=0.43,
        )
        resultado = mapear_resultado_microservicio(ai_result)
        assert resultado["resultado"] == "requiere_revision"
        assert resultado["confianza"] == 0.03

    def test_patologia_real_severidad_alta_es_anomalia_grave(self):
        ai_result = _ai_result(
            [{"pathology": "hidrocefalia", "confidence": 0.88, "severity": "alta"}],
            score_global=0.88,
        )
        resultado = mapear_resultado_microservicio(ai_result)
        assert resultado["resultado"] == "anomalia_grave"
        assert resultado["confianza"] == 0.88

    def test_patologia_real_severidad_media_es_anomalia_leve(self):
        ai_result = _ai_result(
            [{"pathology": "oligohidramnios", "confidence": 0.40, "severity": "media"}],
            score_global=0.40,
        )
        resultado = mapear_resultado_microservicio(ai_result)
        assert resultado["resultado"] == "anomalia_leve"
        assert resultado["confianza"] == 0.40

    def test_confianza_no_se_mezcla_con_score_global(self):
        """Antes: confianza = max(todas las probabilidades, score_global).
        Ahora: confianza = la probabilidad de lo que realmente se reporta.
        Si "normal" tiene 0.92 pero el veredicto real es "baja_confianza"
        (otra clase), la confianza mostrada no debe ser 0.92."""
        ai_result = _ai_result(
            [{"pathology": "baja_confianza", "confidence": 0.05, "severity": "media"}],
            score_global=0.92,
        )
        resultado = mapear_resultado_microservicio(ai_result)
        assert resultado["confianza"] == 0.05
        assert resultado["confianza"] != 0.92

    def test_elige_la_patologia_de_mayor_probabilidad_si_hay_varias(self):
        ai_result = _ai_result(
            [
                {"pathology": "oligohidramnios", "confidence": 0.30, "severity": "media"},
                {"pathology": "macrosomia_fetal", "confidence": 0.75, "severity": "media-alta"},
            ],
            score_global=0.75,
        )
        resultado = mapear_resultado_microservicio(ai_result)
        assert resultado["top"]["name"] == "macrosomia_fetal"
        assert resultado["resultado"] == "anomalia_moderada"

    def test_pathologies_vacio_no_rompe(self):
        ai_result = _ai_result([], score_global=0.0)
        resultado = mapear_resultado_microservicio(ai_result)
        assert resultado["resultado"] == "requiere_revision"
        assert resultado["top"] is None
