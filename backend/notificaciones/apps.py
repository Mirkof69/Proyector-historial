"""Apps module."""
from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    """Notificacionesconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "notificaciones"
    verbose_name = "Notificaciones"
