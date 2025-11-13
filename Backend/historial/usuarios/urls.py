from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet,
    login_view,
    logout_view,
    refresh_token_view
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = [
    # Autenticación
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', refresh_token_view, name='refresh-token'),
    
    # CRUD de usuarios
    path('', include(router.urls)),
]