"""Apps module."""
from django.apps import AppConfig


class CitasConfig(AppConfig):
    """Citasconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "citas"

    def ready(self):
        """Conecta las señales del módulo (avisos de cita al médico)."""
        from citas import signals as _signals
        _ = _signals
