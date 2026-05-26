"""Tests for Ecografia model and API endpoints.
"""

import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ecografias.models import AnatomiaFetal, BiometriaFetal, Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class EcografiaModelTest(TestCase):
    """Tests for the Ecografia model."""

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
        self.ecografia_data = {
            "embarazo": self.embarazo,
            "paciente": self.paciente,
            "medico": self.medico_user,
            "fecha_ecografia": datetime.date.today(),
            "tipo_ecografia": "primer_trimestre",
            "indicacion": "control_rutina",
            "edad_gestacional_semanas": 12,
            "edad_gestacional_dias": 0,
            "numero_fetos": 1,
            "vitalidad_fetal": True,
            "diagnostico": "Embarazo normal de 12 semanas",
            "created_by": self.admin_user,
        }

    def test_create_ecografia(self):
        """Test creating an ecografia instance."""
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertEqual(Ecografia.objects.count(), 1)
        self.assertEqual(eco.tipo_ecografia, "primer_trimestre")
        self.assertTrue(eco.vitalidad_fetal)

    def test_ecografia_str(self):
        """Test __str__ method."""
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertIn("Ecografia", str(eco))
        self.assertIn("Maria", str(eco))

    def test_edad_gestacional_texto(self):
        """Test edad gestacional formatted text."""
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertEqual(eco.get_edad_gestacional_texto(), "12+0 semanas")

    def test_edad_gestacional_con_dias(self):
        """Test edad gestacional with days."""
        self.ecografia_data["edad_gestacional_dias"] = 3
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertEqual(eco.get_edad_gestacional_texto(), "12+3 semanas")

    def test_evaluacion_fcf_normal(self):
        """Test FCF evaluation when normal."""
        self.ecografia_data["frecuencia_cardiaca_fetal"] = 140
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertIn("Normal", eco.get_evaluacion_fcf())

    def test_evaluacion_fcf_bradicardia(self):
        """Test FCF evaluation when bradycardia."""
        self.ecografia_data["frecuencia_cardiaca_fetal"] = 100
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertIn("Bradicardia", eco.get_evaluacion_fcf())

    def test_evaluacion_fcf_taquicardia(self):
        """Test FCF evaluation when tachycardia."""
        self.ecografia_data["frecuencia_cardiaca_fetal"] = 170
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertIn("Taquicardia", eco.get_evaluacion_fcf())

    def test_estado_liquido_amniotico_normal(self):
        """Test amniotic fluid evaluation when normal."""
        self.ecografia_data["indice_liquido_amniotico"] = Decimal("14.0")
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertIn("Normal", eco.get_estado_liquido_amniotico())

    def test_estado_liquido_amniotico_oligohidramnios(self):
        """Test amniotic fluid evaluation when oligohydramnios."""
        self.ecografia_data["indice_liquido_amniotico"] = Decimal("4.0")
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertIn("Oligohidramnios", eco.get_estado_liquido_amniotico())

    def test_estado_liquido_amniotico_polihidramnios(self):
        """Test amniotic fluid evaluation when polyhydramnios."""
        self.ecografia_data["indice_liquido_amniotico"] = Decimal("26.0")
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertIn("Polihidramnios", eco.get_estado_liquido_amniotico())

    def test_edad_gestacional_completa_property(self):
        """Test edad_gestacional_completa property."""
        eco = Ecografia.objects.create(**self.ecografia_data)
        self.assertEqual(eco.edad_gestacional_completa, "12+0")


