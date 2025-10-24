from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ControlPrenatalViewSet

router = DefaultRouter()
router.register(r'controles', ControlPrenatalViewSet, basename='control')

urlpatterns = [
    path('', include(router.urls)),
]