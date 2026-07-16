"""Apps module."""
from django.apps import AppConfig


class ControlesConfig(AppConfig):
    """Controlesconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "controles"

    def ready(self):
        """Conecta las señales del módulo (alertas de control al médico)."""
        from controles import signals as _signals
        _ = _signals
