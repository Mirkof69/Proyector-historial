"""Apps module."""
from django.apps import AppConfig


class LaboratorioConfig(AppConfig):
    """Laboratorioconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "laboratorio"

    def ready(self):
        """Ready"""
