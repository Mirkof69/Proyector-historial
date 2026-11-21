"""La descarga de reportes no puede servir archivos fuera de su carpeta.

Fallo que previene: `descargar` abría cualquier `ruta_archivo`, y esa ruta la
podía escribir el cliente de dos formas (la acción `marcar_completado` y un
PATCH normal, que además dejaba poner `estado=completado`). Con la ruta del
`.env` se descargaban las claves del servidor. Se prueba con el administrador:
ni siquiera él puede saltarse la carpeta.
"""
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from reportes.models import ReporteGenerado, TipoReporte
from usuarios.models import Usuario

SECRETO = Path(settings.BASE_DIR) / "settings.py"   # un archivo real fuera de la carpeta de reportes


class DescargaDeReportesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_superuser(
            email="admin.rep@test.bo", nombre="Admin", apellido_paterno="Rep", password="clave-123-segura",
        )
        cls.tipo = TipoReporte.objects.create(nombre="R", descripcion="d", categoria="estadistico")

    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.admin)
        self.reporte = ReporteGenerado.objects.create(tipo_reporte=self.tipo, usuario_solicitante=self.admin)
        self.url = f"/api/reportes/reportes-generados/{self.reporte.pk}/"

    def test_marcar_completado_con_ruta_de_fuera_se_rechaza(self):
        """ESPERADO: 400, y el reporte no queda apuntando al archivo."""
        with override_settings(REPORTES_DIR=self.carpeta):
            r = self.cliente.post(self.url + "marcar_completado/", {"ruta_archivo": str(SECRETO)}, format="json")
        self.assertEqual(r.status_code, 400, r.content)
        self.reporte.refresh_from_db()
        self.assertNotEqual(self.reporte.ruta_archivo, str(SECRETO))

    def test_la_ruta_con_puntos_tampoco_sale_de_la_carpeta(self):
        with override_settings(REPORTES_DIR=self.carpeta):
            r = self.cliente.post(self.url + "marcar_completado/",
                                  {"ruta_archivo": str(self.carpeta / ".." / "fuera.txt")}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_un_patch_no_puede_cambiar_ruta_ni_estado(self):
        """ESPERADO: ruta y estado se ignoran; el reporte sigue pendiente."""
        self.cliente.patch(self.url, {"ruta_archivo": str(SECRETO), "estado": "completado"}, format="json")
        self.reporte.refresh_from_db()
        self.assertNotEqual(self.reporte.ruta_archivo, str(SECRETO))
        self.assertNotEqual(self.reporte.estado, "completado")

    def test_un_reporte_que_ya_apunta_fuera_no_se_descarga(self):
        """Aunque la base ya tenga una ruta mala (datos viejos), la descarga da 404."""
        ReporteGenerado.objects.filter(pk=self.reporte.pk).update(estado="completado", ruta_archivo=str(SECRETO))
        with override_settings(REPORTES_DIR=self.carpeta):
            r = self.cliente.get(self.url + "descargar/")
        self.assertEqual(r.status_code, 404)

    def test_un_archivo_dentro_de_la_carpeta_si_se_descarga(self):
        archivo = self.carpeta / "reporte.xlsx"
        archivo.write_bytes(b"contenido")
        with override_settings(REPORTES_DIR=self.carpeta):
            r = self.cliente.post(self.url + "marcar_completado/", {"ruta_archivo": str(archivo)}, format="json")
            self.assertEqual(r.status_code, 200, r.content)
            d = self.cliente.get(self.url + "descargar/")
        self.assertEqual(d.status_code, 200)
        self.assertEqual(b"".join(d.streaming_content), b"contenido")


class CallbackIaEliminadoTest(TestCase):
    """El antiguo POST /api/ecografias/<id>/ai-result/ era AllowAny: cualquiera
    en la red podía reescribir el análisis de IA de cualquier ecografía. Nadie
    lo llamaba y se eliminó. ESPERADO: sin sesión, no se acepta nada."""

    def test_sin_sesion_no_se_puede_escribir_un_analisis(self):
        r = APIClient().post("/api/ecografias/1/ai-result/",
                             {"status": "completed", "ai_analysis": {"x": 1}}, format="json")
        self.assertIn(r.status_code, (401, 403, 404, 405))
