"""=============================================================================
MÓDULO: EMBARAZOS - SERIALIZERS V3.0 FINAL CORREGIDO
=============================================================================
✅ BASADO EN EL MODELO REAL - SOLO CAMPOS QUE EXISTEN
✅ Sin errores de campos inexistentes
=============================================================================
"""

from datetime import date, timedelta

from rest_framework import serializers

from pacientes.models import Paciente

from .models import Embarazo


class EmbarazoSerializer(serializers.ModelSerializer):
    """✅ Serializer completo - SOLO CAMPOS DEL MODELO REAL
    """

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ALIAS PARA COMPATIBILIDAD CON FRONTEND
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    partos_previos = serializers.IntegerField(source="numero_para", read_only=True)
    cesareas_previas = serializers.IntegerField(
        source="numero_cesareas", read_only=True,
    )
    abortos_previos = serializers.IntegerField(source="numero_abortos", read_only=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CAMPOS CALCULADOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    paciente_info = serializers.SerializerMethodField()
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    semanas_gestacion = serializers.SerializerMethodField()
    semanas_restantes = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()
    trimestre_actual = serializers.SerializerMethodField()
    clasificacion_riesgo = serializers.SerializerMethodField()
    estado_embarazo = serializers.SerializerMethodField()
    imc_pregestacional = serializers.SerializerMethodField()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TRAZABILIDAD - Información del usuario
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    created_by_display = serializers.SerializerMethodField()
    updated_by_display = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Embarazo
        fields = [
            # ✅ CAMPOS REALES DEL MODELO
            "id",
            "uuid",
            "paciente",
            "numero_gesta",
            "numero_para",
            "numero_abortos",
            "numero_cesareas",
            "fecha_ultima_menstruacion",
            "fecha_probable_parto",
            "tipo_embarazo",
            "riesgo_embarazo",
            "estado",
            "notas",
            "medico_responsable",
            "fecha_registro",
            "fecha_modificacion",
            # ✅ CAMPOS ANTROPOMÉTRICOS
            "peso_pregestacional",
            "talla_materna",
            # ✅ TRAZABILIDAD
            "created_by",
            "updated_by",
            "created_by_display",
            "updated_by_display",
            # ✅ ALIAS PARA FRONTEND
            "partos_previos",
            "cesareas_previas",
            "abortos_previos",
            # ✅ CAMPOS CALCULADOS
            "paciente_info",
            "paciente_nombre",
            "edad_gestacional",
            "semanas_gestacion",
            "semanas_restantes",
            "dias_restantes",
            "trimestre_actual",
            "clasificacion_riesgo",
            "estado_embarazo",
            "imc_pregestacional",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "updated_by",
        ]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MÉTODOS PARA CAMPOS CALCULADOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_paciente_info(self, obj):
        """✅ Información completa del paciente"""
        paciente = obj.paciente
        apellido_materno = (
            f" {paciente.apellido_materno}" if paciente.apellido_materno else ""
        )

        # Calcular edad
        edad = None
        if paciente.fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - paciente.fecha_nacimiento.year
            if (hoy.month, hoy.day) < (
                paciente.fecha_nacimiento.month,
                paciente.fecha_nacimiento.day,
            ):
                edad -= 1

        return {
            "id": paciente.id,
            "id_clinico": paciente.id_clinico,
            "nombre_completo": f"{paciente.nombre} {paciente.apellido_paterno}{apellido_materno}",
            "cedula_identidad": paciente.ci if hasattr(paciente, "ci") else None,
            "fecha_nacimiento": paciente.fecha_nacimiento,
            "edad": edad,
            "telefono": paciente.telefono if hasattr(paciente, "telefono") else None,
            "peso_kg": float(paciente.peso_kg)
            if paciente.peso_kg
            else None,  # ✅ AGREGADO
            "altura_cm": float(paciente.altura_cm)
            if paciente.altura_cm
            else None,  # ✅ AGREGADO
            "imc": paciente.imc,  # ✅ AGREGADO - Usa la propiedad calculada del modelo
        }

    def get_paciente_nombre(self, obj):
        """✅ Nombre completo formato estándar"""
        paciente = obj.paciente
        apellido_materno = (
            f" {paciente.apellido_materno}" if paciente.apellido_materno else ""
        )
        return f"{paciente.id_clinico} - {paciente.nombre} {paciente.apellido_paterno}{apellido_materno}"

    def get_edad_gestacional(self, obj):
        """✅ Edad gestacional detallada"""
        if not obj.fecha_ultima_menstruacion:
            return None

        today = date.today()
        diferencia = (today - obj.fecha_ultima_menstruacion).days
        semanas = diferencia // 7
        dias = diferencia % 7

        # Determinar trimestre
        if semanas <= 13:
            trimestre = 1
            trimestre_texto = "Primer Trimestre"
        elif semanas <= 27:
            trimestre = 2
            trimestre_texto = "Segundo Trimestre"
        else:
            trimestre = 3
            trimestre_texto = "Tercer Trimestre"

        return {
            "semanas": semanas,
            "dias": dias,
            "total_dias": diferencia,
            "texto": f"{semanas} semanas + {dias} días",
            "texto_corto": f"{semanas}+{dias}",
            "trimestre": trimestre,
            "trimestre_texto": trimestre_texto,
            "es_pretermino": semanas < 37,
            "es_termino": 37 <= semanas <= 42,
            "es_postermino": semanas > 42,
        }

    def get_semanas_gestacion(self, obj):
        """✅ Formato corto semanas+días"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas}+{dias}"
        return None

    def get_semanas_restantes(self, obj):
        """✅ Semanas hasta FPP"""
        if not obj.fecha_probable_parto:
            return None

        today = date.today()
        if today >= obj.fecha_probable_parto:
            return 0

        diferencia = (obj.fecha_probable_parto - today).days
        semanas = diferencia // 7
        return semanas

    def get_dias_restantes(self, obj):
        """✅ Días exactos hasta FPP"""
        if not obj.fecha_probable_parto:
            return None

        today = date.today()
        if today >= obj.fecha_probable_parto:
            return 0

        return (obj.fecha_probable_parto - today).days

    def get_trimestre_actual(self, obj):
        """✅ Número de trimestre (1, 2 o 3)"""
        if not obj.fecha_ultima_menstruacion:
            return None

        hoy = date.today()
        diferencia = (hoy - obj.fecha_ultima_menstruacion).days
        semanas = diferencia // 7

        if semanas <= 13:
            return 1
        if semanas <= 27:
            return 2
        return 3

    def get_clasificacion_riesgo(self, obj):
        """✅ Texto descriptivo del riesgo"""
        clasificaciones = {
            "bajo": "Riesgo Bajo - Control prenatal estándar",
            "medio": "Riesgo Moderado - Control prenatal frecuente",
            "alto": "Alto Riesgo - Requiere seguimiento especializado",
        }
        return clasificaciones.get(obj.riesgo_embarazo, "No especificado")

    def get_estado_embarazo(self, obj):
        """✅ Texto descriptivo del estado"""
        estados = {
            "activo": "Embarazo Activo",
            "finalizado": "Embarazo Finalizado",
            "perdida": "Pérdida Gestacional",
        }
        return estados.get(obj.estado, obj.estado)

    def get_imc_pregestacional(self, obj):
        """✅ Retorna el IMC pregestacional calculado"""
        return obj.imc_pregestacional  # Usa la propiedad del modelo

    def get_created_by_display(self, obj):
        """✅ TRAZABILIDAD: Información del usuario que creó el registro"""
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "email": obj.created_by.email,
                "nombre_completo": obj.created_by.get_full_name()
                if hasattr(obj.created_by, "get_full_name")
                else obj.created_by.email,
                "fecha": obj.fecha_registro.isoformat() if obj.fecha_registro else None,
            }
        return None

    def get_updated_by_display(self, obj):
        """✅ TRAZABILIDAD: Información del usuario que actualizó el registro"""
        if obj.updated_by:
            return {
                "id": obj.updated_by.id,
                "email": obj.updated_by.email,
                "nombre_completo": obj.updated_by.get_full_name()
                if hasattr(obj.updated_by, "get_full_name")
                else obj.updated_by.email,
                "fecha": obj.fecha_modificacion.isoformat()
                if hasattr(obj, "fecha_modificacion") and obj.fecha_modificacion
                else None,
            }
        return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VALIDACIONES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def validate_paciente(self, value):
        """✅ Validar que el paciente existe"""
        if not Paciente.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("El paciente seleccionado no existe")
        return value

    def validate_numero_gesta(self, value):
        """✅ Validar número de gesta"""
        if value < 1:
            raise serializers.ValidationError("El número de gesta debe ser mayor a 0")
        if value > 20:
            raise serializers.ValidationError(
                "El número de gesta parece incorrecto (máximo 20)",
            )
        return value

    def validate_fecha_ultima_menstruacion(self, value):
        """✅ Validar FUM"""
        if not value:
            raise serializers.ValidationError(
                "La Fecha de Última Menstruación es obligatoria",
            )

        if value > date.today():
            raise serializers.ValidationError("La FUM no puede ser una fecha futura")

        # Validar que no sea muy antigua (máximo 42 semanas)
        diferencia_dias = (date.today() - value).days
        if diferencia_dias > 294:  # 42 semanas
            raise serializers.ValidationError(
                f"La FUM es muy antigua ({diferencia_dias} días). "
                "Si el embarazo ya finalizó, actualice el estado.",
            )

        return value

    def validate(self, attrs):
        """✅ Validaciones generales"""
        # 1. Calcular FPP automáticamente (Regla de Naegele: FUM + 280 días)
        if "fecha_ultima_menstruacion" in attrs and not attrs.get("fecha_probable_parto"):
            fum = attrs["fecha_ultima_menstruacion"]
            attrs["fecha_probable_parto"] = fum + timedelta(days=280)

        # 2. ✅ VALIDACIÓN MEJORADA: Prevenir embarazos activos duplicados
        paciente = attrs.get("paciente") or (
            self.instance.paciente if self.instance else None
        )
        nuevo_estado = attrs.get("estado") or (
            self.instance.estado if self.instance else "activo"
        )

        if paciente and nuevo_estado == "activo":
            # Buscar otros embarazos activos del mismo paciente
            query = Embarazo.objects.filter(paciente=paciente, estado="activo")

            # Si estamos actualizando, excluir el embarazo actual
            if self.instance:
                query = query.exclude(id=self.instance.id)

            if query.exists():
                raise serializers.ValidationError(
                    {
                        "estado": f"❌ Esta paciente ya tiene un embarazo activo (ID: {query.first().id}). "
                        "Solo puede haber UN embarazo activo por paciente. "
                        "Finalice el embarazo anterior antes de crear/activar otro.",
                    },
                )

        # 3. Validar tipo de embarazo
        tipo = attrs.get("tipo_embarazo", "simple")
        if tipo not in ["simple", "gemelar", "multiple"]:
            raise serializers.ValidationError(
                {
                    "tipo_embarazo": "Tipo de embarazo inválido. Opciones: simple, gemelar, multiple",
                },
            )

        # 4. Validar riesgo
        riesgo = attrs.get("riesgo_embarazo", "bajo")
        if riesgo not in ["bajo", "medio", "alto"]:
            raise serializers.ValidationError(
                {
                    "riesgo_embarazo": "Nivel de riesgo inválido. Opciones: bajo, medio, alto",
                },
            )

        # 5. Clasificación automática de riesgo si es embarazo múltiple
        if tipo in ["gemelar", "multiple"] and riesgo == "bajo":
            attrs["riesgo_embarazo"] = "alto"

        return attrs

    def update(self, instance, validated_data):
        """✅ Actualizar con recálculo de FPP"""
        # Recalcular FPP si se actualiza FUM
        if (
            "fecha_ultima_menstruacion" in validated_data
            and "fecha_probable_parto" not in validated_data
        ):
            validated_data["fecha_probable_parto"] = validated_data[
                "fecha_ultima_menstruacion"
            ] + timedelta(days=280)

        return super().update(instance, validated_data)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SERIALIZERS ADICIONALES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class EmbarazoListSerializer(serializers.ModelSerializer):
    """✅ Serializer optimizado para listados - INCLUYE TODOS LOS CAMPOS PARA EDICIÓN"""

    # Alias para compatibilidad con frontend
    partos_previos = serializers.IntegerField(source="numero_para", read_only=True)
    cesareas_previas = serializers.IntegerField(
        source="numero_cesareas", read_only=True,
    )
    abortos_previos = serializers.IntegerField(source="numero_abortos", read_only=True)

    # Campos calculados
    paciente_info = serializers.SerializerMethodField()  # ✅ AGREGADO
    paciente_nombre = serializers.SerializerMethodField()
    semanas_gestacion = serializers.SerializerMethodField()
    trimestre = serializers.SerializerMethodField()
    dias_hasta_fpp = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Embarazo
        fields = [
            "id",
            "uuid",
            "paciente",  # ✅ AGREGADO: ID del paciente necesario para edición
            "paciente_info",  # ✅ AGREGADO: Información completa del paciente
            "paciente_nombre",
            "numero_gesta",
            "numero_para",
            "numero_abortos",
            "numero_cesareas",
            "fecha_ultima_menstruacion",  # ✅ AGREGADO: CRÍTICO para edición
            "fecha_probable_parto",
            "tipo_embarazo",
            "riesgo_embarazo",
            "estado",
            "notas",  # ✅ AGREGADO: Para edición
            "medico_responsable",  # ✅ AGREGADO: Para edición
            "peso_pregestacional",  # ✅ AGREGADO: Para edición
            "talla_materna",  # ✅ AGREGADO: Para edición
            "semanas_gestacion",
            "trimestre",
            "dias_hasta_fpp",
            "fecha_registro",
            # Alias para frontend
            "partos_previos",
            "cesareas_previas",
            "abortos_previos",
        ]

    def get_paciente_info(self, obj):
        """✅ Información completa del paciente"""
        paciente = obj.paciente
        apellido_materno = (
            f" {paciente.apellido_materno}" if paciente.apellido_materno else ""
        )

        # Calcular edad
        edad = None
        if paciente.fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - paciente.fecha_nacimiento.year
            if (hoy.month, hoy.day) < (
                paciente.fecha_nacimiento.month,
                paciente.fecha_nacimiento.day,
            ):
                edad -= 1

        return {
            "id": paciente.id,
            "id_clinico": paciente.id_clinico,
            "nombre": paciente.nombre,  # ✅ AGREGADO
            "apellido_paterno": paciente.apellido_paterno,  # ✅ AGREGADO
            "apellido_materno": paciente.apellido_materno,  # ✅ AGREGADO
            "nombre_completo": f"{paciente.nombre} {paciente.apellido_paterno}{apellido_materno}",
            "cedula_identidad": paciente.ci if hasattr(paciente, "ci") else None,
            "fecha_nacimiento": paciente.fecha_nacimiento,
            "edad": edad,
            "telefono": paciente.telefono if hasattr(paciente, "telefono") else None,
            "peso_kg": float(paciente.peso_kg) if paciente.peso_kg else None,
            "altura_cm": float(paciente.altura_cm) if paciente.altura_cm else None,
            "imc": paciente.imc,
        }

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        paciente = obj.paciente
        apellido_materno = (
            f" {paciente.apellido_materno}" if paciente.apellido_materno else ""
        )
        return f"{paciente.id_clinico} - {paciente.nombre} {paciente.apellido_paterno}{apellido_materno}"

    def get_semanas_gestacion(self, obj):
        """Get semanas gestacion"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas}+{dias}"
        return None

    def get_trimestre(self, obj):
        """Get trimestre"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7

            if semanas <= 13:
                return 1
            if semanas <= 27:
                return 2
            return 3
        return None

    def get_dias_hasta_fpp(self, obj):
        """Get dias hasta fpp"""
        if obj.fecha_probable_parto:
            hoy = date.today()
            if hoy < obj.fecha_probable_parto:
                return (obj.fecha_probable_parto - hoy).days
            return 0
        return None


class EmbarazoCreateUpdateSerializer(serializers.ModelSerializer):
    """✅ Serializer para crear/actualizar - SOLO CAMPOS EDITABLES"""

    # ✅ ALIAS PARA COMPATIBILIDAD CON FRONTEND (acepta ambos nombres)
    partos_previos = serializers.IntegerField(
        source="numero_para", required=False, allow_null=True,
    )
    cesareas_previas = serializers.IntegerField(
        source="numero_cesareas", required=False, allow_null=True,
    )
    abortos_previos = serializers.IntegerField(
        source="numero_abortos", required=False, allow_null=True,
    )

    class Meta:
        """Meta"""
        model = Embarazo
        fields = [
            "paciente",
            "numero_gesta",
            "numero_para",
            "numero_abortos",
            "numero_cesareas",
            "fecha_ultima_menstruacion",
            "fecha_probable_parto",
            "tipo_embarazo",
            "riesgo_embarazo",
            "estado",
            "notas",
            "medico_responsable",
            # ✅ CAMPOS ANTROPOMÉTRICOS
            "peso_pregestacional",
            "talla_materna",
            # ✅ ALIAS PARA FRONTEND
            "partos_previos",
            "cesareas_previas",
            "abortos_previos",
        ]

    def validate(self, attrs):
        """Reutilizar validaciones del serializer principal"""
        # ✅ FIX: Pasar self.instance para que la validación sepa si es CREATE o UPDATE
        serializer = EmbarazoSerializer(instance=self.instance)
        return serializer.validate(attrs)


class EmbarazoResumenSerializer(serializers.ModelSerializer):
    """✅ Serializer para resúmenes ejecutivos"""

    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional_texto = serializers.SerializerMethodField()
    estado_texto = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Embarazo
        fields = [
            "id",
            "paciente_nombre",
            "numero_gesta",
            "edad_gestacional_texto",
            "riesgo_embarazo",
            "estado",
            "estado_texto",
            "fecha_probable_parto",
        ]

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno}"

    def get_edad_gestacional_texto(self, obj):
        """Get edad gestacional texto"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas} semanas + {dias} días"
        return "No calculado"

    def get_estado_texto(self, obj):
        """Get estado texto"""
        estados = {
            "activo": "Activo",
            "finalizado": "Finalizado",
            "perdida": "Pérdida",
        }
        return estados.get(obj.estado, obj.estado)
