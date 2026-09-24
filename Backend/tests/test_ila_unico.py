"""El ILA se clasifica igual en todo el sistema.

Fallo que previene: el modelo decía «Oligohidramnios» con ILA 7 y
«Polihidramnios» con ILA 22, mientras la calculadora daba «normal» para los
dos. La misma ecografía salía normal en una pantalla y patológica en otra.
"""
from decimal import Decimal

from django.test import SimpleTestCase

from calculadoras.utils import CalculadorasObstetricas
from ecografias.liquido_amniotico import clasificar_ila
from ecografias.models import Ecografia


class ClasificacionIlaTest(SimpleTestCase):
    def test_bordes(self):
        esperado = {
            4.0: "oligohidramnios", 5.0: "oligohidramnios", 5.1: "limite_bajo", 7.9: "limite_bajo",
            8.0: "normal", 22.0: "normal", 24.9: "normal", 25.0: "polihidramnios", 40.0: "polihidramnios",
        }
        for ila, codigo in esperado.items():
            self.assertEqual(clasificar_ila(ila)["codigo"], codigo, ila)

    def test_grados_de_polihidramnios(self):
        self.assertEqual(clasificar_ila(26)["grado"], "leve")
        self.assertEqual(clasificar_ila(31)["grado"], "moderado")
        self.assertEqual(clasificar_ila(36)["grado"], "severo")

    def test_sin_valor(self):
        self.assertIsNone(clasificar_ila(None))

    def test_modelo_y_calculadora_coinciden(self):
        """ESPERADO: el mismo texto en la ficha de la ecografía y en la calculadora."""
        for ila_cm in (4, 7, 14, 22, 26, 36):
            eco = Ecografia(indice_liquido_amniotico=Decimal(str(ila_cm)), edad_gestacional_semanas=30)
            mm = Decimal(ila_cm * 10) / 4
            calc = CalculadorasObstetricas.calcular_ila(mm, mm, mm, mm)
            self.assertEqual(eco.get_estado_liquido_amniotico(), calc["interpretacion_texto"], ila_cm)

    def test_ila_7_y_22_ya_no_son_patologicos(self):
        self.assertNotIn("Oligohidramnios", Ecografia(indice_liquido_amniotico=Decimal("7")).get_estado_liquido_amniotico())
        self.assertEqual(Ecografia(indice_liquido_amniotico=Decimal("22")).get_estado_liquido_amniotico(), "Normal")

    def test_el_percentil_no_es_un_diagnostico(self):
        texto = Ecografia(indice_liquido_amniotico=Decimal("7"), edad_gestacional_semanas=28).get_percentil_ila()
        self.assertNotIn("hidramnios", texto)
