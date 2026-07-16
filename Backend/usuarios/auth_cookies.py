"""=============================================================================
AUTENTICACIÓN JWT VÍA COOKIES httpOnly + PROTECCIÓN CSRF
=============================================================================
Migración de seguridad: los JWT dejan de viajar/almacenarse en localStorage
(vulnerable a XSS) y pasan a cookies httpOnly emitidas por el servidor.

- ``set_jwt_cookies`` / ``clear_jwt_cookies``: helpers para las vistas.
- ``CookieJWTAuthentication``: igual que JWTAuthentication (header Bearer,
  usado por Kong y clientes API externos) pero con fallback a la cookie
  ``access_token``. Cuando autentica por cookie, aplica el chequeo CSRF de
  Django (double-submit: cookie ``csrftoken`` + header ``X-CSRFToken``).

NOTA: este módulo se referencia desde ``DEFAULT_AUTHENTICATION_CLASSES`` en
settings, por lo que NO debe importar vistas de DRF (import circular). Las
vistas cookie-based viven en ``usuarios/auth_cookie_views.py``.
=============================================================================
"""

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

# Nombres de cookies (el frontend NO las lee: son httpOnly)
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
COOKIE_PATH = "/"


def _cookie_kwargs() -> dict:
    """Atributos comunes de las cookies JWT (httpOnly SIEMPRE)."""
    return {
        "httponly": True,
        "secure": bool(getattr(settings, "SESSION_COOKIE_SECURE", False)),
        "samesite": "Lax",
        "path": COOKIE_PATH,
    }


def set_jwt_cookies(response, access=None, refresh=None):
    """Adjunta los JWT como cookies httpOnly a la respuesta."""
    if access is not None:
        response.set_cookie(
            ACCESS_COOKIE,
            str(access),
            max_age=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
            **_cookie_kwargs(),
        )
    if refresh is not None:
        response.set_cookie(
            REFRESH_COOKIE,
            str(refresh),
            max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
            **_cookie_kwargs(),
        )
    return response


def clear_jwt_cookies(response):
    """Elimina las cookies JWT (logout)."""
    response.delete_cookie(ACCESS_COOKIE, path=COOKIE_PATH)
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    return response


def enforce_csrf(request) -> None:
    """Aplica el chequeo CSRF estándar de Django a una request DRF.

    Solo se invoca cuando la autenticación se hizo vía cookie (un cliente
    con header Authorization explícito no es vulnerable a CSRF).
    """

    def _dummy_get_response(_request):  # pragma: no cover - nunca se llama
        return None

    check = CSRFCheck(_dummy_get_response)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")


class CookieJWTAuthentication(JWTAuthentication):
    """JWT por header Bearer (Kong / API externa) con fallback a cookie.

    - Header ``Authorization: Bearer`` presente → comportamiento estándar.
    - Sin header → intenta la cookie httpOnly ``access_token`` y, si valida,
      exige CSRF (double-submit cookie) para métodos no-safe.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get(ACCESS_COOKIE)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        if header is None:
            # Autenticación por cookie → proteger contra CSRF
            enforce_csrf(request)

        return self.get_user(validated_token), validated_token
