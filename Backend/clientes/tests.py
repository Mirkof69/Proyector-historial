"""Tests para el módulo de clientes (multi-tenancy con django-tenants).

Crear un Client dispara la creación de un schema PostgreSQL real, así que aquí
se verifica la CONFIGURACIÓN de seguridad a nivel de clase (sin escribir en BD),
que es lo crítico: que no se dropeen schemas de tenants automáticamente.
"""
from django.test import SimpleTestCase

from .models import Client, Domain


class ClientConfigTest(SimpleTestCase):
    def test_no_dropea_schema_automaticamente(self):
        """Seguridad: borrar un tenant NO debe dropear su schema (y sus datos)
        automáticamente."""
        self.assertFalse(Client.auto_drop_schema)

    def test_crea_schema_automaticamente(self):
        self.assertTrue(Client.auto_create_schema)

    def test_modelos_existen_con_mixins_de_tenant(self):
        from django_tenants.models import DomainMixin, TenantMixin
        self.assertTrue(issubclass(Client, TenantMixin))
        self.assertTrue(issubclass(Domain, DomainMixin))
