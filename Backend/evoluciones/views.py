"""Evoluciones Views"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from core.permissions import EsMedicoOEnfermera

from .models import EvolucionEmbarazo
from .serializers import (
    EvolucionEmbarazoCreateSerializer,
    EvolucionEmbarazoDetailSerializer,
    EvolucionEmbarazoListSerializer,
    EvolucionEmbarazoSerializer,
)


class EvolucionEmbarazoViewSet(viewsets.ModelViewSet):
    """ViewSet for managing pregnancy evolutions — restringido a médicos y enfermeras"""

    permission_classes = [IsAuthenticated, EsMedicoOEnfermera]

    queryset = EvolucionEmbarazo.objects.select_related(
        "embarazo", "paciente", "medico",
    ).order_by("-fecha_evento")

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["embarazo", "paciente", "tipo_evento"]
    ordering_fields = ["fecha_evento", "fecha_registro"]
    ordering = ["-fecha_evento"]

    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == "list":
            return EvolucionEmbarazoListSerializer
        if self.action == "create":
            return EvolucionEmbarazoCreateSerializer
        if self.action == "retrieve":
            return EvolucionEmbarazoDetailSerializer
        return EvolucionEmbarazoSerializer
