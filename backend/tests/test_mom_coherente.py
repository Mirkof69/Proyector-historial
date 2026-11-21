"""El MoM (múltiplo de la mediana) sale en la escala correcta y coincide entre calculadoras.

Fallos que previene:
- MOMConverter usaba mediana 1,0 para todo: el «MoM» era el valor crudo (una
  PAM de 90 daba MoM 90) y el riesgo de preeclampsia calculado con él no
  tenía sentido.
- CalculadorMoM no reconocía «PAPP-A», «PlGF» ni «free_bhcg» (sus tablas
  usan PAPP_A, PLGF…): el registro de marcadores fallaba con todos.
- Un marcador sin mediana de referencia (sFlt-1) debe quedar sin MoM, no
  con uno inventado ni con un error 500.
"""
from django.test import SimpleTestCase

from calculadoras.services.calculador_mom import CalculadorMoM
from calculadoras.services.calculador_riesgos_fmf import CalculadorRiesgosFMF
from calculadoras.services.mom_converter import MOMConverter


class MomCoherenteTest(SimpleTestCase):
    def test_una_pam_normal_da_mom_cercano_a_1(self):
        """ESPERADO: PAM 87 a las 13 semanas ≈ MoM 1,0 (antes: 87)."""
        mom = MOMConverter().calcular_mom("pam", 87, 13 * 7, 65)["mom"]
        self.assertAlmostEqual(mom, 1.0, places=2)

    def test_las_dos_calculadoras_dan_el_mismo_mom_de_pam(self):
        c = MOMConverter().calcular_mom("pam", 95, 12 * 7, 65)["mom"]
        f = CalculadorRiesgosFMF._calcular_map_mom(95, 12)
        self.assertAlmostEqual(c, f, places=2)

    def test_uta_pi_usa_la_misma_mediana_en_las_dos(self):
        c = MOMConverter().calcular_mom("utpi", 1.6, 12 * 7, 65)
        self.assertAlmostEqual(c["mediana_base"], CalculadorMoM.obtener_mediana_esperada("UTA_PI", 12), places=3)

    def test_nombres_de_marcador_con_guion_o_minusculas(self):
        for nombre in ("PAPP-A", "pappa", "PAPP_A"):
            self.assertEqual(CalculadorMoM.obtener_mediana_esperada(nombre, 12),
                             CalculadorMoM.PAPP_A_MEDIANAS[12], nombre)
        self.assertEqual(CalculadorMoM.obtener_mediana_esperada("PlGF", 12),
                         CalculadorMoM.obtener_mediana_esperada("PLGF", 12))

    def test_sin_mediana_no_hay_mom_inventado(self):
        with self.assertRaises(ValueError):
            MOMConverter().calcular_mom("sflt1", 1500, 84, 65)
        with self.assertRaises(ValueError):
            CalculadorMoM.obtener_mediana_esperada("sFlt-1", 12)

    def test_sigue_avisando_que_no_hay_ajuste_poblacional(self):
        r = MOMConverter().calcular_mom("pam", 90, 84, 65)
        self.assertFalse(r["ajustado_poblacionalmente"])
        self.assertTrue(r["advertencia"])
