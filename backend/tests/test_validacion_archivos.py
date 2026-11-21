"""Los archivos subidos se validan por su contenido, no por su nombre.

Fallo que previene: se podía subir una página HTML con JavaScript llamada
«resultado.pdf» o «eco.png»; al abrirla desde /media/ se ejecutaba en el
navegador de quien la mirara.
"""
import datetime
import io

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from PIL import Image
from rest_framework.test import APIClient

from core.validacion_archivos import DOCUMENTOS, IMAGENES, detectar_formato, validar_archivo

HTML_MALICIOSO = b"<html><script>fetch('/api/usuarios/')</script></html>"


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("L", (8, 8)).save(buf, "PNG")
    return buf.getvalue()


class DetectarFormatoTest(SimpleTestCase):
    def test_reconoce_los_formatos_reales(self):
        self.assertEqual(detectar_formato(io.BytesIO(b"%PDF-1.7\n...")), "PDF")
        self.assertEqual(detectar_formato(io.BytesIO(_png())), "PNG")
        self.assertEqual(detectar_formato(io.BytesIO(b"\xff\xd8\xff\xe0" + b"0" * 20)), "JPG")
        self.assertEqual(detectar_formato(io.BytesIO(b"\x00" * 128 + b"DICM" + b"\x00" * 4)), "DICOM")

    def test_un_html_llamado_pdf_se_rechaza(self):
        falso = SimpleUploadedFile("resultado.pdf", HTML_MALICIOSO, content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validar_archivo(falso, permitidos=DOCUMENTOS)

    def test_un_pdf_de_verdad_pasa(self):
        bueno = SimpleUploadedFile("resultado.pdf", b"%PDF-1.4\n%...", content_type="application/pdf")
        self.assertEqual(validar_archivo(bueno, permitidos=DOCUMENTOS), "PDF")

    def test_el_tamano_maximo_se_respeta(self):
        grande = SimpleUploadedFile("x.pdf", b"%PDF-" + b"0" * (2 * 1024 * 1024))
        with self.assertRaises(ValidationError):
            validar_archivo(grande, permitidos=DOCUMENTOS, max_mb=1)

    def test_la_lectura_no_mueve_el_puntero(self):
        f = io.BytesIO(b"%PDF-1.4 resto")
        f.seek(3)
        detectar_formato(f)
        self.assertEqual(f.tell(), 3)


class SubirImagenEcografiaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        from ecografias.models import Ecografia
        from embarazos.models import Embarazo
        from pacientes.models import Paciente
        from usuarios.models import Usuario

        cls.medico = Usuario.objects.create_user(email="img.eco@test.bo", nombre="M", apellido_paterno="E",
                                                 password="clave-segura-123", rol="medico")
        p = Paciente.objects.create(nombre="Ana", apellido_paterno="Img", apellido_materno="T",
                                    fecha_nacimiento=datetime.date(1994, 4, 4), genero="femenino", ci="7922001")
        e = Embarazo.objects.create(paciente=p, numero_gesta=1,
                                    fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=22))
        cls.eco = Ecografia.objects.create(paciente=p, embarazo=e, fecha_ecografia=datetime.date.today(),
                                           edad_gestacional_semanas=22)

    def _subir(self, nombre, contenido, **extra):
        c = APIClient()
        c.force_authenticate(self.medico)
        return c.post(f"/api/ecografias/{self.eco.pk}/subir_imagen/",
                      {"imagen": SimpleUploadedFile(nombre, contenido), **extra}, format="multipart")

    def test_html_disfrazado_de_png_da_400(self):
        r = self._subir("eco.png", HTML_MALICIOSO)
        self.assertEqual(r.status_code, 400, r.content[:200])

    def test_orden_con_texto_da_400_no_500(self):
        r = self._subir("eco.png", _png(), orden="primero")
        self.assertEqual(r.status_code, 400, r.content[:200])

    def test_png_de_verdad_se_acepta(self):
        r = self._subir("eco.png", _png())
        self.assertIn(r.status_code, (200, 201), r.content[:300])


class FormatosPermitidosTest(SimpleTestCase):
    def test_las_imagenes_no_incluyen_pdf(self):
        self.assertNotIn("PDF", IMAGENES)
