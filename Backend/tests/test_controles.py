"""Tests for ControlPrenatal model and API endpoints.
"""

import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.core.exceptions import ValidationError
from controles.models import ControlPrenatal
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class ControlPrenatalModelTest(TestCase):
    """Tests for the ControlPrenatal model."""

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
        self.paciente = Paciente.objects.create(
            nombre="Maria",
            apellido_paterno="Lopez",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            genero="femenino",
            ci="12345678",
        )
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )
        self.control_data = {
            "embarazo": self.embarazo,
            "paciente": self.paciente,
            "medico": self.medico_user,
            "numero_control": 1,
            "fecha_control": datetime.date.today(),
            "semanas_gestacion": 12,
            "dias_gestacion": 0,
            "peso_actual": Decimal("65.00"),
            "talla": Decimal("165.00"),
            "presion_arterial_sistolica": 110,
            "presion_arterial_diastolica": 70,
            "created_by": self.admin_user,
        }

    def test_create_control(self):
        """Test creating a control prenatal instance."""
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertEqual(ControlPrenatal.objects.count(), 1)
        self.assertEqual(control.numero_control, 1)
        self.assertEqual(control.semanas_gestacion, 12)

    def test_control_str(self):
        """Test __str__ method."""
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertIn("Control #1", str(control))
        self.assertIn("Maria", str(control))

    def test_edad_gestacional_texto(self):
        """Test edad gestacional formatted text."""
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertEqual(control.edad_gestacional_texto, "12+0")

    def test_edad_gestacional_dias(self):
        """Test edad gestacional in total days."""
        self.control_data["semanas_gestacion"] = 20
        self.control_data["dias_gestacion"] = 3
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertEqual(control.edad_gestacional_dias, 20 * 7 + 3)

    def test_trimestre_property(self):
        """Test trimestre calculation."""
        self.control_data["semanas_gestacion"] = 10
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertEqual(control.trimestre, 1)

        self.control_data["semanas_gestacion"] = 20
        control2 = ControlPrenatal.objects.create(
            **{**self.control_data, "numero_control": 2},
        )
        self.assertEqual(control2.trimestre, 2)

        self.control_data["semanas_gestacion"] = 30
        control3 = ControlPrenatal.objects.create(
            **{**self.control_data, "numero_control": 3},
        )
        self.assertEqual(control3.trimestre, 3)

    def test_imc_property(self):
        """Test IMC calculation."""
        control = ControlPrenatal.objects.create(**self.control_data)
        expected_imc = round(65.0 / (1.65**2), 2)
        self.assertEqual(control.imc, expected_imc)

    def test_clasificacion_imc(self):
        """Test IMC classification."""
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertEqual(control.clasificacion_imc, "Normal")

    def test_presion_arterial_media(self):
        """Test PAM calculation."""
        control = ControlPrenatal.objects.create(**self.control_data)
        expected_pam = round((110 + 2 * 70) / 3, 2)
        self.assertEqual(control.presion_arterial_media, expected_pam)

    def test_tiene_hipertension(self):
        """Test hypertension detection."""
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertFalse(control.tiene_hipertension())

        self.control_data["presion_arterial_sistolica"] = 145
        self.control_data["numero_control"] = 2
        control2 = ControlPrenatal.objects.create(**self.control_data)
        self.assertTrue(control2.tiene_hipertension())

    def test_fcf_es_anormal(self):
        """Test abnormal FCF detection."""
        self.control_data["frecuencia_cardiaca_fetal"] = 140
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertFalse(control.fcf_es_anormal())

        self.control_data["frecuencia_cardiaca_fetal"] = 100
        self.control_data["numero_control"] = 2
        control2 = ControlPrenatal.objects.create(**self.control_data)
        self.assertTrue(control2.fcf_es_anormal())

    def test_tiene_alertas_criticas(self):
        """Test critical alerts detection."""
        control = ControlPrenatal.objects.create(**self.control_data)
        self.assertFalse(control.tiene_alertas_criticas())

        self.control_data["movimientos_fetales"] = "ausentes"
        self.control_data["numero_control"] = 2
        control2 = ControlPrenatal.objects.create(**self.control_data)
        self.assertTrue(control2.tiene_alertas_criticas())

    def test_clean_future_date(self):
        """Test validation error for future control date."""

        data = {
            **self.control_data,
            "fecha_control": datetime.date.today() + datetime.timedelta(days=30),
        }
        control = ControlPrenatal(**data)
        with self.assertRaises(ValidationError):
            control.clean()

    def test_clean_sistolica_menor_diastolica(self):
        """Test validation when sistolica < diastolica."""
        data = {
            **self.control_data,
            "presion_arterial_sistolica": 60,
            "presion_arterial_diastolica": 90,
        }
        control = ControlPrenatal(**data)
        with self.assertRaises(ValidationError):
            control.clean()

    def test_clean_fcf_too_low(self):
        """Test validation for very low FCF."""
        data = {
            **self.control_data,
            "frecuencia_cardiaca_fetal": 80,
        }
        control = ControlPrenatal(**data)
        with self.assertRaises(ValidationError):
            control.clean()


