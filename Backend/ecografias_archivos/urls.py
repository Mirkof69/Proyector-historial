"""Ecografias Archivos URLs"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EcografiaArchivoViewSet

router = DefaultRouter()
router.register(r"archivos", EcografiaArchivoViewSet)
urlpatterns = [path("", include(router.urls))]
