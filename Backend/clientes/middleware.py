from django_tenants.middleware.main import TenantMainMiddleware
from django.apps import apps
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class FallbackTenantMiddleware(TenantMainMiddleware):
    """
    Si el dominio no está en la BD usa clinica_demo automáticamente.
    Permite acceder desde cualquier IP o red sin configuración extra.
    """

    def get_tenant(self, domain_model, hostname):
        try:
            return super().get_tenant(domain_model, hostname)
        except Exception:
            ClientModel = apps.get_model(settings.TENANT_MODEL)
            tenant = ClientModel.objects.get(schema_name="clinica_demo")
            logger.debug("Dominio '%s' sin registro — fallback a clinica_demo", hostname)
            return tenant
