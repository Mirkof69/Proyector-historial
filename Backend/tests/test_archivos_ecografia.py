"""Adjuntos de una ecografía (imagen, DICOM, PDF, video).

Antes era imposible crear uno: el modelo aceptaba «imagen/video/dicom/pd» y
el serializer exigía «DICOM/JPG/PNG/PDF/VIDEO» en mayúsculas. La pantalla
pedía /ecografias/<id>/archivos/ (404). Ahora el tipo sale del contenido.
"""
import datetime
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from ecografias.models import Ecografia
from ecografias_archivos.models import EcografiaArchivo
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/ecografias-archivos/archivos/"


def _png():
    buf = BytesIO()
    Image.new("L", (8, 8)).save(buf, "PNG")
    return SimpleUploadedFile("corte.png", buf.getvalue(), content_type="image/png")


@override_settings()
class ArchivosEcografiaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="arch.med@test.bo", nombre="Ana", apellido_paterno="Arch",
                                                 password="clave-segura-123", rol="medico")
        cls.recepcion = Usuario.objects.create_user(email="arch.rec@test.bo", nombre="Rita", apellido_paterno="Rec",
                                                    password="clave-segura-123", rol="recepcion")
        p = Paciente.objects.create(nombre="Ari", apellido_paterno="Chivo", apellido_materno="X",
                                    fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci="7899901")
        e = Embarazo.objects.create(paciente=p, fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=22),
                                    numero_gesta=1, numero_para=0, numero_abortos=0)
        cls.eco = Ecografia.objects.create(embarazo=e, paciente=p, medico=cls.medico, fecha_ecografia=datetime.date.today(),
                                           tipo_ecografia="segundo_trimestre", indicacion="control_rutina",
                                           edad_gestacional_semanas=22, edad_gestacional_dias=0)

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def test_subir_un_png_deduce_el_tipo_y_guarda_quien_lo_subio(self):
        r = self.c.post(URL, {"ecografia": self.eco.id, "archivo": _png(), "descripcion": "corte axial"}, format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        a = EcografiaArchivo.objects.get()
        self.assertEqual(a.tipo_archivo, "imagen")
        self.assertEqual(a.subido_por, self.medico)
        self.assertGreater(a.tamano_bytes, 0)
        self.assertEqual(a.nombre_archivo, "corte.png")

    def test_listar_los_de_una_ecografia(self):
        self.c.post(URL, {"ecografia": self.eco.id, "archivo": _png()}, format="multipart")
        r = self.c.get(URL, {"ecografia": self.eco.id})
        self.assertEqual(r.status_code, 200)
        fila = r.json()["results"][0]
        self.assertEqual(fila["tipo_archivo"], "imagen")
        self.assertTrue(fila["subido_por_nombre"])

    def test_un_html_disfrazado_de_pdf_se_rechaza(self):
        falso = SimpleUploadedFile("informe.pdf", b"<html><script>alert(1)</script></html>", content_type="application/pdf")
        r = self.c.post(URL, {"ecografia": self.eco.id, "archivo": falso}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_recepcion_no_ve_adjuntos_clinicos(self):
        c = APIClient()
        c.force_authenticate(self.recepcion)
        self.assertEqual(c.get(URL).status_code, 403)
