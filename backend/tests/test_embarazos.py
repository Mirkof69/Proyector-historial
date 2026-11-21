"""Tests for Embarazo model and API endpoints.
"""

import datetime
from decimal import Decimal
from typing import cast

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class EmbarazoModelTest(TestCase):
    """Tests for the Embarazo model."""

    def setUp(self):
        """Setup"""
        self.admin_user = Usuario.objects.create_superuser(
            email="admin@test.com",
            nombre="Admin",
            apellido_paterno="User",
            password="adminpass123",
        )
        self.paciente = Paciente.objects.create(
            nombre="Maria",
            apellido_paterno="Lopez",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            genero="femenino",
            ci="12345678",
        )
        self.embarazo_data = {
            "paciente": self.paciente,
            "numero_gesta": 1,
            "numero_para": 0,
            "numero_abortos": 0,
            "numero_cesareas": 0,
            "fecha_ultima_menstruacion": datetime.date.today()
            - datetime.timedelta(weeks=12),
            "tipo_embarazo": "simple",
            "riesgo_embarazo": "bajo",
            "estado": "activo",
        }

    def test_create_embarazo(self):
        """Test creating an embarazo instance."""
        embarazo = Embarazo.objects.create(**self.embarazo_data)
        self.assertEqual(Embarazo.objects.count(), 1)
        self.assertEqual(embarazo.numero_gesta, 1)
        self.assertEqual(embarazo.estado, "activo")
        self.assertIsNotNone(embarazo.uuid)

    def test_embarazo_str(self):
        """Test __str__ method."""
        embarazo = Embarazo.objects.create(**self.embarazo_data)
        self.assertIn("Embarazo", str(embarazo))
        self.assertIn(str(self.paciente.id_clinico), str(embarazo))

    def test_fur_property(self):
        """Test FUR alias property."""
        embarazo = Embarazo.objects.create(**self.embarazo_data)
        self.assertEqual(embarazo.fur, embarazo.fecha_ultima_menstruacion)

    def test_imc_pregestacional(self):
        """Test pregestational IMC calculation."""
        self.embarazo_data["peso_pregestacional"] = Decimal("65.00")
        self.embarazo_data["talla_materna"] = Decimal("165.00")
        embarazo = Embarazo.objects.create(**self.embarazo_data)
        expected_imc = round(65.0 / (1.65**2), 2)
        self.assertEqual(embarazo.imc_pregestacional, expected_imc)

    def test_imc_pregestacional_missing_data(self):
        """Test IMC returns None when data is missing."""
        embarazo = Embarazo.objects.create(**self.embarazo_data)
        self.assertIsNone(embarazo.imc_pregestacional)

    def test_clean_fum_future_date(self):
        """Test validation error for future FUM date."""

        data = {
            **self.embarazo_data,
            "fecha_ultima_menstruacion": datetime.date.today()
            + datetime.timedelta(days=30),
        }
        embarazo = Embarazo(**data)
        with self.assertRaises(ValidationError):
            embarazo.clean()

    def test_clean_para_mayor_que_gesta(self):
        """Test validation error when para > gesta."""
        data = {
            **self.embarazo_data,
            "numero_gesta": 1,
            "numero_para": 2,
        }
        embarazo = Embarazo(**data)
        with self.assertRaises(ValidationError):
            embarazo.clean()

    def test_clean_gesta_no_coincide(self):
        """Test validation error when G != P + Abortos + 1."""
        data = {
            **self.embarazo_data,
            "numero_gesta": 3,
            "numero_para": 0,
            "numero_abortos": 0,
        }
        embarazo = Embarazo(**data)
        with self.assertRaises(ValidationError):
            embarazo.clean()

    def test_clean_peso_out_of_range(self):
        """Test validation for peso out of range."""
        data = {
            **self.embarazo_data,
            "peso_pregestacional": Decimal("20.00"),
        }
        embarazo = Embarazo(**data)
        with self.assertRaises(ValidationError):
            embarazo.clean()

    def test_clean_talla_out_of_range(self):
        """Test validation for talla out of range."""
        data = {
            **self.embarazo_data,
            "talla_materna": Decimal("90.00"),
        }
        embarazo = Embarazo(**data)
        with self.assertRaises(ValidationError):
            embarazo.clean()


