# =============================================================================
# URLS DE EMBARAZOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: embarazos
# Descripción: Configuración de rutas para API REST de embarazos
# Versión: 3.0.0 COMPLETO
# Última actualización: 2025-11-14
# =============================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmbarazoViewSet, ComplicacionEmbarazoViewSet

# Router para ViewSets
router = DefaultRouter()
router.register(r'embarazos', EmbarazoViewSet, basename='embarazo')
router.register(r'complicaciones', ComplicacionEmbarazoViewSet, basename='complicacion')

# URLs de la aplicación
urlpatterns = [
    path('', include(router.urls)),
]

# =============================================================================
# FIN DEL ARCHIVO - embarazos/urls.py
# =============================================================================
