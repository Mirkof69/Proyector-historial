"""Apps module."""
from django.apps import AppConfig


class CalculadorasConfig(AppConfig):
    """Calculadorasconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "calculadoras"
    verbose_name = "Calculadoras Médicas"

    def ready(self):
        """Ready"""
        # Importar signals si los hay
        # Importar DopplerMaterno para registro
        try:
            from . import models_doppler as _models_doppler_register
            _ = _models_doppler_register
        except ImportError:
            pass
