"""Tests para el módulo de Triaje de Enfermería."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from pacientes.models import Paciente

from .models import TriajeEnfermeria

Usuario = get_user_model()


class TriajeTest(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            id_clinico="PAC-T-1", nombre="Luz", apellido_paterno="Mora",
            fecha_nacimiento=date(1993, 7, 7), genero="femenino", ci="6000001",
        )
        self.enfermera = Usuario.objects.create_user(
            email="enf@test.bo", nombre="Enf", apellido_paterno="Uno", password="x",
        )

    def _triaje(self, peso, talla):
        return TriajeEnfermeria.objects.create(
            paciente=self.paciente, peso_kg=Decimal(str(peso)),
            talla_cm=Decimal(str(talla)), presion_sistolica=110,
            presion_diastolica=70, temperatura=Decimal("36.5"),
            frecuencia_cardiaca=75, frecuencia_respiratoria=16,
            motivo_visita="Control", enfermera=self.enfermera,
        )

    def test_imc_se_calcula_en_save(self):
        # 60 kg, 160 cm → IMC = 60 / 1.6² = 23.44
        t = self._triaje(60, 160)
        self.assertAlmostEqual(float(t.imc), 23.44, places=1)

    def test_clasificacion_imc_normal(self):
        t = self._triaje(60, 160)
        self.assertIn("normal", t.get_clasificacion_imc().lower())

    def test_clasificacion_imc_obesidad(self):
        # 95 kg, 160 cm → IMC ≈ 37.1 → obesidad
        t = self._triaje(95, 160)
        self.assertIn("obesidad", t.get_clasificacion_imc().lower())
