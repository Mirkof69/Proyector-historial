"""Evoluciones App Configuration"""

from django.apps import AppConfig


class EvolucionesConfig(AppConfig):
    """Evolucionesconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "evoluciones"
    verbose_name = "Evoluciones de Embarazo"

    def ready(self):
        """Import signals when app is ready"""
        # Add signals import here when created
