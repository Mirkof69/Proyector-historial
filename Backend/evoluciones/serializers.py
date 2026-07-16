"""Evoluciones Serializers"""

from rest_framework import serializers

from .models import EvolucionEmbarazo


class EvolucionEmbarazoSerializer(serializers.ModelSerializer):
    """Serializer for EvolucionEmbarazo model"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    embarazo_info = serializers.SerializerMethodField()
    medico_nombre = serializers.CharField(source="medico.get_full_name", read_only=True)

    class Meta:
        """Meta"""
        model = EvolucionEmbarazo
        fields = "__all__"
        read_only_fields = ("fecha_registro",)

    def get_embarazo_info(self, obj):
        """Get basic pregnancy information"""
        if obj.embarazo:
            return {
                "id": obj.embarazo.id,
                "semanas_gestacion": obj.embarazo.semanas_gestacion,
                "fecha_probable_parto": obj.embarazo.fecha_probable_parto,
            }
        return None


class EvolucionEmbarazoListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    medico_nombre = serializers.CharField(source="medico.get_full_name", read_only=True)

    class Meta:
        """Meta"""
        model = EvolucionEmbarazo
        fields = [
            "id",
            "embarazo",
            "paciente_nombre",
            "tipo_evento",
            "fecha_evento",
            "medico_nombre",
            "descripcion",
        ]
        read_only_fields = fields


class EvolucionEmbarazoCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating evolutions"""

    class Meta:
        """Meta"""
        model = EvolucionEmbarazo
        fields = [
            "embarazo",
            "paciente",
            "tipo_evento",
            "fecha_evento",
            "descripcion",
            "medico",
        ]

    def validate(self, attrs):
        """Validate evolution data"""
        embarazo = attrs.get("embarazo")
        paciente = attrs.get("paciente")

        if embarazo and paciente and embarazo.paciente != paciente:
            raise serializers.ValidationError(
                "El embarazo no pertenece a la paciente seleccionada",
            )

        return attrs


class EvolucionEmbarazoDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all relations"""

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    paciente_detalle = serializers.SerializerMethodField()
    embarazo_detalle = serializers.SerializerMethodField()
    medico_nombre = serializers.CharField(source="medico.get_full_name", read_only=True)

    class Meta:
        """Meta"""
        model = EvolucionEmbarazo
        fields = "__all__"

    def get_paciente_detalle(self, obj):
        """Get patient details"""
        if obj.paciente:
            return {
                "id": obj.paciente.id,
                "nombre": obj.paciente.nombre_completo,
                "edad": obj.paciente.edad,
                "id_clinico": obj.paciente.id_clinico,
            }
        return None

    def get_embarazo_detalle(self, obj):
        """Get pregnancy details"""
        if obj.embarazo:
            return {
                "id": obj.embarazo.id,
                "semanas_gestacion": obj.embarazo.semanas_gestacion,
                "fecha_probable_parto": obj.embarazo.fecha_probable_parto,
                "estado": obj.embarazo.estado,
            }
        return None
