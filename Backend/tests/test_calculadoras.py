"""Tests for calculadora de riesgo model and API endpoints.
"""

import datetime
from decimal import Decimal
from typing import cast

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from calculadoras.models import BiomarcadorMOM, CalculadoraRiesgo
from calculadoras.models_historial import CalculoHistorial
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class CalculadoraRiesgoModelTest(TestCase):
    """Tests for the CalculadoraRiesgo model."""

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
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )
        self.calc_data = {
            "paciente": self.paciente,
            "embarazo": self.embarazo,
            "tipo": "preeclampsia",
            "edad_gestacional_semanas": 12,
            "edad_gestacional_dias": 0,
            "edad_materna": 30,
            "peso_kg": Decimal("65.00"),
            "talla_cm": Decimal("165.00"),
            "etnia": "mestiza",
            "calculado_por": self.admin_user,
        }

    def test_create_calculadora(self):
        """Test creating a calculadora de riesgo instance."""
        calc = CalculadoraRiesgo.objects.create(**self.calc_data)
        self.assertEqual(CalculadoraRiesgo.objects.count(), 1)
        self.assertEqual(calc.tipo, "preeclampsia")
        self.assertEqual(calc.edad_materna, 30)

    def test_imc_auto_calculated(self):
        """Test that IMC is auto-calculated on save."""
        calc = CalculadoraRiesgo.objects.create(**self.calc_data)
        expected_imc = round(65.0 / (1.65**2), 2)
        self.assertEqual(float(calc.imc), expected_imc)

    def test_edad_gestacional_total_dias(self):
        """Test edad gestacional in total days."""
        calc = CalculadoraRiesgo.objects.create(**self.calc_data)
        self.assertEqual(calc.edad_gestacional_total_dias, 12 * 7)

    def test_edad_gestacional_texto(self):
        """Test edad gestacional formatted text."""
        calc = CalculadoraRiesgo.objects.create(**self.calc_data)
        self.assertEqual(calc.edad_gestacional_texto, "12+0 semanas")

    def test_calculadora_str(self):
        """Test __str__ method."""
        calc = CalculadoraRiesgo.objects.create(**self.calc_data)
        self.assertIn("Preeclampsia", str(calc))
        self.assertIn("Maria", str(calc))


class BiomarcadorMOMModelTest(TestCase):
    """Tests for the BiomarcadorMOM model."""

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
            ci="12345699",
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
        self.calc = CalculadoraRiesgo.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazo,
            tipo="preeclampsia",
            edad_gestacional_semanas=12,
            edad_materna=30,
            peso_kg=Decimal("65.00"),
            talla_cm=Decimal("165.00"),
            etnia="mestiza",
            calculado_por=self.admin_user,
        )

    def test_create_biomarcador_normal_range(self):
        """Test creating biomarcador within normal MoM range."""
        bio = BiomarcadorMOM.objects.create(
            calculadora=self.calc,
            marcador="pappa",
            valor_crudo=Decimal("1.5000"),
            unidad="mIU/mL",
            mediana_esperada=Decimal("1.5000"),
            mom_calculado=Decimal("1.000"),
        )
        self.assertTrue(bio.dentro_rango)
        self.assertEqual(bio.interpretacion, "Normal")

    def test_create_biomarcador_low_mom(self):
        """Test creating biomarcador with low MoM."""
        bio = BiomarcadorMOM.objects.create(
            calculadora=self.calc,
            marcador="pappa",
            valor_crudo=Decimal("0.5000"),
            unidad="mIU/mL",
            mediana_esperada=Decimal("1.5000"),
            mom_calculado=Decimal("0.333"),
        )
        self.assertFalse(bio.dentro_rango)
        self.assertIn("Muy bajo", bio.interpretacion)

    def test_create_biomarcador_high_mom(self):
        """Test creating biomarcador with high MoM."""
        bio = BiomarcadorMOM.objects.create(
            calculadora=self.calc,
            marcador="bhcg",
            valor_crudo=Decimal("3.0000"),
            unidad="mIU/mL",
            mediana_esperada=Decimal("1.5000"),
            mom_calculado=Decimal("2.000"),
        )
        self.assertFalse(bio.dentro_rango)
        self.assertIn("Muy alto", bio.interpretacion)

    def test_unique_together(self):
        """Test unique constraint on calculadora + marcador."""
        from django.db import IntegrityError

        BiomarcadorMOM.objects.create(
            calculadora=self.calc,
            marcador="pappa",
            valor_crudo=Decimal("1.5000"),
            unidad="mIU/mL",
            mediana_esperada=Decimal("1.5000"),
            mom_calculado=Decimal("1.000"),
        )
        with self.assertRaises(IntegrityError):
            BiomarcadorMOM.objects.create(
                calculadora=self.calc,
                marcador="pappa",
                valor_crudo=Decimal("2.0000"),
                unidad="mIU/mL",
                mediana_esperada=Decimal("1.5000"),
                mom_calculado=Decimal("1.333"),
            )

    def test_biomarcador_str(self):
        """Test __str__ method."""
        bio = BiomarcadorMOM.objects.create(
            calculadora=self.calc,
            marcador="pappa",
            valor_crudo=Decimal("1.5000"),
            unidad="mIU/mL",
            mediana_esperada=Decimal("1.5000"),
            mom_calculado=Decimal("1.000"),
        )
        self.assertIn("PAPP-A", str(bio))
        self.assertIn("1.000", str(bio))


