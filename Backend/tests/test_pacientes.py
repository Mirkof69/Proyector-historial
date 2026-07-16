"""Tests for Paciente model and API endpoints.
"""

import datetime
from decimal import Decimal
from typing import cast

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from pacientes.models import Paciente
from usuarios.models import Usuario


class PacienteModelTest(TestCase):
    """Tests for the Paciente model."""

    def setUp(self):
        """Setup"""
        self.admin_user = Usuario.objects.create_superuser(
            email="admin@test.com",
            nombre="Admin",
            apellido_paterno="User",
            password="adminpass123",
        )
        self.paciente_data = {
            "nombre": "Maria",
            "apellido_paterno": "Lopez",
            "apellido_materno": "Garcia",
            "fecha_nacimiento": datetime.date(1990, 5, 15),
            "genero": "femenino",
            "ci": "12345678",
            "telefono": "70712345",
            "email": "maria@test.com",
            "direccion": "Calle 123",
            "ciudad": "La Paz",
            "estado_civil": "casado",
            "ocupacion": "Profesora",
            "created_by": self.admin_user,
        }

    def test_create_paciente(self):
        """Test creating a paciente instance."""
        paciente = Paciente.objects.create(**self.paciente_data)
        self.assertEqual(Paciente.objects.count(), 1)
        self.assertEqual(paciente.nombre, "Maria")
        self.assertEqual(paciente.ci, "12345678")
        self.assertIsNotNone(paciente.id_clinico)
        self.assertTrue(paciente.id_clinico.startswith("PAC-"))
        self.assertTrue(paciente.activo)
        self.assertEqual(paciente.estado_paciente, "activo")

    def test_nombre_completo_property(self):
        """Test nombre_completo property."""
        paciente = Paciente.objects.create(**self.paciente_data)
        self.assertEqual(paciente.nombre_completo, "Maria Lopez Garcia")

        paciente2 = Paciente.objects.create(
            nombre="Juan",
            apellido_paterno="Perez",
            fecha_nacimiento=datetime.date(1985, 1, 1),
            genero="masculino",
            ci="87654321",
        )
        self.assertEqual(paciente2.nombre_completo, "Juan Perez")

    def test_edad_property(self):
        """Test edad calculation."""
        paciente = Paciente.objects.create(**self.paciente_data)
        today = datetime.date.today()
        expected_age = today.year - 1990 - ((today.month, today.day) < (5, 15))
        self.assertEqual(paciente.edad, expected_age)

    def test_imc_property(self):
        """Test IMC calculation."""
        self.paciente_data["peso_kg"] = Decimal("70.00")
        self.paciente_data["altura_cm"] = Decimal("165.00")
        paciente = Paciente.objects.create(**self.paciente_data)
        expected_imc = round(70.0 / (1.65**2), 2)
        self.assertEqual(paciente.imc, expected_imc)

    def test_imc_property_missing_data(self):
        """Test IMC returns None when data is missing."""
        paciente = Paciente.objects.create(**self.paciente_data)
        self.assertIsNone(paciente.imc)

    def test_unique_ci_constraint(self):
        """Test that CI must be unique."""
        Paciente.objects.create(**self.paciente_data)
        duplicate_data = self.paciente_data.copy()
        duplicate_data["ci"] = "12345678"
        duplicate_data["nombre"] = "Otro"
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Paciente.objects.create(**duplicate_data)

    def test_unique_id_clinico_auto_generated(self):
        """Test that id_clinico is auto-generated and unique."""
        p1 = Paciente.objects.create(**self.paciente_data)
        p2_data = self.paciente_data.copy()
        p2_data["ci"] = "11111111"
        p2 = Paciente.objects.create(**p2_data)
        self.assertNotEqual(p1.id_clinico, p2.id_clinico)

    def test_paciente_str(self):
        """Test __str__ method."""
        paciente = Paciente.objects.create(**self.paciente_data)
        self.assertIn("Maria", str(paciente))
        self.assertIn("12345678", str(paciente))

    def test_paciente_with_all_optional_fields(self):
        """Test creating paciente with all optional fields."""
        data = {
            **self.paciente_data,
            "contacto_emergencia_nombre": "Juan Perez",
            "contacto_emergencia_telefono": "70799999",
            "contacto_emergencia_relacion": "Esposo",
            "tipo_sangre": "O+",
            "factor_rh": "positivo",
            "peso_kg": Decimal("65.50"),
            "altura_cm": Decimal("160.00"),
        }
        paciente = Paciente.objects.create(**data)
        self.assertEqual(paciente.contacto_emergencia_nombre, "Juan Perez")
        self.assertEqual(paciente.tipo_sangre, "O+")
        self.assertEqual(paciente.peso_kg, Decimal("65.50"))


