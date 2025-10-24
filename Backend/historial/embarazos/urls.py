from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmbarazoViewSet

router = DefaultRouter()
router.register(r'embarazos', EmbarazoViewSet, basename='embarazo')

urlpatterns = [
    path('', include(router.urls)),
]