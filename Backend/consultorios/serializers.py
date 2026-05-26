"""CONSULTORIOS - SERIALIZERS"""

from rest_framework import serializers

from .models import Consultorio


class ConsultorioSerializer(serializers.ModelSerializer):
    """Consultorioserializer"""
    disponible = serializers.SerializerMethodField()
    descripcion_completa = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Consultorio
        fields = "__all__"
        read_only_fields = ["fecha_registro", "fecha_modificacion"]

    def get_disponible(self, obj):
        """Get disponible"""
        return obj.esta_disponible()

    def get_descripcion_completa(self, obj):
        """Get descripcion completa"""
        return obj.get_descripcion_completa()
