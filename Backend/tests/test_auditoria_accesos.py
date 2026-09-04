"""Tests del registro de accesos: quién vio qué historia clínica y cuándo.

Por qué existe este archivo
---------------------------
La acción `VER` estaba declarada en `RegistroAuditoria.ACCIONES` desde el
principio, pero **nunca se registraba**: había 0 filas con esa acción en una
base con 18.834 registros de auditoría. Es decir, el sistema sabía quién creó
y quién editó, pero no quién *consultó* una historia clínica — que en un
hospital es precisamente el acceso que hay que poder auditar.

Cada test declara el resultado esperado y lo compara con el obtenido.
"""

import datetime

from django.test import TestCase
from rest_framework.test import APITestCase

from auditoria.acceso import describir_ruta, es_lectura_auditable
from auditoria.models import RegistroAuditoria
from pacientes.models import Paciente
from usuarios.models import Usuario


class DescribirRutaTest(TestCase):
    """La ruta debe traducirse a (módulo, id) de forma predecible."""

    def test_detalle_de_paciente(self):
        """ESPERADO: ('Paciente', '14')"""
        assert describir_ruta("/api/pacientes/14/") == ("Paciente", "14")

    def test_accion_anidada_conserva_el_id(self):
        """ESPERADO: ('Paciente', '14') aunque la ruta siga con sub-acciones."""
        assert describir_ruta("/api/pacientes/14/historia-clinica/") == ("Paciente", "14")

    def test_listado_sin_id(self):
        """ESPERADO: ('Paciente', '') — es un listado, no un registro."""
        assert describir_ruta("/api/pacientes/") == ("Paciente", "")

    def test_modulos_clinicos_reconocidos(self):
        """ESPERADO: cada módulo clínico se identifica por su nombre real."""
        assert describir_ruta("/api/embarazos/3/")[0] == "Embarazo"
        assert describir_ruta("/api/ecografias/")[0] == "Ecografia"
        assert describir_ruta("/api/controles/7/")[0] == "ControlPrenatal"

    def test_rutas_no_clinicas_se_ignoran(self):
        """ESPERADO: ('', '') — no son datos de pacientes, no se auditan."""
        assert describir_ruta("/api/schema/") == ("", "")
        assert describir_ruta("/api/usuarios/2/") == ("", "")
        assert describir_ruta("/admin/") == ("", "")


class EsLecturaAuditableTest(TestCase):
    """Solo se audita la lectura clínica de un usuario autenticado."""

    class _Req:
        def __init__(self, method, path, user):
            self.method = method
            self.path = path
            self.user = user

    class _Usuario:
        is_authenticated = True

    class _Anonimo:
        is_authenticated = False

    def test_get_clinico_autenticado_si_se_audita(self):
        """ESPERADO: True."""
        r = self._Req("GET", "/api/pacientes/14/", self._Usuario())
        assert es_lectura_auditable(r) is True

    def test_escritura_no_se_audita_aqui(self):
        """ESPERADO: False — los POST ya los cubren los signals.

        Si esto devolviera True, cada creación quedaría registrada dos veces.
        """
        r = self._Req("POST", "/api/pacientes/", self._Usuario())
        assert es_lectura_auditable(r) is False

    def test_anonimo_no_se_audita(self):
        """ESPERADO: False — sin usuario no hay acceso que atribuir."""
        r = self._Req("GET", "/api/pacientes/14/", self._Anonimo())
        assert es_lectura_auditable(r) is False

    def test_infraestructura_no_se_audita(self):
        """ESPERADO: False — el esquema OpenAPI no es un dato clínico."""
        r = self._Req("GET", "/api/schema/", self._Usuario())
        assert es_lectura_auditable(r) is False


class RegistroDeAccesoConMiddlewareTest(APITestCase):
    """Al consultar una paciente debe quedar una fila VER con quién y qué.

    El middleware se instancia a mano en vez de confiar en `settings.MIDDLEWARE`
    porque `conftest.py` quita `AuditoriaMiddleware` en toda la suite (necesita
    contexto de tenant). Ejercitarlo aquí de forma explícita es lo que evita que
    esta protección quede, otra vez, sin ninguna prueba que la cubra.
    """

    def setUp(self):
        """Una médica y una paciente reales."""
        self.medica = Usuario.objects.create_user(
            email="dra.acceso@test.bo",
            nombre="Elena",
            apellido_paterno="Choque",
            password="clave-de-prueba-123",
            rol="medico",
        )
        self.paciente = Paciente.objects.create(
            nombre="Rosa",
            apellido_paterno="Yujra",
            apellido_materno="Cusi",
            fecha_nacimiento=datetime.date(1993, 6, 1),
            genero="femenino",
            ci="6655443",
        )
        self.client.force_authenticate(user=self.medica)

    def _consultar_con_auditoria(self, url):
        """Hace la petición y la pasa por el middleware de auditoría real."""
        from auditoria.middleware import AuditoriaMiddleware

        respuesta = self.client.get(url)
        peticion = respuesta.wsgi_request
        peticion.user = self.medica
        AuditoriaMiddleware(lambda _req: respuesta)(peticion)
        return respuesta

    def test_consultar_una_paciente_deja_registro_VER(self):
        """ESPERADO: 1 fila VER con el usuario, el módulo y el id correctos."""
        antes = RegistroAuditoria.objects.filter(accion="VER").count()

        respuesta = self._consultar_con_auditoria(f"/api/pacientes/{self.paciente.id}/")
        assert respuesta.status_code == 200

        registros = RegistroAuditoria.objects.filter(accion="VER").order_by("-id")
        assert registros.count() == antes + 1, (
            "No quedó registro de que se consultó la historia de la paciente."
        )

        r = registros.first()
        assert r.modulo == "Paciente"
        assert r.registro_id == str(self.paciente.id)
        assert r.usuario_id == self.medica.id
        assert r.usuario_rol == "medico"

    def test_el_registro_guarda_el_quien_y_el_donde(self):
        """ESPERADO: usuario, rol, endpoint y fecha quedan guardados.

        Es lo que hace utilizable la auditoría: sin el "quién" y el "dónde"
        solo queda saber que alguien miró algo.
        """
        self._consultar_con_auditoria(f"/api/pacientes/{self.paciente.id}/")
        r = RegistroAuditoria.objects.filter(accion="VER").order_by("-id").first()

        assert r is not None, "No se registró el acceso."
        assert r.usuario_nombre, "Falta el nombre del usuario."
        assert r.usuario_rol == "medico"
        assert r.endpoint, "Falta el endpoint consultado."
        assert r.fecha is not None

    def test_una_respuesta_de_error_no_deja_registro_de_acceso(self):
        """ESPERADO: 0 filas nuevas — no hubo acceso a los datos, hubo un rechazo.

        Registrar un acceso que nunca ocurrió falsearía la auditoría.
        """
        from auditoria.middleware import AuditoriaMiddleware

        respuesta = self.client.get(f"/api/pacientes/{self.paciente.id}/")
        peticion = respuesta.wsgi_request
        peticion.user = self.medica
        antes = RegistroAuditoria.objects.filter(accion="VER").count()

        respuesta.status_code = 403
        AuditoriaMiddleware(lambda _req: respuesta)(peticion)

        assert RegistroAuditoria.objects.filter(accion="VER").count() == antes
