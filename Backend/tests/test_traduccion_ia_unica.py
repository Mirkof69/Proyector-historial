"""Una sola traducción de la respuesta de la IA a AnalisisCNN.

Fallos que previene:
- Dos copias distintas de la traducción (ecografías e IA médica).
- Una ecografía normal quedaba con nivel de riesgo ALTO (salía de
  score_global, que incluía la probabilidad de «normal»).
- Sin modelo, se guardaba un «análisis» vacío como si se hubiera hecho.
- Biometría sintética copiada a los campos bpd_mm/hc_mm como si fuera medida.
"""
from django.test import SimpleTestCase

from ia_medica.services.result_mapping import IANoDisponible, defaults_analisis_cnn


def _respuesta(patologia, confianza, severidad="ninguna", **extra):
    return {
        "status": "success", "score_global": 0.02 if patologia == "normal" else confianza,
        "pathology_detection": {"pathologies": [
            {"pathology": patologia, "confidence": confianza, "severity": severidad}]},
        "biometry": {"BPD_mm": 48.0, "disponible": False},
        "advertencia": "Detector experimental", **extra,
    }


class TraduccionIaTest(SimpleTestCase):
    def test_normal_es_riesgo_bajo(self):
        d = defaults_analisis_cnn(_respuesta("normal", 0.97))
        self.assertEqual(d["resultado"], "normal")
        self.assertEqual(d["nivel_riesgo"], "BAJO")

    def test_anomalia_grave_es_riesgo_alto(self):
        d = defaults_analisis_cnn(_respuesta("anencefalia", 0.9, "alta"))
        self.assertEqual(d["nivel_riesgo"], "ALTO")
        self.assertEqual(d["patologias"], ["anencefalia"])

    def test_sin_modelo_no_hay_analisis(self):
        with self.assertRaises(IANoDisponible):
            defaults_analisis_cnn({"status": "fallback", "advertencia": "Modelo CNN no cargado."})

    def test_biometria_no_disponible_no_se_copia(self):
        d = defaults_analisis_cnn(_respuesta("normal", 0.97))
        self.assertIsNone(d["bpd_mm"])
        self.assertIsNone(d["medidas_estimadas"])

    def test_la_advertencia_queda_con_el_resultado(self):
        self.assertIn("Detector experimental", defaults_analisis_cnn(_respuesta("normal", 0.97))["alertas"])
