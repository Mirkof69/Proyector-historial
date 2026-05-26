"""Ecografias Archivos Views"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from .models import EcografiaArchivo
from .serializers import (
    EcografiaArchivoCreateSerializer,
    EcografiaArchivoListSerializer,
    EcografiaArchivoSerializer,
)


class EcografiaArchivoViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ultrasound files"""

    queryset = EcografiaArchivo.objects.select_related(
        "ecografia", "subido_por",
    ).order_by("-fecha_subida")

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["ecografia", "tipo_archivo"]
    ordering_fields = ["fecha_subida", "nombre_archivo"]
    ordering = ["-fecha_subida"]

    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == "list":
            return EcografiaArchivoListSerializer
        if self.action == "create":
            return EcografiaArchivoCreateSerializer
        return EcografiaArchivoSerializer
