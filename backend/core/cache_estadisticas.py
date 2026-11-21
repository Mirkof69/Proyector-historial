"""Caché corta para agregados del Panel y de Reportes que son iguales para todo el personal.

Por qué existe
--------------
`estadisticas-generales`, `indicadores-gestion` y `dashboard-kpis/resumen`
recorren tablas enteras (12 meses de partos, todas las citas, todos los
controles) y su resultado no depende de quién lo pide. Cada Panel que se abre
los recalculaba: en la prueba de carga del 29/10/2026, con 50 usuarios sin
pausa, `estadisticas-generales` llegó a pasar de 30 s y dio timeouts.

Qué se cachea y qué no
----------------------
Solo conteos y porcentajes del establecimiento, nunca datos de una paciente ni
listas clínicas (alertas, resultados críticos): esas siempre se leen en vivo.
La clave lleva el esquema de la clínica (django-tenants) y los parámetros de
la consulta, así dos clínicas o dos rangos de fechas nunca comparten valor.

Invalidación: por tiempo. Un indicador anual o el conteo de citas del Panel
puede mostrarse con hasta `ESTADISTICAS_CACHE_SEGUNDOS` (60 por defecto) de
retraso; no es información que se use para decidir sobre una paciente. Con 0
la caché queda apagada (así corren los tests, que cambian datos entre llamadas).

La permisología no cambia: se llama DENTRO de la vista, después de que DRF
autenticó y comprobó permisos.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.db import connection


def segundos_cache() -> int:
    return int(getattr(settings, "ESTADISTICAS_CACHE_SEGUNDOS", 60))


def clave(nombre: str, params=None) -> str:
    esquema = getattr(connection, "schema_name", "public")
    consulta = urlencode(sorted((params or {}).items()))
    return f"estadisticas:{esquema}:{nombre}:{consulta}"


def valor_cacheado(nombre: str, calcular: Callable[[], Any], params=None,
                   cacheable: Callable[[Any], bool] | None = None) -> Any:
    """Devuelve `calcular()` guardándolo `segundos_cache()` segundos.

    `cacheable(valor)` permite no guardar un resultado con errores parciales.
    """
    ttl = segundos_cache()
    if ttl <= 0:
        return calcular()
    k = clave(nombre, params)
    valor = cache.get(k)
    if valor is not None:
        return valor
    valor = calcular()
    if cacheable is None or cacheable(valor):
        cache.set(k, valor, ttl)
    return valor
