"""Un solo motor de riesgo de preeclampsia, con Bayes bien aplicado.

Fallos que previene:
- El riesgo se multiplicaba en porcentaje por los LR (2 % x 40 = 80 %) en vez
  de hacerlo sobre odds; una mujer de 40 años obesa salía con 84 %.
- Había dos motores: la misma paciente daba 9,9 % en /calculadoras/ y 84 %
  en /calculadoras-avanzadas/.
"""
from django.test import SimpleTestCase

from calculadoras.services.calculador_riesgos_fmf import CalculadorRiesgosFMF, aplicar_lr
from calculadoras.views import riesgo_preeclampsia_unificado


class BayesTest(SimpleTestCase):
    def test_se_aplica_sobre_odds(self):
        """ESPERADO: 2 % con LR 40 → 44,9 % (antes 80 %)."""
        self.assertAlmostEqual(aplicar_lr(2.0, 40), 44.9, places=1)

    def test_lr_1_no_cambia_nada_y_nunca_pasa_de_100(self):
        self.assertAlmostEqual(aplicar_lr(3.0, 1.0), 3.0, places=6)
        self.assertLess(aplicar_lr(50.0, 1e6), 100.0)


class MotorUnicoTest(SimpleTestCase):
    DATOS = {"edad_materna": 40, "peso_kg": 100, "talla_cm": 158, "edad_gestacional_semanas": 12,
             "pas_mmhg": 125, "pad_mmhg": 80, "utpi_crudo": 1.8, "plgf_crudo": 30}

    def test_los_dos_endpoints_dan_el_mismo_riesgo(self):
        directo = CalculadorRiesgosFMF.calcular_riesgo_preeclampsia_completo(
            edad_materna=40, peso_kg=100, talla_cm=158, semanas=12, pas_mmhg=125, pad_mmhg=80,
            utap_ip_promedio=1.8, plgf_pg_ml=30)
        adaptado = riesgo_preeclampsia_unificado(self.DATOS)
        self.assertAlmostEqual(adaptado["riesgo_porcentaje"], round(directo["riesgo_final"], 2), places=2)

    def test_la_respuesta_avisa_que_no_esta_validado(self):
        r = CalculadorRiesgosFMF.calcular_riesgo_preeclampsia_completo(edad_materna=30, peso_kg=60, talla_cm=160, semanas=12)
        self.assertIn("no es el algoritmo", r["advertencia"])
        self.assertIn("orientativa", riesgo_preeclampsia_unificado(
            {"edad_materna": 30, "peso_kg": 60, "talla_cm": 160, "edad_gestacional_semanas": 12})["interpretacion_clinica"])
