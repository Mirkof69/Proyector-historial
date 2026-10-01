"""Apps module."""
from django.apps import AppConfig


class IaMedicaConfig(AppConfig):
    """Iamedicaconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "ia_medica"

    def ready(self):
        from . import signals  # noqa: F401  (cierre de predicciones de peso)
