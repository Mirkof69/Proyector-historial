"""Tests para Calculadoras Obstétricas"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from .services.mom_converter import MOMConverter
from .utils import (
    CalculadorasObstetricas,
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

    def test_peso_fetal_hadlock(self):
        """El peso fetal por Hadlock cae en un rango fisiológico y trae percentil.

        La fórmula de Hadlock implementada consume las medidas en cm
        (DBP≈8.5, CA≈30, FL≈6.5 para ~34 semanas).
        """
        resultado = CalculadorasObstetricas.calcular_peso_fetal(
            dbp=Decimal("8.5"),
            _cc=Decimal("31.0"),
            ca=Decimal("30.0"),
            lf=Decimal("6.5"),
            semanas_gestacion=34,
        )
        self.assertIn("peso_estimado", resultado)
        self.assertIn("percentil", resultado)
        # Un feto de ~34 semanas pesa aproximadamente 1.8–3.0 kg
        self.assertGreater(resultado["peso_estimado"], 1000)
        self.assertLess(resultado["peso_estimado"], 5000)

    def test_ila_normal(self):
        """4 cuadrantes de 40 mm → 16 cm → interpretación normal."""
        resultado = CalculadorasObstetricas.calcular_ila(
            Decimal("40"), Decimal("40"), Decimal("40"), Decimal("40"),
        )
        self.assertEqual(resultado["ila_cm"], 16.0)
        self.assertEqual(resultado["interpretacion"], "normal")

    def test_ila_oligohidramnios(self):
        """Suma < 50 mm (< 5 cm) → oligohidramnios."""
        resultado = CalculadorasObstetricas.calcular_ila(
            Decimal("10"), Decimal("10"), Decimal("10"), Decimal("10"),
        )
        self.assertEqual(resultado["ila_cm"], 4.0)
        self.assertEqual(resultado["interpretacion"], "oligohidramnios")

    def test_ila_polihidramnios(self):
        """Suma > 250 mm (> 25 cm) → polihidramnios."""
        resultado = CalculadorasObstetricas.calcular_ila(
            Decimal("80"), Decimal("80"), Decimal("80"), Decimal("80"),
        )
        self.assertEqual(resultado["ila_cm"], 32.0)
        self.assertEqual(resultado["interpretacion"], "polihidramnios")


class MOMConverterTestCase(TestCase):
    """Tests del convertidor MoM — verifica el cálculo y el flag de honestidad."""

    def setUp(self):
        self.converter = MOMConverter()

    def test_mom_marca_resultado_como_no_ajustado(self):
        """Sin referencias poblacionales, el MoM debe declararse no ajustado."""
        resultado = self.converter.calcular_mom(
            marcador="pappa",
            valor_crudo=1.0,
            edad_gestacional_dias=84,
            peso_kg=65,
        )
        # Con mediana_base=1.0 y factores neutros, MoM == valor_crudo
        self.assertEqual(resultado["mom"], 1.0)
        self.assertFalse(resultado["ajustado_poblacionalmente"])
        self.assertIsNotNone(resultado["advertencia"])

    def test_mom_semaforo_verde_en_rango_normal(self):
        """Un MoM de 1.0 debe interpretarse como normal (semáforo verde)."""
        resultado = self.converter.calcular_mom(
            marcador="pappa",
            valor_crudo=1.0,
            edad_gestacional_dias=84,
            peso_kg=65,
        )
        self.assertEqual(resultado["semaforo"], "verde")

    def test_mom_semaforo_rojo_valor_muy_bajo(self):
        """Un valor crudo muy bajo debe disparar semáforo rojo (alto riesgo)."""
        resultado = self.converter.calcular_mom(
            marcador="pappa",
            valor_crudo=0.3,
            edad_gestacional_dias=84,
            peso_kg=65,
        )
        self.assertEqual(resultado["semaforo"], "rojo")

    def test_z_score(self):
        """Z-score = (valor - media) / desviación."""
        self.assertEqual(self.converter.calcular_z_score(12, 10, 2), 1.0)
        self.assertEqual(self.converter.calcular_z_score(10, 10, 0), 0)
