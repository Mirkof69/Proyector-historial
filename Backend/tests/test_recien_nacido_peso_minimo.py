"""Un recién nacido de 300 g se puede guardar (BUG-010).

El campo, el serializer y el formulario aceptaban 300 g, pero `clean()` del
modelo exigía 400 g y el parto no se guardaba.
"""
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from partos.models import RecienNacido


def _errores(**datos):
    try:
        RecienNacido(**datos).clean()
    except ValidationError as e:
        return e.message_dict
    return {}


class PesoMinimoRecienNacidoTest(SimpleTestCase):
    def test_300_g_es_valido(self):
        self.assertNotIn("peso_nacimiento", _errores(peso_nacimiento=300, apgar_1_minuto=7, apgar_5_minutos=8))

    def test_299_g_se_rechaza_con_el_minimo(self):
        errores = _errores(peso_nacimiento=299, apgar_1_minuto=7, apgar_5_minutos=8)
        self.assertIn("300 g", errores["peso_nacimiento"][0])
