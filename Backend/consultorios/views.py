"""CONSULTORIOS - VIEWS"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import EsSoloMedico

from .models import Consultorio
from .serializers import ConsultorioSerializer


class ConsultorioViewSet(viewsets.ModelViewSet):
    """Consultorioviewset"""
    queryset = Consultorio.objects.all()
    serializer_class = ConsultorioSerializer
    permission_classes = [IsAuthenticated, EsSoloMedico]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["activo", "en_mantenimiento", "tipo_consultorio"]
    search_fields = ["nombre", "codigo", "ubicacion"]
    ordering = ["nombre"]

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def disponibles(self, _request):
        """Disponibles"""
        consultorios = self.get_queryset().filter(activo=True, en_mantenimiento=False)
        serializer = self.get_serializer(consultorios, many=True)
        return Response(serializer.data)
