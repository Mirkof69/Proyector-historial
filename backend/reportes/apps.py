"""Apps module."""
from django.apps import AppConfig


class ReportesConfig(AppConfig):
    """Reportesconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "reportes"

    def ready(self):
        # Alertas médicas desde controles y laboratorio (reportes/signals.py).
        from . import signals  # noqa: F401
