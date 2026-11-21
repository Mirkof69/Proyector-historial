"""Apps module."""
from django.apps import AppConfig


class RolesConfig(AppConfig):
    """Cargos del hospital sobre los roles del sistema."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "roles"
    verbose_name = "Cargos"

    def ready(self):
        from . import signals  # noqa: F401
