"""Apps module."""
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Usuariosconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"

    def ready(self):
        # Grupo de permisos según el rol (ver usuarios/permisos_por_rol.py)
        from . import signals  # noqa: F401
