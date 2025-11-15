"""URLs para módulo de Partos"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartoViewSet, RecienNacidoViewSet, ComplicacionPartoViewSet

router = DefaultRouter()
router.register(r'', PartoViewSet, basename='partos')
router.register(r'recien-nacidos', RecienNacidoViewSet, basename='recien-nacidos')
router.register(r'complicaciones', ComplicacionPartoViewSet, basename='complicaciones')

urlpatterns = [
    path('', include(router.urls)),
]
