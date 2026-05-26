"""=============================================================================
MÓDULO: VACUNAS - SERIALIZERS
=============================================================================
Serializers para gestión de vacunas en sistema de atención prenatal
- TipoVacuna: Serializers para catálogo de vacunas
- RegistroVacuna: Serializers para registros de vacunación
=============================================================================
"""

from rest_framework import serializers

from .models import RegistroVacuna, TipoVacuna

# =============================================================================
# TIPO VACUNA SERIALIZERS
# =============================================================================


class TipoVacunaSerializer(serializers.ModelSerializer):
    """Serializer completo para TipoVacuna
    Incluye todos los campos y propiedades calculadas
    """

    # Campos calculados
    es_multidosis = serializers.ReadOnlyField()
    tiene_contraindicaciones = serializers.ReadOnlyField()
    resumen = serializers.SerializerMethodField()
    total_registros = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = TipoVacuna
        fields = [
            "id",
            "nombre",
            "descripcion",
            "dosis_requeridas",
            "intervalo_dosis_dias",
            "edad_minima_aplicacion",
            "contraindicaciones",
            "efectos_secundarios",
            "obligatoria_embarazo",
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
            # Campos calculados
            "es_multidosis",
            "tiene_contraindicaciones",
            "resumen",
            "total_registros",
        ]
        read_only_fields = ["id", "fecha_creacion", "fecha_modificacion"]

    def get_resumen(self, obj):
        """Retorna resumen de la vacuna"""
        return obj.get_resumen()

    def get_total_registros(self, obj):
        """Retorna el total de registros de aplicación de esta vacuna"""
        return obj.registros.count()

    def validate(self, attrs):
        """Validaciones personalizadas"""
        dosis_requeridas = attrs.get("dosis_requeridas")
        intervalo_dosis_dias = attrs.get("intervalo_dosis_dias")

        if dosis_requeridas and dosis_requeridas > 1 and not intervalo_dosis_dias:
            raise serializers.ValidationError(
                {
                    "intervalo_dosis_dias": "Las vacunas multidosis deben especificar el intervalo entre dosis",
                },
            )

        return attrs


class TipoVacunaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de TipoVacuna
    Solo incluye campos esenciales para optimizar performance
    """

    es_multidosis = serializers.ReadOnlyField()
    total_registros = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = TipoVacuna
        fields = [
            "id",
            "nombre",
            "descripcion",
            "dosis_requeridas",
            "obligatoria_embarazo",
            "activo",
            "es_multidosis",
            "total_registros",
        ]

    def get_total_registros(self, obj):
        """Retorna el total de registros de aplicación de esta vacuna"""
        return obj.registros.count()


# =============================================================================
# REGISTRO VACUNA SERIALIZERS
# =============================================================================


class RegistroVacunaSerializer(serializers.ModelSerializer):
    """Serializer completo para RegistroVacuna con objetos anidados
    Incluye información detallada de relaciones
    """

    # Relaciones anidadas (solo lectura)
    paciente_info = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()
    tipo_vacuna_info = serializers.SerializerMethodField()
    aplicado_por_info = serializers.SerializerMethodField()

    # Campos calculados
    esquema_completo = serializers.ReadOnlyField()
    tiene_reacciones_adversas = serializers.ReadOnlyField()
    requiere_siguiente_dosis = serializers.ReadOnlyField()
    progreso_esquema = serializers.SerializerMethodField()
    resumen = serializers.SerializerMethodField()
    via_administracion_display = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = RegistroVacuna
        fields = [
            "id",
            "paciente",
            "embarazo",
            "tipo_vacuna",
            "fecha_aplicacion",
            "numero_dosis",
            "lote",
            "laboratorio",
            "via_administracion",
            "via_administracion_display",
            "sitio_aplicacion",
            "aplicado_por",
            "proxima_dosis_fecha",
            "reacciones_adversas",
            "observaciones",
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
            # Relaciones anidadas
            "paciente_info",
            "embarazo_info",
            "tipo_vacuna_info",
            "aplicado_por_info",
            # Campos calculados
            "esquema_completo",
            "tiene_reacciones_adversas",
            "requiere_siguiente_dosis",
            "progreso_esquema",
            "resumen",
        ]
        read_only_fields = ["id", "fecha_creacion", "fecha_modificacion"]

    def get_paciente_info(self, obj):
        """Información del paciente"""
        if not obj.paciente:
            return None
        return {
            "id": obj.paciente.id,
            "nombre_completo": obj.paciente.nombre_completo,
            "id_clinico": obj.paciente.id_clinico,
            "ci": obj.paciente.ci,
        }

    def get_embarazo_info(self, obj):
        """Información del embarazo"""
        if not obj.embarazo:
            return None
        return {
            "id": obj.embarazo.id,
            "numero_gesta": obj.embarazo.numero_gesta,
            "numero_para": obj.embarazo.numero_para,
            "estado": obj.embarazo.estado,
        }

    def get_tipo_vacuna_info(self, obj):
        """Información del tipo de vacuna"""
        if not obj.tipo_vacuna:
            return None
        return {
            "id": obj.tipo_vacuna.id,
            "nombre": obj.tipo_vacuna.nombre,
            "dosis_requeridas": obj.tipo_vacuna.dosis_requeridas,
            "obligatoria_embarazo": obj.tipo_vacuna.obligatoria_embarazo,
        }

    def get_aplicado_por_info(self, obj):
        """Información del profesional que aplicó la vacuna"""
        if not obj.aplicado_por:
            return None
        return {
            "id": obj.aplicado_por.id,
            "nombre_completo": obj.aplicado_por.nombre_completo,
            "rol": obj.aplicado_por.get_rol_display(),
            "especialidad": obj.aplicado_por.especialidad,
        }

    def get_progreso_esquema(self, obj):
        """Progreso del esquema de vacunación"""
        return obj.get_progreso_esquema()

    def get_resumen(self, obj):
        """Resumen del registro"""
        return obj.get_resumen()

    def get_via_administracion_display(self, obj):
        """Nombre legible de la vía de administración"""
        return obj.get_via_administracion_display() if obj.via_administracion else None


class RegistroVacunaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de RegistroVacuna
    Solo incluye campos esenciales para optimizar performance
    """

    paciente_nombre = serializers.SerializerMethodField()
    tipo_vacuna_nombre = serializers.SerializerMethodField()
    esquema_completo = serializers.ReadOnlyField()
    progreso = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = RegistroVacuna
        fields = [
            "id",
            "paciente_nombre",
            "tipo_vacuna_nombre",
            "fecha_aplicacion",
            "numero_dosis",
            "via_administracion",
            "esquema_completo",
            "proxima_dosis_fecha",
            "progreso",
        ]

    def get_paciente_nombre(self, obj):
        """Nombre del paciente"""
        return obj.paciente.nombre_completo if obj.paciente else None

    def get_tipo_vacuna_nombre(self, obj):
        """Nombre de la vacuna"""
        return obj.tipo_vacuna.nombre if obj.tipo_vacuna else None

    def get_progreso(self, obj):
        """Progreso simplificado del esquema"""
        return f"{obj.numero_dosis}/{obj.tipo_vacuna.dosis_requeridas}"


class RegistroVacunaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar RegistroVacuna
    Incluye validaciones específicas para operaciones de escritura
    """

    class Meta:
        """Meta"""
        model = RegistroVacuna
        fields = [
            "id",
            "paciente",
            "embarazo",
            "tipo_vacuna",
            "fecha_aplicacion",
            "numero_dosis",
            "lote",
            "laboratorio",
            "via_administracion",
            "sitio_aplicacion",
            "aplicado_por",
            "proxima_dosis_fecha",
            "reacciones_adversas",
            "observaciones",
            "activo",
        ]
        read_only_fields = ["id"]

    def validate_numero_dosis(self, value):
        """Validar número de dosis"""
        if value < 1:
            raise serializers.ValidationError("El número de dosis debe ser mayor a 0")
        if value > 10:
            raise serializers.ValidationError("El número de dosis no puede exceder 10")
        return value

    def validate_lote(self, value):
        """Validar lote"""
        if not value or not value.strip():
            raise serializers.ValidationError("El lote es obligatorio")
        return value.strip().upper()

    def validate_laboratorio(self, value):
        """Validar laboratorio"""
        if not value or not value.strip():
            raise serializers.ValidationError("El laboratorio es obligatorio")
        return value.strip()

    def validate(self, attrs):
        """Validaciones generales"""
        tipo_vacuna = attrs.get("tipo_vacuna")
        numero_dosis = attrs.get("numero_dosis")
        paciente = attrs.get("paciente")
        fecha_aplicacion = attrs.get("fecha_aplicacion")

        # Validar que el número de dosis no exceda las requeridas
        if tipo_vacuna and numero_dosis:
            if numero_dosis > tipo_vacuna.dosis_requeridas:
                raise serializers.ValidationError(
                    {
                        "numero_dosis": f"El número de dosis no puede exceder {tipo_vacuna.dosis_requeridas} para {tipo_vacuna.nombre}",
                    },
                )

        # Validar que no se duplique la misma dosis para el mismo paciente
        if paciente and tipo_vacuna and numero_dosis and fecha_aplicacion:
            query = RegistroVacuna.objects.filter(
                paciente=paciente,
                tipo_vacuna=tipo_vacuna,
                numero_dosis=numero_dosis,
                fecha_aplicacion=fecha_aplicacion,
            )

            # Excluir el registro actual en caso de actualización
            if self.instance:
                query = query.exclude(pk=self.instance.pk)

            if query.exists():
                raise serializers.ValidationError(
                    "Ya existe un registro de esta vacuna con el mismo número de dosis para este paciente en esta fecha",
                )

        # Validar que la fecha de próxima dosis sea futura
        if attrs.get("proxima_dosis_fecha"):
            from datetime import date

            if attrs["proxima_dosis_fecha"] <= date.today():
                raise serializers.ValidationError(
                    {"proxima_dosis_fecha": "La fecha de próxima dosis debe ser futura"},
                )

        # Validar que exista dosis anterior si no es la primera dosis
        if numero_dosis and numero_dosis > 1 and paciente and tipo_vacuna:
            dosis_anterior = RegistroVacuna.objects.filter(
                paciente=paciente,
                tipo_vacuna=tipo_vacuna,
                numero_dosis=numero_dosis - 1,
            ).exists()

            if not dosis_anterior:
                raise serializers.ValidationError(
                    {
                        "numero_dosis": f"Debe aplicar primero la dosis {numero_dosis - 1}",
                    },
                )

        return attrs

    def create(self, validated_data):
        """Crear registro con usuario que lo registra"""
        request = self.context.get("request")
        if (
            request
            and hasattr(request, "user")
            and not validated_data.get("aplicado_por")
        ):
            validated_data["aplicado_por"] = request.user

        return super().create(validated_data)
