"""Cada acción queda asociada a la sesión de login en que se hizo.

Pedido: «logs para cada sesión». Antes la auditoría registraba entradas,
salidas y acciones sueltas, sin forma de saber qué hizo alguien entre que
entró y salió.
"""
import datetime

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from auditoria.models import RegistroAuditoria
from pacientes.models import Paciente
from usuarios.models import Usuario


class SesionesAuditoriaTest(APITestCase):
    def setUp(self):
        self.enfermera = Usuario.objects.create_user(email="enf.ses@test.bo", nombre="Eva", apellido_paterno="Ses",
                                                     password="clave-segura-123", rol="enfermera")
        self.admin = Usuario.objects.create_user(email="adm.ses@test.bo", nombre="Ada", apellido_paterno="Ses",
                                                 password="clave-segura-123", rol="administrador")

    def _sesion_con_una_accion(self):
        c = APIClient()
        r = c.post(reverse("login"), {"email": self.enfermera.email, "password": "clave-segura-123"}, format="json")
        self.assertEqual(r.status_code, 200, r.content[:200])
        Paciente.objects.create(nombre="Tmp", apellido_paterno="Ses", apellido_materno="X",
                                fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci="7944001")
        c.get("/api/pacientes/")  # request autenticado con el token de la sesión
        c.post(reverse("logout"))
        return RegistroAuditoria.objects.filter(usuario=self.enfermera).exclude(sesion_id="")

    def test_login_y_logout_comparten_sesion(self):
        registros = self._sesion_con_una_accion()
        sids = set(registros.values_list("sesion_id", flat=True))
        self.assertEqual(len(sids), 1, sids)
        acciones = set(registros.values_list("accion", flat=True))
        self.assertTrue({"LOGIN", "LOGOUT"} <= acciones, acciones)

    def test_el_admin_ve_la_sesion_y_su_detalle(self):
        sid = self._sesion_con_una_accion().first().sesion_id
        c = APIClient()
        c.force_authenticate(self.admin)
        r = c.get("/api/auditoria/sesiones/")
        self.assertEqual(r.status_code, 200, r.content[:300])
        filas = r.json()["results"] if isinstance(r.json(), dict) else r.json()
        fila = next(f for f in filas if f["sesion_id"] == sid)
        self.assertTrue(fila["cerrada"])
        self.assertEqual(fila["usuario_rol"], "enfermera")
        detalle = c.get(f"/api/auditoria/sesiones/{sid}/")
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(detalle.json()[0]["accion"], "LOGIN")

    def test_otros_roles_no_ven_sesiones(self):
        c = APIClient()
        c.force_authenticate(Usuario.objects.create_user(email="med.ses@test.bo", nombre="M", apellido_paterno="S",
                                                         password="clave-segura-123", rol="medico"))
        self.assertEqual(c.get("/api/auditoria/sesiones/").status_code, 403)
