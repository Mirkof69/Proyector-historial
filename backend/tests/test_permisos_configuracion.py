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


class AlertasLasCambianMedicoYAdministradorTest(APITestCase):
    """Los umbrales de alertas son de todo el sistema: los lee cualquiera, los cambian médico y administrador.

    Regresión (21/11/2026): la vista exigía solo estar autenticado, y una recepcionista podía subir el umbral de
    presión arterial con un POST.
    """

    def _usuario(self, rol):
        return Usuario.objects.create_user(
            email=f"{rol}@alertas.test", nombre="Prueba", apellido_paterno=rol.title(),
            password="Clave-de-prueba-123!", rol=rol,
        )

    def test_todos_los_roles_la_leen_y_solo_medico_y_administrador_la_cambian(self):
        ruta = "/api/reportes/configuracion/alertas/"
        for rol in ("enfermera", "laboratorista", "recepcion"):
            with self.subTest(rol=rol):
                self.client.force_authenticate(self._usuario(rol))
                self.assertEqual(self.client.get(ruta).status_code, 200)
                self.assertEqual(self.client.post(ruta, {}, format="json").status_code, 403)
        for rol in ("medico", "administrador"):
            with self.subTest(rol=rol):
                self.client.force_authenticate(self._usuario(rol))
                self.assertEqual(self.client.post(ruta, {}, format="json").status_code, 200)


class CargarRespaldoTest(APITestCase):
    """Un respaldo descargado se puede volver a cargar desde otro equipo para restaurarlo."""

    def setUp(self):
        import tempfile

        from django.test import override_settings

        self.carpeta = tempfile.TemporaryDirectory()
        self.ajustes = override_settings(BASE_DIR=__import__("pathlib").Path(self.carpeta.name))
        self.ajustes.enable()
        self.admin = Usuario.objects.create_user(
            email="carga@config.test", nombre="Prueba", apellido_paterno="Admin",
            password="Clave-de-prueba-123!", rol="administrador",
        )

    def tearDown(self):
        self.ajustes.disable()
        self.carpeta.cleanup()

    @staticmethod
    def _archivo(nombre, contenido):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(nombre, contenido, content_type="application/sql")

    def test_carga_un_pg_dump_y_queda_en_la_lista(self):
        import os

        self.client.force_authenticate(self.admin)
        dump = b"--\n-- PostgreSQL database dump\n--\nSET statement_timeout = 0;\n"
        r = self.client.post("/api/reportes/configuracion/backups/cargar/",
                             {"archivo": self._archivo("copia del hospital.sql", dump)}, format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        nombre = r.json()["filename"]
        self.assertTrue(nombre.startswith("backup_cargado_") and nombre.endswith("_copia_del_hospital.sql"))
        self.assertTrue(os.path.exists(os.path.join(self.carpeta.name, "backups", nombre)))
        lista = self.client.get("/api/reportes/configuracion/backups/").json()
        self.assertIn(nombre, [b["filename"] for b in lista])

    def test_rechaza_lo_que_no_es_un_respaldo(self):
        self.client.force_authenticate(self.admin)
        for nombre, contenido in (("respaldo.txt", b"-- PostgreSQL database dump"),
                                  ("respaldo.sql", b"DROP TABLE pacientes;"),
                                  ("vacio.sql", b"")):
            with self.subTest(nombre=nombre):
                r = self.client.post("/api/reportes/configuracion/backups/cargar/",
                                     {"archivo": self._archivo(nombre, contenido)}, format="multipart")
                self.assertEqual(r.status_code, 400, r.content)

    def test_solo_el_administrador_carga(self):
        medico = Usuario.objects.create_user(
            email="medico-carga@config.test", nombre="Prueba", apellido_paterno="Medico",
            password="Clave-de-prueba-123!", rol="medico",
        )
        self.client.force_authenticate(medico)
        r = self.client.post("/api/reportes/configuracion/backups/cargar/",
                             {"archivo": self._archivo("r.sql", b"-- PostgreSQL database dump")}, format="multipart")
        self.assertEqual(r.status_code, 403)
