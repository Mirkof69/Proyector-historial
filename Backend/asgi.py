"""ASGI config for historial project.

Exposes the ASGI callable as a module-level variable named ``application``.

Integrates Django Channels for WebSocket support alongside standard
HTTP request handling.

For more information on this file, see:
    pass
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
https://channels.readthedocs.io/en/stable/deploying.html
"""

import os

import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# Initialize Django early so Channels can access settings
django.setup()

# Get the standard Django ASGI application for HTTP requests
django_asgi_app = get_asgi_application()

# Import Channels routing after Django is set up
from channels.routing import ProtocolTypeRouter

# Build the combined ASGI application
# The ws_application already contains ProtocolTypeRouter with both
# HTTP (placeholder) and WebSocket handlers. We merge with django_asgi_app
# so HTTP requests go to Django and WebSocket connections go to Channels.


def get_combined_application():
    """Combine Django's HTTP ASGI app with Channels WebSocket routing.

    Returns a ProtocolTypeRouter that routes:
        pass
    - 'http' -> Django's standard ASGI handler
    - 'websocket' -> Channels WebSocket consumers (with JWT auth)
    """
    from channels.routing import URLRouter
    from channels.security.websocket import AllowedHostsOriginValidator

    from notifications_websocket.middleware import JWTAuthMiddlewareStrict
    from notifications_websocket.routing import websocket_urlpatterns

    return ProtocolTypeRouter(
        {
            # Standard HTTP requests -> Django
            "http": django_asgi_app,
            # WebSocket connections -> Channels consumers
            "websocket": AllowedHostsOriginValidator(
                JWTAuthMiddlewareStrict(URLRouter(websocket_urlpatterns)),
            ),
        },
    )


application = get_combined_application()
