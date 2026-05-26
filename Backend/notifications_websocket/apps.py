"""Apps module."""
from django.apps import AppConfig


class NotificationsWebsocketConfig(AppConfig):
    """Notificationswebsocketconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications_websocket"
    verbose_name = "WebSocket Notifications"
