"""CONSULTORIOS - URLS"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConsultorioViewSet

router = DefaultRouter()
router.register(r"consultorios", ConsultorioViewSet, basename="consultorio")

urlpatterns = [path("", include(router.urls))]
