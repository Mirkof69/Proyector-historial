"""Tests para Calculadoras Obstétricas"""

from datetime import date, timedelta

from django.test import TestCase

from .utils import (
    calcular_edad_gestacional,
    calcular_fecha_probable_parto,
    calcular_imc,
    interpretar_imc_gestacional,
)


class CalculosObstetricosTestCase(TestCase):
    """Tests para cálculos obstétricos"""

    def test_calcular_edad_gestacional_fur(self):
        """Test cálculo de edad gestacional por FUR"""
        fur = date.today() - timedelta(weeks=20)
        resultado = calcular_edad_gestacional(fur=fur)

        self.assertIsNotNone(resultado)
        self.assertIn("semanas", resultado)
        self.assertIn("dias", resultado)
        self.assertEqual(resultado["semanas"], 20)

    def test_calcular_fpp(self):
        """Test cálculo de fecha probable de parto"""
        fur = date(2024, 1, 1)
        fpp = calcular_fecha_probable_parto(fur)

        self.assertIsNotNone(fpp)
        # FPP = FUR + 280 días
        esperado = fur + timedelta(days=280)
        self.assertEqual(fpp, esperado)

    def test_calcular_imc(self):
        """Test cálculo de IMC"""
        peso = 70  # kg
        talla = 1.65  # metros
        imc = calcular_imc(peso, talla)

        self.assertIsNotNone(imc)
        self.assertAlmostEqual(imc, 25.71, places=2)

    def test_interpretar_imc_gestacional(self):
        """Test interpretación de IMC gestacional"""
        imc = 25.5
        interpretacion = interpretar_imc_gestacional(imc, semanas_gestacion=20)

        self.assertIsNotNone(interpretacion)
        self.assertIn("categoria", interpretacion)
        self.assertIn("recomendacion", interpretacion)


class CalculosAvanzadosTestCase(TestCase):
    """Tests para cálculos avanzados"""

    def test_percentil_peso_fetal(self):
        """Test cálculo de percentil de peso fetal"""
        # placeholder

    def test_calculo_liquido_amniotico(self):
        """Test cálculo de líquido amniótico"""
        # placeholder
