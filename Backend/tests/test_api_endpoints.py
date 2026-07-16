"""Tests for all API endpoints returning correct status codes.
Verifies authentication, CRUD operations, and custom actions.
"""

import datetime
from decimal import Decimal
from typing import cast

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from calculadoras.models import CalculadoraRiesgo
from controles.models import ControlPrenatal
from ecografias.models import Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        },
    },
)
class APIEndpointStatusTest(APITestCase):
    """Comprehensive tests for all API endpoint status codes."""

    def setUp(self):
        """Setup"""
        # Create users
        self.admin = Usuario.objects.create_superuser(
            email="admin@test.com",
            nombre="Admin",
            apellido_paterno="User",
            password="adminpass123",
        )
        # The model's save() auto-sets mfa_obligatorio=True for administrador when
        # DEBUG=False. Use QuerySet.update() to bypass that hook so login returns 200.
        Usuario.objects.filter(pk=self.admin.pk).update(mfa_obligatorio=False)
        self.medico = Usuario.objects.create_user(
            email="medico@test.com",
            nombre="Dr",
            apellido_paterno="Medico",
            password="medicopass123",
            rol="medico",
        )
        self.enfermero = Usuario.objects.create_user(
            email="enfermero@test.com",
            nombre="Nurse",
            apellido_paterno="User",
            password="nursepass123",
            rol="enfermero",
        )

        # Create base paciente
        self.paciente = cast(Paciente, Paciente.objects.create(
            nombre="Maria",
            apellido_paterno="Lopez",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            genero="femenino",
            ci="12345678",
        ))

        # Create base embarazo
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )

        # Create base control
        self.control = ControlPrenatal.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico,
            numero_control=1,
            fecha_control=datetime.date.today(),
            semanas_gestacion=12,
            peso_actual=Decimal("65.00"),
            talla=Decimal("165.00"),
            presion_arterial_sistolica=110,
            presion_arterial_diastolica=70,
        )

        # Create base ecografia
        self.ecografia = Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="primer_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=12,
            diagnostico="Normal",
        )

        # Create base calculadora
        self.calculadora = CalculadoraRiesgo.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazo,
            tipo="preeclampsia",
            edad_gestacional_semanas=12,
            edad_materna=30,
            peso_kg=Decimal("65.00"),
            talla_cm=Decimal("165.00"),
            etnia="mestiza",
            calculado_por=self.admin,
        )

    def _authenticate(self, user=None):
        """Authenticate"""
        if user is None:
            user = self.admin
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    # ===================== AUTH ENDPOINTS =====================

    def test_token_obtain_pair_200_with_valid_creds(self):
        """POST /api/usuarios/login/ returns 200 with valid credentials."""
        response = self.client.post(
            reverse("login"),
            {
                "email": "admin@test.com",
                "password": "adminpass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_obtain_pair_401_with_invalid_creds(self):
        """POST /api/usuarios/login/ returns 401 with invalid credentials."""
        response = self.client.post(
            reverse("login"),
            {
                "email": "admin@test.com",
                "password": "wrongpass",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_200_with_valid_token(self):
        """POST /api/usuarios/refresh/ returns 200 with valid refresh token."""
        obtain = self.client.post(
            reverse("login"),
            {
                "email": "admin@test.com",
                "password": "adminpass123",
            },
            format="json",
        )
        refresh_token = obtain.data.get("refresh_token")
        if not refresh_token:
            self.skipTest("Login did not return refresh_token (MFA flow)")
        response = self.client.post(
            reverse("refresh-token"),
            {
                "refresh_token": refresh_token,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_refresh_400_with_invalid_token(self):
        """POST /api/usuarios/refresh/ returns 400/401 with invalid refresh token."""
        response = self.client.post(
            reverse("refresh-token"),
            {
                "refresh_token": "invalid.refresh.token",
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
        )

    # ===================== UNAUTHENTICATED ACCESS =====================

    def test_unauthenticated_pacientes_list_401(self):
        """GET /api/pacientes/ returns 401 when unauthenticated."""
        response = self.client.get(reverse("paciente-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_embarazos_list_401(self):
        """GET /api/embarazos/ returns 401 when unauthenticated."""
        response = self.client.get(reverse("embarazo-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_controles_list_401(self):
        """GET /api/controles/ returns 401 when unauthenticated."""
        response = self.client.get(reverse("controlprenatal-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_ecografias_list_401(self):
        """GET /api/ecografias/ returns 401 when unauthenticated."""
        response = self.client.get(reverse("ecografia-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_calculadoras_list_401(self):
        """GET /api/calculadoras/ returns 401 when unauthenticated."""
        response = self.client.get(reverse("calculadora-riesgo-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ===================== PACIENTES ENDPOINTS =====================

    def test_pacientes_list_200(self):
        """GET /api/pacientes/ returns 200 when authenticated."""
        self._authenticate()
        response = self.client.get(reverse("paciente-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pacientes_create_201(self):
        """POST /api/pacientes/ returns 201 on successful creation."""
        self._authenticate()
        data = {
            "nombre": "API",
            "apellido_paterno": "Test",
            "fecha_nacimiento": "1990-01-01",
            "genero": "femenino",
            "ci": "11111111",
        }
        response = self.client.post(reverse("paciente-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_pacientes_retrieve_200(self):
        """GET /api/pacientes/{id}/ returns 200."""
        self._authenticate()
        url = reverse("paciente-detail", kwargs={"pk": self.paciente.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pacientes_retrieve_404_nonexistent(self):
        """GET /api/pacientes/{id}/ returns 404 for non-existent."""
        self._authenticate()
        response = self.client.get(reverse("paciente-detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pacientes_update_200(self):
        """PUT /api/pacientes/{id}/ returns 200."""
        self._authenticate()
        url = reverse("paciente-detail", kwargs={"pk": self.paciente.pk})
        data = {
            "nombre": "Updated",
            "apellido_paterno": "Test",
            "fecha_nacimiento": "1990-01-01",
            "genero": "femenino",
            "ci": "12345678",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pacientes_partial_update_200(self):
        """PATCH /api/pacientes/{id}/ returns 200."""
        self._authenticate()
        url = reverse("paciente-detail", kwargs={"pk": self.paciente.pk})
        response = self.client.patch(url, {"nombre": "Patched"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pacientes_delete_admin_200(self):
        """DELETE /api/pacientes/{id}/ returns 200 for admin."""
        self._authenticate(user=self.admin)
        url = reverse("paciente-detail", kwargs={"pk": self.paciente.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pacientes_buscar_200(self):
        """GET /api/pacientes/buscar/q=test returns 200."""
        self._authenticate()
        response = self.client.get(reverse("paciente-buscar"), {"q": "Maria"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pacientes_buscar_400_no_query(self):
        """GET /api/pacientes/buscar/ without q returns 400."""
        self._authenticate()
        response = self.client.get(reverse("paciente-buscar"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pacientes_estadisticas_200(self):
        """GET /api/pacientes/estadisticas/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("paciente-estadisticas"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ===================== EMBARAZOS ENDPOINTS =====================

    def test_embarazos_list_200(self):
        """GET /api/embarazos/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("embarazo-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_embarazos_create_201(self):
        """POST /api/embarazos/ returns 201."""
        self._authenticate()
        # First finalise the existing active embarazo to avoid duplicate-active validation
        self.embarazo.estado = "finalizado"
        self.embarazo.save(update_fields=["estado"])
        # Use gesta=2, para=1 so the model clean() is satisfied:
        # numero_gesta(2) == numero_para(1) + numero_abortos(0) + actual(1)
        data = {
            "paciente": self.paciente.id,
            "numero_gesta": 2,
            "numero_para": 1,
            "numero_abortos": 0,
            "numero_cesareas": 0,
            "fecha_ultima_menstruacion": (
                datetime.date.today() - datetime.timedelta(weeks=10)
            ).isoformat(),
            "tipo_embarazo": "simple",
            "riesgo_embarazo": "bajo",
            "estado": "activo",
        }
        response = self.client.post(reverse("embarazo-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_embarazos_retrieve_200(self):
        """GET /api/embarazos/{id}/ returns 200."""
        self._authenticate()
        url = reverse("embarazo-detail", kwargs={"pk": self.embarazo.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_embarazos_update_200(self):
        """PUT /api/embarazos/{id}/ returns 200."""
        self._authenticate()
        url = reverse("embarazo-detail", kwargs={"pk": self.embarazo.pk})
        data = {
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
            "notas": "Updated",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_embarazos_activos_200(self):
        """GET /api/embarazos/activos/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("embarazo-activos"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_embarazos_estadisticas_200(self):
        """GET /api/embarazos/estadisticas/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("embarazo-estadisticas"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_embarazos_alto_riesgo_200(self):
        """GET /api/embarazos/alto_riesgo/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("embarazo-alto-riesgo"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_embarazos_multiples_200(self):
        """GET /api/embarazos/multiples/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("embarazo-multiples"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ===================== CONTROLES ENDPOINTS =====================

    def test_controles_list_200(self):
        """GET /api/controles/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("controlprenatal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_controles_create_201(self):
        """POST /api/controles/ returns 201."""
        self._authenticate()
        data = {
            "embarazo": self.embarazo.id,
            "paciente": self.paciente.id,
            "numero_control": 2,
            "fecha_control": datetime.date.today().isoformat(),
            "semanas_gestacion": 14,
            "dias_gestacion": 0,
            "peso_actual": "66.00",
            "talla": "165.00",
            "presion_arterial_sistolica": 115,
            "presion_arterial_diastolica": 72,
        }
        response = self.client.post(
            reverse("controlprenatal-list"), data, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_controles_retrieve_200(self):
        """GET /api/controles/{id}/ returns 200."""
        self._authenticate()
        url = reverse("controlprenatal-detail", kwargs={"pk": self.control.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_controles_update_200(self):
        """PUT /api/controles/{id}/ returns 200."""
        self._authenticate()
        url = reverse("controlprenatal-detail", kwargs={"pk": self.control.pk})
        data = {
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
            "observaciones": "Updated",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_controles_estadisticas_200(self):
        """GET /api/controles/estadisticas/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("controlprenatal-estadisticas"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_controles_alertas_200(self):
        """GET /api/controles/alertas/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("controlprenatal-alertas"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_controles_recientes_200(self):
        """GET /api/controles/recientes/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("controlprenatal-recientes"), {"dias": 7})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ===================== ECOGRAFIAS ENDPOINTS =====================

    def test_ecografias_list_200(self):
        """GET /api/ecografias/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("ecografia-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ecografias_create_201(self):
        """POST /api/ecografias/ returns 201."""
        self._authenticate()
        data = {
            "embarazo": self.embarazo.id,
            "paciente": self.paciente.id,
            "fecha_ecografia": datetime.date.today().isoformat(),
            "tipo_ecografia": "segundo_trimestre",
            "indicacion": "control_rutina",
            "edad_gestacional_semanas": 20,
            "edad_gestacional_dias": 0,
            "numero_fetos": 1,
            "vitalidad_fetal": True,
            "diagnostico": "Normal at 20 weeks",
        }
        response = self.client.post(reverse("ecografia-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ecografias_retrieve_200(self):
        """GET /api/ecografias/{id}/ returns 200."""
        self._authenticate()
        url = reverse("ecografia-detail", kwargs={"pk": self.ecografia.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ecografias_update_200(self):
        """PUT /api/ecografias/{id}/ returns 200."""
        self._authenticate()
        url = reverse("ecografia-detail", kwargs={"pk": self.ecografia.pk})
        data = {
            "embarazo": self.embarazo.id,
            "paciente": self.paciente.id,
            "fecha_ecografia": datetime.date.today().isoformat(),
            "tipo_ecografia": "primer_trimestre",
            "indicacion": "control_rutina",
            "edad_gestacional_semanas": 12,
            "edad_gestacional_dias": 0,
            "numero_fetos": 1,
            "vitalidad_fetal": True,
            "diagnostico": "Updated diagnosis",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ecografias_estadisticas_200(self):
        """GET /api/ecografias/estadisticas/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("ecografia-estadisticas"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ===================== CALCULADORAS ENDPOINTS =====================

    def test_calculadoras_list_200(self):
        """GET /api/calculadoras/ returns 200."""
        self._authenticate()
        response = self.client.get(reverse("calculadora-riesgo-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calculadoras_retrieve_200(self):
        """GET /api/calculadoras/{id}/ returns 200."""
        self._authenticate()
        url = reverse("calculadora-riesgo-detail", kwargs={"pk": self.calculadora.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calculadoras_update_200(self):
        """PUT /api/calculadoras/{id}/ returns 200."""
        self._authenticate()
        url = reverse("calculadora-riesgo-detail", kwargs={"pk": self.calculadora.pk})
        data = {
            "paciente_id": self.paciente.id,
            "embarazo_id": self.embarazo.id,
            "tipo": "preeclampsia",
            "edad_gestacional_semanas": 12,
            "edad_gestacional_dias": 0,
            "edad_materna": 30,
            "peso_kg": "65.00",
            "talla_cm": "165.00",
            "etnia": "mestiza",
            "tabaquismo": False,
            "hta_cronica": False,
            "diabetes_previa": False,
            "preeclampsia_previa": False,
            "paridad": 0,
            "metodo_concepcion": "espontaneo",
            "notas_adicionales": "Updated",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calculadoras_delete_204(self):
        """DELETE /api/calculadoras/{id}/ returns 204."""
        self._authenticate()
        url = reverse("calculadora-riesgo-detail", kwargs={"pk": self.calculadora.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===================== VALIDATION ERRORS =====================

    def test_pacientes_create_400_missing_required(self):
        """POST /api/pacientes/ returns 400 with missing required fields."""
        self._authenticate()
        response = self.client.post(
            reverse("paciente-list"),
            {
                "nombre": "Incomplete",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_embarazos_create_400_missing_required(self):
        """POST /api/embarazos/ returns 400 with missing required fields."""
        self._authenticate()
        response = self.client.post(
            reverse("embarazo-list"),
            {
                "paciente": self.paciente.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_controles_create_400_missing_required(self):
        """POST /api/controles/ returns 400 with missing required fields."""
        self._authenticate()
        response = self.client.post(
            reverse("controlprenatal-list"),
            {
                "embarazo": self.embarazo.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ecografias_create_400_missing_required(self):
        """POST /api/ecografias/ returns 400 with missing required fields."""
        self._authenticate()
        response = self.client.post(
            reverse("ecografia-list"),
            {
                "embarazo": self.embarazo.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ===================== DELETE PERMISSIONS =====================

    def test_pacientes_delete_non_admin_403(self):
        """DELETE /api/pacientes/{id}/ returns 403 for non-admin."""
        self._authenticate(user=self.medico)
        url = reverse("paciente-detail", kwargs={"pk": self.paciente.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_embarazos_delete_non_admin_403(self):
        """DELETE /api/embarazos/{id}/ returns 403 for non-admin."""
        self._authenticate(user=self.medico)
        url = reverse("embarazo-detail", kwargs={"pk": self.embarazo.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_controles_delete_non_admin_403(self):
        """DELETE /api/controles/{id}/ returns 403 for non-admin."""
        self._authenticate(user=self.medico)
        url = reverse("controlprenatal-detail", kwargs={"pk": self.control.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
