"""Ejecuta el escalamiento de alertas críticas sin leer.

Útil para correrlo por cron si no se usa Celery beat, o para probarlo a mano:

    python manage.py escalar_criticas
"""
from django.core.management.base import BaseCommand

from notificaciones.services import escalar_notificaciones_criticas


class Command(BaseCommand):
    help = "Escala las notificaciones críticas sin leer según los umbrales de settings."

    def handle(self, *args, **options):
        escaladas = escalar_notificaciones_criticas()
        self.stdout.write(
            self.style.SUCCESS(f"Escalamiento completado: {escaladas} alerta(s) escaladas."),
        )
