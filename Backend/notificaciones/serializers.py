"""=============================================================================
MÓDULO: NOTIFICACIONES - SERIALIZERS
=============================================================================
Serializers para el sistema de notificaciones
=============================================================================
"""

from rest_framework import serializers

from .models import ConfiguracionNotificaciones, HistorialNotificaciones, Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer completo para Notificaciones"""

    tiempo_transcurrido = serializers.SerializerMethodField()
    esta_vigente = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    prioridad_display = serializers.CharField(
        source="get_prioridad_display", read_only=True,
    )
    usuario_nombre = serializers.CharField(
        source="usuario.nombre_completo", read_only=True,
    )

    class Meta:
        """Meta"""
        model = Notificacion
        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "tipo",
            "tipo_display",
            "prioridad",
            "prioridad_display",
            "titulo",
            "mensaje",
            "icono",
            "color",
            "url",
            "url_texto",
            "leida",
            "fecha_leida",
            "archivada",
            "metadata",
            "entidad_tipo",
            "entidad_id",
            "fecha_creacion",
            "fecha_expiracion",
            "tiempo_transcurrido",
            "esta_vigente",
            "enviada_push",
            "enviada_email",
            "enviada_sms",
        ]
        read_only_fields = ["fecha_creacion", "fecha_leida", "icono", "color"]

    def get_tiempo_transcurrido(self, obj):
        """Obtiene el tiempo transcurrido en formato legible"""
        return obj.get_tiempo_transcurrido()

    def get_esta_vigente(self, obj):
        """Verifica si la notificación está vigente"""
        return obj.esta_vigente()


class NotificacionListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de notificaciones"""

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    tiempo_transcurrido = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Notificacion
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "prioridad",
            "titulo",
            "icono",
            "color",
            "leida",
            "archivada",
            "fecha_creacion",
            "tiempo_transcurrido",
        ]

    def get_tiempo_transcurrido(self, obj):
        """Get tiempo transcurrido"""
        return obj.get_tiempo_transcurrido()


class NotificacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear notificaciones"""

    class Meta:
        """Meta"""
        model = Notificacion
        fields = [
            "usuario",
            "tipo",
            "prioridad",
            "titulo",
            "mensaje",
            "url",
            "url_texto",
            "metadata",
            "entidad_tipo",
            "entidad_id",
            "fecha_expiracion",
        ]

    def create(self, validated_data):
        """Crea la notificación con icono y color automáticos"""
        notificacion = Notificacion(**validated_data)
        notificacion.save()  # El save() asignará icono y color automáticamente
        return notificacion


class MarcarLeidaSerializer(serializers.Serializer):
    """Serializer para marcar notificaciones como leídas"""

    notificacion_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Lista de IDs de notificaciones a marcar como leídas",
    )

    marcar_todas = serializers.BooleanField(
        default=False,
        help_text="Marcar todas las notificaciones del usuario como leídas",
    )

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance

    def validate_notificacion_ids(self, value):
        if value is not None:
            for id_val in value:
                if not isinstance(id_val, int) or id_val <= 0:
                    raise serializers.ValidationError(
                        "Todos los IDs deben ser enteros positivos",
                    )
        return value

    def validate(self, data):
        request = self.context.get("request")
        if not data.get("marcar_todas") and data.get("notificacion_ids"):
            from .models import Notificacion
            if request and request.user.is_authenticated:
                ids = data["notificacion_ids"]
                count = Notificacion.objects.filter(
                    id__in=ids, usuario=request.user,
                ).count()
                if count != len(ids):
                    raise serializers.ValidationError(
                        {"notificacion_ids": "Alguna(s) notificación(es) no pertenecen al usuario"},
                    )
        return data


class ConfiguracionNotificacionesSerializer(serializers.ModelSerializer):
    """Serializer para configuración de notificaciones"""

    usuario_nombre = serializers.CharField(
        source="usuario.nombre_completo", read_only=True,
    )

    class Meta:
        """Meta"""
        model = ConfiguracionNotificaciones
        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "recibir_push",
            "recibir_email",
            "recibir_sms",
            "notificar_citas",
            "notificar_examenes",
            "notificar_alertas",
            "notificar_mensajes",
            "notificar_documentos",
            "recordatorio_citas_horas",
            "recordatorio_controles",
            "no_molestar_inicio",
            "no_molestar_fin",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = ["fecha_creacion", "fecha_modificacion"]


class HistorialNotificacionesSerializer(serializers.ModelSerializer):
    """Serializer para historial de notificaciones"""

    accion_display = serializers.CharField(source="get_accion_display", read_only=True)
    notificacion_titulo = serializers.CharField(
        source="notificacion.titulo", read_only=True,
    )

    class Meta:
        """Meta"""
        model = HistorialNotificaciones
        fields = [
            "id",
            "notificacion",
            "notificacion_titulo",
            "accion",
            "accion_display",
            "fecha",
            "detalles",
        ]
        read_only_fields = ["fecha"]


class EstadisticasNotificacionesSerializer(serializers.Serializer):
    """Serializer para estadísticas de notificaciones"""

    total_notificaciones = serializers.IntegerField()
    no_leidas = serializers.IntegerField()
    leidas = serializers.IntegerField()
    archivadas = serializers.IntegerField()
    por_tipo = serializers.DictField()
    por_prioridad = serializers.DictField()
    recientes_24h = serializers.IntegerField()

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance

    def validate_fecha_desde(self, value):
        return value

    def validate(self, data):
        return data
