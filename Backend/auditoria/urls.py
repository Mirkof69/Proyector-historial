"""=============================================================================
URLS: API DE AUDITORÍA
=============================================================================
Configuración de rutas para la API de auditoría.
=============================================================================
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RegistroAuditoriaViewSet

# Router para el ViewSet
router = DefaultRouter()
router.register(r"", RegistroAuditoriaViewSet, basename="auditoria")

urlpatterns = [
    path("", include(router.urls)),
]
