"""=============================================================================
MÓDULO: VACUNAS - URLS
=============================================================================
Configuración de rutas para el módulo de vacunas
=============================================================================
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RegistroVacunaViewSet, TipoVacunaViewSet

# Crear router
router = DefaultRouter()

# Registrar viewsets
router.register(r"tipos-vacunas", TipoVacunaViewSet, basename="tipo-vacuna")
router.register(r"registros", RegistroVacunaViewSet, basename="registro-vacuna")

# URLs
urlpatterns = [
    path("", include(router.urls)),
]
