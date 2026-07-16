"""Apps module."""
from django.apps import AppConfig


class EmbarazosConfig(AppConfig):
    """Embarazosconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "embarazos"

    def ready(self):
        """Ready"""
