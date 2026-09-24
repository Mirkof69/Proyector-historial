"""«Crear ecografía desde IA» no inventa embarazos ni cruza pacientes.

Fallos que previene:
- Sin embarazo activo se creaba uno con FUM = hoy - 280 días, G1P0: la edad
  gestacional y la fecha probable de parto de la paciente quedaban falsas.
- La ecografía se creaba con 12 semanas por defecto.
- No se comprobaba que la imagen fuera de esa paciente.
"""
import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from ia_medica.models import ImagenEcografica
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/ecografias/crear-desde-ia/"


def _paciente(ci):
    return Paciente.objects.create(nombre="Ana", apellido_paterno="Ia", apellido_materno="Eco",
                                   fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci=ci)


class CrearDesdeIaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.ia@test.bo", nombre="M", apellido_paterno="I",
                                                 password="clave-segura-123", rol="medico")
        cls.paciente = _paciente("7933001")
        cls.otra = _paciente("7933002")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def _imagen(self, paciente, semana=None):
        return ImagenEcografica.objects.create(
            paciente=paciente, subida_por=self.medico, semana_gestacional=semana,
            imagen=SimpleUploadedFile("eco.png", b"\x89PNG\r\n\x1a\n0000", content_type="image/png"),
            nombre_original="eco.png", fecha_captura=datetime.date.today())

    def test_sin_embarazo_activo_no_se_inventa_uno(self):
        """ESPERADO: 409 y ningún embarazo nuevo."""
        r = self.c.post(URL, {"imagen_ia_id": self._imagen(self.paciente).pk, "paciente_id": self.paciente.pk})
        self.assertEqual(r.status_code, 409, r.content[:200])
        self.assertFalse(Embarazo.objects.filter(paciente=self.paciente).exists())

    def test_una_imagen_de_otra_paciente_se_rechaza(self):
        Embarazo.objects.create(paciente=self.paciente, numero_gesta=1,
                                fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=20))
        r = self.c.post(URL, {"imagen_ia_id": self._imagen(self.otra).pk, "paciente_id": self.paciente.pk})
        self.assertEqual(r.status_code, 400, r.content[:200])

    def test_las_semanas_salen_de_la_fum_no_de_un_12_fijo(self):
        """FUM hace 20 semanas y 3 días -> la ecografía queda en 20+3."""
        from ecografias.models import Ecografia

        Embarazo.objects.create(paciente=self.paciente, numero_gesta=1,
                                fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(days=143))
        r = self.c.post(URL, {"imagen_ia_id": self._imagen(self.paciente).pk, "paciente_id": self.paciente.pk})
        self.assertIn(r.status_code, (200, 201), r.content[:300])
        eco = Ecografia.objects.get(paciente=self.paciente)
        self.assertEqual((eco.edad_gestacional_semanas, eco.edad_gestacional_dias), (20, 3))
