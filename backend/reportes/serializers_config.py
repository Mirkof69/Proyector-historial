"""=============================================================================
SERIALIZERS PARA CONFIGURACIÓN DEL SISTEMA
=============================================================================
"""

from rest_framework import serializers

from .models_config import ConfiguracionAlertas, HorarioAtencion, SistemaConfiguracion


class ConfiguracionAlertasSerializer(serializers.ModelSerializer):
    """Serializer para la configuración de umbrales y notificaciones de alertas"""

    class Meta:
        """Meta"""
        model = ConfiguracionAlertas
        fields = [
            "id",
            "alertar_presion_alta",
            "limite_presion_sistolica",
            "alertar_glucosa_alta",
            "limite_glucosa_ayunas",
            "alertar_resultados_criticos",
            "alertar_resultados_anormales",
            "notificar_por_email",
            "notificar_por_sistema",
            "fecha_actualizacion",
        ]
        read_only_fields = ["id", "fecha_actualizacion"]


class SistemaConfiguracionSerializer(serializers.ModelSerializer):
    """Serializer para la configuración del sistema"""

    class Meta:
        """Meta"""
        model = SistemaConfiguracion
        fields = [
            "id",
            "nombre_clinica",
            "direccion",
            "telefono_contacto",
            "email_contacto",
            "logo",
            "modo_mantenimiento",
            "permitir_registro_publico",
            "dias_retencion_logs",
            "smtp_host",
            "smtp_port",
            "smtp_user",
            "smtp_secure",
            "fecha_actualizacion",
        ]
        read_only_fields = ["id", "fecha_actualizacion"]
        # No incluir smtp_password en serializer por seguridad


class HorarioAtencionSerializer(serializers.ModelSerializer):
    """Serializer para horarios de atención"""

    dia_display = serializers.CharField(source="get_dia_display", read_only=True)

    class Meta:
        """Meta"""
        model = HorarioAtencion
        fields = [
            "id",
            "dia",
            "dia_display",
            "activo",
            "hora_inicio",
            "hora_fin",
            "fecha_actualizacion",
        ]
        read_only_fields = ["id", "fecha_actualizacion"]

    def validate(self, attrs):
        """Validar que hora_fin sea después de hora_inicio"""
        if attrs.get("hora_inicio") and attrs.get("hora_fin"):
            if attrs["hora_fin"] <= attrs["hora_inicio"]:
                raise serializers.ValidationError(
                    {
                        "hora_fin": "La hora de cierre debe ser posterior a la hora de inicio",
                    },
                )
        return attrs