class BiometriaFetalModelTest(TestCase):
    """Tests for the BiometriaFetal model."""

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
            ci="12345679",
        )
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=20),
        )
        self.ecografia = Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="segundo_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=20,
            diagnostico="Normal",
        )

    def test_create_biometria(self):
        """Test creating a biometria fetal instance."""
        biometria = BiometriaFetal.objects.create(
            ecografia=self.ecografia,
            diametro_biparietal=Decimal("48.0"),
            circunferencia_cefalica=Decimal("177.0"),
            circunferencia_abdominal=Decimal("154.0"),
            longitud_femur=Decimal("33.0"),
        )
        self.assertEqual(BiometriaFetal.objects.count(), 1)
        self.assertEqual(biometria.diametro_biparietal, Decimal("48.0"))

    def test_calcular_relaciones(self):
        """Test biometric relationship calculations."""
        biometria = BiometriaFetal.objects.create(
            ecografia=self.ecografia,
            diametro_biparietal=Decimal("48.0"),
            circunferencia_cefalica=Decimal("177.0"),
            circunferencia_abdominal=Decimal("154.0"),
            longitud_femur=Decimal("33.0"),
        )
        self.assertIsNotNone(biometria.relacion_cc_ca)
        self.assertIsNotNone(biometria.relacion_lf_ca)

    def test_calcular_peso_fetal_hadlock(self):
        """Test Hadlock fetal weight calculation."""
        biometria = BiometriaFetal.objects.create(
            ecografia=self.ecografia,
            diametro_biparietal=Decimal("48.0"),
            circunferencia_cefalica=Decimal("177.0"),
            circunferencia_abdominal=Decimal("154.0"),
            longitud_femur=Decimal("33.0"),
        )
        peso = biometria.calcular_peso_fetal_hadlock()
        self.assertIsNotNone(peso)
        self.assertGreater(peso, 0)

    def test_save_auto_calculates(self):
        """Test that save auto-calculates relationships and weight."""
        biometria = BiometriaFetal.objects.create(
            ecografia=self.ecografia,
            diametro_biparietal=Decimal("48.0"),
            circunferencia_cefalica=Decimal("177.0"),
            circunferencia_abdominal=Decimal("154.0"),
            longitud_femur=Decimal("33.0"),
        )
        self.assertIsNotNone(biometria.relacion_cc_ca)
        self.assertIsNotNone(biometria.peso_fetal_estimado)

    def test_biometria_str(self):
        """Test __str__ method."""
        biometria = BiometriaFetal.objects.create(
            ecografia=self.ecografia,
            diametro_biparietal=Decimal("48.0"),
            circunferencia_cefalica=Decimal("177.0"),
            circunferencia_abdominal=Decimal("154.0"),
            longitud_femur=Decimal("33.0"),
        )
        self.assertIn("Biometria", str(biometria))


class AnatomiaFetalModelTest(TestCase):
    """Tests for the AnatomiaFetal model."""

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
            ci="12345680",
        )
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=datetime.date.today()
            - datetime.timedelta(weeks=20),
        )
        self.ecografia = Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="segundo_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=20,
            diagnostico="Normal",
        )

    def test_create_anatomia_normal(self):
        """Test creating a normal anatomia fetal."""
        anatomia = AnatomiaFetal.objects.create(ecografia=self.ecografia)
        self.assertTrue(anatomia.craneo_normal)
        self.assertTrue(anatomia.corazon_normal)

    def test_get_evaluacion_anatomica_normal(self):
        """Test anatomical evaluation when all normal."""
        anatomia = AnatomiaFetal.objects.create(ecografia=self.ecografia)
        self.assertIn("normal", anatomia.get_evaluacion_anatomica().lower())

    def test_get_evaluacion_anatomica_abnormal(self):
        """Test anatomical evaluation with abnormalities."""
        anatomia = AnatomiaFetal.objects.create(
            ecografia=self.ecografia,
            corazon_normal=False,
            hallazgos_anormales="Defecto septal ventricular",
        )
        evaluacion = anatomia.get_evaluacion_anatomica()
        self.assertIn("anormal", evaluacion.lower())

    def test_get_riesgo_cromosomopatias(self):
        """Test chromosomal risk evaluation."""
        anatomia = AnatomiaFetal.objects.create(
            ecografia=self.ecografia,
            translucencia_nucal=Decimal("1.5"),
        )
        self.assertIn("Bajo riesgo", anatomia.get_riesgo_cromosomopatias())

    def test_get_riesgo_cromosomopatias_alto(self):
        """Test chromosomal risk evaluation with high risk."""
        anatomia = AnatomiaFetal.objects.create(
            ecografia=self.ecografia,
            translucencia_nucal=Decimal("4.0"),
        )
        self.assertIn("Alto riesgo", anatomia.get_riesgo_cromosomopatias())


