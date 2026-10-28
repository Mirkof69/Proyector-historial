"""TRIAJE - VIEWS"""

from django.db import models
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.exportacion import ExportarExcelMixin
from core.filtros import BusquedaClinicaFilter
from core.permissions import EsMedicoOEnfermera

from .models import TriajeEnfermeria
from .serializers import TriajeEnfermeriaSerializer


class TriajeEnfermeriaViewSet(ExportarExcelMixin, viewsets.ModelViewSet):
    """Triajeenfermeriaviewset"""
    queryset = TriajeEnfermeria.objects.all()
    serializer_class = TriajeEnfermeriaSerializer
    permission_classes = [EsMedicoOEnfermera]
    filter_backends = [
        DjangoFilterBackend,
        BusquedaClinicaFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "paciente": ["exact"],
        "cita": ["exact"],
        "enfermera": ["exact"],
        "alerta_presion_alta": ["exact"],
        "alerta_fiebre": ["exact"],
        "alerta_taquicardia": ["exact"],
        # Filtros de la pantalla de triaje. Antes los aplicaba el navegador
        # sobre la primera página (200) y, como estado y prioridad no
        # existían en el modelo, elegir cualquiera vaciaba la tabla.
        "estado": ["exact"],
        "prioridad": ["exact"],
        "fecha_registro": ["gte", "lte"],
    }
    # Búsqueda por paciente vía BusquedaClinicaFilter: los datos
    # identificatorios de Paciente están cifrados y el SearchFilter de DRF
    # (icontains en SQL) no encontraba NUNCA nada. Ver core/filtros.py.
    busqueda_ruta_paciente = "paciente"
    busqueda_campos_claros = [
        "motivo_visita",
    ]
    ordering_fields = ["fecha_registro", "prioridad", "estado"]
    # `-id` desempata triajes registrados en el mismo instante al paginar.
    ordering = ["-fecha_registro", "-id"]

    # Excel con los mismos filtros que la pantalla (y auditado). Antes se
    # armaba en el navegador con lo que hubiera en la primera página.
    excel_nombre = "triaje"
    excel_columnas = [
        ("Fecha/Hora", "fecha_registro"),
        ("Paciente", "paciente.nombre_completo"),
        ("ID clínico", "paciente.id_clinico"),
        ("Prioridad", "prioridad"),
        ("Estado", "estado"),
        ("Motivo", "motivo_visita"),
        ("Peso (kg)", "peso_kg"),
        ("Talla (cm)", "talla_cm"),
        ("Presión arterial", "get_presion_arterial"),
        ("Temperatura (°C)", "temperatura"),
        ("FC (lpm)", "frecuencia_cardiaca"),
        ("SpO2 (%)", "saturacion_oxigeno"),
        ("Enfermera", "enfermera.nombre_completo"),
    ]

    def get_queryset(self):
        """Get queryset"""
        return TriajeEnfermeria.objects.select_related("paciente", "cita", "enfermera")

    def perform_create(self, serializer):
        """TRAZABILIDAD: Auto-asignar enfermera y created_by al crear"""
        serializer.save(enfermera=self.request.user, created_by=self.request.user)

    def perform_update(self, serializer):
        """TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def resumen(self, request):
        """Tarjetas de la pantalla con los MISMOS filtros que el listado.

        GET /api/triaje/triajes/resumen/?search=&estado=&prioridad=&fecha_registro__gte=

        Antes se contaban en el navegador sobre la primera página (200
        triajes como mucho), y pendientes/completados/urgentes daban 0
        siempre porque esos campos no existían.
        """
        qs = self.filter_queryset(self.get_queryset()).order_by()
        por_estado = dict(qs.values_list("estado").annotate(n=Count("id")))
        por_prioridad = dict(qs.values_list("prioridad").annotate(n=Count("id")))
        return Response({
            "total": sum(por_estado.values()),
            "pendiente": por_estado.get("pendiente", 0),
            "completado": por_estado.get("completado", 0),
            "cancelado": por_estado.get("cancelado", 0),
            "urgente": por_prioridad.get("urgente", 0),
            "alto": por_prioridad.get("alto", 0),
            "normal": por_prioridad.get("normal", 0),
            "bajo": por_prioridad.get("bajo", 0),
            "presion_alta": qs.filter(alerta_presion_alta=True).count(),
        })

    @action(detail=False, methods=["get"])
    def con_alertas(self, _request):
        """Con alertas"""
        triajes = self.get_queryset().filter(
            models.Q(alerta_presion_alta=True)
            | models.Q(alerta_fiebre=True)
            | models.Q(alerta_taquicardia=True),
        )
        serializer = self.get_serializer(triajes, many=True)
        return Response(serializer.data)
