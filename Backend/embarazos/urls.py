"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .estadisticas_views import ClasificacionRiesgosViewSet
from .views import EmbarazoViewSet

# Crear router para registrar el ViewSet
router = DefaultRouter()
router.register(r"", EmbarazoViewSet, basename="embarazo")
router.register(
    r"clasificacion-riesgos",
    ClasificacionRiesgosViewSet,
    basename="clasificacion-riesgos",
)

urlpatterns = [
    path("", include(router.urls)),
]
