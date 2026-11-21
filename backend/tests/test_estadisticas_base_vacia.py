"""Ningún endpoint de estadísticas revienta con la base vacía.

Con cero registros los agregados (Avg, Max, Sum) devuelven None y cualquier
round(None) o float(None) da un 500: justo lo que ve una clínica nueva el
primer día. Recorre todas las rutas GET sin parámetros de la API cuyo nombre
indica estadísticas, resúmenes o tableros.
"""
import re

from django.test import TestCase
from django.urls import get_resolver
from rest_framework.test import APIClient

from usuarios.models import Usuario

PALABRAS = re.compile(r"estadistic|statistic|resumen|dashboard|kpi|indicador|tendencia", re.I)


def _rutas_sin_parametros():
    rutas = set()

    def recorrer(patrones, prefijo=""):
        for p in patrones:
            texto = prefijo + str(p.pattern)
            if hasattr(p, "url_patterns"):
                recorrer(p.url_patterns, texto)
            elif "<" not in texto and "(?P" not in texto and PALABRAS.search(texto):
                limpio = texto.replace("^", "").replace("$", "").replace(r"\.(?P<format>[a-z0-9]+)/?", "")
                if limpio.startswith("api/") and not limpio.endswith("?"):
                    rutas.add("/" + limpio)

    recorrer(get_resolver().url_patterns)
    return sorted(rutas)


class EstadisticasBaseVaciaTest(TestCase):
    def test_ninguna_da_500(self):
        admin = Usuario.objects.create_user(email="adm.vacia@test.bo", nombre="A", apellido_paterno="V",
                                            password="clave-segura-123", rol="administrador")
        c = APIClient()
        c.force_authenticate(admin)
        rutas = _rutas_sin_parametros()
        self.assertGreater(len(rutas), 10, rutas)
        fallos = []
        for ruta in rutas:
            try:
                r = c.get(ruta)
                if r.status_code >= 500:
                    fallos.append(f"{r.status_code} {ruta}")
            except Exception as e:  # excepción no capturada = 500 en producción
                fallos.append(f"EXC {ruta}: {type(e).__name__}: {e}")
        detalle = "\n".join(f[:220] for f in fallos)
        self.assertFalse(fallos, f"{len(fallos)} de {len(rutas)} rutas fallan:\n{detalle}")
