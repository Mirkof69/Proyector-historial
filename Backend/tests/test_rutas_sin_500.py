"""Quality gate: ninguna ruta GET de la API responde 500.

Recorre todas las rutas sin parámetros (≈300) con la base vacía, que es donde
aparecen los agregados en None y los campos mal escritos (así se encontraron
dos rutas de estadísticas que fallaban siempre). La salud del servicio de IA
puede dar 503: es su forma correcta de decir que el microservicio no está.
"""
from django.test import TestCase
from django.urls import get_resolver
from rest_framework.test import APIClient

from usuarios.models import Usuario

EXCLUIDAS = ("logout", "backup")  # cambian estado aunque sean GET/POST
PUEDEN_DAR_503 = ("/ai/health",)


def rutas_get_sin_parametros():
    rutas = set()

    def recorrer(patrones, prefijo=""):
        for p in patrones:
            texto = prefijo + str(p.pattern)
            if hasattr(p, "url_patterns"):
                recorrer(p.url_patterns, texto)
            elif "<" not in texto and "(?P" not in texto:
                limpio = texto.replace("^", "").replace("$", "").replace(r"\.(?P<format>[a-z0-9]+)/?", "")
                if limpio.startswith("api/") and not limpio.endswith("?") and not any(x in limpio for x in EXCLUIDAS):
                    rutas.add("/" + limpio)

    recorrer(get_resolver().url_patterns)
    return sorted(rutas)


class RutasSin500Test(TestCase):
    def test_ninguna_ruta_get_da_500(self):
        admin = Usuario.objects.create_user(email="adm.rutas@test.bo", nombre="A", apellido_paterno="R",
                                            password="clave-segura-123", rol="administrador")
        c = APIClient()
        c.force_authenticate(admin)
        rutas = rutas_get_sin_parametros()
        self.assertGreater(len(rutas), 200)
        fallos = []
        for ruta in rutas:
            try:
                r = c.get(ruta)
            except Exception as e:  # sin capturar = 500 en producción
                fallos.append(f"EXC {ruta}: {type(e).__name__}: {str(e)[:150]}")
                continue
            if r.status_code >= 500 and not (r.status_code == 503 and any(x in ruta for x in PUEDEN_DAR_503)):
                fallos.append(f"{r.status_code} {ruta}")
        detalle = "\n".join(fallos)
        self.assertFalse(fallos, f"{len(fallos)} de {len(rutas)} rutas fallan:\n{detalle}")
