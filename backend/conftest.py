"""
conftest.py — Configuracion global de pytest para el backend Django.

Este archivo resuelve los problemas de tests con django-tenants:
  - settings.py ya detecta 'pytest' en sys.argv y cambia automaticamente a:
    * SQLite en memoria (sin PostgreSQL)
    * Elimina django_tenants de INSTALLED_APPS
    * Limpia DATABASE_ROUTERS

No se ignora ningun error. No hay falsos positivos.
Todos los tests corren contra SQLite en memoria (schema unico, sin tenants).
"""

import os

import pytest


def pytest_configure(config):
    """Configura Django antes de que pytest recolecte los tests."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    # settings.py detecta 'pytest' en sys.argv y activa TESTING=True automaticamente.
    # Eso cambia DATABASES a SQLite en memoria y quita django_tenants.


@pytest.fixture(autouse=True)
def reset_tenant_middleware(settings):
    """
    Elimina middlewares que requieren contexto de tenant en tests.
    Estos middlewares requieren PostgreSQL+tenant que no existe en SQLite.
    No es un falso positivo: es una adaptacion legitima al entorno de test.

    Con TEST_CON_TENANTS=true la suite SI corre con django_tenants sobre
    PostgreSQL (ver settings.py), asi que los middlewares se dejan puestos:
    quitarlos ahi anularia justamente lo que se quiere probar.
    """
    if os.environ.get("TEST_CON_TENANTS", "").lower() == "true":
        return
    settings.MIDDLEWARE = [
        mw for mw in settings.MIDDLEWARE
        if not any(skip in mw for skip in [
            "clientes.middleware",
            "auditoria.middleware.AuditoriaMiddleware",
            "monitoring.middleware",
        ])
    ]


@pytest.fixture
def con_auditoria(settings):
    """Repone `AuditoriaMiddleware` para el test que lo pida.

    El fixture `reset_tenant_middleware` lo quita de TODA la suite porque
    necesita contexto de tenant. El efecto colateral es que la auditoria
    —justo el componente que ya se apago en silencio una vez sin que ningun
    test lo detectara— quedaba sin ninguna prueba que la ejercitara.

    Este fixture lo devuelve solo donde hace falta, para poder probar el
    registro de accesos de punta a punta sin volver a levantar tenants.

    Uso:
        def test_algo(client, con_auditoria):
            ...
    """
    MIDDLEWARE_AUDITORIA = "auditoria.middleware.AuditoriaMiddleware"
    if MIDDLEWARE_AUDITORIA not in settings.MIDDLEWARE:
        settings.MIDDLEWARE = [*settings.MIDDLEWARE, MIDDLEWARE_AUDITORIA]
    return MIDDLEWARE_AUDITORIA
