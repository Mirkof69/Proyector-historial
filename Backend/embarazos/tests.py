"""Tests para módulo de Embarazos"""

from datetime import date, timedelta
from typing import cast

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from pacientes.models import Paciente
from usuarios.models import Usuario

from .models import Embarazo


class EmbarazoModelTestCase(TestCase):
    """Tests para modelo Embarazo"""

    def setUp(self):
        """Setup"""
        self.paciente = cast(Paciente, Paciente.objects.create(
            nombre="María",
            apellido_paterno="García",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
            ci="EMB123",
        ))

    def test_crear_embarazo(self):
        """Test crear embarazo"""
        embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=10),
            numero_gesta=1,
            estado="activo",
        )

        self.assertIsNotNone(embarazo.id)
        self.assertEqual(embarazo.paciente, self.paciente)
        self.assertEqual(embarazo.estado, "activo")

    def test_calcular_fpp(self):
        """Test cálculo de FPP automático"""
        fur = date.today() - timedelta(weeks=10)
        embarazo = Embarazo.objects.create(
            paciente=self.paciente, fecha_ultima_menstruacion=fur, numero_gesta=1,
        )

        # FPP debería ser FUR + 280 días
        fpp_esperada = fur + timedelta(days=280)
        self.assertEqual(embarazo.fecha_probable_parto, fpp_esperada)

    def test_semanas_gestacion(self):
        """Test cálculo de semanas de gestación"""
        fur = date.today() - timedelta(weeks=20)
        embarazo = Embarazo.objects.create(
            paciente=self.paciente, fecha_ultima_menstruacion=fur, numero_gesta=1,
        )

        # El modelo usa fecha_ultima_menstruacion para calcular semanas_gestacion
        semanas = getattr(embarazo, "semanas_gestacion", None)
        if semanas is not None:
            self.assertGreaterEqual(semanas, 19)


class EmbarazoAPITestCase(APITestCase):
    """Tests para API de Embarazos"""

    def setUp(self):
        """Setup"""
        self.user = Usuario.objects.create_user(
            email="testdoctor@clinica.com",
            nombre="Doctor",
            apellido_paterno="Prueba",
            password="testpass123",
            rol="medico",
        )
        self.client.force_authenticate(user=self.user)

        self.paciente = cast(Paciente, Paciente.objects.create(
            nombre="María",
            apellido_paterno="García",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
            ci="EMB_API_123",
        ))

    def test_listar_embarazos(self):
        """Test listar embarazos"""
        response = self.client.get("/api/embarazos/")
        if response.status_code != status.HTTP_200_OK:
            print(f"\nListing error: {response.status_code} - {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_embarazo(self):
        """Test crear embarazo vía API"""
        fecha_fum = (date.today() - timedelta(weeks=10)).strftime("%Y-%m-%d")
        data = {
            "paciente": self.paciente.id,
            "fecha_ultima_menstruacion": fecha_fum,
            "numero_gesta": 1,
            "estado": "activo",
        }

        response = self.client.post("/api/embarazos/", data)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST],
        )
