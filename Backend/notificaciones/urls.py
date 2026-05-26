"""=============================================================================
MÓDULO: NOTIFICACIONES - URLS
=============================================================================
Configuración de rutas para notificaciones
=============================================================================
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ConfiguracionNotificacionesViewSet,
    HistorialNotificacionesViewSet,
    NotificacionViewSet,
)

# Router para ViewSets
router = DefaultRouter()
router.register(r"notificaciones", NotificacionViewSet, basename="notificacion")
router.register(
    r"configuracion-notificaciones",
    ConfiguracionNotificacionesViewSet,
    basename="configuracion-notificaciones",
)
router.register(
    r"historial-notificaciones",
    HistorialNotificacionesViewSet,
    basename="historial-notificaciones",
)

urlpatterns = [
    path("", include(router.urls)),
]
