"""/media/ solo con sesión, sin salir de MEDIA_ROOT y sin nombres de paciente.

Fallos que previene: las imágenes de ecografía se servían a cualquiera con la
URL (que llevaba el nombre de la paciente) y en producción no se servían.
"""
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from ia_medica.models import imagen_ecografica_upload_path
from usuarios.models import Usuario

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class MediaProtegidaTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (Path(MEDIA) / "ecografias").mkdir(exist_ok=True)
        (Path(MEDIA) / "ecografias" / "eco.png").write_bytes(b"\x89PNG\r\n\x1a\nxx")
        (Path(MEDIA).parent / "secreto_fuera.txt").write_text("no")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def _cliente(self, rol=None):
        c = APIClient()
        if rol:
            c.force_authenticate(Usuario.objects.create_user(
                email=f"{rol}.media@test.bo", nombre="X", apellido_paterno="Y",
                password="clave-segura-123", rol=rol))
        return c

    def test_sin_sesion_no_se_ve(self):
        """ESPERADO: 401/403. Antes: 200 para cualquiera."""
        r = self._cliente().get("/media/ecografias/eco.png")
        self.assertIn(r.status_code, (401, 403))

    def test_el_medico_la_ve(self):
        r = self._cliente("medico").get("/media/ecografias/eco.png")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/png")
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")

    def test_recepcion_no_ve_archivos_clinicos(self):
        r = self._cliente("recepcion").get("/media/ecografias/eco.png")
        self.assertEqual(r.status_code, 403)

    def test_no_se_sale_de_media(self):
        c = self._cliente("medico")
        r = c.get("/media/..%2Fsecreto_fuera.txt")
        self.assertEqual(r.status_code, 404)
        r = c.get("/media/ecografias/no_existe.png")
        self.assertEqual(r.status_code, 404)

    def test_la_ruta_de_subida_no_lleva_datos_de_la_paciente(self):
        ruta = imagen_ecografica_upload_path(SimpleNamespace(paciente_id=4321), "Maria_Perez.JPG")
        nombre = ruta.rsplit("/", 1)[-1]
        self.assertNotIn("4321", nombre)
        self.assertNotIn("Maria", nombre)
        self.assertRegex(nombre, r"^[0-9a-f]{32}\.jpg$")


class NombreArchivoTest(TestCase):
    def test_el_nombre_lo_decide_upload_to(self):
        """ESPERADO: ecografias/AAAA/MM/DD/<uuid>.png, sin datos de la paciente.

        Antes se renombraba en save(): si el archivo ya estaba escrito, la base
        apuntaba a un nombre que no existía en disco.
        """
        from core.nombres_archivo import ruta_archivo_ecografia, ruta_imagen_ecografia

        self.assertRegex(ruta_imagen_ecografia(None, "Maria_Perez.PNG"),
                         r"^ecografias/\d{4}/\d{2}/\d{2}/[0-9a-f]{32}\.png$")
        self.assertRegex(ruta_archivo_ecografia(None, "informe.pdf"),
                         r"^ecografias/archivos/\d{4}/\d{2}/\d{2}/[0-9a-f]{32}\.pdf$")
