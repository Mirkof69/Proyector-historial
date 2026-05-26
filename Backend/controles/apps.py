"""Apps module."""
from django.apps import AppConfig


class ControlesConfig(AppConfig):
    """Controlesconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "controles"

    def ready(self):
        """Ready"""
