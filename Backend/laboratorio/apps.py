"""Apps module."""
from django.apps import AppConfig


class LaboratorioConfig(AppConfig):
    """Laboratorioconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "laboratorio"

    def ready(self):
        """Conecta las señales del módulo (notificar examen/resultado al médico)."""
        from laboratorio import signals as _signals
        _ = _signals
