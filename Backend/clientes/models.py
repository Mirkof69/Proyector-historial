"""Models module."""
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Client(TenantMixin):
    """Client"""
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    # default false — SEGURIDAD: no dropear schemas automáticamente al borrar tenant
    auto_drop_schema = False


class Domain(DomainMixin):
    """Domain"""
