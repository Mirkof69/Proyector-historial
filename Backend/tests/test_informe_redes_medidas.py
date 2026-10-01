"""El informe de las redes medidas (reemplazo de la EfficientNet-B4) en Django.

Esperado vs obtenido. Fallos que previene:
- una alarma del cribado cerebral guardada como «normal»;
- un índice cardiotorácico alto o un plano dudoso sin pedir revisión;
- el catálogo de modelos con exactitudes inventadas cuando el microservicio no responde;
- el reporte narrativo afirmando patologías que ninguna red evaluó.
"""
from unittest import mock

from django.test import SimpleTestCase, TestCase

from ia_medica.services.llm_narrative_service import _adaptar_informe_medido, _campos_honestos_desde_cnn
from ia_medica.services.result_mapping import defaults_analisis_cnn


def informe(**extra):
    base = {
        "status": "success", "version_flujo": "2.0",
        "plano": {"plano": "cerebro fetal", "confianza": 0.96, "probabilidades": {"cerebro fetal": 0.96, "otro": 0.04}},
        "medidas": {"circunferencia_cefalica_mm": 250.4, "diametro_biparietal_mm": 68.1},
        "hallazgos": [], "avisos": [], "estructuras_vistas": {"Cráneo": True},
        "superposicion_png": "iVBORw0KGgo=", "requiere_revision": False, "tiempo_ms": 85,
        "modelos_usados": [{"archivo": "plano_anatomico_fetal_planes", "sha256": "a" * 64, "dataset": "FETAL_PLANES_DB"}],
        "informe_texto": "Plano detectado: cerebro fetal.",
        "anomalias_cerebrales": {"aplicable": True, "alarma_anomalia": False, "probabilidad_anomalia": 0.03,
                                 "familia_sospechada": None, "familia_sospechada_nombre": None},
    }
    base.update(extra)
    return base


class MapeoTest(SimpleTestCase):
    def test_cabeza_normal_con_medidas(self):
        d = defaults_analisis_cnn(informe())
        self.assertEqual((d["resultado"], d["nivel_riesgo"], d["modelo_usado"]), ("normal", "BAJO", "redes_medidas"))
        self.assertEqual((d["hc_mm"], d["bpd_mm"]), (250.4, 68.1))
        self.assertTrue(d["version_modelo"].startswith("flujo 2.0@aaaaaaaaaaaa"))
        self.assertIsNone(d["riesgo_preeclampsia"])  # ninguna red estima riesgos maternos

    def test_alarma_cerebral_no_queda_como_normal(self):
        d = defaults_analisis_cnn(informe(
            hallazgos=["Posible anomalía cerebral (Encefalocele): derivar a especialista."],
            anomalias_cerebrales={"aplicable": True, "alarma_anomalia": True, "probabilidad_anomalia": 0.91,
                                  "familia_sospechada": "encefalocele", "familia_sospechada_nombre": "Encefalocele"}))
        self.assertEqual(d["resultado"], "anomalia_moderada")
        self.assertEqual(d["patologias"], ["encefalocele"])
        self.assertAlmostEqual(d["confianza"], 0.91)

    def test_indice_cardiotoracico_alto_pide_revision(self):
        d = defaults_analisis_cnn(informe(
            plano={"plano": "tórax fetal", "confianza": 0.9, "probabilidades": {}},
            medidas={"indice_cardiotoracico_areas": 0.41, "referencia_areas": [0.25, 0.35]},
            anomalias_cerebrales=None))
        self.assertEqual((d["resultado"], d["nivel_riesgo"]), ("requiere_revision", "MODERADO"))

    def test_plano_abdominal_no_adecuado_pide_revision(self):
        d = defaults_analisis_cnn(informe(plano={"plano": "abdomen fetal", "confianza": 0.9, "probabilidades": {}},
                                          medidas={"plano_adecuado_para_ca": False}, anomalias_cerebrales=None))
        self.assertEqual(d["resultado"], "requiere_revision")


class NarrativaTest(SimpleTestCase):
    def test_sin_cribado_no_se_inventa_patologia(self):
        adaptado = _adaptar_informe_medido(informe(
            plano={"plano": "fémur fetal", "confianza": 0.95, "probabilidades": {}}, medidas={}, anomalias_cerebrales=None))
        campos = _campos_honestos_desde_cnn(adaptado)
        self.assertEqual(campos["patologias_detectadas"], [])

    def test_alarma_aparece_como_unica_patologia(self):
        adaptado = _adaptar_informe_medido(informe(anomalias_cerebrales={
            "aplicable": True, "alarma_anomalia": True, "probabilidad_anomalia": 0.8,
            "familia_sospechada": "fosa_posterior", "familia_sospechada_nombre": "Fosa posterior"}))
        self.assertEqual(_campos_honestos_desde_cnn(adaptado)["clasificacion_clinica"], "Patología detectada")

    def test_foto_no_es_ecografia(self):
        adaptado = _adaptar_informe_medido(informe(avisos=["La imagen tiene colores de fotografía, no de ecografía"]))
        self.assertFalse(adaptado["ultrasound_validation"]["es_ecografia_obstetrica_valida"])


class CatalogoTest(TestCase):
    def test_sin_microservicio_no_hay_numeros_inventados(self):
        from ia_medica.services.catalogo_modelos import catalogo

        with mock.patch("requests.get", side_effect=ConnectionError("apagado")):
            redes = [m for m in catalogo() if m["origen"] == "microservicio"]
        self.assertTrue(redes)
        self.assertTrue(all(not m["disponible"] and m["metrica_principal"] is None for m in redes))
        self.assertNotIn("efficientnet", " ".join(m["codigo"] for m in redes))
