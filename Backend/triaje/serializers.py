"""TRIAJE - SERIALIZERS"""

from rest_framework import serializers

from .models import TriajeEnfermeria


class TriajeEnfermeriaSerializer(serializers.ModelSerializer):
    """Triajeenfermeriaserializer"""
    paciente_info = serializers.SerializerMethodField()
    enfermera_info = serializers.SerializerMethodField()
    clasificacion_imc = serializers.SerializerMethodField()
    clasificacion_presion = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    resumen_completo = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = TriajeEnfermeria
        fields = "__all__"
        read_only_fields = [
            "fecha_registro",
            "imc",
            "alerta_presion_alta",
            "alerta_fiebre",
            "alerta_taquicardia",
        ]

    def get_paciente_info(self, obj):
        """Get paciente info"""
        return (
            {"id": obj.paciente.id, "nombre_completo": obj.paciente.nombre_completo}
            if obj.paciente
            else None
        )

    def get_enfermera_info(self, obj):
        """Get enfermera info"""
        return (
            {"id": obj.enfermera.id, "nombre": obj.enfermera.nombre}
            if obj.enfermera
            else None
        )

    def get_clasificacion_imc(self, obj):
        """Get clasificacion imc"""
        return obj.get_clasificacion_imc()

    def get_clasificacion_presion(self, obj):
        """Get clasificacion presion"""
        return obj.get_clasificacion_presion()

    def get_presion_arterial(self, obj):
        """Get presion arterial"""
        return obj.get_presion_arterial()

    def get_resumen_completo(self, obj):
        """Get resumen completo"""
        return obj.get_resumen()
