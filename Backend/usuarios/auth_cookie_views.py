"""Vistas del flujo de autenticación por cookies httpOnly.

Separadas de ``usuarios/auth_cookies.py`` porque aquel módulo se carga desde
``DEFAULT_AUTHENTICATION_CLASSES`` y no puede importar vistas de DRF
(import circular durante la inicialización de rest_framework).
"""

from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from .auth_cookies import REFRESH_COOKIE, set_jwt_cookies


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    """TokenRefreshSerializer que acepta el refresh desde la cookie."""

    refresh = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context.get("request")
        raw = attrs.get("refresh") or (
            request.COOKIES.get(REFRESH_COOKIE) if request is not None else None
        )
        if not raw:
            raise InvalidToken(
                "No se encontró refresh token (ni en cookie ni en el body).",
            )
        attrs["refresh"] = raw
        return super().validate(attrs)


class CookieTokenRefreshView(TokenRefreshView):
    """Refresh vía cookie httpOnly.

    Los nuevos tokens se emiten SOLO como cookies; el body no expone JWT.
    """

    serializer_class = CookieTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data.get("access")
            new_refresh = response.data.get("refresh")  # rotación activada
            set_jwt_cookies(response, access=access, refresh=new_refresh)
            response.data = {"success": True}
        return response


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_bootstrap_view(request):
    """Garantiza la cookie ``csrftoken`` (legible por JS a propósito).

    El frontend la reenvía como header ``X-CSRFToken`` en métodos no-safe.
    """
    get_token(request)
    return Response({"detail": "CSRF cookie set"})
