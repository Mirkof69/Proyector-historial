"""La clínica (esquema de django-tenants) de una conexión WebSocket.

En HTTP la elige `clientes.middleware.FallbackTenantMiddleware` por el host.
Los WebSockets no pasan por ese middleware: el consumidor consultaba las
notificaciones en el esquema `public`, donde la tabla no existe («no existe la
relación notificaciones», visto el 01/10/2026). Las notificaciones pendientes
nunca llegaban en tiempo real.

Aquí se replica la misma regla: el dominio del host decide la clínica; en
desarrollo un host desconocido usa la clínica principal, en producción se rechaza.
Sin django-tenants (la suite de pruebas) no hay esquemas y todo se ejecuta tal cual.
"""
from __future__ import annotations

import contextlib
import functools

from django.conf import settings
from django.db import connection

from clientes.constantes import ESQUEMA_PRINCIPAL as ESQUEMA_DE_DESARROLLO


def hay_tenants() -> bool:
    return hasattr(connection, "set_schema") and "django_tenants" in settings.INSTALLED_APPS


def esquema_de_host(scope) -> str | None:
    """Esquema para el host del handshake; None si el dominio no es de ninguna clínica."""
    if not hay_tenants():
        return None
    from django_tenants.utils import get_tenant_domain_model, remove_www

    cabeceras = dict(scope.get("headers") or [])
    host = remove_www(cabeceras.get(b"host", b"").decode("latin-1").split(":")[0].lower())
    dominio = get_tenant_domain_model().objects.select_related("tenant").filter(domain=host).first()
    if dominio:
        return dominio.tenant.schema_name
    return ESQUEMA_DE_DESARROLLO if settings.DEBUG else None


def en_esquema(funcion):
    """Ejecuta un método del consumidor dentro del esquema de su conexión."""

    @functools.wraps(funcion)
    def envoltura(self, *args, **kwargs):
        esquema = (getattr(self, "scope", None) or {}).get("schema_name")
        if not (esquema and hay_tenants()):
            return funcion(self, *args, **kwargs)
        from django_tenants.utils import schema_context

        with schema_context(esquema):
            return funcion(self, *args, **kwargs)

    return envoltura


@contextlib.contextmanager
def contexto(esquema: str | None):
    if esquema and hay_tenants():
        from django_tenants.utils import schema_context

        with schema_context(esquema):
            yield
    else:
        yield
