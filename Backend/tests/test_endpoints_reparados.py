"""Endpoints que daban error 500 y ya no.

Cada test fija un fallo concreto encontrado en la auditoría del 24-09-2026.
"""
import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from pacientes.models import Paciente
from usuarios.models import Usuario


class AnalizarPacienteTest(TestCase):
    """`/api/partos/analizar-paciente/<id>/` pasaba `paciente_id` como kwarg a un
    método que no lo aceptaba: TypeError, 500. Es la ruta que usa el frontend."""

    def test_la_ruta_del_frontend_responde_200(self):
        medico = Usuario.objects.create_user(
            email="med.partos@test.bo", nombre="M", apellido_paterno="P",
            password="clave-segura-123", rol="medico")
        paciente = Paciente.objects.create(
            nombre="Ana", apellido_paterno="Parto", apellido_materno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci="7700001")
        c = APIClient()
        c.force_authenticate(medico)
        r = c.get(f"/api/partos/analizar-paciente/{paciente.pk}/")
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(r.json()["total_partos"], 0)


class ValidacionControlTempranoTest(TestCase):
    """`import warnings` dentro de un `if` hacía `warnings` local de toda la
    función: un control de menos de 12 semanas con presentación fetal y sin FCF
    daba UnboundLocalError (500)."""

    def test_presentacion_antes_de_12_semanas_no_revienta(self):
        from controles.serializers import ControlPrenatalCreateUpdateSerializer

        s = ControlPrenatalCreateUpdateSerializer()
        attrs = {"semanas_gestacion": 10, "presentacion_fetal": "cefalica"}
        resultado = s.validate(dict(attrs))   # ESPERADO: no lanza nada
        self.assertEqual(resultado["semanas_gestacion"], 10)


class PartoYEstadoDelEmbarazoTest(TestCase):
    """Un parto en curso no finaliza el embarazo; uno terminado sí."""

    def setUp(self):
        from embarazos.models import Embarazo

        self.medico = Usuario.objects.create_user(
            email="med.parto2@test.bo", nombre="M", apellido_paterno="P",
            password="clave-segura-123", rol="medico")
        paciente = Paciente.objects.create(
            nombre="Rosa", apellido_paterno="Parto", apellido_materno="Curso",
            fecha_nacimiento=datetime.date(1991, 2, 2), genero="femenino", ci="7700002")
        self.embarazo = Embarazo.objects.create(
            paciente=paciente, numero_gesta=1,
            fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=39))
        self.paciente = paciente

    def _parto(self, finalizado, numero):
        from django.utils import timezone

        from partos.models import Parto

        return Parto.objects.create(
            paciente=self.paciente, embarazo=self.embarazo, medico_responsable=self.medico,
            numero_parto=numero, fecha_parto=timezone.now(), edad_gestacional_parto="39+0",
            parto_finalizado=finalizado)

    def test_trabajo_de_parto_en_curso_deja_el_embarazo_activo(self):
        self._parto(False, "P-CURSO-1")
        self.embarazo.refresh_from_db()
        self.assertEqual(self.embarazo.estado, "activo")

    def test_parto_terminado_finaliza_el_embarazo(self):
        self._parto(True, "P-FIN-1")
        self.embarazo.refresh_from_db()
        self.assertEqual(self.embarazo.estado, "finalizado")
