"""Cortes de las calculadoras en el límite exacto (BUG-005 y BUG-006).

64 kg y 160 cm dan 24,999999999999996 en coma flotante: sin redondear, un IMC
de 25,0 salía «Normal» y uno de 30,0 «Sobrepeso». Bishop 5 salía «intermedio»
en la calculadora rápida y «desfavorable» en la especializada.
"""
from decimal import Decimal

from django.test import SimpleTestCase

from calculadoras.utils import CalculadorasObstetricas as C


class CortesIMCTest(SimpleTestCase):
    def test_imc_25_es_sobrepeso(self):
        r = C.calcular_imc(Decimal("64"), Decimal("160"))
        self.assertEqual((r["imc"], r["clasificacion"]), (25.0, "sobrepeso"))

    def test_imc_30_es_obesidad(self):
        r = C.calcular_imc(Decimal("76.8"), Decimal("160"))
        self.assertEqual(r["imc"], 30.0)
        self.assertTrue(r["clasificacion"].startswith("obesidad"))


class CortesBishopTest(SimpleTestCase):
    def test_bishop_5_desfavorable(self):
        # dilatación 1-2 (1), borramiento 40-50 (1), estación -2 (1), media (1), media (1)
        r = C.calcular_bishop(2, 45, -2, 1, 1)
        self.assertEqual(r["puntaje_total"], 5)
        self.assertIn("desfavorable", r["interpretacion"])

    def test_bishop_6_intermedio_y_8_favorable(self):
        self.assertIn("intermedio", C.calcular_bishop(2, 45, -2, 2, 1)["interpretacion"])
        self.assertIn("favorable", C.calcular_bishop(3, 65, -1, 1, 1)["interpretacion"])
