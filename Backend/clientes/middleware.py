import logging

from django.apps import apps
from django.conf import settings
from django_tenants.middleware.main import TenantMainMiddleware

logger = logging.getLogger(__name__)


class FallbackTenantMiddleware(TenantMainMiddleware):
    """
    En DESARROLLO, si el dominio no está en la BD usa clinica_demo (permite
    entrar desde cualquier IP de la red sin configurar nada).

    En PRODUCCIÓN no hay respaldo: un dominio desconocido da 404. Antes caía
    siempre en clinica_demo, así que cualquier nombre de host apuntado al
    servidor servía los datos de esa clínica.
    """

    def get_tenant(self, domain_model, hostname):
        try:
            return super().get_tenant(domain_model, hostname)
        except Exception:
            if not settings.DEBUG:
                raise
            ClientModel = apps.get_model(settings.TENANT_MODEL)
            tenant = ClientModel.objects.get(schema_name="clinica_demo")
            logger.debug("Dominio '%s' sin registro — fallback a clinica_demo", hostname)
            return tenant
