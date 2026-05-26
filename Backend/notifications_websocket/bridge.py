"""=============================================================================
WEBSOCKET NOTIFICATION BRIDGE
=============================================================================
Bridges the synchronous NotificacionService with the async
WebSocket layer, allowing notifications created anywhere in
the codebase to be pushed to connected clients in real time.

Usage:
    from notifications_websocket.bridge import broadcast_notification

    # After creating a notification in sync code:
        pass
    notification = Notificacion.objects.create(...)
    broadcast_notification(notification)
=============================================================================
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def broadcast_notification(notification) -> bool:
    """Broadcast a notification model instance to the user's WebSocket channel.

    This is a synchronous wrapper that schedules the async broadcast
    via Django's channel layer. It works correctly whether called
    from a sync or async context.

    Args:
        notification: A Notificacion model instance

    Returns:
        True if the broadcast was scheduled, False otherwise

    """
    try:

        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning(
                "Channel layer not configured. Skipping WebSocket broadcast.",
            )
            return False

        group_name = f"user_{notification.usuario_id}_notifications"

        notification_data = {
            "id": notification.id,
            "tipo": notification.tipo,
            "titulo": notification.titulo,
            "mensaje": notification.mensaje,
            "prioridad": notification.prioridad,
            "icono": notification.icono,
            "color": notification.color,
            "url": notification.url,
            "url_texto": notification.url_texto,
            "fecha_creacion": notification.fecha_creacion.isoformat(),
            "tiempo": notification.get_tiempo_transcurrido(),
            "metadata": notification.metadata,
        }

        # Use async_to_sync to bridge sync -> async
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification_message",
                "data": notification_data,
            },
        )

        logger.debug(
            "Broadcast notification %s to group '%s' for user %s",
            notification.id,
            group_name,
            notification.usuario_id,
        )
        return True

    except Exception as e:
        # Log but don't break the main notification flow
        logger.error(
            "Failed to broadcast notification %s via WebSocket: %s",
            notification.id,
            e,
        )
        return False


def broadcast_dashboard_event(group_name: str, event_data: dict) -> bool:
    """Broadcast an arbitrary event to a dashboard group.

    Args:
        group_name: Dashboard group name (e.g., 'dashboard_medicos', 'dashboard_global')
        event_data: Dictionary containing the event payload

    Returns:
        True if broadcast was scheduled, False otherwise

    Example:
        broadcast_dashboard_event('dashboard_global', {
            'event_type': 'new_patient_admission',
            'patient_name': 'Maria Lopez',
            'doctor': 'Dr. Garcia',
        })

    """
    try:

        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning(
                "Channel layer not configured. Skipping dashboard broadcast.",
            )
            return False

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "broadcast_message",
                "data": event_data,
            },
        )

        logger.debug("Broadcast dashboard event to group '%s'", group_name)
        return True

    except Exception as e:
        logger.error("Failed to broadcast dashboard event to '%s': %s", group_name, e)
        return False
