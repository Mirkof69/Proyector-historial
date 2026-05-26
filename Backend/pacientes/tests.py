"""Tests para módulo de Pacientes"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Paciente

User = get_user_model()


class PacienteModelTestCase(TestCase):
    """Tests para modelo Paciente"""

    def test_crear_paciente(self):
        """Test crear paciente"""
        paciente = Paciente.objects.create(
            nombre="María",
            apellido_paterno="García",
            apellido_materno="López",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
        )

        self.assertIsNotNone(paciente.id)
        self.assertEqual(paciente.nombre, "María")

    def test_edad_automatica(self):
        """Test cálculo automático de edad"""
        paciente = Paciente.objects.create(
            nombre="María",
            apellido_paterno="García",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
        )

        self.assertIsNotNone(paciente.edad)
        self.assertGreater(paciente.edad, 30)


class PacienteAPITestCase(APITestCase):
    """Tests para API de Pacientes"""

    def setUp(self):
        """Setup"""
        self.user = User.objects.create_user(
            email="testdoctor@clinica.com",
            nombre="Doctor",
            apellido_paterno="Prueba",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

    def test_listar_pacientes(self):
        """Test listar pacientes"""
        response = self.client.get("/api/pacientes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
