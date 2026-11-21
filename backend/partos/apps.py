"""Apps module."""
from django.apps import AppConfig


class PartosConfig(AppConfig):
    """Partosconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "partos"

    def ready(self):
        """Importar señales cuando la app esté lista"""
        from partos import signals as _signals_register
        _ = _signals_register
