"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    HorarioAtencionViewSet,
    UsuarioViewSet,
    current_user_view,
    login_view,
    logout_view,
    mfa_verify_view,
    refresh_token_view,
)

router = DefaultRouter()
router.register(r"horarios", HorarioAtencionViewSet, basename="horario")
# El ViewSet de prefijo vacio va AL FINAL: su ruta de detalle
# ^(?P<pk>[^/.]+)/$ se comia los prefijos registrados despues
# (p. ej. /recien-nacidos/ se leia como pk='recien-nacidos' -> 404/405).
router.register(r"", UsuarioViewSet, basename="usuario")

urlpatterns = [
    # Autenticación paso 1 (email + password)
    path("login/", login_view, name="login"),
    # Autenticación paso 2 (TOTP MFA con temp_token)
    path("mfa-verify/", mfa_verify_view, name="mfa-verify"),
    path("logout/", logout_view, name="logout"),
    path("refresh/", refresh_token_view, name="refresh-token"),
    # Usuario actual
    path("me/", current_user_view, name="current-user"),
    # CRUD de usuarios
    path("", include(router.urls)),
]

# Flujo MFA de 2 pasos:
#   Paso 1: POST /api/usuarios/login/        → si mfa_required=true → retorna temp_token
#   Paso 2: POST /api/usuarios/mfa-verify/   → temp_token + totp_code → retorna JWT completo
# Setup MFA:  POST /api/usuarios/mfa/setup/   (action en UsuarioViewSet)
#             POST /api/usuarios/mfa/confirm/ (action en UsuarioViewSet)
