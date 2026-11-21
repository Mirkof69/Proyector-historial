"""Una ecografía no puede ser futura, anterior a la FUM, ni de otra paciente."""
import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

HOY = datetime.date.today()


def _paciente(ci):
    return Paciente.objects.create(nombre="Eva", apellido_paterno="Coh", apellido_materno="Eco",
                                   fecha_nacimiento=datetime.date(1992, 1, 1), genero="femenino", ci=ci)


class CoherenciaEcografiaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.coh@test.bo", nombre="M", apellido_paterno="C",
                                                 password="clave-segura-123", rol="medico")
        cls.a, cls.b = _paciente("7955001"), _paciente("7955002")
        cls.embarazo_a = Embarazo.objects.create(paciente=cls.a, numero_gesta=1,
                                                 fecha_ultima_menstruacion=HOY - datetime.timedelta(weeks=20))

    def _crear(self, **cambios):
        datos = {"paciente": self.a.pk, "embarazo": self.embarazo_a.pk, "fecha_ecografia": HOY.isoformat(),
                 "tipo_ecografia": "segundo_trimestre", "edad_gestacional_semanas": 20,
                 "edad_gestacional_dias": 0, "diagnostico": "Normal", **cambios}
        c = APIClient()
        c.force_authenticate(self.medico)
        return c.post("/api/ecografias/", datos, format="json")

    def test_una_ecografia_normal_se_crea(self):
        r = self._crear()
        self.assertEqual(r.status_code, 201, r.content[:300])

    def test_fecha_futura_se_rechaza(self):
        r = self._crear(fecha_ecografia=(HOY + datetime.timedelta(days=3)).isoformat())
        self.assertEqual(r.status_code, 400)
        self.assertIn("fecha_ecografia", r.json().get("errors", r.json()) if isinstance(r.json(), dict) else {})

    def test_anterior_a_la_fum_se_rechaza(self):
        r = self._crear(fecha_ecografia=(HOY - datetime.timedelta(weeks=25)).isoformat())
        self.assertEqual(r.status_code, 400)

    def test_paciente_distinta_de_la_del_embarazo_se_rechaza(self):
        """ESPERADO: 400. Antes se guardaba y mezclaba dos historias clínicas."""
        r = self._crear(paciente=self.b.pk)
        self.assertEqual(r.status_code, 400)
