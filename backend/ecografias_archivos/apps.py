"""Ecografias Archivos App Configuration"""

from django.apps import AppConfig


class EcografiasArchivosConfig(AppConfig):
    """Ecografiasarchivosconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "ecografias_archivos"
    verbose_name = "Archivos de Ecografías"

    def ready(self):
        """Import signals when app is ready"""
        # Add signals import here when created
