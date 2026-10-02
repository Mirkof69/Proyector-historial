"""Apps module."""
from django.apps import AppConfig


class NotificationsWebsocketConfig(AppConfig):
    """Notificationswebsocketconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications_websocket"
    verbose_name = "WebSocket Notifications"

    def ready(self):
        from . import checks  # noqa: F401  registra la comprobación de Redis
