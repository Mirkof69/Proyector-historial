"""Evoluciones URLs"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EvolucionEmbarazoViewSet

router = DefaultRouter()
router.register(r"evoluciones", EvolucionEmbarazoViewSet)
urlpatterns = [path("", include(router.urls))]
