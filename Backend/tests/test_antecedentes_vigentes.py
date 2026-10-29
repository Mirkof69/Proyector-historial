"""Datos clínicos de una paciente con más de un antecedente del mismo tipo.

El formulario de Antecedentes registra uno nuevo cada vez y el triaje crea uno
en blanco al abrir los datos clínicos. Con dos, /antecedentes-personales/
respondía 500 (get_or_create → MultipleObjectsReturned) en todas las pantallas
que muestran los datos de esa paciente (hallado por la prueba E2E de módulos).
"""
import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from antecedentes.models import AntecedentePatologico
from pacientes.models import Paciente
from usuarios.models import Usuario


class AntecedenteVigenteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(
            email="medico.ant@test.bo", nombre="N", apellido_paterno="A",
            password="clave-segura-123", rol="medico")
        cls.paciente = Paciente.objects.create(
            nombre="Ana", apellido_paterno="Test", apellido_materno="Ant",
            fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci="7811077")

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def test_con_dos_antecedentes_personales_responde_el_ultimo(self):
        AntecedentePatologico.objects.create(paciente=self.paciente, tipo="personal", registrado_por=self.medico)
        ultimo = AntecedentePatologico.objects.create(
            paciente=self.paciente, tipo="personal", registrado_por=self.medico, asma=True)
        r = self.cliente.get(f"/api/pacientes/{self.paciente.id}/antecedentes-personales/")
        # ESPERADO: 200 con el último cargado (antes: 500).
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["id"], ultimo.id)

    def test_sin_antecedentes_crea_uno_en_blanco_una_sola_vez(self):
        url = f"/api/pacientes/{self.paciente.id}/antecedentes-personales/"
        self.assertEqual(self.cliente.get(url).status_code, 200)
        self.assertEqual(self.cliente.get(url).status_code, 200)
        self.assertEqual(AntecedentePatologico.objects.filter(paciente=self.paciente, tipo="personal").count(), 1)
