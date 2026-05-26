"""Backup service module."""
import os
from datetime import datetime


class DatabaseBackupService:
    """Servicio para gestión de backups de base de datos.
    Implementación Mock/Stub para asegurar arranque del sistema.
    """

    def __init__(self):
        """Init"""
        from django.conf import settings as django_settings
        self.backup_dir = os.path.join(django_settings.BASE_DIR, "backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, backup_type="manual"):
        """Crea un backup dummy"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{backup_type}_{timestamp}.sql"
        filepath = os.path.join(self.backup_dir, filename)

        # Crear archivo dummy
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"-- Dummy backup created at {timestamp}")

        return {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "message": "Backup creado correctament (Mock)",
        }

    def get_backups(self):
        """Lista backups dummy"""
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
        return backups

    def download_backup(self, filename):
        """Descarga backup"""
        filepath = os.path.join(self.backup_dir, filename)
        if os.path.exists(filepath):
            from django.http import FileResponse

            return FileResponse(
                open(filepath, "rb"), as_attachment=True, filename=filename,
            )
        return None

    def delete_backup(self, filename):
        """Elimina backup"""
        filepath = os.path.join(self.backup_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
