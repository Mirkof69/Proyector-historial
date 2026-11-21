"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .estadisticas_views import ClasificacionRiesgosViewSet
from .views import EmbarazoViewSet

# Crear router para registrar el ViewSet
router = DefaultRouter()
router.register(
    r"clasificacion-riesgos",
    ClasificacionRiesgosViewSet,
    basename="clasificacion-riesgos",
)
# El ViewSet de prefijo vacio va AL FINAL: su ruta de detalle
# ^(?P<pk>[^/.]+)/$ se comia los prefijos registrados despues
# (p. ej. /recien-nacidos/ se leia como pk='recien-nacidos' -> 404/405).
router.register(r"", EmbarazoViewSet, basename="embarazo")

urlpatterns = [
    path("", include(router.urls)),
]
