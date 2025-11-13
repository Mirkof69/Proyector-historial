from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmbarazoViewSet

# Crear router para registrar el ViewSet
router = DefaultRouter()
router.register(r'', EmbarazoViewSet, basename='embarazo')

urlpatterns = [
    path('', include(router.urls)),
]