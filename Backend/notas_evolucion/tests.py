"""Tests para el módulo de Notas de Evolución (SOAP)."""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from pacientes.models import Paciente

from .models import NotaEvolucion

Usuario = get_user_model()


class NotaEvolucionTest(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            id_clinico="PAC-NE-1", nombre="Elena", apellido_paterno="Paz",
            fecha_nacimiento=date(1994, 9, 9), genero="femenino", ci="4000001",
        )
        self.medico = Usuario.objects.create_user(
            email="med@test.bo", nombre="Med", apellido_paterno="Uno", password="x",
        )

    def _nota(self, **extra):
        return NotaEvolucion.objects.create(
            paciente=self.paciente, medico=self.medico,
            fecha_consulta=timezone.now(), motivo_consulta="Dolor",
            examen_fisico="Normal", diagnosticos="Sano", plan_tratamiento="Reposo",
            **extra,
        )

    def test_presion_arterial_property(self):
        nota = self._nota(presion_arterial_sistolica=120, presion_arterial_diastolica=80)
        self.assertEqual(nota.presion_arterial, "120/80")

    def test_presion_arterial_none_sin_datos(self):
        nota = self._nota()
        self.assertIsNone(nota.presion_arterial)

    def test_edad_gestacional_completa(self):
        nota = self._nota(edad_gestacional_semanas=32, edad_gestacional_dias=4)
        self.assertEqual(nota.edad_gestacional_completa, "32s 4d")
