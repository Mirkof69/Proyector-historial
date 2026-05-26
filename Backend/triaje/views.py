"""TRIAJE - VIEWS"""

from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import EsMedicoOEnfermera

from .models import TriajeEnfermeria
from .serializers import TriajeEnfermeriaSerializer


class TriajeEnfermeriaViewSet(viewsets.ModelViewSet):
    """Triajeenfermeriaviewset"""
    queryset = TriajeEnfermeria.objects.all()
    serializer_class = TriajeEnfermeriaSerializer
    permission_classes = [EsMedicoOEnfermera]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "paciente",
        "cita",
        "enfermera",
        "alerta_presion_alta",
        "alerta_fiebre",
        "alerta_taquicardia",
    ]
    search_fields = ["paciente__nombre", "motivo_visita"]
    ordering = ["-fecha_registro"]

    def get_queryset(self):
        """Get queryset"""
        return TriajeEnfermeria.objects.select_related("paciente", "cita", "enfermera")

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar enfermera y created_by al crear"""
        serializer.save(enfermera=self.request.user, created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

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