class EcografiaAPITest(APITestCase):
    """Tests for Ecografia API endpoints."""

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
            ci="12345681",
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
        self.ecografia_data = {
            "embarazo": self.embarazo.id,
            "paciente": self.paciente.id,
            "fecha_ecografia": datetime.date.today().isoformat(),
            "tipo_ecografia": "primer_trimestre",
            "indicacion": "control_rutina",
            "edad_gestacional_semanas": 12,
            "edad_gestacional_dias": 0,
            "numero_fetos": 1,
            "vitalidad_fetal": True,
            "diagnostico": "Embarazo normal de 12 semanas",
        }
        self.list_url = reverse("ecografia-list")

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

    def test_create_ecografia_success(self):
        """Test creating an ecografia via API."""
        self._authenticate()
        response = self.client.post(self.list_url, self.ecografia_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_create_ecografia_validation_missing_fields(self):
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

    def test_list_ecografias(self):
        """Test listing ecografias."""
        self._authenticate()
        Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="primer_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=12,
            diagnostico="Normal",
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_ecografia(self):
        """Test retrieving a single ecografia."""
        self._authenticate()
        eco = Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="primer_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=12,
            diagnostico="Normal",
        )
        url = reverse("ecografia-detail", kwargs={"pk": eco.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_ecografia(self):
        """Test updating an ecografia via PUT."""
        self._authenticate()
        eco = Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="primer_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=12,
            diagnostico="Original diagnosis",
        )
        url = reverse("ecografia-detail", kwargs={"pk": eco.pk})
        update_data = {
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
        response = self.client.put(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        eco.refresh_from_db()
        self.assertEqual(eco.diagnostico, "Updated diagnosis")

    def test_partial_update_ecografia(self):
        """Test partial update via PATCH."""
        self._authenticate()
        eco = Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="primer_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=12,
            diagnostico="Original",
        )
        url = reverse("ecografia-detail", kwargs={"pk": eco.pk})
        response = self.client.patch(url, {"diagnostico": "Patched"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        eco.refresh_from_db()
        self.assertEqual(eco.diagnostico, "Patched")

    def test_delete_ecografia(self):
        """Test deleting an ecografia."""
        self._authenticate()
        eco = Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="primer_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=12,
            diagnostico="To delete",
        )
        url = reverse("ecografia-detail", kwargs={"pk": eco.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Ecografia.objects.count(), 0)

    def test_estadisticas_endpoint(self):
        """Test estadisticas custom endpoint."""
        self._authenticate()
        url = reverse("ecografia-estadisticas")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_ecografias", response.data)

    def test_por_embarazo_endpoint(self):
        """Test por_embarazo custom endpoint."""
        self._authenticate()
        Ecografia.objects.create(
            embarazo=self.embarazo,
            paciente=self.paciente,
            medico=self.medico_user,
            fecha_ecografia=datetime.date.today(),
            tipo_ecografia="primer_trimestre",
            indicacion="control_rutina",
            edad_gestacional_semanas=12,
            diagnostico="Normal",
        )
        url = reverse("ecografia-por_embarazo")
        response = self.client.get(url, {"embarazo_id": self.embarazo.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("ecografias", response.data)

    def test_por_embarazo_missing_param(self):
        """Test por_embarazo without embarazo_id returns 400."""
        self._authenticate()
        url = reverse("ecografia-por_embarazo")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
