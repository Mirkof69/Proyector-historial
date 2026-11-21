"""Respaldo programado de la base de datos (pg_dump) con retención.

Uso (lo lanza RESPALDO_DIARIO.bat desde el Programador de tareas):
    python manage.py respaldar_base --conservar 30

Crea el respaldo con el mismo servicio que la pantalla de Backup, borra los
respaldos programados con más de --conservar días y sale con código 1 si el
respaldo falla, para que el Programador de tareas lo marque como error.

Con --copiar-a (o la variable RESPALDO_COPIA_DIR del .env) deja además una copia
en otra carpeta, idealmente en otro disco o una unidad de red: un respaldo que
vive en el mismo disco que la base se pierde junto con ella.
"""
import os
import shutil
import time

from django.core.management.base import BaseCommand, CommandError

from reportes.services.backup_service import BackupError, DatabaseBackupService

PREFIJO = "backup_programado_"


class Command(BaseCommand):
    help = "Respalda la base de datos con pg_dump y borra respaldos antiguos"

    def add_arguments(self, parser):
        parser.add_argument("--conservar", type=int, default=30,
                            help="Días que se guardan los respaldos programados (por defecto 30)")
        parser.add_argument("--copiar-a", default=os.environ.get("RESPALDO_COPIA_DIR", ""),
                            help="Carpeta adicional (otro disco o red) donde se copia cada respaldo")

    def handle(self, *args, **opciones):
        servicio = DatabaseBackupService()
        try:
            resultado = servicio.create_backup("programado")
        except BackupError as e:
            raise CommandError(f"El respaldo falló: {e}") from e
        tam = os.path.getsize(resultado["filepath"]) / 1024 / 1024
        self.stdout.write(self.style.SUCCESS(f"Respaldo creado: {resultado['filepath']} ({tam:.1f} MB)"))

        limite = time.time() - opciones["conservar"] * 86400
        borrados = self._borrar_antiguos(servicio.backup_dir, limite)
        self.stdout.write(f"Respaldos antiguos borrados (> {opciones['conservar']} días): {borrados}")

        copia = opciones["copiar_a"].strip()
        if copia:
            try:
                os.makedirs(copia, exist_ok=True)
                destino = shutil.copy2(resultado["filepath"], copia)
                if os.path.getsize(destino) != os.path.getsize(resultado["filepath"]):
                    raise OSError("la copia no tiene el mismo tamaño que el respaldo")
            except OSError as e:
                raise CommandError(f"El respaldo se creó, pero no se pudo copiar a {copia}: {e}") from e
            self.stdout.write(self.style.SUCCESS(f"Copia en: {destino}"))
            self.stdout.write(f"Copias antiguas borradas: {self._borrar_antiguos(copia, limite)}")

    @staticmethod
    def _borrar_antiguos(carpeta: str, limite: float) -> int:
        borrados = 0
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if nombre.startswith(PREFIJO) and os.path.getmtime(ruta) < limite:
                os.remove(ruta)
                borrados += 1
        return borrados
