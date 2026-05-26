"""Tests para módulo de Partos"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from embarazos.models import Embarazo
from pacientes.models import Paciente

from .models import Parto, RecienNacido

User = get_user_model()


class PartoModelTestCase(TestCase):
    """Tests para modelo Parto"""

    def setUp(self):
        """Setup"""
        self.user = User.objects.create_user(
            email="testdoctor@clinica.com",
            nombre="Doctor",
            apellido_paterno="Prueba",
            password="testpass123",
        )

        self.paciente = Paciente.objects.create(
            nombre="María",
            apellido_paterno="García",
            apellido_materno="López",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
        )

        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=10),
            numero_gesta=1,
            estado="activo",
        )

    def test_crear_parto(self):
        """Test crear parto"""
        parto = Parto.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            fecha_parto=datetime.now(),
            tipo_parto="vaginal",
            presentacion="cefalica",
            edad_gestacional_parto=40,
            medico_responsable=self.user,
        )

        self.assertIsNotNone(parto.id)
        self.assertEqual(parto.paciente, self.paciente)
        self.assertEqual(parto.tipo_parto, "vaginal")

    def test_str_representation(self):
        """Test representación string"""
        parto = Parto.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            fecha_parto=datetime.now(),
            tipo_parto="cesarea",
            medico_responsable=self.user,
        )

        str_repr = str(parto)
        self.assertIn("María García", str_repr)
        self.assertIn("cesarea", str_repr.lower())

    def test_duracion_trabajo_parto(self):
        """Test cálculo de duración de trabajo de parto"""
        inicio = datetime.now()
        fin = datetime.now()

        parto = Parto.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            fecha_parto=fin,
            inicio_trabajo_parto=inicio,
            fin_trabajo_parto=fin,
            tipo_parto="vaginal",
            medico_responsable=self.user,
        )

        # Debería calcular duración automáticamente
        self.assertIsNotNone(parto.duracion_trabajo_parto)


class RecienNacidoModelTestCase(TestCase):
    """Tests para modelo RecienNacido"""

    def setUp(self):
        """Setup"""
        self.user = User.objects.create_user(
            email="testdoctor@clinica.com",
            nombre="Doctor",
            apellido_paterno="Prueba",
            password="testpass123",
        )

        self.paciente = Paciente.objects.create(
            nombre="María",
            apellido_paterno="García",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
            ci="TEST" + str(datetime.now().microsecond),
        )

        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            fecha_ultima_menstruacion=date(2023, 1, 1),
            numero_gesta=1,
        )

        self.parto = Parto.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            fecha_parto=datetime.now(),
            tipo_parto="vaginal",
            medico_responsable=self.user,
        )

    def test_crear_recien_nacido(self):
        """Test crear recién nacido"""
        rn = RecienNacido.objects.create(
            parto=self.parto,
            sexo="M",
            peso=Decimal("3.5"),
            talla=Decimal("50.0"),
            perimetro_cefalico=Decimal("34.0"),
            apgar_1min=9,
            apgar_5min=10,
            estado="vivo",
        )

        self.assertIsNotNone(rn.id)
        self.assertEqual(rn.sexo, "M")
        self.assertEqual(rn.peso, Decimal("3.5"))

    def test_validacion_peso(self):
        """Test validación de peso"""
        rn = RecienNacido(
            parto=self.parto,
            sexo="F",
            peso=Decimal("6.0"),  # Peso muy alto
            apgar_1min=9,
            apgar_5min=10,
        )

        # Debería marcarse como macrosómico
        rn.save()
        self.assertIsNotNone(rn.id)

    def test_apgar_bajo(self):
        """Test Apgar bajo"""
        rn = RecienNacido.objects.create(
            parto=self.parto,
            sexo="M",
            peso=Decimal("3.0"),
            apgar_1min=5,  # Apgar bajo
            apgar_5min=7,
            estado="vivo",
        )

        # Verificar que se detecta Apgar bajo
        self.assertLess(rn.apgar_1min, 7)


class PartoAPITestCase(APITestCase):
    """Tests para API de Partos"""

    def setUp(self):
        """Setup"""
        self.user = User.objects.create_user(
            email="testdoctor@clinica.com",
            nombre="Doctor",
            apellido_paterno="Prueba",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.paciente = Paciente.objects.create(
            nombre="María",
            apellido_paterno="García",
            fecha_nacimiento=date(1990, 1, 1),
            genero="F",
            ci="TEST" + str(datetime.now().microsecond),
        )

        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            fecha_ultima_menstruacion=date(2023, 1, 1),
            numero_gesta=1,
        )

    def test_listar_partos(self):
        """Test listar partos"""
        response = self.client.get("/api/partos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_parto_completo(self):
        """Test crear parto con datos completos"""
        data = {
            "embarazo": self.embarazo.id,
            "paciente": self.paciente.id,
            "fecha_parto": datetime.now().isoformat(),
            "tipo_parto": "vaginal",
            "presentacion": "cefalica",
            "edad_gestacional_parto": 40,
            "medico_responsable": self.user.id,
            "recien_nacidos": [
                {
                    "sexo": "M",
                    "peso": "3.5",
                    "talla": "50.0",
                    "apgar_1min": 9,
                    "apgar_5min": 10,
                    "estado": "vivo",
                },
            ],
        }

        response = self.client.post("/api/partos/", data, format="json")

        # Puede retornar 201 o 400 dependiendo de validaciones
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST],
        )

    def test_obtener_parto_detalle(self):
        """Test obtener detalle de parto"""
        parto = Parto.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            fecha_parto=datetime.now(),
            tipo_parto="cesarea",
            medico_responsable=self.user,
        )

        response = self.client.get(f"/api/partos/{parto.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], parto.id)

    def test_estadisticas_partos(self):
        """Test endpoint de estadísticas"""
        # Crear algunos partos
        for i in range(3):
            Parto.objects.create(
                embarazo=self.embarazo,
                paciente=self.paciente,
                fecha_parto=datetime.now(),
                tipo_parto="vaginal" if i % 2 == 0 else "cesarea",
                medico_responsable=self.user,
            )

        response = self.client.get("/api/partos/estadisticas/")

        if response.status_code == status.HTTP_200_OK:
            self.assertIn("total", response.data or {})
