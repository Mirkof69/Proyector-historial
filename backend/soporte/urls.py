"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TicketSoporteViewSet

router = DefaultRouter()
router.register(r"tickets", TicketSoporteViewSet, basename="ticket-soporte")

urlpatterns = [
    path("", include(router.urls)),
]
