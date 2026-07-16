"""=============================================================================
WEBSOCKET CONSUMERS
=============================================================================
WebSocket consumers for real-time notifications and dashboard updates
in the Fetal Medical System.
=============================================================================
"""

import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from notificaciones.models import Notificacion
from notificaciones.services import NotificacionService

logger = logging.getLogger(__name__)

User = get_user_model()


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================


async def send_notification_to_user(
    user_id: int, notification_data: dict[str, Any],
) -> bool:
    """Send a real-time notification to a specific user via their WebSocket group.

    This function can be called from anywhere in the codebase (sync or async)
    to push a notification to a connected client.

    Args:
        user_id: ID of the user to notify
        notification_data: Dictionary containing notification payload

    Returns:
        True if the notification was sent, False otherwise

    Example:
        await send_notification_to_user(user_id, {
            'type': 'cita_confirmada',
            'title': 'Cita Confirmada',
            'message': 'Su cita ha sido confirmada',
            'priority': 'alta',
        })

    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.error(
            "Channel layer is not configured. Cannot send WebSocket notification.",
        )
        return False

    group_name = f"user_{user_id}_notifications"

    try:
        await channel_layer.group_send(
            group_name,
            {
                "type": "notification_message",
                "data": notification_data,
            },
        )
        return True
    except Exception as e:
        logger.error("Failed to send notification to user %s: %s", user_id, e)
        return False


async def broadcast_to_group(group_name: str, data: dict[str, Any]) -> bool:
    """Broadcast a message to all members of a WebSocket group.

    Useful for dashboard-wide announcements, system alerts, etc.

    Args:
        group_name: Name of the group to broadcast to
        data: Dictionary containing the broadcast payload

    Returns:
        True if the broadcast was sent, False otherwise

    Example:
        await broadcast_to_group('dashboard', {
            'type': 'system_alert',
            'message': 'System maintenance in 30 minutes',
        })

    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.error("Channel layer is not configured. Cannot broadcast to group.")
        return False

    try:
        await channel_layer.group_send(
            group_name,
            {
                "type": "broadcast_message",
                "data": data,
            },
        )
        return True
    except Exception as e:
        logger.error("Failed to broadcast to group '%s': %s", group_name, e)
        return False


