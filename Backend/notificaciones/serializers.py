"""=============================================================================
MÓDULO: NOTIFICACIONES - SERIALIZERS
=============================================================================
Serializers para el sistema de notificaciones
=============================================================================
"""
import re

from django.apps import apps

from rest_framework import serializers

from .models import ConfiguracionNotificaciones, HistorialNotificaciones, Notificacion



# Pantalla de cada entidad. Las notificaciones guardaban rutas que no existen
# («/laboratorio/resultados/14247», «/citas/5» sin /dashboard) o ninguna: al
# hacer clic no se abría nada.
_RUTA_ENTIDAD = {
    "paciente": "/dashboard/historia-clinica/{id}",
    "embarazo": "/dashboard/embarazos/{id}",
    "control": "/dashboard/controles/{id}",
    "cita": "/dashboard/citas/{id}",
    "examen": "/dashboard/laboratorio/{id}",
    "parto": "/dashboard/partos/{id}",
}


_MODELO_ENTIDAD = {
    "paciente": "pacientes.Paciente",
    "embarazo": "embarazos.Embarazo",
    "control": "controles.ControlPrenatal",
    "cita": "citas.Cita",
    "examen": "laboratorio.ExamenLaboratorio",
    "parto": "partos.Parto",
}


def enlace_de(obj, usuario=None) -> str:
    """Ruta del frontend que abre lo que la notificación anuncia."""

    entidad, eid = obj.entidad_tipo, obj.entidad_id
    if entidad == "resultado_laboratorio" and eid:
        from laboratorio.models import ResultadoLaboratorio

        examen = ResultadoLaboratorio.objects.filter(pk=eid).values_list("examen_id", flat=True).first()
        if examen:
            return f"/dashboard/laboratorio/{examen}"
    if entidad in _RUTA_ENTIDAD and eid:
        # Si el registro ya no existe (p. ej. lo borró la limpieza de pruebas),
        # se abre la bandeja en vez de una pantalla que da 404.
        modelo = apps.get_model(*_MODELO_ENTIDAD[entidad].split("."))
        if not modelo.objects.filter(pk=eid).exists():
            return "/dashboard/notificaciones"
        if entidad == "paciente" and usuario is not None and not usuario.has_perm("controles.view_controlprenatal"):
            return f"/dashboard/pacientes/{eid}"  # recepción no abre la historia clínica
        return _RUTA_ENTIDAD[entidad].format(id=eid)
    url = (obj.url or "").strip()
    if re.match(r"^/(?:dashboard/)?laboratorio/resultados/", url):
        return "/dashboard/laboratorio"
    m = re.match(r"^/(?:dashboard/)?laboratorio/examenes/(\d+)", url)
    if m:
        return f"/dashboard/laboratorio/{m.group(1)}"
    if url.startswith("/") and not url.startswith("/dashboard"):
        return "/dashboard" + url
    return url or "/dashboard/notificaciones"

class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer completo para Notificaciones"""

    tiempo_transcurrido = serializers.SerializerMethodField()
    esta_vigente = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    enlace = serializers.SerializerMethodField()
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
            "enlace",
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

    def get_enlace(self, obj):
        request = self.context.get("request")
        return enlace_de(obj, getattr(request, "user", None))


class NotificacionListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de notificaciones"""

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    tiempo_transcurrido = serializers.SerializerMethodField()
    enlace = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Notificacion
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "prioridad",
            "titulo",
            "mensaje",
            "icono",
            "color",
            "url_texto",
            "enlace",
            "leida",
            "archivada",
            "fecha_creacion",
            "tiempo_transcurrido",
        ]

    def get_tiempo_transcurrido(self, obj):
        """Get tiempo transcurrido"""
        return obj.get_tiempo_transcurrido()

    def get_enlace(self, obj):
        request = self.context.get("request")
        return enlace_de(obj, getattr(request, "user", None))


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
