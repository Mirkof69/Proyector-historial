"""Serializers module."""
from rest_framework import serializers

from .models import TicketSoporte


class TicketSoporteSerializer(serializers.ModelSerializer):
    """Serializer para tickets de soporte tecnico."""

    usuario_nombre = serializers.CharField(
        source="usuario.nombre_completo", read_only=True, default=None,
    )
    modulo_display = serializers.CharField(source="get_modulo_display", read_only=True)
    prioridad_display = serializers.CharField(
        source="get_prioridad_display", read_only=True,
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        """Meta"""
        model = TicketSoporte
        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "asunto",
            "modulo",
            "modulo_display",
            "prioridad",
            "prioridad_display",
            "descripcion",
            "estado",
            "estado_display",
            "respuesta_admin",
            "fecha_creacion",
            "fecha_resolucion",
        ]
        read_only_fields = ["id", "usuario", "estado", "respuesta_admin", "fecha_creacion", "fecha_resolucion"]
