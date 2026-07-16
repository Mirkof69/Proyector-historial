"""Apps module."""
from django.apps import AppConfig


class PacientesConfig(AppConfig):
    """Pacientesconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "pacientes"

    def ready(self):
        """Conecta las señales del módulo (registro/riesgo de paciente)."""
        from pacientes import signals as _signals
        _ = _signals
