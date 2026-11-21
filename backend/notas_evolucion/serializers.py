"""=============================================================================
SERIALIZERS - NOTAS DE EVOLUCIÓN
=============================================================================
Serializers para el sistema de notas médicas de evolución
"""

from rest_framework import serializers

from embarazos.models import Embarazo
from pacientes.models import Paciente

# from controles.models import ControlPrenatal  # REMOVED to fix circular import
from usuarios.models import Usuario

from .models import NotaEvolucion


class PacienteSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para información básica del paciente"""

    nombre_completo = serializers.ReadOnlyField()
    edad = serializers.ReadOnlyField()

    class Meta:
        """Meta"""
        model = Paciente
        fields = [
            "id",
            "id_clinico",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "nombre_completo",
            "ci",
            "edad",
            "fecha_nacimiento",
            "genero",
            "tipo_sangre",
        ]


class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para información básica del usuario"""

    nombre_completo = serializers.ReadOnlyField()

    class Meta:
        """Meta"""
        model = Usuario
        fields = [
            "id",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "nombre_completo",
            "rol",
            "especialidad",
            "email",
        ]


class EmbarazoSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para información básica del embarazo"""

    class Meta:
        """Meta"""
        model = Embarazo
        fields = [
            "id",
            "uuid",
            "numero_gesta",
            "fecha_ultima_menstruacion",
            "fecha_probable_parto",
            "tipo_embarazo",
            "riesgo_embarazo",
            "estado",
        ]


class ControlPrenatalSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para información básica del control prenatal"""

    class Meta:
        """Meta"""
        from controles.models import ControlPrenatal  # Deferred import

        model = ControlPrenatal
        fields = [
            "id",
            "numero_control",
            "fecha_control",
            "semanas_gestacion",
            "dias_gestacion",
        ]


class NotaEvolucionSerializer(serializers.ModelSerializer):
    """Serializer completo de NotaEvolucion con objetos relacionados anidados
    Usado para lectura detallada (retrieve)
    """

    paciente = PacienteSimpleSerializer(read_only=True)
    embarazo = EmbarazoSimpleSerializer(read_only=True)
    control_prenatal = ControlPrenatalSimpleSerializer(read_only=True)
    medico = UsuarioSimpleSerializer(read_only=True)
    revisado_por = UsuarioSimpleSerializer(read_only=True)

    # Propiedades calculadas
    presion_arterial = serializers.ReadOnlyField()
    edad_gestacional_completa = serializers.ReadOnlyField()

    # Display fields para choices
    tipo_consulta_display = serializers.CharField(
        source="get_tipo_consulta_display", read_only=True,
    )

    class Meta:
        """Meta"""
        model = NotaEvolucion
        fields = [
            "id",
            "paciente",
            "embarazo",
            "control_prenatal",
            "medico",
            "fecha_consulta",
            "tipo_consulta",
            "tipo_consulta_display",
            "motivo_consulta",
            # Signos vitales
            "presion_arterial_sistolica",
            "presion_arterial_diastolica",
            "presion_arterial",
            "frecuencia_cardiaca",
            "frecuencia_respiratoria",
            "temperatura",
            "saturacion_oxigeno",
            # Datos obstétricos
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "edad_gestacional_completa",
            "altura_uterina",
            "frecuencia_cardiaca_fetal",
            "presentacion_fetal",
            "movimientos_fetales",
            # Examen físico
            "examen_fisico",
            "examen_obstetrico",
            # Diagnóstico y plan
            "diagnosticos",
            "plan_tratamiento",
            "indicaciones",
            "observaciones",
            # Control de calidad
            "revisado_por",
            "fecha_revision",
            # Trazabilidad
            "fecha_creacion",
            "fecha_modificacion",
            "activo",
        ]
        read_only_fields = ["fecha_creacion", "fecha_modificacion"]


class NotaEvolucionListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de NotaEvolucion
    Optimizado para rendimiento en listas grandes
    """

    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True,
    )
    paciente_id_clinico = serializers.CharField(
        source="paciente.id_clinico", read_only=True,
    )
    medico_nombre = serializers.CharField(
        source="medico.nombre_completo", read_only=True,
    )
    tipo_consulta_display = serializers.CharField(
        source="get_tipo_consulta_display", read_only=True,
    )
    presion_arterial = serializers.ReadOnlyField()
    edad_gestacional_completa = serializers.ReadOnlyField()

    class Meta:
        """Meta"""
        model = NotaEvolucion
        fields = [
            "id",
            "paciente_nombre",
            "paciente_id_clinico",
            "medico_nombre",
            "fecha_consulta",
            "tipo_consulta",
            "tipo_consulta_display",
            "motivo_consulta",
            "presion_arterial",
            "temperatura",
            "edad_gestacional_completa",
            "diagnosticos",
            "activo",
        ]


class NotaEvolucionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar NotaEvolucion
    Valida relaciones y campos requeridos
    """

    class Meta:
        """Meta"""
        model = NotaEvolucion
        fields = [
            "id",
            "paciente",
            "embarazo",
            "control_prenatal",
            "medico",
            "fecha_consulta",
            "tipo_consulta",
            "motivo_consulta",
            # Signos vitales
            "presion_arterial_sistolica",
            "presion_arterial_diastolica",
            "frecuencia_cardiaca",
            "frecuencia_respiratoria",
            "temperatura",
            "saturacion_oxigeno",
            # Datos obstétricos
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "altura_uterina",
            "frecuencia_cardiaca_fetal",
            "presentacion_fetal",
            "movimientos_fetales",
            # Examen físico
            "examen_fisico",
            "examen_obstetrico",
            # Diagnóstico y plan
            "diagnosticos",
            "plan_tratamiento",
            "indicaciones",
            "observaciones",
            # Control de calidad
            "revisado_por",
            "fecha_revision",
            "activo",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Validaciones personalizadas
        """
        # Validar que si hay embarazo, pertenezca al paciente
        if "embarazo" in attrs and attrs["embarazo"] is not None:
            if "paciente" in attrs and attrs["embarazo"].paciente != attrs["paciente"]:
                raise serializers.ValidationError(
                    "El embarazo seleccionado no pertenece al paciente indicado",
                )

        # Validar que si hay control prenatal, pertenezca al embarazo y paciente
        if "control_prenatal" in attrs and attrs["control_prenatal"] is not None:
            control = attrs["control_prenatal"]
            if "paciente" in attrs and control.paciente != attrs["paciente"]:
                raise serializers.ValidationError(
                    "El control prenatal seleccionado no pertenece al paciente indicado",
                )
            if "embarazo" in attrs and attrs["embarazo"] is not None:
                if control.embarazo != attrs["embarazo"]:
                    raise serializers.ValidationError(
                        "El control prenatal seleccionado no pertenece al embarazo indicado",
                    )

        # Validar presión arterial
        if (
            "presion_arterial_sistolica" in attrs
            and "presion_arterial_diastolica" in attrs
        ):
            sistolica = attrs.get("presion_arterial_sistolica")
            diastolica = attrs.get("presion_arterial_diastolica")
            if sistolica and diastolica and sistolica <= diastolica:
                raise serializers.ValidationError(
                    "La presión arterial sistólica debe ser mayor que la diastólica",
                )

        # Validar edad gestacional
        dias = attrs.get("edad_gestacional_dias", 0)
        if dias and (dias < 0 or dias > 6):
            raise serializers.ValidationError(
                "Los días adicionales de edad gestacional deben estar entre 0 y 6",
            )

        # Validar que el médico tenga rol de médico
        if "medico" in attrs:
            if attrs["medico"].rol not in ["medico", "administrador"]:
                raise serializers.ValidationError(
                    "El usuario asignado como médico debe tener rol de médico o administrador",
                )

        # Si hay revisado_por, debe haber fecha_revision
        if "revisado_por" in attrs and attrs["revisado_por"] is not None:
            if "fecha_revision" not in attrs or attrs["fecha_revision"] is None:
                raise serializers.ValidationError(
                    "Si se indica un revisor, debe especificarse la fecha de revisión",
                )

        return attrs

    def to_representation(self, instance):
        """Usar el serializer completo para la respuesta después de crear/actualizar
        """
        return NotaEvolucionSerializer(instance, context=self.context).data
