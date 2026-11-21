from typing import Any, cast

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path as django_path

from .consumers import DashboardConsumer, NotificationConsumer
from .middleware import JWTAuthMiddlewareStrict

path = cast(Any, django_path)

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/dashboard/", DashboardConsumer.as_asgi()),
]

application = ProtocolTypeRouter(
    {
        "http": URLRouter([]),
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStrict(URLRouter(websocket_urlpatterns)),
        ),
    },
)


def get_asgi_application():
    return application
