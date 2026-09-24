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


class AnalisisNoCruzaPacientesTest(TestCase):
    """Con ids coincidentes, el análisis de una imagen IA de la paciente A se
    escribía en las imágenes de la ecografía (clínica) de la paciente B."""

    def test_el_analisis_no_se_escribe_en_la_ecografia_de_otra_paciente(self):
        from unittest.mock import MagicMock, patch

        from ecografias.models import Ecografia, ImagenEcografia

        medico = Usuario.objects.create_user(email="med.cruce@test.bo", nombre="M", apellido_paterno="C",
                                             password="clave-segura-123", rol="medico")
        a, b = _paciente("7944001"), _paciente("7944002")
        emb_b = Embarazo.objects.create(paciente=b, numero_gesta=1,
                                        fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=24))
        eco_b = Ecografia.objects.create(paciente=b, embarazo=emb_b, fecha_ecografia=datetime.date.today(),
                                         edad_gestacional_semanas=24)
        img_b = ImagenEcografia.objects.create(
            ecografia=eco_b, imagen=SimpleUploadedFile("b.png", b"\x89PNG\r\n\x1a\n0000"), titulo="B")
        img_ia_a = ImagenEcografica.objects.create(
            paciente=a, subida_por=medico, nombre_original="a.png",
            imagen=SimpleUploadedFile("a.png", b"\x89PNG\r\n\x1a\n0000"))
        # Forzar la coincidencia de ids que producía el cruce
        ImagenEcografica.objects.filter(pk=img_ia_a.pk).update(pk=eco_b.pk) if img_ia_a.pk != eco_b.pk else None

        respuesta = MagicMock(status_code=200)
        respuesta.json.return_value = {"status": "success", "pathology_detection": {"pathologies": []},
                                       "biometry": {}, "score_global": 0.1}
        c = APIClient()
        c.force_authenticate(medico)
        with patch("ecografias.ai_views.requests.post", return_value=respuesta):
            c.post("/api/ecografias/analyze-with-ai/", {"ecografia_id": eco_b.pk})
        img_b.refresh_from_db()
        self.assertFalse(img_b.analisis_ia, "el análisis de A acabó en la ecografía de B")
