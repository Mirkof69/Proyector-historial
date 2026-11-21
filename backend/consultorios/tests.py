"""Tests para el módulo de Consultorios."""
from datetime import date, time

from django.test import TestCase

from .models import Consultorio, ReservaConsultorio


class ConsultorioTest(TestCase):
    def test_crear_consultorio(self):
        c = Consultorio.objects.create(nombre="Consultorio 1", ubicacion="Piso 2")
        self.assertIn("Consultorio 1", str(c))

    def test_reserva_consultorio(self):
        c = Consultorio.objects.create(nombre="Consultorio 2", ubicacion="Piso 3")
        r = ReservaConsultorio.objects.create(
            consultorio=c, fecha_reserva=date.today(),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        self.assertEqual(r.consultorio, c)
        self.assertLess(r.hora_inicio, r.hora_fin)
