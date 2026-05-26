"""Apps module."""
from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    """Auditoriaconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditoria"
    verbose_name = "Auditoría y Trazabilidad"

    def ready(self):
        """Importar signals cuando la app esté lista"""