# =====================================================================
# NOTIFICATION CONSUMER
# =====================================================================


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for personal user notifications.

    Handles:
        pass
    - Real-time notification delivery on connect (pending/unread)
    - Client-initiated actions (mark as read, mark all as read, etc.)
    - Cleanup on disconnect

    Connection URL:
        ws://host/ws/notifications/token=<jwt_token>

    Client Messages:
    - {"action": "mark_as_read", "notification_id": 123}
    - {"action": "mark_all_read"}
    - {"action": "archive", "notification_id": 123}
    - {"action": "get_pending"}
    - {"action": "ping"}
    """

    def __init__(self, *args, **kwargs):
        """Init"""
        super().__init__(*args, **kwargs)
        self.user = None
        self.group_name = None

    async def connect(self):
        """Authenticate user and establish WebSocket connection."""
        self.user = self.scope.get("user")

        # Reject unauthenticated connections
        if not self.user or self.user.is_anonymous:
            logger.warning("WebSocket connection rejected: user not authenticated")
            await self.close(code=4001)
            return

        # Build group name and join
        self.group_name = f"user_{self.user.id}_notifications"

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

        logger.info(
            "WebSocket connected for user %s (%s)",
            self.user.id,
            self.user.nombre_completo if hasattr(self.user, 'nombre_completo') else self.user.email,
        )

        # Send a welcome/connected message
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to notification stream",
                    "user_id": self.user.id,
                },
            ),
        )

        # Auto-send pending/unread notifications on connect
        await self._send_pending_notifications()

    async def disconnect(self, code: int):
        """Clean up WebSocket group membership on disconnect."""
        if self.group_name:
            try:
                await self.channel_layer.group_discard(
                    self.group_name, self.channel_name,
                )
            except Exception as e:
                logger.error("Error discarding group %s: %s", self.group_name, str(e))

        logger.info(
            "WebSocket disconnected for user %s, code: %s",
            self.user.id if self.user else "unknown",
            code,
        )

    async def receive(self, text_data: str | None = "", bytes_data: bytes | None = b""):
        """Handle incoming messages from the client."""
        assert self.user is not None
        assert text_data is not None
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                    },
                ),
            )
            return

        action = data.get("action", "").strip()

        # Route to appropriate handler
        handlers = {
            "mark_as_read": self._handle_mark_as_read,
            "mark_all_read": self._handle_mark_all_read,
            "archive": self._handle_archive,
            "get_pending": self._handle_get_pending,
            "ping": self._handle_ping,
        }

        handler = handlers.get(action)
        if handler:
            await handler(data)
        else:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": f"Unknown action: {action}",
                    },
                ),
            )
            logger.warning("Unknown action '%s' from user %s", action, self.user.id)

    # ---------------------------------------------------------------
    # Notification broadcast from group (server -> client)
    # ---------------------------------------------------------------

    async def notification_message(self, event: dict[str, Any]):
        """Send a notification to the client.

        This is called when send_notification_to_user() is invoked
        from elsewhere in the codebase.
        """
        data = event.get("data", {})
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "data": data,
                },
            ),
        )

    # ---------------------------------------------------------------
    # Client action handlers
    # ---------------------------------------------------------------

    async def _handle_mark_as_read(self, data: dict[str, Any]):
        """Mark a single notification as read."""
        notification_id = data.get("notification_id")
        if not notification_id:
            await self._send_error("notification_id is required")
            return

        success = await self._db_mark_as_read(notification_id)

        if success:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "success",
                        "action": "mark_as_read",
                        "notification_id": notification_id,
                    },
                ),
            )
        else:
            await self._send_error("Failed to mark notification as read")

    async def _handle_mark_all_read(self, _data: dict[str, Any]):
        """Mark all notifications as read for the current user."""
        count = await self._db_mark_all_read()

        await self.send(
            text_data=json.dumps(
                {
                    "type": "success",
                    "action": "mark_all_read",
                    "count": count,
                },
            ),
        )

    async def _handle_archive(self, data: dict[str, Any]):
        """Archive a notification."""
        notification_id = data.get("notification_id")
        if not notification_id:
            await self._send_error("notification_id is required")
            return

        success = await self._db_archive(notification_id)

        if success:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "success",
                        "action": "archive",
                        "notification_id": notification_id,
                    },
                ),
            )
        else:
            await self._send_error("Failed to archive notification")

    async def _handle_get_pending(self, _data: dict[str, Any]):
        """Return pending/unread notifications."""
        notifications = await self._db_get_pending()

        await self.send(
            text_data=json.dumps(
                {
                    "type": "pending_notifications",
                    "data": notifications,
                },
            ),
        )

    async def _handle_ping(self, _data: dict[str, Any]):
        """Simple heartbeat ping/pong."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "pong",
                    "timestamp": __import__("time").time(),
                },
            ),
        )

    # ---------------------------------------------------------------
    # Database operations (sync -> async)
    # ---------------------------------------------------------------

    async def _send_pending_notifications(self):
        """Fetch and send all unread notifications on connect."""
        notifications = await self._db_get_pending()

        if notifications:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "pending_notifications",
                        "data": notifications,
                    },
                ),
            )

    async def _send_error(self, message: str):
        """Send an error message to the client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                },
            ),
        )

    @database_sync_to_async
    def _db_mark_as_read(self, notification_id: int) -> bool:
        """Mark a notification as read in the database."""
        assert self.user is not None
        try:
            notification = Notificacion.objects.get(
                id=notification_id, usuario=self.user,
            )
            notification.marcar_como_leida()
            return True
        except Notificacion.DoesNotExist:
            logger.warning(
                "Notification %s not found for user %s",
                notification_id,
                self.user.id,
            )
            return False
        except Exception as e:
            logger.error(
                "Error marking notification %s as read: %s",
                notification_id,
                e,
            )
            return False

    @database_sync_to_async
    def _db_mark_all_read(self) -> int:
        """Mark all notifications as read for the user."""
        assert self.user is not None
        try:
            return NotificacionService.marcar_todas_leidas(self.user.id)
        except Exception as e:
            logger.error(
                "Error marking all notifications as read for user %s: %s",
                self.user.id,
                e,
            )
            return 0

    @database_sync_to_async
    def _db_archive(self, notification_id: int) -> bool:
        """Archive a notification."""
        assert self.user is not None
        try:
            notification = Notificacion.objects.get(
                id=notification_id, usuario=self.user,
            )
            notification.archivar()
            return True
        except Notificacion.DoesNotExist:
            logger.warning(
                "Notification %s not found for user %s",
                notification_id,
                self.user.id,
            )
            return False
        except Exception as e:
            logger.error("Error archiving notification %s: %s", notification_id, e)
            return False

    @database_sync_to_async
    def _db_get_pending(self) -> list:
        """Get unread notifications for the user."""
        assert self.user is not None
        try:
            notifications = NotificacionService.obtener_no_leidas(
                self.user.id, limite=50,
            )
            return [
                {
                    "id": getattr(n, 'id', None),
                    "tipo": n.tipo,
                    "titulo": n.titulo,
                    "mensaje": n.mensaje,
                    "prioridad": n.prioridad,
                    "icono": n.icono,
                    "color": n.color,
                    "url": n.url,
                    "url_texto": n.url_texto,
                    "fecha_creacion": n.fecha_creacion.isoformat(),
                    "tiempo": n.get_tiempo_transcurrido(),
                    "metadata": getattr(n, 'metadata', {}),
                }
                for n in notifications
            ]
        except Exception as e:
            logger.error(
                "Error fetching pending notifications for user %s: %s",
                self.user.id,
                e,
            )
            return []


# =====================================================================
# DASHBOARD CONSUMER
# =====================================================================


class DashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time dashboard updates.

    Broadcasts system-wide or role-specific events such as:
        pass
    - New patient admissions
    - Critical lab results
    - Appointment changes
    - System alerts

    Connection URL:
        ws://host/ws/dashboard/token=<jwt_token>

    The consumer auto-joins a group based on the user's role
    (e.g., 'dashboard_medicos', 'dashboard_admin').
    """

    def __init__(self, *args, **kwargs):
        """Init"""
        super().__init__(*args, **kwargs)
        self.user = None
        self.group_name = None

    async def connect(self):
        """Authenticate user and join the appropriate dashboard group."""
        self.user = self.scope.get("user")

        if not self.user or self.user.is_anonymous:
            logger.warning(
                "Dashboard WebSocket connection rejected: user not authenticated",
            )
            await self.close(code=4001)
            return

        # Determine group based on user role
        role_group = await self._get_user_role_group()
        self.group_name = role_group

        # Join role-based group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Also join the global dashboard group
        await self.channel_layer.group_add("dashboard_global", self.channel_name)

        await self.accept()

        logger.info(
            "Dashboard WebSocket connected for user %s, joined group: %s",
            self.user.id,
            self.group_name,
        )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to dashboard stream",
                    "groups": [self.group_name, "dashboard_global"],
                },
            ),
        )

    async def disconnect(self, code: int):
        """Clean up group memberships."""
        groups_to_leave = []
        if self.group_name:
            groups_to_leave.append(self.group_name)
        groups_to_leave.append("dashboard_global")

        for group in groups_to_leave:
            try:
                await self.channel_layer.group_discard(group, self.channel_name)
            except Exception as e:
                logger.error("Error discarding group %s: %s", group, str(e))

        logger.info(
            "Dashboard WebSocket disconnected for user %s",
            self.user.id if self.user else 'unknown',
        )

    async def receive(self, text_data: str | None = "", bytes_data: bytes | None = b""):
        """Handle client messages (mostly pings for dashboard)."""
        assert text_data is not None
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format")
            return

        action = data.get("action", "").strip()

        if action == "ping":
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "pong",
                        "timestamp": __import__("time").time(),
                    },
                ),
            )
        else:
            await self._send_error(f"Unknown action: {action}")

    async def broadcast_message(self, event: dict[str, Any]):
        """Handle broadcasted messages from the server."""
        data = event.get("data", {})
        await self.send(
            text_data=json.dumps(
                {
                    "type": "dashboard_update",
                    "data": data,
                },
            ),
        )

    @database_sync_to_async
    def _get_user_role_group(self) -> str:
        """Determine the dashboard group based on user role.

        Returns:
            Group name string (e.g., 'dashboard_medicos', 'dashboard_admin')

        """
        assert self.user is not None
        try:
            if hasattr(self.user, "rol"):
                rol = self.user.rol
                if rol:
                    rol_name = str(rol).lower() if hasattr(rol, "__str__") else ""
                    if "admin" in rol_name or "administrador" in rol_name:
                        return "dashboard_admin"
                    if "medico" in rol_name or "doctor" in rol_name:
                        return "dashboard_medicos"
                    if "enfermer" in rol_name:
                        return "dashboard_enfermeria"
                    if "laboratorio" in rol_name:
                        return "dashboard_laboratorio"
                    return f"dashboard_{rol_name}"

            # Default group
            return "dashboard_general"

        except Exception as e:
            logger.error("Error determining user role group: %s", e)
            return "dashboard_general"

    async def _send_error(self, message: str):
        """Send an error message to the client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                },
            ),
        )
