"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CitaViewSet, DisponibilidadViewSet

router = DefaultRouter()
router.register(r"disponibilidades", DisponibilidadViewSet, basename="disponibilidad")
router.register(r"citas", CitaViewSet, basename="cita")

urlpatterns = [
    path("", include(router.urls)),
]