class ControlPrenatalAPITest(APITestCase):
    """Tests for ControlPrenatal API endpoints."""

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
        self.paciente = Paciente.objects.create(
            nombre="Maria",
            apellido_paterno="Lopez",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            genero="femenino",
            ci="12345678",
        )
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )
        self.control_data = {
            "embarazo": self.embarazo.id,
            "paciente": self.paciente.id,
            "numero_control": 1,
            "fecha_control": datetime.date.today().isoformat(),
            "semanas_gestacion": 12,
            "dias_gestacion": 0,
            "peso_actual": "65.00",
            "talla": "165.00",
            "presion_arterial_sistolica": 110,
            "presion_arterial_diastolica": 70,
        }
        self.list_url = reverse("controlprenatal-list")

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

    def test_create_control_success(self):
        """Test creating a control prenatal via API."""
        self._authenticate()
        response = self.client.post(self.list_url, self.control_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_create_control_validation_missing_fields(self):
        """Test validation error on missing required fields."""
        self._authenticate()
        response = self.client.post(
            self.list_url,
            {
                "embarazo": self.embarazo.id,
                "paciente": self.paciente.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_control_validation_future_date(self):
        """Test validation error for future control date."""
        self._authenticate()
        data = {
            **self.control_data,
            "fecha_control": (
                datetime.date.today() + datetime.timedelta(days=30)
            ).isoformat(),
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_controles(self):
        """Test listing controles."""
        self._authenticate()
        ControlPrenatal.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            numero_control=1,
            fecha_control=datetime.date.today(),
            semanas_gestacion=12,
            peso_actual=Decimal("65.00"),
            talla=Decimal("165.00"),
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_control(self):
        """Test retrieving a single control."""
        self._authenticate()
        control = ControlPrenatal.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            numero_control=1,
            fecha_control=datetime.date.today(),
            semanas_gestacion=12,
            peso_actual=Decimal("65.00"),
            talla=Decimal("165.00"),
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
        )
        url = reverse("controlprenatal-detail", kwargs={"pk": control.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_control(self):
        """Test updating a control via PUT."""
        self._authenticate()
        control = ControlPrenatal.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            numero_control=1,
            fecha_control=datetime.date.today(),
            semanas_gestacion=12,
            peso_actual=Decimal("65.00"),
            talla=Decimal("165.00"),
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
            observaciones="Original",
        )
        url = reverse("controlprenatal-detail", kwargs={"pk": control.pk})
        update_data = {
            "embarazo": self.embarazo.id,
            "paciente": self.paciente.id,
            "numero_control": 1,
            "fecha_control": datetime.date.today().isoformat(),
            "semanas_gestacion": 12,
            "dias_gestacion": 0,
            "peso_actual": "66.00",
            "talla": "165.00",
            "presion_arterial_sistolica": 110,
            "presion_arterial_diastolica": 70,
            "observaciones": "Updated",
        }
        response = self.client.put(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        control.refresh_from_db()
        self.assertEqual(control.observaciones, "Updated")

    def test_partial_update_control(self):
        """Test partial update via PATCH."""
        self._authenticate()
        control = ControlPrenatal.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            numero_control=1,
            fecha_control=datetime.date.today(),
            semanas_gestacion=12,
            peso_actual=Decimal("65.00"),
            talla=Decimal("165.00"),
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
            observaciones="Original",
        )
        url = reverse("controlprenatal-detail", kwargs={"pk": control.pk})
        response = self.client.patch(url, {"observaciones": "Patched"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        control.refresh_from_db()
        self.assertEqual(control.observaciones, "Patched")

    def test_delete_control_non_admin_forbidden(self):
        """Test that non-admin cannot delete control."""
        self._authenticate(user=self.medico_user)
        control = ControlPrenatal.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            numero_control=1,
            fecha_control=datetime.date.today(),
            semanas_gestacion=12,
            peso_actual=Decimal("65.00"),
            talla=Decimal("165.00"),
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
        )
        url = reverse("controlprenatal-detail", kwargs={"pk": control.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_por_embarazo_endpoint(self):
        """Test por_embarazo custom endpoint."""
        self._authenticate()
        ControlPrenatal.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            numero_control=1,
            fecha_control=datetime.date.today(),
            semanas_gestacion=12,
            peso_actual=Decimal("65.00"),
            talla=Decimal("165.00"),
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
        )
        url = reverse("controlprenatal-por_embarazo")
        response = self.client.get(url, {"embarazo_id": self.embarazo.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("controles", response.data)

    def test_por_paciente_endpoint(self):
        """Test por_paciente custom endpoint."""
        self._authenticate()
        url = reverse("controlprenatal-por_paciente")
        response = self.client.get(url, {"paciente_id": self.paciente.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_por_paciente_missing_param(self):
        """Test por_paciente without paciente_id returns 400."""
        self._authenticate()
        url = reverse("controlprenatal-por_paciente")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_estadisticas_endpoint(self):
        """Test estadisticas custom endpoint."""
        self._authenticate()
        url = reverse("controlprenatal-estadisticas")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resumen", response.data)

    def test_alertas_endpoint(self):
        """Test alertas custom endpoint."""
        self._authenticate()
        url = reverse("controlprenatal-alertas")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recientes_endpoint(self):
        """Test recientes custom endpoint."""
        self._authenticate()
        url = reverse("controlprenatal-recientes")
        response = self.client.get(url, {"dias": 7})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