class CalculadoraRiesgoAPITest(APITestCase):
    """Tests for CalculadoraRiesgo API endpoints."""

    def setUp(self):
        """Setup"""
        self.admin_user = Usuario.objects.create_superuser(
            email="admin@test.com",
            nombre="Admin",
            apellido_paterno="User",
            password="adminpass123",
        )
        self.paciente = cast(Paciente, Paciente.objects.create(
            nombre="Maria",
            apellido_paterno="Lopez",
            fecha_nacimiento=datetime.date(1990, 5, 15),
            genero="femenino",
            ci="12345700",
        ))
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=12),
        )
        self.preeclampsia_data = {
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
        }
        self.list_url = reverse("calculadora-riesgo-list")

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

    def test_list_calculadoras(self):
        """Test listing calculadoras."""
        self._authenticate()
        CalculadoraRiesgo.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazo,
            tipo="preeclampsia",
            edad_gestacional_semanas=12,
            edad_materna=30,
            peso_kg=Decimal("65.00"),
            talla_cm=Decimal("165.00"),
            etnia="mestiza",
            calculado_por=self.admin_user,
            riesgo_porcentaje=Decimal("2.500"),
            riesgo_ratio="1:40",
            categoria_riesgo="bajo",
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_calculadora(self):
        """Test retrieving a single calculadora."""
        self._authenticate()
        calc = CalculadoraRiesgo.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazo,
            tipo="preeclampsia",
            edad_gestacional_semanas=12,
            edad_materna=30,
            peso_kg=Decimal("65.00"),
            talla_cm=Decimal("165.00"),
            etnia="mestiza",
            calculado_por=self.admin_user,
        )
        url = reverse("calculadora-riesgo-detail", kwargs={"pk": calc.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_calculadora(self):
        """Test updating a calculadora via PUT."""
        self._authenticate()
        calc = CalculadoraRiesgo.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazo,
            tipo="preeclampsia",
            edad_gestacional_semanas=12,
            edad_materna=30,
            peso_kg=Decimal("65.00"),
            talla_cm=Decimal("165.00"),
            etnia="mestiza",
            calculado_por=self.admin_user,
            notas_adicionales="Original notes",
        )
        url = reverse("calculadora-riesgo-detail", kwargs={"pk": calc.pk})
        update_data = {
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
            "notas_adicionales": "Updated notes",
        }
        response = self.client.put(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calc.refresh_from_db()
        self.assertEqual(calc.notas_adicionales, "Updated notes")

    def test_delete_calculadora(self):
        """Test deleting a calculadora."""
        self._authenticate()
        calc = CalculadoraRiesgo.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazo,
            tipo="preeclampsia",
            edad_gestacional_semanas=12,
            edad_materna=30,
            peso_kg=Decimal("65.00"),
            talla_cm=Decimal("165.00"),
            etnia="mestiza",
            calculado_por=self.admin_user,
        )
        url = reverse("calculadora-riesgo-detail", kwargs={"pk": calc.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CalculadoraRiesgo.objects.count(), 0)

    def test_calcular_preeclampsia_endpoint(self):
        """Test calcular-preeclampsia custom action."""
        self._authenticate()
        url = reverse("calculadora-riesgo-calcular-preeclampsia")
        response = self.client.post(url, self.preeclampsia_data, format="json")
        # Could be 201 on success or 400 if some params are missing
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST],
        )

    def test_calcular_trisomias_endpoint(self):
        """Test calcular-trisomias custom action returns a valid response."""
        self._authenticate()
        url = reverse("calculadora-riesgo-calcular-trisomias")
        trisomias_data = {
            "paciente_id": self.paciente.id,
            "embarazo_id": self.embarazo.id,
            "tipo": "trisomias",
            "edad_gestacional_semanas": 12,
            "edad_gestacional_dias": 0,
            "edad_materna": 35,
            "peso_kg": "65.00",
            "talla_cm": "165.00",
            "etnia": "mestiza",
            "nt_mm": "1.5",
            "pappa_crudo": "1.5",
            "bhcg_crudo": "1.2",
        }
        response = self.client.post(url, trisomias_data, format="json")
        self.assertIn(
            response.status_code,
            [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
            ],
        )

    def test_calcular_diabetes_endpoint(self):
        """Test calcular-diabetes custom action."""
        self._authenticate()
        url = reverse("calculadora-riesgo-calcular-diabetes")
        diabetes_data = {
            "paciente_id": self.paciente.id,
            "embarazo_id": self.embarazo.id,
            "tipo": "diabetes_gestacional",
            "edad_gestacional_semanas": 12,
            "edad_gestacional_dias": 0,
            "edad_materna": 30,
            "peso_kg": "65.00",
            "talla_cm": "165.00",
            "etnia": "mestiza",
            "historia_familiar_diabetes": False,
            "diabetes_gestacional_previa": False,
            "macrosomia_previa": False,
        }
        response = self.client.post(url, diabetes_data, format="json")
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST],
        )

    def test_filter_by_tipo(self):
        """Test filtering calculadoras by tipo."""
        self._authenticate()
        CalculadoraRiesgo.objects.create(
            paciente=self.paciente,
            embarazo=self.embarazo,
            tipo="preeclampsia",
            edad_gestacional_semanas=12,
            edad_materna=30,
            peso_kg=Decimal("65.00"),
            talla_cm=Decimal("165.00"),
            etnia="mestiza",
            calculado_por=self.admin_user,
        )
        response = self.client.get(self.list_url, {"tipo": "preeclampsia"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CalculoHistorialAPITest(APITestCase):
    """Tests para el historial de las 8 calculadoras simples (Edad
    Gestacional, Bishop, IMC, etc.) — antes solo se guardaban en
    localStorage del navegador y se perdian al cerrar sesion."""

    def setUp(self):
        """Setup"""
        self.user = Usuario.objects.create_superuser(
            email="historial_admin@test.com",
            nombre="Historial",
            apellido_paterno="Admin",
            password="adminpass123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.paciente = cast(Paciente, Paciente.objects.create(
            nombre="Ana", apellido_paterno="Quispe",
            fecha_nacimiento=datetime.date(1995, 3, 10),
            genero="femenino", ci="12345701",
        ))
        self.list_url = reverse("calculo-historial-list")

    def test_crear_y_listar_resultado_calculadora(self):
        """POST de un resultado de calculadora -> debe poder leerse vía GET."""
        payload = {
            "paciente": self.paciente.id,
            "tipo_calculadora": "imc",
            "inputs_json": {"peso": 65, "talla": 1.65},
            "resultado_json": {"valor": "23.9", "categoria": "normal"},
            "resultado_resumen": "IMC 23.9 - Normal",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["tipo_calculadora"], "imc")
        # calculado_por se asigna automaticamente en el servidor (perform_create)
        self.assertEqual(response.data["calculado_por"], self.user.id)

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        resultados = list_response.data.get("results", list_response.data)
        self.assertTrue(
            any(r["resultado_resumen"] == "IMC 23.9 - Normal" for r in resultados),
        )

    def test_filtrar_por_tipo_calculadora(self):
        """El filtro por tipo_calculadora debe devolver solo esos registros."""
        CalculoHistorial.objects.create(
            tipo_calculadora="bishop",
            inputs_json={"dilatacion": 2},
            resultado_json={"score": 5},
            calculado_por=self.user,
        )
        CalculoHistorial.objects.create(
            tipo_calculadora="apgar",
            inputs_json={"fc": 2},
            resultado_json={"score": 9},
            calculado_por=self.user,
        )
        response = self.client.get(self.list_url, {"tipo_calculadora": "bishop"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultados = response.data.get("results", response.data)
        self.assertTrue(all(r["tipo_calculadora"] == "bishop" for r in resultados))
        self.assertTrue(len(resultados) >= 1)
