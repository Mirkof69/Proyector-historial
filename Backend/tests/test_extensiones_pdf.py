"""Las extensiones .pdf, .tiff y .gif se reconocen.

Fallo que previene: estaban truncadas a .pd, .ti y .gi. Un PDF de laboratorio
nunca se reconocía como PDF (y no se verificaba su firma digital), y las
estadísticas se descargaban como «estadisticas.pd» con tipo application/pd.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from laboratorio.models import ImagenLaboratorio
from usuarios.models import Usuario


class ExtensionesTest(TestCase):
    def test_un_pdf_de_laboratorio_es_pdf(self):
        self.assertTrue(ImagenLaboratorio(archivo="laboratorio/informe.PDF").es_pdf())
        self.assertTrue(ImagenLaboratorio(archivo="laboratorio/placa.tiff").es_imagen())
        self.assertTrue(ImagenLaboratorio(archivo="laboratorio/anim.gif").es_imagen())

    def test_las_estadisticas_se_descargan_como_pdf(self):
        admin = Usuario.objects.create_user(email="adm.pdf@test.bo", nombre="A", apellido_paterno="P",
                                            password="clave-segura-123", rol="administrador")
        c = APIClient()
        c.force_authenticate(admin)
        r = c.get("/api/reportes/statistics/download-pdf/")
        self.assertEqual(r.status_code, 200, r.content[:200])
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertRegex(r["Content-Disposition"], r'\.pdf"$')
        self.assertTrue(b"".join(r.streaming_content if r.streaming else [r.content]).startswith(b"%PDF"))
