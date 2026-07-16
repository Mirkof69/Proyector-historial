"""CONSULTORIOS - SERIALIZERS"""

from rest_framework import serializers

from .models import (
    Consultorio,
    HorarioConsultorio,
    MantenimientoConsultorio,
    OcupacionConsultorio,
    ReservaConsultorio,
)


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


class HorarioConsultorioSerializer(serializers.ModelSerializer):
    """Horarioconsultorioserializer"""

    class Meta:
        """Meta"""
        model = HorarioConsultorio
        fields = "__all__"
        read_only_fields = ["id"]


class OcupacionConsultorioSerializer(serializers.ModelSerializer):
    """Ocupacionconsultorioserializer"""
    consultorio_nombre = serializers.CharField(
        source="consultorio.nombre", read_only=True
    )
    paciente_nombre = serializers.SerializerMethodField(read_only=True)
    medico_nombre = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Meta"""
        model = OcupacionConsultorio
        fields = "__all__"
        read_only_fields = ["id", "fecha_registro"]

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        if obj.paciente:
            return str(obj.paciente)
        return None

    def get_medico_nombre(self, obj):
        """Get medico nombre"""
        if obj.medico:
            return obj.medico.get_full_name() or obj.medico.username
        return None


class ReservaConsultorioSerializer(serializers.ModelSerializer):
    """Reservaconsultorioserializer"""
    consultorio_nombre = serializers.CharField(
        source="consultorio.nombre", read_only=True
    )
    medico_nombre = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Meta"""
        model = ReservaConsultorio
        fields = "__all__"
        read_only_fields = ["id", "fecha_registro", "fecha_modificacion"]

    def get_medico_nombre(self, obj):
        """Get medico nombre"""
        if obj.medico:
            return obj.medico.get_full_name() or obj.medico.username
        return None


class MantenimientoConsultorioSerializer(serializers.ModelSerializer):
    """Mantenimientoconsultorioserializer"""
    consultorio_nombre = serializers.CharField(
        source="consultorio.nombre", read_only=True
    )

    class Meta:
        """Meta"""
        model = MantenimientoConsultorio
        fields = "__all__"
        read_only_fields = ["id", "fecha_registro"]
