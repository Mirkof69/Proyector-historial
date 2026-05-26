"""=============================================================================
MIDDLEWARE: CAPTURA DE USUARIO PARA AUDITORÍA
=============================================================================
Middleware que captura el usuario actual de cada request y lo almacena
en thread-local storage para que los signals puedan acceder a él.
=============================================================================
"""

from .signals import set_current_user


class AuditoriaMiddleware:
    """Middleware que captura el usuario actual y lo almacena para auditoría.
    Debe ser agregado a MIDDLEWARE en settings.py
    """

    def __init__(self, get_response):
        """Init"""
        self.get_response = get_response

    def __call__(self, request):
        """Call"""
        # Establecer el usuario actual en thread-local storage
        if hasattr(request, "user") and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)

        response = self.get_response(request)

        # Limpiar el usuario después del request
        set_current_user(None)

        return response
