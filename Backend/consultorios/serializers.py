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
    """Consultorio con los nombres que usa la pantalla.

    El frontend se escribió con `tipo`, `area`, `estado` y `equipamiento` (nivel);
    el modelo los llama `tipo_consultorio`, `edificio`, `activo`/`en_mantenimiento`
    y `nivel_equipamiento`. Sin estos alias la tabla mostraba «—», todos los
    consultorios como inactivos, y crear uno desde la pantalla fallaba.
    """
    disponible = serializers.SerializerMethodField()
    descripcion_completa = serializers.SerializerMethodField()
    tipo = serializers.ChoiceField(source="tipo_consultorio", choices=Consultorio._meta.get_field(
        "tipo_consultorio").choices, required=False)
    tipo_display = serializers.CharField(source="get_tipo_consultorio_display", read_only=True)
    area = serializers.CharField(source="edificio", required=False, allow_blank=True, allow_null=True)
    equipamiento = serializers.CharField(source="nivel_equipamiento", required=False, allow_blank=True,
                                         allow_null=True)
    equipamiento_detalle = serializers.CharField(source="equipamiento", required=False, allow_blank=True,
                                                 allow_null=True)
    estado = serializers.ChoiceField(choices=["disponible", "ocupado", "mantenimiento", "limpieza", "reservado",
                                              "inactivo"], required=False, write_only=True)

    class Meta:
        """Meta"""
        model = Consultorio
        fields = "__all__"
        read_only_fields = ["fecha_registro", "fecha_modificacion"]

    def to_representation(self, instance):
        datos = super().to_representation(instance)
        datos["estado"] = estado_consultorio(instance)
        return datos

    def validate(self, attrs):
        # El estado de la pantalla se guarda en los dos booleanos del modelo;
        # «ocupado» y «reservado» se deducen de las ocupaciones, no se fijan a mano.
        estado = attrs.pop("estado", None)
        if estado == "inactivo":
            attrs["activo"] = False
        elif estado == "mantenimiento":
            attrs["en_mantenimiento"] = True
        elif estado is not None:
            attrs["en_mantenimiento"] = False
        if attrs.get("nivel_equipamiento") is None and "nivel_equipamiento" in attrs:
            attrs["nivel_equipamiento"] = ""
        return attrs

    def get_disponible(self, obj):
        """Get disponible"""
        return obj.esta_disponible()

    def get_descripcion_completa(self, obj):
        """Get descripcion completa"""
        return obj.get_descripcion_completa()


def estado_consultorio(consultorio) -> str:
    """inactivo · mantenimiento · ocupado (ocupación en curso) · disponible."""
    if not consultorio.activo:
        return "inactivo"
    if consultorio.en_mantenimiento:
        return "mantenimiento"
    if OcupacionConsultorio.objects.filter(consultorio=consultorio, estado="en_curso").exists():
        return "ocupado"
    return "disponible"


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
