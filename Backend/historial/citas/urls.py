from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DisponibilidadViewSet, CitaViewSet

router = DefaultRouter()
router.register(r'disponibilidades', DisponibilidadViewSet, basename='disponibilidad')
router.register(r'citas', CitaViewSet, basename='cita')

urlpatterns = [
    path('', include(router.urls)),
]