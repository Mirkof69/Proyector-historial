"""Ecografias Archivos Views"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from core.permissions import FetalMedicalPermission

from .models import EcografiaArchivo
from .serializers import (
    EcografiaArchivoCreateSerializer,
    EcografiaArchivoListSerializer,
    EcografiaArchivoSerializer,
)


class EcografiaArchivoViewSet(viewsets.ModelViewSet):
    """Adjuntos de una ecografía (imagen, DICOM, PDF, video).

    `?ecografia=<id>` lista los de una ecografía. Mismos permisos que el resto
    de la historia clínica (recepción no ve archivos clínicos).
    """

    permission_classes = [FetalMedicalPermission]

    queryset = EcografiaArchivo.objects.select_related(
        "ecografia", "subido_por",
    ).order_by("-fecha_subida")

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["ecografia", "tipo_archivo"]
    ordering_fields = ["fecha_subida", "nombre_archivo"]
    ordering = ["-fecha_subida"]

    def perform_create(self, serializer):
        serializer.save(subido_por=self.request.user)

    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == "list":
            return EcografiaArchivoListSerializer
        if self.action == "create":
            return EcografiaArchivoCreateSerializer
        return EcografiaArchivoSerializer
