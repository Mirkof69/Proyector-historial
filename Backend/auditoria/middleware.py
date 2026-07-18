"""=============================================================================
MIDDLEWARE: CAPTURA DE USUARIO PARA AUDITORÍA
=============================================================================
Guarda el request en thread-local para que los signals de auditoría puedan
resolver el usuario EN EL MOMENTO en que se dispara la señal.

Por qué el request y no el usuario (bug encontrado en pruebas de carga):
con autenticación DRF por JWT/cookie, quien autentica es la vista (las
authentication_classes de DRF), NO el AuthenticationMiddleware de Django.
Cuando este middleware corría, `request.user` todavía era AnonymousUser, así
que la auditoría guardaba usuario vacío en TODOS los registros: quedaba el
"qué" y el "cuándo", pero se perdía el "quién".

Guardando el request y leyendo `request.user` de forma diferida (dentro del
signal, ya dentro de la vista) el usuario sí está resuelto: DRF propaga el
usuario autenticado al HttpRequest subyacente.
=============================================================================
"""

from .signals import set_current_request, verificar_tabla_auditoria_existe


class AuditoriaMiddleware:
    """Middleware que expone el request actual para la auditoría.
    Debe estar en MIDDLEWARE en settings.py, después de AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        """Init"""
        self.get_response = get_response

    def __call__(self, request):
        """Call"""
        set_current_request(request)
        # "Warm-up" de la detección de la tabla de auditoría en un momento
        # LIMPIO (fuera de cualquier signal). Si la primera comprobación cae
        # dentro de un pre_save —es decir, dentro de la transacción de un
        # save— falla, y entonces debe_auditar_modelo() devuelve False en cada
        # save posterior: la auditoría de pacientes, embarazos, controles y
        # partos se apagaba EN SILENCIO. Aquí se resuelve una vez por proceso
        # y el resultado positivo queda memorizado.
        try:
            verificar_tabla_auditoria_existe()
        except Exception:  # nunca romper un request por la auditoría
            pass
        try:
            return self.get_response(request)
        finally:
            # Siempre limpiar: los hilos se reutilizan entre requests
            set_current_request(None)
