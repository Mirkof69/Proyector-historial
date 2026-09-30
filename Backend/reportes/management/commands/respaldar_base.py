"""Respaldo programado de la base de datos (pg_dump) con retención.

Uso (lo lanza RESPALDO_DIARIO.bat desde el Programador de tareas):
    python manage.py respaldar_base --conservar 30

Crea el respaldo con el mismo servicio que la pantalla de Backup, borra los
respaldos programados con más de --conservar días y sale con código 1 si el
respaldo falla, para que el Programador de tareas lo marque como error.
"""
import os
import time

from django.core.management.base import BaseCommand, CommandError

from reportes.services.backup_service import BackupError, DatabaseBackupService

PREFIJO = "backup_programado_"


class Command(BaseCommand):
    help = "Respalda la base de datos con pg_dump y borra respaldos antiguos"

    def add_arguments(self, parser):
        parser.add_argument("--conservar", type=int, default=30,
                            help="Días que se guardan los respaldos programados (por defecto 30)")

    def handle(self, *args, **opciones):
        servicio = DatabaseBackupService()
        try:
            resultado = servicio.create_backup("programado")
        except BackupError as e:
            raise CommandError(f"El respaldo falló: {e}") from e
        tam = os.path.getsize(resultado["filepath"]) / 1024 / 1024
        self.stdout.write(self.style.SUCCESS(f"Respaldo creado: {resultado['filepath']} ({tam:.1f} MB)"))

        limite = time.time() - opciones["conservar"] * 86400
        borrados = 0
        for nombre in os.listdir(servicio.backup_dir):
            ruta = os.path.join(servicio.backup_dir, nombre)
            if nombre.startswith(PREFIJO) and os.path.getmtime(ruta) < limite:
                os.remove(ruta)
                borrados += 1
        self.stdout.write(f"Respaldos antiguos borrados (> {opciones['conservar']} días): {borrados}")
