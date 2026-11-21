"""Tests para cache_utils (generación de claves e invalidación)."""
from django.test import TestCase

from .decorators import _generate_cache_key


class _Obj:
    def __init__(self, id):
        self.id = id


class GenerateCacheKeyTest(TestCase):
    def test_clave_con_prefijo_y_args(self):
        self.assertEqual(_generate_cache_key("pac", 1, 2), "pac:1:2")

    def test_usa_id_de_objetos(self):
        self.assertEqual(_generate_cache_key("pac", _Obj(42)), "pac:42")

    def test_kwargs_ordenados_para_consistencia(self):
        # El orden de kwargs no debe alterar la clave (se ordenan)
        k1 = _generate_cache_key("q", b=2, a=1)
        k2 = _generate_cache_key("q", a=1, b=2)
        self.assertEqual(k1, k2)
        self.assertEqual(k1, "q:a=1:b=2")

    def test_kwarg_con_objeto_usa_id(self):
        self.assertEqual(_generate_cache_key("q", paciente=_Obj(7)), "q:paciente=7")
