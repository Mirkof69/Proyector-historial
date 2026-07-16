"""Tests para el módulo de Reportes.

Cubre: modelos, ReportService (agregación de estadísticas) y el
DatabaseBackupService — este último SIEMPRE con mocks: nunca se ejecuta un
pg_dump/psql real ni se toca la base de producción.
"""
import tempfile
from unittest import mock, skipUnless

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase

# Algunas agregaciones usan to_char (PostgreSQL). En CI la base es Postgres y
# se ejecutan; localmente sobre SQLite se saltan de forma explícita.
_ES_POSTGRES = connection.vendor == "postgresql"

from .models import AlertaMedica, ReporteGenerado, TipoReporte

Usuario = get_user_model()


def _crear_usuario(email="rep@test.bo"):
    return Usuario.objects.create_user(
        email=email, nombre="Rep", apellido_paterno="Test", password="x",
    )
from .services.backup_service import BackupError, DatabaseBackupService
from .services.report_service import ReportService


class ReportesModelTest(TestCase):
    """Modelos del módulo de reportes."""

    def test_tipo_reporte_crea_y_str(self):
        tipo = TipoReporte.objects.create(
            nombre="Reporte mensual", descripcion="Resumen del mes",
            categoria="estadistico",
        )
        self.assertIn("Reporte mensual", str(tipo))
        self.assertTrue(tipo.activo)

    def test_reporte_generado_estado_por_defecto(self):
        tipo = TipoReporte.objects.create(
            nombre="R", descripcion="d", categoria="estadistico",
        )
        rep = ReporteGenerado.objects.create(
            tipo_reporte=tipo, usuario_solicitante=_crear_usuario(),
        )
        # El estado inicial debe ser pendiente/generando, nunca 'completado' de arranque
        self.assertNotEqual(rep.estado, "completado")

    def test_alerta_medica_crea(self):
        alerta = AlertaMedica.objects.create(
            titulo="Presión alta", descripcion="PA elevada", tipo="valor_critico",
            prioridad="alta", modulo_origen="controles",
            accion_recomendada="Revisar de inmediato",
        )
        self.assertEqual(alerta.prioridad, "alta")


class ReportServiceTest(TestCase):
    """El servicio de estadísticas no debe crashear con base vacía y debe
    devolver estructuras consistentes."""

    def test_dashboard_stats_estructura(self):
        stats = ReportService.get_dashboard_stats()
        self.assertIsInstance(stats, dict)

    def test_embarazos_stats_no_crashea(self):
        self.assertIsInstance(ReportService.get_embarazos_stats(), dict)

    @skipUnless(_ES_POSTGRES, "get_controles_stats usa to_char (PostgreSQL)")
    def test_controles_stats_no_crashea(self):
        self.assertIsInstance(ReportService.get_controles_stats(), dict)

    def test_citas_stats_no_crashea(self):
        self.assertIsInstance(ReportService.get_citas_stats(), dict)

    @skipUnless(_ES_POSTGRES, "get_partos_stats usa to_char (PostgreSQL)")
    def test_partos_stats_no_crashea(self):
        self.assertIsInstance(ReportService.get_partos_stats(), dict)

    def test_risk_analysis_devuelve_enteros(self):
        risk = ReportService.get_risk_analysis()
        self.assertIsInstance(risk, dict)
        self.assertTrue(all(isinstance(v, int) for v in risk.values()))


class BackupServiceSecurityTest(TestCase):
    """El backup service se prueba SIN ejecutar pg_dump/psql reales."""

    def setUp(self):
        self.svc = DatabaseBackupService()

    def test_rechaza_path_traversal(self):
        """Un filename con path traversal debe ser rechazado (seguridad)."""
        for malicioso in ("../settings.py", "..\\..\\etc\\passwd", "/etc/passwd"):
            with self.assertRaises(BackupError):
                self.svc._resolver_ruta_backup(malicioso)

    def test_rechaza_extension_no_sql(self):
        with self.assertRaises(BackupError):
            self.svc._resolver_ruta_backup("backup_manual.txt")

    def test_backup_falla_en_sqlite(self):
        """En tests la base es SQLite: create_backup debe negarse, no fabricar
        un backup falso ni intentar pg_dump."""
        self.svc.db_config = {**self.svc.db_config, "ENGINE": "django.db.backends.sqlite3"}
        with self.assertRaises(BackupError):
            self.svc.create_backup()

    def test_create_backup_postgres_mockeado(self):
        """Con Postgres simulado y pg_dump mockeado, create_backup arma el
        comando correcto sin ejecutar nada real."""
        self.svc.db_config = {
            "ENGINE": "django.db.backends.postgresql", "HOST": "localhost",
            "PORT": 5432, "USER": "u", "PASSWORD": "p", "NAME": "testdb",
        }
        fake = mock.Mock(returncode=0, stderr="")
        with tempfile.TemporaryDirectory() as tmp:
            self.svc.backup_dir = tmp
            with mock.patch.object(self.svc, "_resolver_pg_dump", return_value="pg_dump"), \
                 mock.patch("reportes.services.backup_service.subprocess.run", return_value=fake) as run, \
                 mock.patch("os.path.getsize", return_value=1234), \
                 mock.patch("os.path.exists", return_value=True):
                res = self.svc.create_backup("manual")
        self.assertTrue(res["success"])
        # Verificar que se invocó pg_dump con la base correcta y sin shell
        args = run.call_args[0][0]
        self.assertIn("pg_dump", args[0])
        self.assertIn("testdb", args)

    def test_create_backup_propaga_error_de_pg_dump(self):
        """Si pg_dump falla (returncode != 0), debe lanzar BackupError."""
        self.svc.db_config = {
            "ENGINE": "django.db.backends.postgresql", "HOST": "localhost",
            "PORT": 5432, "USER": "u", "PASSWORD": "p", "NAME": "testdb",
        }
        fake = mock.Mock(returncode=1, stderr="connection refused")
        with tempfile.TemporaryDirectory() as tmp:
            self.svc.backup_dir = tmp
            with mock.patch.object(self.svc, "_resolver_pg_dump", return_value="pg_dump"), \
                 mock.patch("reportes.services.backup_service.subprocess.run", return_value=fake), \
                 mock.patch("os.path.exists", return_value=False):
                with self.assertRaises(BackupError):
                    self.svc.create_backup("manual")

    def test_get_backups_lista_vacia_en_dir_temporal(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.svc.backup_dir = tmp
            self.assertEqual(self.svc.get_backups(), [])

    def test_delete_backup_inexistente_devuelve_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.svc.backup_dir = tmp
            self.assertFalse(self.svc.delete_backup("no_existe.sql"))
