"""=============================================================================
SERIALIZERS: API DE AUDITORÍA
=============================================================================
Serializers para exponer los registros de auditoría a través de la API REST.
=============================================================================
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import RegistroAuditoria

Usuario = get_user_model()


class UsuarioAuditoriaSerializer(serializers.ModelSerializer):
    """Serializer simplificado para mostrar información del usuario en auditoría"""

    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Usuario
        fields = ["id", "email", "nombre_completo"]

    def get_nombre_completo(self, obj):
        """Retorna el nombre completo del usuario"""
        if hasattr(obj, "get_full_name"):
            return obj.get_full_name()
        if hasattr(obj, "nombre") and hasattr(obj, "apellido_paterno"):
            return f"{obj.nombre} {obj.apellido_paterno}"
        return obj.email


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    """Serializer completo para registros de auditoría"""

    usuario = UsuarioAuditoriaSerializer(read_only=True)
    accion_display = serializers.CharField(source="get_accion_display", read_only=True)
    cambios_resumidos = serializers.ReadOnlyField()

    class Meta:
        """Meta"""
        model = RegistroAuditoria
        fields = [
            "id",
            "modulo",
            "accion",
            "accion_display",
            "registro_id",
            "usuario",
            "fecha",
            "datos_anteriores",
            "datos_nuevos",
            "cambios_resumidos",
            "ip_address",
            "user_agent",
        ]
        read_only_fields = ["__all__"]


class RegistroAuditoriaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados (sin datos completos)"""

    usuario = UsuarioAuditoriaSerializer(read_only=True)
    accion_display = serializers.CharField(source="get_accion_display", read_only=True)

    class Meta:
        """Meta"""
        model = RegistroAuditoria
        fields = [
            "id",
            "modulo",
            "accion",
            "accion_display",
            "registro_id",
            "usuario",
            "fecha",
        ]
        read_only_fields = ["__all__"]
