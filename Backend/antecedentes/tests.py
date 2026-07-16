"""Tests para el módulo de Antecedentes."""
from datetime import date

from django.test import TestCase

from pacientes.models import Paciente

from .models import AntecedenteGinecoObstetrico, AntecedentePatologico


class AntecedentesTest(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            id_clinico="PAC-A-1", nombre="Rita", apellido_paterno="Vaca",
            fecha_nacimiento=date(1988, 4, 4), genero="femenino", ci="3000001",
        )

    def test_antecedente_gineco_uno_a_uno(self):
        a = AntecedenteGinecoObstetrico.objects.create(paciente=self.paciente)
        self.assertEqual(a.paciente, self.paciente)
        # OneToOne: no debe permitir un segundo para el mismo paciente
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            AntecedenteGinecoObstetrico.objects.create(paciente=self.paciente)

    def test_antecedente_patologico(self):
        p = AntecedentePatologico.objects.create(paciente=self.paciente, tipo="personal")
        self.assertEqual(p.tipo, "personal")
        self.assertEqual(p.paciente, self.paciente)
