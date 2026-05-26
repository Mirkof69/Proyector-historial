"""TRIAJE - URLS"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TriajeEnfermeriaViewSet

router = DefaultRouter()
router.register(r"triajes", TriajeEnfermeriaViewSet, basename="triaje")

urlpatterns = [path("", include(router.urls))]
