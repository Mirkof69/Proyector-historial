"""Tests de compresión de las respuestas de la API.

Por qué existe este archivo
---------------------------
La API enviaba el JSON sin comprimir. Medido contra los datos reales del
tenant de demostración:

    listar pacientes    164,9 KB  ->  18,7 KB   (89% menos)
    notificaciones       54,5 KB  ->   1,6 KB   (97% menos)
    buscar paciente      20,1 KB  ->   3,1 KB   (85% menos)

En la red 3G de una clínica (400 kbps) eso es la diferencia entre 3,4
segundos y 0,4 por abrir la lista de pacientes. Es el mayor ahorro
disponible para móvil, y cuesta una línea de middleware.

Estos tests fijan que la compresión siga activa: si alguien la quita en un
refactor, la aplicación no falla —solo se vuelve lenta en móvil, que es
justo el tipo de regresión que nadie nota hasta que una médica se queja.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime
import gzip
import json

from django.test import TestCase
from rest_framework.test import APITestCase

from pacientes.models import Paciente
from usuarios.models import Usuario


class MiddlewareDeCompresionTest(TestCase):
    """El middleware tiene que estar puesto, y en el orden correcto."""

    def test_gzip_esta_en_la_cadena(self):
        """ESPERADO: GZipMiddleware presente en MIDDLEWARE."""
        from django.conf import settings

        assert "django.middleware.gzip.GZipMiddleware" in settings.MIDDLEWARE, (
            "Sin GZipMiddleware la API envía el JSON en crudo: el listado de "
            "pacientes pasa de 19 KB a 165 KB."
        )

    def test_va_antes_que_el_resto_del_stack(self):
        """ESPERADO: entre los tres primeros.

        Debe comprimir la respuesta YA terminada. Si queda por debajo, el
        resto del stack la modifica después de comprimirla.
        """
        from django.conf import settings

        posicion = settings.MIDDLEWARE.index("django.middleware.gzip.GZipMiddleware")
        assert posicion <= 2, (
            f"GZipMiddleware está en la posición {posicion}; debe ir arriba "
            f"para comprimir la respuesta completa."
        )


class RespuestasComprimidasTest(APITestCase):
    """Una respuesta grande debe llegar comprimida al navegador."""

    @classmethod
    def setUpTestData(cls):
        """Pacientes suficientes para superar el umbral del middleware.

        Django no comprime respuestas menores de 200 bytes: no compensa. Hacen
        falta datos de verdad para comprobar el comportamiento real.
        """
        cls.medica = Usuario.objects.create_user(
            email="dra.compresion@test.bo",
            nombre="Elena",
            apellido_paterno="Choque",
            password="clave-de-prueba-123",
            rol="medico",
        )
        for i in range(40):
            Paciente.objects.create(
                nombre=f"Paciente{i}",
                apellido_paterno="Mamani",
                apellido_materno="Choque",
                fecha_nacimiento=datetime.date(1990, 5, 15),
                genero="femenino",
                ci=f"7{i:06d}",
            )

    def setUp(self):
        self.client.force_authenticate(user=self.medica)

    def test_el_listado_llega_comprimido(self):
        """ESPERADO: cabecera Content-Encoding: gzip."""
        respuesta = self.client.get("/api/pacientes/", HTTP_ACCEPT_ENCODING="gzip")

        assert respuesta.status_code == 200
        assert respuesta.get("Content-Encoding") == "gzip", (
            f"Esperado 'gzip', obtenido {respuesta.get('Content-Encoding')!r}. "
            f"La respuesta viaja sin comprimir."
        )

    def test_comprimido_pesa_mucho_menos(self):
        """ESPERADO: al menos 60% menos que el JSON en crudo.

        En la práctica el JSON de pacientes baja un 89%; se exige 60% para
        dejar margen a que cambien los campos sin volver el test frágil.
        """
        comprimida = self.client.get("/api/pacientes/", HTTP_ACCEPT_ENCODING="gzip")
        crudo = gzip.decompress(comprimida.content)

        ahorro = 1 - len(comprimida.content) / len(crudo)
        assert ahorro >= 0.60, (
            f"Solo se ahorra un {ahorro:.0%}; se esperaba al menos 60%. "
            f"Crudo {len(crudo)} bytes, comprimido {len(comprimida.content)}."
        )

    def test_el_contenido_sigue_siendo_el_mismo(self):
        """ESPERADO: los datos no cambian al comprimir.

        Comprimir es transparente: la médica tiene que ver exactamente los
        mismos pacientes.
        """
        comprimida = self.client.get("/api/pacientes/", HTTP_ACCEPT_ENCODING="gzip")
        datos = json.loads(gzip.decompress(comprimida.content))

        assert datos["count"] == Paciente.objects.count()
        assert len(datos["results"]) == Paciente.objects.count()

    def test_sin_soporte_del_cliente_no_se_comprime(self):
        """ESPERADO: sin Accept-Encoding gzip, la respuesta va en crudo.

        Un cliente viejo que no sepa descomprimir debe seguir funcionando.
        """
        respuesta = self.client.get("/api/pacientes/", HTTP_ACCEPT_ENCODING="identity")

        assert respuesta.status_code == 200
        assert respuesta.get("Content-Encoding") != "gzip"
        assert json.loads(respuesta.content)["count"] == Paciente.objects.count()
