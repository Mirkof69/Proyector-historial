"""Configuración del sistema: la abre el administrador por su ROL, no por is_staff.

Regresión (14/10/2026, hallado por e2e/tests/pantallas.spec.js): las vistas
de configuración usaban IsAdminUser de DRF, que mira `is_staff`. El
administrador del hospital (rol «administrador», sin is_staff) abría
Configuración y veía «Acceso Denegado» y el formulario vacío.
"""
from rest_framework.test import APITestCase

from usuarios.models import Usuario


class ConfiguracionPorRolTest(APITestCase):
    def _usuario(self, rol):
        u = Usuario.objects.create_user(
            email=f"{rol}@config.test", nombre="Prueba", apellido_paterno=rol.title(),
            password="Clave-de-prueba-123!", rol=rol,
        )
        Usuario.objects.filter(pk=u.pk).update(is_staff=False)
        u.refresh_from_db()
        return u

    def test_el_administrador_sin_is_staff_entra(self):
        """ESPERADO: 200 en la configuración general, horarios y respaldos."""
        self.client.force_authenticate(self._usuario("administrador"))
        for ruta in ("/api/reportes/configuracion/general/", "/api/reportes/configuracion/horarios/",
                     "/api/reportes/configuracion/backups/"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_un_medico_no_entra(self):
        """ESPERADO: 403 — la configuración del hospital es solo del administrador."""
        self.client.force_authenticate(self._usuario("medico"))
        self.assertEqual(self.client.get("/api/reportes/configuracion/backups/").status_code, 403)
