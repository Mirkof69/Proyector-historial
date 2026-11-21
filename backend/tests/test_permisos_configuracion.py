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


class RestaurarQuedaAuditadoTest(APITestCase):
    """Restaurar reemplaza toda la base: quién lo hizo y desde qué respaldo
    tiene que quedar en la auditoría, igual que al crear un respaldo."""

    def test_restaurar_registra_quien_y_desde_que_respaldo(self):
        from unittest import mock

        from auditoria.models import RegistroAuditoria

        admin = Usuario.objects.create_user(
            email="restaura@config.test", nombre="Prueba", apellido_paterno="Admin",
            password="Clave-de-prueba-123!", rol="administrador",
        )
        self.client.force_authenticate(admin)
        resultado = {"success": True, "filename": "backup_manual_x.sql",
                     "backup_seguridad": "backup_pre_restore_y.sql", "message": "ok"}
        with mock.patch("reportes.views_config.DatabaseBackupService") as servicio:
            servicio.return_value.restore_backup.return_value = resultado
            r = self.client.post("/api/reportes/configuracion/backups/backup_manual_x.sql/restore/")
        self.assertEqual(r.status_code, 200)
        registro = RegistroAuditoria.objects.filter(accion="BACKUP", detalle__startswith="Base restaurada").get()
        self.assertEqual(registro.usuario, admin)
        self.assertIn("backup_manual_x.sql", registro.detalle)
        self.assertIn("backup_pre_restore_y.sql", registro.detalle)
