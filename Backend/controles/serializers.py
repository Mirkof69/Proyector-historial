"""Serializers module."""
from datetime import datetime

from rest_framework import serializers

from .models import ControlPrenatal

# from embarazos.models import Embarazo  # REMOVED
# from pacientes.models import Paciente  # REMOVED


class ControlPrenatalListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados rápidos"""

    id_clinico = serializers.SerializerMethodField()  # ✅ AGREGADO
    paciente_nombre = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()
    num_alertas = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ControlPrenatal
        fields = [
            "id",
            "embarazo_id",
            "embarazo_info",
            "id_clinico",  # ✅ AGREGADO
            "paciente_nombre",
            "numero_control",
            "fecha_control",
            "edad_gestacional",
            "presion_arterial",
            "frecuencia_cardiaca_fetal",
            "tiene_alertas",
            "num_alertas",
        ]

    def get_id_clinico(self, obj):
        """Obtener ID clínico del paciente"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                return obj.embarazo.paciente.id_clinico
            if obj.paciente:
                return obj.paciente.id_clinico
            return None
        except Exception:
            return None

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                return f"{paciente.nombre} {paciente.apellido_paterno}"
            if obj.paciente:
                return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno}"
            return "Sin nombre"
        except Exception:
            return None

    def get_embarazo_info(self, obj):
        """Get embarazo info"""
        try:
            if obj.embarazo:
                return {
                    "id": obj.embarazo.id,
                    "numero_gesta": getattr(obj.embarazo, "numero_gesta", None),
                    "riesgo": getattr(obj.embarazo, "riesgo_embarazo", None),
                    "estado": obj.embarazo.estado,
                }
            return None
        except Exception:
            return None

    def get_edad_gestacional(self, obj):
        """Get edad gestacional"""
        return f"{obj.semanas_gestacion}+{obj.dias_gestacion or 0}"

    def get_presion_arterial(self, obj):
        """Get presion arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None

    def get_tiene_alertas(self, obj):
        """Verificar si tiene alertas críticas usando métodos del modelo"""
        return obj.tiene_alertas_criticas()

    def get_num_alertas(self, obj):
        """Contar número de alertas"""
        count = 0
        if obj.tiene_hipertension() or obj.tiene_prehipertension():
            count += 1
        if obj.fcf_es_anormal():
            count += 1
        if obj.edema in ["severo", "generalizado"]:
            count += 1
        if obj.proteinuria in ["positiva_1", "positiva_2", "positiva_3", "positiva_4"]:
            count += 1
        if obj.movimientos_fetales == "ausentes":
            count += 1
        return count


class ControlPrenatalSerializer(serializers.ModelSerializer):
    """Serializer COMPLETO para visualización detallada de controles prenatales"""

    # ✅ ALIAS PARA COMPATIBILIDAD CON FRONTEND
    edad_gestacional_semanas = serializers.IntegerField(
        source="semanas_gestacion", read_only=True,
    )
    edad_gestacional_dias = serializers.IntegerField(
        source="dias_gestacion", read_only=True,
    )

    # Campos calculados y de lectura
    id_clinico = serializers.SerializerMethodField()  # ✅ AGREGADO
    paciente_nombre = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    imc_actual = serializers.SerializerMethodField()
    clasificacion_imc = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    presion_arterial_media = serializers.SerializerMethodField()
    ganancia_peso = serializers.SerializerMethodField()
    alertas = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()

    # ✅ TRAZABILIDAD - Información del usuario
    created_by_display = serializers.SerializerMethodField()
    modified_by_display = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ControlPrenatal
        fields = [
            "id",
            "embarazo",  # ✅ Usar 'embarazo' (permite escritura) en lugar de embarazo_id
            "embarazo_info",
            "id_clinico",  # ✅ AGREGADO
            "paciente",
            "paciente_nombre",
            "numero_control",
            "fecha_control",
            "semanas_gestacion",
            "dias_gestacion",
            "edad_gestacional",
            # ✅ ALIAS PARA FRONTEND
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "peso_actual",
            "peso_pregestacional",
            "ganancia_peso",
            "talla",
            "imc_actual",
            "clasificacion_imc",
            "presion_arterial_sistolica",
            "presion_arterial_diastolica",
            "presion_arterial",
            "presion_arterial_media",
            "frecuencia_cardiaca",
            "temperatura",
            "altura_uterina",
            "frecuencia_cardiaca_fetal",
            "presentacion_fetal",
            "movimientos_fetales",
            "edema",
            "proteinuria",
            "observaciones",
            "medico_id",
            "fecha_registro",
            # ✅ TRAZABILIDAD
            "created_by",
            "modified_by",
            "created_by_display",
            "modified_by_display",
            "alertas",
            "tiene_alertas",
        ]
        read_only_fields = ["id", "fecha_registro", "created_by", "modified_by"]

    def get_id_clinico(self, obj):
        """Obtener ID clínico del paciente"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                return obj.embarazo.paciente.id_clinico
            if obj.paciente:
                return obj.paciente.id_clinico
            return None
        except Exception:
            return None

    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        try:
            if obj.embarazo and obj.embarazo.paciente:
                paciente = obj.embarazo.paciente
                apellido_materno = (
                    paciente.apellido_materno or ""
                )
                return f"{paciente.nombre} {paciente.apellido_paterno} {apellido_materno}".strip()
            if obj.paciente:
                apellido_materno = (
                    obj.paciente.apellido_materno or ""
                )
                return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno} {apellido_materno}".strip()
            return "Paciente no especificado"
        except Exception:
            return None

    def get_embarazo_info(self, obj):
        """Información adicional del embarazo"""
        try:
            if obj.embarazo:
                embarazo = obj.embarazo
                return {
                    "id": embarazo.id,
                    "paciente_id": embarazo.paciente.id,
                    "paciente_nombre": f"{embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                    "numero_gesta": getattr(embarazo, "numero_gesta", None),
                    "fecha_ultima_menstruacion": str(
                        embarazo.fecha_ultima_menstruacion,
                    ),
                    "fecha_probable_parto": str(embarazo.fecha_probable_parto),
                    "estado": embarazo.estado,
                }
        except Exception:
            pass
        return None

    def get_edad_gestacional(self, obj):
        """✅ Calcular edad gestacional en TIEMPO REAL desde FUM del embarazo"""
        if obj.embarazo and obj.embarazo.fecha_ultima_menstruacion:
            hoy = datetime.now().date()
            fum = obj.embarazo.fecha_ultima_menstruacion
            dias_diferencia = (hoy - fum).days
            semanas = dias_diferencia // 7
            dias = dias_diferencia % 7
            return f"{semanas}+{dias}"

        # Fallback: usar valores guardados si no hay FUM
        dias = obj.dias_gestacion or 0
        return f"{obj.semanas_gestacion}+{dias}"

    def get_imc_actual(self, obj):
        """Calcular IMC actual usando el property del modelo"""
        return obj.imc

    def get_clasificacion_imc(self, obj):
        """Obtener clasificación IMC usando el property del modelo"""
        return obj.clasificacion_imc

    def get_presion_arterial(self, obj):
        """Formatear presión arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None

    def get_presion_arterial_media(self, obj):
        """Calcular PAM usando el property del modelo"""
        return obj.presion_arterial_media

    def get_ganancia_peso(self, obj):
        """Calcular ganancia de peso usando el property del modelo"""
        return obj.ganancia_peso

    def get_alertas(self, obj):
        """Obtener lista detallada de alertas"""
        alertas = []

        # Hipertensión
        if obj.tiene_hipertension():
            alertas.append(
                {
                    "tipo": "hipertension",
                    "nivel": "alto",
                    "mensaje": "Hipertensión detectada",
                    "valor": f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}",
                },
            )
        elif obj.tiene_prehipertension():
            alertas.append(
                {
                    "tipo": "prehipertension",
                    "nivel": "medio",
                    "mensaje": "Prehipertensión detectada",
                    "valor": f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}",
                },
            )

        # FCF anormal
        if obj.fcf_es_anormal():
            alertas.append(
                {
                    "tipo": "fcf_anormal",
                    "nivel": "alto",
                    "mensaje": "Frecuencia cardíaca fetal anormal",
                    "valor": obj.frecuencia_cardiaca_fetal,
                },
            )

        # Edema severo
        if obj.edema in ["severo", "generalizado"]:
            alertas.append(
                {
                    "tipo": "edema_severo",
                    "nivel": "medio",
                    "mensaje": f"Edema {obj.edema}",
                    "valor": obj.edema,
                },
            )

        # Proteinuria
        if obj.proteinuria in ["positiva_1", "positiva_2", "positiva_3", "positiva_4"]:
            alertas.append(
                {
                    "tipo": "proteinuria",
                    "nivel": "alto",
                    "mensaje": "Proteinuria positiva",
                    "valor": obj.proteinuria,
                },
            )

        # Movimientos fetales ausentes
        if obj.movimientos_fetales == "ausentes":
            alertas.append(
                {
                    "tipo": "movimientos_ausentes",
                    "nivel": "alto",
                    "mensaje": "Movimientos fetales ausentes",
                },
            )

        # IMC
        imc = obj.imc
        if imc:
            if imc < 18.5:
                alertas.append(
                    {
                        "tipo": "bajo_peso",
                        "nivel": "medio",
                        "mensaje": "Bajo peso materno",
                        "valor": round(imc, 2),
                    },
                )
            elif imc >= 30:
                alertas.append(
                    {
                        "tipo": "obesidad",
                        "nivel": "medio",
                        "mensaje": "Obesidad materna",
                        "valor": round(imc, 2),
                    },
                )

        # Fiebre
        if obj.temperatura and float(obj.temperatura) >= 38:
            alertas.append(
                {
                    "tipo": "fiebre",
                    "nivel": "alto",
                    "mensaje": f"Fiebre: {obj.temperatura}°C",
                    "valor": float(obj.temperatura),
                },
            )

        return alertas

    def get_tiene_alertas(self, obj):
        """Verificar si tiene alertas críticas"""
        return obj.tiene_alertas_criticas()

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

    def get_modified_by_display(self, obj):
        """✅ TRAZABILIDAD: Información del usuario que modificó el registro"""
        if obj.modified_by:
            return {
                "id": obj.modified_by.id,
                "email": obj.modified_by.email,
                "nombre_completo": obj.modified_by.get_full_name()
                if hasattr(obj.modified_by, "get_full_name")
                else obj.modified_by.email,
                "fecha": obj.fecha_registro.isoformat() if obj.fecha_registro else None,
            }
        return None


class ControlPrenatalCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar controles prenatales"""

    # ✅ ALIAS PARA COMPATIBILIDAD CON FRONTEND (acepta ambos nombres)
    edad_gestacional_semanas = serializers.IntegerField(
        source="semanas_gestacion", required=False, allow_null=False,
    )
    edad_gestacional_dias = serializers.IntegerField(
        source="dias_gestacion", required=False, allow_null=False, default=0,
    )

    # Campos calculados y de lectura
    id_clinico = serializers.SerializerMethodField()  # ✅ AGREGADO
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    imc_actual = serializers.SerializerMethodField()
    clasificacion_imc = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()
    presion_arterial_media = serializers.SerializerMethodField()
    ganancia_peso = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ControlPrenatal
        fields = [
            "id",
            "embarazo",  # ✅ CAMBIADO de embarazo_id a embarazo para permitir escritura
            "embarazo_info",
            "id_clinico",  # ✅ AGREGADO
            "paciente",
            "paciente_nombre",
            "numero_control",
            "fecha_control",
            "semanas_gestacion",
            "dias_gestacion",
            "edad_gestacional",
            # ✅ ALIAS PARA FRONTEND
            "edad_gestacional_semanas",
            "edad_gestacional_dias",
            "peso_actual",
            "peso_pregestacional",
            "ganancia_peso",
            "talla",
            "imc_actual",
            "clasificacion_imc",
            "presion_arterial_sistolica",
            "presion_arterial_diastolica",
            "presion_arterial",
            "presion_arterial_media",
            "frecuencia_cardiaca",
            "temperatura",
            "altura_uterina",
            "frecuencia_cardiaca_fetal",
            "presentacion_fetal",
            "movimientos_fetales",
            "edema",
            "proteinuria",
            "observaciones",
            "medico_id",
            "fecha_registro",
        ]
        read_only_fields = ["id", "fecha_registro"]
        extra_kwargs = {
            "semanas_gestacion": {"required": False},
            "dias_gestacion": {"required": False},
        }

    def get_id_clinico(self, obj):
        """Obtener ID clínico del paciente"""
        try:
            if hasattr(obj, "embarazo") and obj.embarazo and obj.embarazo.paciente:
                return obj.embarazo.paciente.id_clinico
            if obj.paciente:
                return obj.paciente.id_clinico
            return None
        except Exception:
            return None

    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        try:
            if hasattr(obj, "embarazo") and obj.embarazo:
                paciente = obj.embarazo.paciente
                apellido_materno = (
                    paciente.apellido_materno
                    if hasattr(paciente, "apellido_materno")
                    else ""
                )
                return f"{paciente.nombre} {paciente.apellido_paterno} {apellido_materno or ''}".strip()
            if obj.paciente:
                apellido_materno = (
                    obj.paciente.apellido_materno
                    if hasattr(obj.paciente, "apellido_materno")
                    else ""
                )
                return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno} {apellido_materno or ''}".strip()
            return "Paciente no especificado"
        except Exception:
            return None

    def get_edad_gestacional(self, obj):
        """✅ Calcular edad gestacional en TIEMPO REAL desde FUM del embarazo"""
        if obj.embarazo and obj.embarazo.fecha_ultima_menstruacion:
            hoy = datetime.now().date()
            fum = obj.embarazo.fecha_ultima_menstruacion
            dias_diferencia = (hoy - fum).days
            semanas = dias_diferencia // 7
            dias = dias_diferencia % 7
            return f"{semanas}+{dias}"

        # Fallback: usar valores guardados si no hay FUM
        dias = obj.dias_gestacion or 0
        return f"{obj.semanas_gestacion}+{dias}"

    def get_imc_actual(self, obj):
        """Calcular IMC actual usando el property del modelo"""
        return obj.imc

    def get_clasificacion_imc(self, obj):
        """Obtener clasificación IMC usando el property del modelo"""
        return obj.clasificacion_imc

    def get_presion_arterial(self, obj):
        """Formatear presión arterial"""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            return f"{obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica}"
        return None

    def get_presion_arterial_media(self, obj):
        """Calcular PAM usando el property del modelo"""
        return obj.presion_arterial_media

    def get_ganancia_peso(self, obj):
        """Calcular ganancia de peso usando el property del modelo"""
        return obj.ganancia_peso

    def get_embarazo_info(self, obj):
        """Información adicional del embarazo"""
        try:
            if hasattr(obj, "embarazo") and obj.embarazo:
                embarazo = obj.embarazo
                return {
                    "id": embarazo.id,
                    "paciente_id": embarazo.paciente.id,
                    "paciente_nombre": f"{embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                    "numero_gesta": getattr(embarazo, "numero_gesta", None),
                    "fecha_ultima_menstruacion": str(
                        embarazo.fecha_ultima_menstruacion,
                    ),
                    "fecha_probable_parto": str(embarazo.fecha_probable_parto),
                    "estado": embarazo.estado,
                }
        except Exception:
            pass
        return None

    def validate(self, attrs):
        """Validaciones adicionales y completas"""
        # Validar que la PA sistólica sea mayor que la diastólica
        sistolica = attrs.get("presion_arterial_sistolica")
        diastolica = attrs.get("presion_arterial_diastolica")

        if sistolica and diastolica:
            if sistolica <= diastolica:
                raise serializers.ValidationError(
                    {
                        "presion_arterial_sistolica": "La presión sistólica debe ser mayor que la diastólica",
                    },
                )

        # ✅ VALIDACIÓN INTELIGENTE: FCF según semanas de gestación
        semanas = attrs.get("semanas_gestacion", 0)

        if "frecuencia_cardiaca_fetal" in attrs:
            fcf = attrs["frecuencia_cardiaca_fetal"]

            # Si tiene menos de 6 semanas y envía FCF, dar advertencia (pero permitir)
            if fcf and semanas < 6:
                import warnings

                warnings.warn(
                    f"FCF detectada con {semanas} semanas. Normalmente no es detectable antes de 6 semanas.",
                    UserWarning,
                )

            # Validar rango de FCF solo si se proporciona
            if fcf and (fcf < 90 or fcf > 180):
                raise serializers.ValidationError(
                    {"frecuencia_cardiaca_fetal": "FCF debe estar entre 90 y 180 lpm"},
                )

        # ✅ VALIDACIÓN INTELIGENTE: Presentación fetal según semanas
        if "presentacion_fetal" in attrs:
            presentacion = attrs["presentacion_fetal"]

            # Si tiene menos de 12 semanas y envía presentación, dar advertencia
            if presentacion and presentacion != "no_evaluable" and semanas < 12:

                warnings.warn(
                    f"Presentación fetal registrada con {semanas} semanas. Normalmente no es evaluable antes de 12 semanas.",
                    UserWarning,
                )

        # Validar semanas de gestación
        if "semanas_gestacion" in attrs:
            if semanas < 0 or semanas > 42:
                raise serializers.ValidationError(
                    {"semanas_gestacion": "Las semanas deben estar entre 0 y 42"},
                )

        # Validar días de gestación
        if "dias_gestacion" in attrs and attrs["dias_gestacion"] is not None:
            dias = attrs["dias_gestacion"]
            if dias < 0 or dias > 6:
                raise serializers.ValidationError(
                    {"dias_gestacion": "Los días deben estar entre 0 y 6"},
                )

        # Validar embarazo activo
        if "embarazo" in attrs:
            try:
                from embarazos.models import Embarazo  # Deferred import

                if isinstance(attrs["embarazo"], Embarazo):
                    embarazo = attrs["embarazo"]
                else:
                    embarazo = Embarazo.objects.get(id=attrs["embarazo"])

                if embarazo.estado != "activo":
                    raise serializers.ValidationError(
                        {
                            "embarazo": "El embarazo debe estar activo para registrar controles",
                        },
                    )

                # Establecer automáticamente el paciente si no se proporciona
                if "paciente" not in attrs or not attrs["paciente"]:
                    attrs["paciente"] = embarazo.paciente

            except Embarazo.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"embarazo": "El embarazo especificado no existe"},
                ) from exc
            except Exception as e:
                raise serializers.ValidationError(
                    {"embarazo": f"Error al validar embarazo: {e!s}"},
                ) from e

        return attrs

    def to_representation(self, instance):
        """Personalizar la representación de salida con alertas"""
        representation = super().to_representation(instance)

        # Formatear fechas
        if representation.get("fecha_control"):

            try:
                fecha = datetime.strptime(
                    str(representation["fecha_control"]), "%Y-%m-%d",
                )
                representation["fecha_control_formatted"] = fecha.strftime("%d/%m/%Y")
            except Exception:
                pass

        # Agregar estado de alertas usando los métodos del modelo
        alertas = []

        if instance.tiene_hipertension():
            alertas.append("hipertension")
        elif instance.tiene_prehipertension():
            alertas.append("prehipertension")

        if instance.fcf_es_anormal():
            alertas.append("fcf_anormal")

        if instance.edema in ["severo", "generalizado"]:
            alertas.append("edema_severo")

        if instance.proteinuria in [
            "positiva_1",
            "positiva_2",
            "positiva_3",
            "positiva_4",
        ]:
            alertas.append("proteinuria_positiva")

        if instance.movimientos_fetales == "ausentes":
            alertas.append("movimientos_ausentes")

        # Alertas de IMC
        imc = instance.imc
        if imc:
            if imc < 18.5:
                alertas.append("bajo_peso")
            elif imc >= 30:
                alertas.append("obesidad")

        # Alerta de temperatura
        if instance.temperatura and float(instance.temperatura) >= 38:
            alertas.append("fiebre")

        representation["alertas"] = alertas
        representation["tiene_alertas"] = len(alertas) > 0

        return representation
