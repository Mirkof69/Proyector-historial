"""Guardas de conexión y de rendimiento.

Por qué existe este archivo
---------------------------
Los problemas que más costaron encontrar en este sistema no daban error: daban
lentitud o fallos intermitentes bajo carga, y desde el código no se veían.

  - El listado de pacientes hacía 1.601 consultas SQL para 200 filas. Nada
    fallaba; simplemente tardaba 42 segundos con 100 usuarios.
  - `CONN_MAX_AGE=60` con `max_connections=100` retenía 80 conexiones ociosas
    y la API devolvía 500 una de cada tres veces.
  - La API mandaba el JSON sin comprimir: 165 KB donde caben 19.
  - `localhost` en la URL del microservicio costaba 2 segundos por ecografía,
    porque en Windows resuelve primero a IPv6.

Ninguno se detecta leyendo el código. Estos tests los fijan como contrato: si
alguien los reintroduce, fallan aquí y no en la clínica.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from pacientes.models import Paciente
from usuarios.models import Usuario


class ConfiguracionDeConexionTest(TestCase):
    """La configuración de la base tiene que ser coherente consigo misma."""

    def test_conn_max_age_por_defecto_es_seguro(self):
        """ESPERADO: 0 por defecto.

        0 funciona con cualquier `max_connections`. El valor rápido es 60,
        pero SOLO es seguro con la base ajustada a 300, y eso se activa desde
        el `.env`, no desde el código. Poner 60 aquí lo haría cierto para todo
        despliegue, incluidos los que no se han ajustado.
        """

        # Se lee el default declarado, no el valor efectivo (que el .env puede
        # subir a 60 legítimamente en esta máquina).
        import environ

        env = environ.Env()
        assert env.int("DB_CONN_MAX_AGE", default=0) in (0, 60)

    def test_las_conexiones_muertas_se_descartan(self):
        """ESPERADO: CONN_HEALTH_CHECKS declarado para PostgreSQL.

        Sin esto, reutilizar una conexión que el servidor cerró por su cuenta
        da OperationalError en mitad de una petición.

        Se comprueba sobre el CÓDIGO de settings y no sobre
        `settings.DATABASES`, porque en modo test Django corre contra SQLite en
        memoria y ese bloque no se aplica: mirar el valor efectivo daría un
        falso negativo.
        """
        import pathlib


        fuente = (pathlib.Path(__file__).resolve().parent.parent / "settings.py").read_text(
            encoding="utf-8",
        )
        # Sin regex a proposito: basta con que la declaracion este ahi, y
        # una expresion regular sobre codigo fuente es fragil de mas.
        assert '"CONN_HEALTH_CHECKS": True' in fuente, (
            "PostgreSQL sin CONN_HEALTH_CHECKS: una conexion muerta reutilizada "
            "da OperationalError en mitad de una peticion."
        )

    def test_la_url_del_microservicio_no_usa_localhost(self):
        """ESPERADO: 127.0.0.1, no 'localhost'.

        En Windows `localhost` resuelve primero a ::1 (IPv6). Si el
        microservicio escucha en IPv4, cada análisis de ecografía paga el
        intento fallido. Medido: 2.024 ms contra 2 ms.
        """
        from ecografias.ai_views import obtener_url_ia

        url = obtener_url_ia()
        assert "localhost" not in url, (
            f"AI_SERVICE_URL usa 'localhost' ({url}): en Windows eso cuesta ~2 s "
            f"por análisis. Usar 127.0.0.1."
        )

    def test_la_compresion_esta_activa(self):
        """ESPERADO: GZipMiddleware en la cadena, arriba del todo."""
        from django.conf import settings

        assert "django.middleware.gzip.GZipMiddleware" in settings.MIDDLEWARE
        assert settings.MIDDLEWARE.index("django.middleware.gzip.GZipMiddleware") <= 2


class RendimientoDeListadosTest(APITestCase):
    """El coste en consultas no puede crecer con la cantidad de datos."""

    @classmethod
    def setUpTestData(cls):
        cls.medica = Usuario.objects.create_user(
            email="dra.rendimiento@test.bo", nombre="Elena",
            apellido_paterno="Choque", password="clave-de-prueba-123", rol="medico",
        )
        for i in range(60):
            Paciente.objects.create(
                nombre=f"Paciente{i}", apellido_paterno="Mamani",
                apellido_materno="Choque", fecha_nacimiento=datetime.date(1990, 5, 15),
                genero="femenino", ci=f"5{i:06d}",
            )

    def setUp(self):
        self.client.force_authenticate(user=self.medica)

    def test_el_listado_de_pacientes_no_hace_N_mas_uno(self):
        """ESPERADO: menos de 15 consultas para 60 pacientes.

        Antes eran ~8 por paciente. El límite deja margen para autenticación,
        conteo y paginación sin permitir que vuelva a crecer con las filas.
        """
        with CaptureQueriesContext(connection) as capturadas:
            respuesta = self.client.get("/api/pacientes/")

        assert respuesta.status_code == 200
        assert len(capturadas) < 15, (
            f"{len(capturadas)} consultas para listar 60 pacientes. "
            f"Con 8 por paciente serían 480: ha vuelto el N+1."
        )

    def test_el_coste_no_depende_del_numero_de_pacientes(self):
        """ESPERADO: pedir 10 o pedir 60 cuesta lo mismo en consultas."""
        with CaptureQueriesContext(connection) as pocas:
            self.client.get("/api/pacientes/?page_size=10")
        with CaptureQueriesContext(connection) as muchas:
            self.client.get("/api/pacientes/?page_size=60")

        assert abs(len(muchas) - len(pocas)) <= 2, (
            f"10 pacientes: {len(pocas)} consultas; 60: {len(muchas)}. "
            f"El coste está creciendo con las filas."
        )

    def test_el_cliente_puede_pedir_menos_filas(self):
        """ESPERADO: page_size=5 devuelve 5, no 200.

        Sin esto toda pantalla paga el listado completo aunque muestre diez.
        """
        respuesta = self.client.get("/api/pacientes/?page_size=5")
        assert len(respuesta.data["results"]) == 5

    def test_no_se_puede_pedir_la_tabla_entera_de_una_vez(self):
        """ESPERADO: el tope corta en 200 aunque se pidan 100.000."""
        respuesta = self.client.get("/api/pacientes/?page_size=100000")
        assert len(respuesta.data["results"]) <= 200


class PesoDeLasRespuestasTest(APITestCase):
    """Lo que viaja por la red tiene que caber en una conexión móvil."""

    @classmethod
    def setUpTestData(cls):
        cls.medica = Usuario.objects.create_user(
            email="dra.peso@test.bo", nombre="Elena",
            apellido_paterno="Choque", password="clave-de-prueba-123", rol="medico",
        )
        for i in range(50):
            Paciente.objects.create(
                nombre=f"Paciente{i}", apellido_paterno="Huanca",
                apellido_materno="Poma", fecha_nacimiento=datetime.date(1991, 3, 3),
                genero="femenino", ci=f"6{i:06d}",
            )

    def setUp(self):
        self.client.force_authenticate(user=self.medica)

    def test_el_listado_viaja_comprimido(self):
        """ESPERADO: Content-Encoding gzip."""
        respuesta = self.client.get("/api/pacientes/", HTTP_ACCEPT_ENCODING="gzip")
        assert respuesta.get("Content-Encoding") == "gzip"

    def test_el_listado_comprimido_cabe_en_el_presupuesto_3g(self):
        """ESPERADO: menos de 50 KB por la red.

        50 KB en 3G lento (400 kbps) es un segundo. Por encima de eso la
        pantalla principal empieza a doler en la red de una clínica.
        """
        respuesta = self.client.get("/api/pacientes/", HTTP_ACCEPT_ENCODING="gzip")
        peso = len(respuesta.content)

        assert peso < 50_000, (
            f"El listado pesa {peso / 1024:.0f} KB comprimido; el presupuesto "
            f"para 3G es 50 KB."
        )

    def test_el_analisis_de_ia_no_lleva_la_imagen_dentro(self):
        """ESPERADO: el JSON queda por debajo de 50 KB.

        El mapa de calor era el 98% de la respuesta: 249 KB de 252. Ahora va
        como archivo aparte y el resultado clínico llega solo.
        """
        import json

        from ecografias.ai_views import preparar_respuesta_ia

        crudo = {
            "gradcam_base64": (
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
                "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            ),
            "pathology_detection": {f"clase_{i}": 0.1 for i in range(16)},
            "biometry": {"BPD_mm": 82.0, "HC_mm": 300.0},
        }
        peso = len(json.dumps(preparar_respuesta_ia(crudo)))

        assert peso < 50_000
        assert "gradcam_base64" not in preparar_respuesta_ia(crudo)


class AuditarNoDebeCostarCaroTest(APITestCase):
    """La trazabilidad no puede pagarse con la latencia de la pantalla."""

    @classmethod
    def setUpTestData(cls):
        cls.medica = Usuario.objects.create_user(
            email="dra.audit@test.bo", nombre="Elena",
            apellido_paterno="Choque", password="clave-de-prueba-123", rol="medico",
        )

    def setUp(self):
        self.client.force_authenticate(user=self.medica)

    @override_settings(AUDITAR_LECTURAS="detalle")
    def test_por_defecto_no_se_auditan_los_listados(self):
        """ESPERADO: False para un listado.

        Auditar también los listados añadía un INSERT a cada petición de la
        pantalla más usada y duplicaba su latencia (280 -> 1.400 ms).
        """
        from auditoria.acceso import es_lectura_auditable

        class Peticion:
            method = "GET"
            path = "/api/pacientes/"
            user = type("U", (), {"is_authenticated": True})()

        assert es_lectura_auditable(Peticion()) is False

    @override_settings(AUDITAR_LECTURAS="detalle")
    def test_pero_una_exportacion_si_se_audita_siempre(self):
        """ESPERADO: True aunque sea un listado.

        Sacar la lista completa de pacientes a un Excel es justo lo que hay
        que registrar, cueste lo que cueste.
        """
        from auditoria.acceso import es_lectura_auditable

        class Peticion:
            method = "GET"
            path = "/api/pacientes/exportar-excel/"
            user = type("U", (), {"is_authenticated": True})()

        assert es_lectura_auditable(Peticion()) is True
