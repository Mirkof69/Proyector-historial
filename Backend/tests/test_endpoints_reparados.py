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
