"""Backup service module.

Antes esta clase escribia un archivo .sql con un solo comentario ("Dummy
backup created at ...") y lo llamaba backup. Ahora invoca pg_dump real
contra la base configurada en settings.DATABASES["default"].
"""
import logging
import os
import shutil
import subprocess
from datetime import datetime

logger = logging.getLogger("reportes")


class BackupError(Exception):
    """Error real al crear un backup (pg_dump ausente, falla de conexion, etc.)"""


class DatabaseBackupService:
    """Servicio para gestión de backups de base de datos (pg_dump real)."""

    def __init__(self):
        """Init"""
        from django.conf import settings as django_settings
        self.backup_dir = os.path.join(django_settings.BASE_DIR, "backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
        self.db_config = django_settings.DATABASES["default"]

    def _resolver_binario(self, nombre: str) -> str:
        """Ubica un binario de PostgreSQL (pg_dump o psql). Lanza BackupError
        con un mensaje claro si no esta disponible, en vez de fabricar un
        resultado falso."""
        ruta = shutil.which(nombre)
        if ruta:
            return ruta
        # Windows: el binario no siempre queda en PATH aunque este instalado.
        for version in ("18", "17", "16"):
            candidate = rf"C:\Program Files\PostgreSQL\{version}\bin\{nombre}.exe"
            if os.path.exists(candidate):
                return candidate
        raise BackupError(
            f"{nombre} no esta instalado o no se encuentra en PATH. "
            "En el contenedor de produccion, agregar el paquete "
            "'postgresql-client' a Backend/Dockerfile.backend.",
        )

    def _resolver_pg_dump(self) -> str:
        """Ubica el binario pg_dump."""
        return self._resolver_binario("pg_dump")

    def create_backup(self, backup_type="manual"):
        """Crea un backup real de la base de datos con pg_dump."""
        if self.db_config["ENGINE"].endswith("sqlite3"):
            raise BackupError(
                "El backup con pg_dump requiere PostgreSQL. La base activa "
                "es SQLite (modo de desarrollo/test, USE_SQLITE=true).",
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{backup_type}_{timestamp}.sql"
        filepath = os.path.join(self.backup_dir, filename)

        try:
            pg_dump_path = self._resolver_pg_dump()

            comando = [
                pg_dump_path,
                "-h", self.db_config["HOST"],
                "-p", str(self.db_config["PORT"]),
                "-U", self.db_config["USER"],
                "-F", "p",  # texto plano: descargable/legible directamente
                "--no-owner",
                "--no-privileges",
                "-f", filepath,
                self.db_config["NAME"],
            ]

            entorno = os.environ.copy()
            entorno["PGPASSWORD"] = self.db_config["PASSWORD"]

            resultado = subprocess.run(
                comando,
                env=entorno,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            if resultado.returncode != 0:
                # No incluir 'entorno' (tiene PGPASSWORD) en el error.
                stderr = resultado.stderr.strip()[:500]
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise BackupError(f"pg_dump fallo (codigo {resultado.returncode}): {stderr}")

            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                raise BackupError("pg_dump no genero un archivo de backup valido")

            logger.info(
                "Backup real creado: %s (%s bytes)",
                filename, os.path.getsize(filepath),
            )
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "message": "Backup creado correctamente",
            }
        except subprocess.TimeoutExpired as e:
            raise BackupError("pg_dump excedio el tiempo limite (300s)") from e
        except BackupError:
            raise
        except Exception as e:
            raise BackupError(f"Error inesperado creando backup: {e}") from e

    def _resolver_ruta_backup(self, filename: str) -> str:
        """Resuelve la ruta de un archivo de backup, rechazando intentos de
        path traversal (filename viene directo de la URL)."""
        nombre_seguro = os.path.basename(filename)
        if nombre_seguro != filename or not nombre_seguro.endswith(".sql"):
            raise BackupError("Nombre de archivo de backup invalido")
        filepath = os.path.join(self.backup_dir, nombre_seguro)
        if not os.path.exists(filepath):
            raise BackupError(f"El backup '{nombre_seguro}' no existe")
        return filepath

    def restore_backup(self, filename: str):
        """Restaura la base de datos completa desde un backup real con psql.

        Antes de restaurar crea automaticamente un backup de seguridad de la
        base ACTUAL (pre-restore), para poder revertir si el restore fue un
        error. El dump original se genero en formato texto plano (-F p), por
        lo que se restaura con `psql`, no con `pg_restore` (ese es solo para
        el formato custom -F c).
        """
        if self.db_config["ENGINE"].endswith("sqlite3"):
            raise BackupError(
                "El restore con psql requiere PostgreSQL. La base activa "
                "es SQLite (modo de desarrollo/test, USE_SQLITE=true).",
            )

        filepath = self._resolver_ruta_backup(filename)

        # Backup de seguridad de la base ACTUAL antes de sobrescribirla.
        backup_seguridad = self.create_backup("pre_restore")

        try:
            psql_path = self._resolver_binario("psql")

            comando = [
                psql_path,
                "-h", self.db_config["HOST"],
                "-p", str(self.db_config["PORT"]),
                "-U", self.db_config["USER"],
                "-v", "ON_ERROR_STOP=1",
                "-f", filepath,
                self.db_config["NAME"],
            ]

            entorno = os.environ.copy()
            entorno["PGPASSWORD"] = self.db_config["PASSWORD"]

            resultado = subprocess.run(
                comando,
                env=entorno,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            if resultado.returncode != 0:
                stderr = resultado.stderr.strip()[:500]
                raise BackupError(
                    f"psql fallo restaurando (codigo {resultado.returncode}): {stderr}. "
                    f"Se creo un backup de seguridad antes del intento: {backup_seguridad['filename']}.",
                )

            logger.warning(
                "Base de datos restaurada desde %s (backup de seguridad pre-restore: %s)",
                filename, backup_seguridad["filename"],
            )
            return {
                "success": True,
                "filename": filename,
                "backup_seguridad": backup_seguridad["filename"],
                "message": "Base de datos restaurada correctamente",
            }
        except subprocess.TimeoutExpired as e:
            raise BackupError("psql excedio el tiempo limite (300s) restaurando") from e
        except BackupError:
            raise
        except Exception as e:
            raise BackupError(f"Error inesperado restaurando backup: {e}") from e

    def get_backups(self):
        """Lista los backups reales en disco"""
        backups = []
        if os.path.exists(self.backup_dir):
            for f in os.listdir(self.backup_dir):
                if f.endswith(".sql"):
                    filepath = os.path.join(self.backup_dir, f)
                    stat = os.stat(filepath)
                    backups.append(
                        {
                            "filename": f,
                            "size": stat.st_size,
                            "created_at": datetime.fromtimestamp(
                                stat.st_ctime,
                            ).isoformat(),
                        },
                    )
        return sorted(backups, key=lambda b: b["created_at"], reverse=True)

    def download_backup(self, filename):
        """Descarga backup"""
        nombre_seguro = os.path.basename(filename)
        filepath = os.path.join(self.backup_dir, nombre_seguro)
        if os.path.exists(filepath):
            from django.http import FileResponse

            return FileResponse(
                open(filepath, "rb"), as_attachment=True, filename=nombre_seguro,
            )
        return None

    def delete_backup(self, filename):
        """Elimina backup"""
        nombre_seguro = os.path.basename(filename)
        filepath = os.path.join(self.backup_dir, nombre_seguro)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
