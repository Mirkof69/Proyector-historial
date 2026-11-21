"""El respaldo diario puede dejar una copia en otra carpeta (otro disco o red).

Un respaldo guardado solo en el mismo disco que la base se pierde junto con ella.
"""
import os
import tempfile
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class CopiaDelRespaldoTest(SimpleTestCase):
    def setUp(self):
        self.origen = tempfile.TemporaryDirectory()
        self.copia = tempfile.TemporaryDirectory()
        self.archivo = os.path.join(self.origen.name, "backup_programado_20261121_020000.sql")
        with open(self.archivo, "w", encoding="utf-8") as f:
            f.write("-- PostgreSQL database dump\n")

    def tearDown(self):
        self.origen.cleanup()
        self.copia.cleanup()

    def _servicio(self):
        servicio = mock.MagicMock()
        servicio.backup_dir = self.origen.name
        servicio.create_backup.return_value = {"filepath": self.archivo, "filename": os.path.basename(self.archivo)}
        return servicio

    def test_copia_el_respaldo_a_la_otra_carpeta(self):
        with mock.patch("reportes.management.commands.respaldar_base.DatabaseBackupService",
                        return_value=self._servicio()):
            call_command("respaldar_base", "--copiar-a", self.copia.name, stdout=StringIO())
        copiado = os.path.join(self.copia.name, os.path.basename(self.archivo))
        self.assertTrue(os.path.exists(copiado))
        self.assertEqual(os.path.getsize(copiado), os.path.getsize(self.archivo))

    def test_sin_carpeta_de_copia_solo_respalda(self):
        with mock.patch("reportes.management.commands.respaldar_base.DatabaseBackupService",
                        return_value=self._servicio()), mock.patch.dict(os.environ, {"RESPALDO_COPIA_DIR": ""}):
            call_command("respaldar_base", "--copiar-a", "", stdout=StringIO())
        self.assertEqual(os.listdir(self.copia.name), [])

    def test_si_la_copia_falla_avisa_con_error(self):
        with mock.patch("reportes.management.commands.respaldar_base.DatabaseBackupService",
                        return_value=self._servicio()), \
                mock.patch("reportes.management.commands.respaldar_base.shutil.copy2", side_effect=OSError("sin disco")):
            with self.assertRaises(CommandError):
                call_command("respaldar_base", "--copiar-a", self.copia.name, stdout=StringIO())
        self.assertTrue(os.path.exists(self.archivo), "el respaldo principal no debe perderse")
