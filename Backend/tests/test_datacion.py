"""Datación: la FPP se corrige con la primera ecografía según la regla ACOG.

Antes el sistema usaba siempre FUM + 280 días, aunque una ecografía del
primer trimestre dijera otra cosa (FUM mal recordada, ciclos irregulares).
"""
import datetime

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from ecografias.models import Ecografia
from embarazos.datacion import umbral_redatacion
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

HOY = timezone.localdate()


class UmbralTest(SimpleTestCase):
    def test_umbrales_por_periodo(self):
        self.assertEqual(umbral_redatacion(8 * 7), 5)
        self.assertEqual(umbral_redatacion(12 * 7), 7)
        self.assertEqual(umbral_redatacion(20 * 7), 10)
        self.assertEqual(umbral_redatacion(25 * 7), 14)
        self.assertEqual(umbral_redatacion(32 * 7), 21)


class DatacionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.dat@test.bo", nombre="M", apellido_paterno="D",
                                                 password="clave-segura-123", rol="medico")
        cls.paciente = Paciente.objects.create(nombre="Eva", apellido_paterno="Dat", apellido_materno="Eco",
                                               fecha_nacimiento=datetime.date(1993, 1, 1), genero="femenino",
                                               ci="7999001")

    def _datacion(self, eg_eco_semanas, eg_eco_dias, dias_desde_fum=12 * 7):
        fum = HOY - datetime.timedelta(days=dias_desde_fum)
        e = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1, fecha_ultima_menstruacion=fum)
        Ecografia.objects.create(paciente=self.paciente, embarazo=e, fecha_ecografia=HOY,
                                 tipo_ecografia="primer_trimestre", edad_gestacional_semanas=eg_eco_semanas,
                                 edad_gestacional_dias=eg_eco_dias)
        c = APIClient()
        c.force_authenticate(self.medico)
        r = c.get(f"/api/embarazos/{e.pk}/")
        self.assertEqual(r.status_code, 200)
        return fum, r.json()["datacion"]

    def test_diferencia_pequena_mantiene_la_fum(self):
        fum, d = self._datacion(12, 5)  # 5 días más que la FUM, umbral 7
        self.assertFalse(d["redatar"])
        self.assertEqual(d["fpp_corregida"], (fum + datetime.timedelta(days=280)).isoformat())

    def test_diferencia_grande_redata_con_la_ecografia(self):
        """ESPERADO: ecografía de 10+0 cuando la FUM dice 12+0 → FPP 14 días más tarde."""
        fum, d = self._datacion(10, 0)
        self.assertTrue(d["redatar"])
        self.assertEqual(d["diferencia_dias"], -14)
        self.assertEqual(d["fpp_corregida"], (fum + datetime.timedelta(days=294)).isoformat())

    def test_sin_ecografia_no_hay_datacion(self):
        e = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1,
                                    fecha_ultima_menstruacion=HOY - datetime.timedelta(weeks=8))
        c = APIClient()
        c.force_authenticate(self.medico)
        self.assertIsNone(c.get(f"/api/embarazos/{e.pk}/").json()["datacion"])
