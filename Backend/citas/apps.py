"""Apps module."""
from django.apps import AppConfig


class CitasConfig(AppConfig):
    """Citasconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "citas"

    def ready(self):
        """Ready"""
