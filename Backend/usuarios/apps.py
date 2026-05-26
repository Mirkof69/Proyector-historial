"""Apps module."""
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Usuariosconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"
