"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PacienteViewSet

# Crear router para registrar el ViewSet
router = DefaultRouter()
router.register(r"", PacienteViewSet, basename="paciente")

urlpatterns = [
    path("", include(router.urls)),
]
