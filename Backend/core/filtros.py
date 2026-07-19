"""Filtros de búsqueda compartidos.

`BusquedaClinicaFilter` reemplaza a `SearchFilter` de DRF en todas las vistas
que buscan por datos de la paciente.

El problema que resuelve: los datos identificatorios de Paciente están
cifrados en la base, así que el `icontains` en SQL de `SearchFilter` corría
contra texto cifrado y devolvía 0 resultados SIEMPRE. Estaba declarado como
`search_fields = ["paciente__nombre", ...]` en 12 viewsets (embarazos,
controles, citas, partos, ecografías, laboratorio, vacunas, triaje,
antecedentes, notas de evolución, calculadoras, IA), o sea que buscar una
paciente por nombre no funcionaba en ninguna de esas pantallas.

Cómo se usa en un ViewSet:

    filter_backends = [DjangoFilterBackend, BusquedaClinicaFilter, OrderingFilter]
    busqueda_ruta_paciente = "paciente"        # o "embarazo__paciente"
    busqueda_campos_claros = ["notas"]         # campos NO cifrados del modelo

`search_fields` deja de usarse en esas vistas: mezclarlo volvería a filtrar
por campos cifrados y vaciaría el resultado.
"""
from __future__ import annotations

from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class BusquedaClinicaFilter(BaseFilterBackend):
    """Búsqueda por `?search=` que entiende los campos cifrados de Paciente."""

    def filter_queryset(self, request, queryset, view):
        """Filtra por término, combinando paciente (cifrado) y campos en claro."""
        termino = (request.query_params.get("search") or "").strip()
        if not termino:
            return queryset

        ruta_paciente = getattr(view, "busqueda_ruta_paciente", "paciente")
        campos_claros = getattr(view, "busqueda_campos_claros", [])

        condicion = Q()
        hubo_condicion = False

        if ruta_paciente:
            from pacientes.busqueda import ids_pacientes_que_coinciden

            ids = ids_pacientes_que_coinciden(termino)
            # Aunque no haya coincidencias se agrega la condición: sin ella el
            # filtro quedaría vacío y devolvería TODO, que es peor que no
            # encontrar nada cuando se busca una paciente concreta.
            condicion |= Q(**{f"{ruta_paciente}__id__in": ids})
            hubo_condicion = True

        for campo in campos_claros:
            condicion |= Q(**{f"{campo}__icontains": termino})
            hubo_condicion = True

        if not hubo_condicion:
            return queryset
        return queryset.filter(condicion).distinct()
