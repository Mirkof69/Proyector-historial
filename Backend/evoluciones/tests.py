"""Tests para el módulo de Evoluciones de embarazo."""
from datetime import date, timedelta

from django.test import TestCase

from embarazos.models import Embarazo
from pacientes.models import Paciente

from .models import EvolucionEmbarazo


class EvolucionEmbarazoTest(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            id_clinico="PAC-EV-1", nombre="Sara", apellido_paterno="León",
            fecha_nacimiento=date(1991, 2, 2), genero="femenino", ci="5000001",
        )
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente, numero_gesta=2,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=30),
        )

    def test_crear_evolucion(self):
        ev = EvolucionEmbarazo.objects.create(
            embarazo=self.embarazo, paciente=self.paciente,
            fecha_evento=date.today(), tipo_evento="cita",
            descripcion="Control sin novedades",
        )
        self.assertEqual(ev.embarazo, self.embarazo)
        self.assertEqual(ev.tipo_evento, "cita")

    def test_str_no_vacio(self):
        ev = EvolucionEmbarazo.objects.create(
            embarazo=self.embarazo, paciente=self.paciente,
            fecha_evento=date.today(), tipo_evento="cita", descripcion="x",
        )
        self.assertTrue(str(ev))