class EmbarazoAPITest(APITestCase):
    """Tests for Embarazo API endpoints."""

    def setUp(self):
        """Setup"""
        self.admin_user = Usuario.objects.create_superuser(
            email="admin@test.com",
            nombre="Admin",
            apellido_paterno="User",
            password="adminpass123",
        )
        self.medico_user = Usuario.objects.create_user(
            email="medico@test.com",
            nombre="Dr",
            apellido_paterno="Medico",
            password="medicopass123",
            rol="medico",
        )
        self.paciente = cast(Paciente, Paciente.objects.create(
            nombre="Maria",
            apellido_paterno="Lopez",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            genero="femenino",
            ci="12345678",
        ))
        self.embarazo_data = {
            "paciente": self.paciente.id,
            "numero_gesta": 1,
            "numero_para": 0,
            "numero_abortos": 0,
            "numero_cesareas": 0,
            "fecha_ultima_menstruacion": (
                datetime.date.today() - datetime.timedelta(weeks=12)
            ).isoformat(),
            "tipo_embarazo": "simple",
            "riesgo_embarazo": "bajo",
            "estado": "activo",
        }
        self.list_url = reverse("embarazo-list")

    def _authenticate(self, user=None):
        """Authenticate"""
        if user is None:
            user = self.admin_user
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    def test_list_requires_authentication(self):
        """Test that list requires auth."""
        response = self.client.get(self.list_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_create_embarazo_success(self):
        """Test creating an embarazo via API."""
        self._authenticate()
        response = self.client.post(self.list_url, self.embarazo_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_create_embarazo_validation_missing_fields(self):
        """Test validation error on missing required fields."""
        self._authenticate()
        response = self.client.post(
            self.list_url,
            {
                "paciente": self.paciente.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_embarazo_validation_gesta_para_mismatch(self):
        """Test validation for gesta/para mismatch."""
        self._authenticate()
        data = {
            **self.embarazo_data,
            "numero_gesta": 1,
            "numero_para": 2,
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_embarazos(self):
        """Test listing embarazos."""
        self._authenticate()
        Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_embarazo(self):
        """Test retrieving a single embarazo."""
        self._authenticate()
        embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )
        url = reverse("embarazo-detail", kwargs={"pk": embarazo.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_embarazo(self):
        """Test updating an embarazo via PUT."""
        self._authenticate()
        embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
            notas="Original notes",
        )
        url = reverse("embarazo-detail", kwargs={"pk": embarazo.pk})
        update_data = {
            "paciente": self.paciente.id,
            "numero_gesta": 1,
            "numero_para": 0,
            "numero_abortos": 0,
            "numero_cesareas": 0,
            "fecha_ultima_menstruacion": (
                datetime.date.today() - datetime.timedelta(weeks=12)
            ).isoformat(),
            "tipo_embarazo": "simple",
            "riesgo_embarazo": "bajo",
            "estado": "activo",
            "notas": "Updated notes",
        }
        response = self.client.put(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        embarazo.refresh_from_db()
        self.assertEqual(embarazo.notas, "Updated notes")

    def test_partial_update_embarazo(self):
        """Test partial update via PATCH."""
        self._authenticate()
        embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
            riesgo_embarazo="bajo",
        )
        url = reverse("embarazo-detail", kwargs={"pk": embarazo.pk})
        response = self.client.patch(url, {"riesgo_embarazo": "alto"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        embarazo.refresh_from_db()
        self.assertEqual(embarazo.riesgo_embarazo, "alto")

    def test_delete_embarazo_non_admin_forbidden(self):
        """Test that non-admin cannot delete embarazo."""
        self._authenticate(user=self.medico_user)
        embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )
        url = reverse("embarazo-detail", kwargs={"pk": embarazo.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_activos_endpoint(self):
        """Test activos custom endpoint."""
        self._authenticate()
        Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
            estado="activo",
        )
        url = reverse("embarazo-activos")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_estadisticas_endpoint(self):
        """Test estadisticas custom endpoint."""
        self._authenticate()
        url = reverse("embarazo-estadisticas")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resumen_general", response.data)

    def test_por_paciente_endpoint(self):
        """Test por_paciente custom endpoint."""
        self._authenticate()
        url = reverse("embarazo-por-paciente")
        response = self.client.get(url, {"paciente_id": self.paciente.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_por_paciente_missing_param(self):
        """Test por_paciente without paciente_id returns 400."""
        self._authenticate()
        url = reverse("embarazo-por-paciente")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_alto_riesgo_endpoint(self):
        """Test alto_riesgo custom endpoint."""
        self._authenticate()
        url = reverse("embarazo-alto-riesgo")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_multiples_endpoint(self):
        """Test multiples custom endpoint."""
        self._authenticate()
        url = reverse("embarazo-multiples")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
