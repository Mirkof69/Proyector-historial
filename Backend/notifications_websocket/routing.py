"""=============================================================================
WEBSOCKET ROUTING
=============================================================================
Defines WebSocket URL patterns and the ASGI application router
for the Fetal Medical System.
=============================================================================
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

from .consumers import DashboardConsumer, NotificationConsumer
from .middleware import JWTAuthMiddlewareStrict

# =====================================================================
# WebSocket URL Patterns
# =====================================================================

websocket_urlpatterns = [
    # Personal notifications: ws://host/ws/notifications/token=<jwt>
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    # Dashboard updates: ws://host/ws/dashboard/token=<jwt>
    path("ws/dashboard/", DashboardConsumer.as_asgi()),
]

# =====================================================================
# ASGI Application
# =====================================================================

application = ProtocolTypeRouter(
    {
        # HTTP requests handled by Django's standard ASGI handler
        "http": URLRouter([]),  # HTTP is handled by Django; this is just a placeholder
        # WebSocket connections
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStrict(URLRouter(websocket_urlpatterns)),
        ),
    },
)


def get_asgi_application():
    """Returns the ASGI application for use in settings.ASGI_APPLICATION.

    This function is referenced by the Django settings file to wire
    up Channels as the ASGI handler.
    """
    return application
