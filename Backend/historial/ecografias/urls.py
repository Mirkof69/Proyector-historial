from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EcografiaViewSet

router = DefaultRouter()
router.register(r'ecografias', EcografiaViewSet, basename='ecografia')

urlpatterns = [
    path('', include(router.urls)),
]