class PacienteAPITest(APITestCase):
    """Tests for Paciente API endpoints."""

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
        self.paciente_data = {
            "nombre": "Maria",
            "apellido_paterno": "Lopez",
            "apellido_materno": "Garcia",
            "fecha_nacimiento": "1990-05-15",
            "genero": "femenino",
            "ci": "12345678",
            "telefono": "70712345",
            "email": "maria@test.com",
            "direccion": "Calle 123",
            "ciudad": "La Paz",
        }
        self.list_url = reverse("paciente-list")

    def _authenticate(self, user=None):
        """Helper to authenticate a user."""
        if user is None:
            user = self.admin_user
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    def _create_paciente(self, data=None):
        """Helper to create a paciente via API."""
        if data is None:
            data = self.paciente_data
        return self.client.post(self.list_url, data, format="json")

    def test_list_requires_authentication(self):
        """Test that list endpoint requires authentication."""
        response = self.client.get(self.list_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_list_authenticated(self):
        """Test that authenticated user can list pacientes."""
        self._authenticate()
        Paciente.objects.create(
            nombre="Test",
            apellido_paterno="User",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="99999999",
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_requires_authentication(self):
        """Test that create endpoint requires authentication."""
        response = self._create_paciente()
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_create_paciente_success(self):
        """Test creating a paciente via API returns 201."""
        self._authenticate()
        response = self._create_paciente()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("id_clinico", response.data)

    def test_create_paciente_validation_missing_fields(self):
        """Test validation error when required fields are missing."""
        self._authenticate()
        response = self._create_paciente(
            data={
                "nombre": "Test",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_paciente_validation_future_birth_date(self):
        """Test validation error for future birth date."""
        self._authenticate()
        future_date = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
        response = self._create_paciente(
            data={
                **self.paciente_data,
                "fecha_nacimiento": future_date,
                "ci": "11111111",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_paciente_validation_age_too_young(self):
        """Test validation error when patient is too young."""
        self._authenticate()
        recent_date = (
            datetime.date.today() - datetime.timedelta(days=365 * 5)
        ).isoformat()
        response = self._create_paciente(
            data={
                **self.paciente_data,
                "fecha_nacimiento": recent_date,
                "ci": "22222222",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_paciente(self):
        """Test retrieving a single paciente."""
        self._authenticate()
        paciente = cast(Paciente, Paciente.objects.create(
            nombre="Retrieve",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="33333333",
        ))
        url = reverse("paciente-detail", kwargs={"pk": paciente.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Retrieve")

    def test_update_paciente(self):
        """Test updating a paciente via PUT."""
        self._authenticate()
        paciente = cast(Paciente, Paciente.objects.create(
            nombre="Update",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="44444444",
        ))
        url = reverse("paciente-detail", kwargs={"pk": paciente.pk})
        update_data = {
            "nombre": "Updated",
            "apellido_paterno": "Test",
            "fecha_nacimiento": "1990-01-01",
            "genero": "femenino",
            "ci": "44444444",
        }
        response = self.client.put(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        paciente.refresh_from_db()
        self.assertEqual(paciente.nombre, "Updated")

    def test_partial_update_paciente(self):
        """Test partial update via PATCH."""
        self._authenticate()
        paciente = cast(Paciente, Paciente.objects.create(
            nombre="Partial",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="55555555",
            telefono="70700000",
        ))
        url = reverse("paciente-detail", kwargs={"pk": paciente.pk})
        response = self.client.patch(url, {"telefono": "70799999"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        paciente.refresh_from_db()
        self.assertEqual(paciente.telefono, "70799999")

    def test_delete_paciente_non_admin_forbidden(self):
        """Test that non-admin cannot delete paciente."""
        self._authenticate(user=self.medico_user)
        paciente = cast(Paciente, Paciente.objects.create(
            nombre="Delete",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="66666666",
        ))
        url = reverse("paciente-detail", kwargs={"pk": paciente.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_paciente(self):
        """Test search endpoint."""
        self._authenticate()
        Paciente.objects.create(
            nombre="Searchable",
            apellido_paterno="User",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="77777777",
        )
        url = reverse("paciente-buscar")
        response = self.client.get(url, {"q": "Searchable"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_search_paciente_no_query(self):
        """Test search endpoint without query returns 400."""
        self._authenticate()
        url = reverse("paciente-buscar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_estadisticas_endpoint(self):
        """Test estadisticas endpoint returns 200."""
        self._authenticate()
        url = reverse("paciente-estadisticas")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_pacientes", response.data)

    def test_filter_by_genero(self):
        """Test filtering by genero."""
        self._authenticate()
        Paciente.objects.create(
            nombre="F",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="88888881",
        )
        Paciente.objects.create(
            nombre="M",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="masculino",
            ci="88888882",
        )
        response = self.client.get(self.list_url, {"genero": "femenino"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
