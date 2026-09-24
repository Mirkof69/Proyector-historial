"""Permisos y configuración segura del Sprint 1.

Cada test fija un hueco concreto de la auditoría del 24-09-2026.
"""
import datetime

from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from pacientes.models import Paciente
from usuarios.models import Usuario


def _usuario(rol, email):
    return Usuario.objects.create_user(email=email, nombre="N", apellido_paterno="A",
                                       password="clave-segura-123", rol=rol)


class RecepcionYDatosClinicosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.recepcion = _usuario("recepcion", "recep.s1@test.bo")
        cls.sin_rol = _usuario("", "sinrol.s1@test.bo")
        cls.paciente = Paciente.objects.create(
            nombre="Luz", apellido_paterno="Test", apellido_materno="S1",
            fecha_nacimiento=datetime.date(1995, 5, 5), genero="femenino", ci="7811001")

    def _get(self, usuario, url):
        c = APIClient()
        c.force_authenticate(usuario)
        return c.get(url)

    def test_recepcion_ve_el_listado_de_pacientes(self):
        self.assertEqual(self._get(self.recepcion, "/api/pacientes/").status_code, 200)

    def test_recepcion_no_ve_la_historia_clinica(self):
        """ESPERADO: 403. Antes el bloqueo iba solo por prefijo y
        /api/pacientes/<id>/historia-clinica/ le quedaba abierto."""
        for accion in ("historia-clinica", "historial-completo", "examenes-laboratorio",
                       "antecedentes-personales", "reporte-pdf"):
            r = self._get(self.recepcion, f"/api/pacientes/{self.paciente.pk}/{accion}/")
            self.assertEqual(r.status_code, 403, accion)

    def test_un_usuario_sin_rol_no_lee_nada(self):
        """ESPERADO: 403. Antes un rol vacío o desconocido podía hacer GET a todo."""
        self.assertEqual(self._get(self.sin_rol, "/api/pacientes/").status_code, 403)
        self.assertEqual(self._get(self.sin_rol, "/api/embarazos/").status_code, 403)

    def test_recepcion_no_ve_estadisticas(self):
        self.assertEqual(self._get(self.recepcion, "/api/reportes/statistics/all/").status_code, 403)


class BorrarEcografiaTest(TestCase):
    def test_enfermeria_no_puede_borrar_una_ecografia(self):
        from ecografias.models import Ecografia
        from embarazos.models import Embarazo

        enfermera = _usuario("enfermera", "enf.s1@test.bo")
        paciente = Paciente.objects.create(
            nombre="Eva", apellido_paterno="Eco", apellido_materno="S1",
            fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci="7811002")
        embarazo = Embarazo.objects.create(
            paciente=paciente, numero_gesta=1, fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=20))
        eco = Ecografia.objects.create(paciente=paciente, embarazo=embarazo,
                                       fecha_ecografia=datetime.date.today(), edad_gestacional_semanas=20)
        c = APIClient()
        c.force_authenticate(enfermera)
        r = c.delete(f"/api/ecografias/{eco.pk}/")
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Ecografia.objects.filter(pk=eco.pk).exists())


class WebhookDicomTest(TestCase):
    """Sin ORTHANC_WEBHOOK_SECRET el webhook aceptaba cualquier POST."""

    def test_sin_secreto_se_rechaza_en_produccion(self):
        from ia_medica import webhook

        peticion = RequestFactory().post("/api/ia/dicom/webhook/", data=b"{}", content_type="application/json")
        with override_settings(DEBUG=False):
            self.assertFalse(webhook._verify_hmac(peticion))
        with override_settings(DEBUG=True):
            self.assertTrue(webhook._verify_hmac(peticion))
