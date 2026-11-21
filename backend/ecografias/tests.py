"""Tests para el módulo de Ecografías."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from embarazos.models import Embarazo
from pacientes.models import Paciente

from .models import BiometriaFetal, Ecografia

Usuario = get_user_model()


def _paciente(ci="1000001"):
    return Paciente.objects.create(
        id_clinico=f"PAC-{ci}", nombre="María", apellido_paterno="Gómez",
        fecha_nacimiento=date(1995, 5, 20), genero="femenino", ci=ci,
    )


def _embarazo(paciente):
    return Embarazo.objects.create(
        paciente=paciente, numero_gesta=1,
        fecha_ultima_menstruacion=date.today() - timedelta(weeks=20),
    )


class EcografiaModelTest(TestCase):
    def setUp(self):
        self.paciente = _paciente()
        self.embarazo = _embarazo(self.paciente)

    def test_crear_ecografia(self):
        eco = Ecografia.objects.create(
            embarazo=self.embarazo, paciente=self.paciente,
            fecha_ecografia=date.today(), tipo_ecografia="primer_trimestre",
            edad_gestacional_semanas=12, diagnostico="Normal",
        )
        self.assertEqual(eco.paciente, self.paciente)
        self.assertEqual(eco.edad_gestacional_semanas, 12)

    def test_biometria_relacion_uno_a_uno(self):
        eco = Ecografia.objects.create(
            embarazo=self.embarazo, paciente=self.paciente,
            fecha_ecografia=date.today(), tipo_ecografia="segundo_trimestre",
            edad_gestacional_semanas=22, diagnostico="Normal",
        )
        bio = BiometriaFetal.objects.create(ecografia=eco)
        self.assertEqual(bio.ecografia, eco)
        # La relación inversa OneToOne debe resolver a la misma ecografía
        self.assertEqual(BiometriaFetal.objects.get(ecografia=eco).pk, bio.pk)


class EcografiaApiTest(TestCase):
    def test_lista_requiere_autenticacion(self):
        resp = self.client.get("/api/ecografias/")
        self.assertIn(resp.status_code, (401, 403))

    def test_lista_autenticado(self):
        user = Usuario.objects.create_user(
            email="eco@test.bo", nombre="E", apellido_paterno="Co", password="x",
        )
        self.client.force_login(user)
        resp = self.client.get("/api/ecografias/")
        # Autenticado: 200 o 403 por permisos de rol, nunca 401
        self.assertNotEqual(resp.status_code, 401)
