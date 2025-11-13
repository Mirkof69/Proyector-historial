from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ControlPrenatalViewSet

# Crear router para registrar el ViewSet
router = DefaultRouter()
router.register(r'', ControlPrenatalViewSet, basename='controlprenatal')

urlpatterns = [
    path('', include(router.urls)),
]