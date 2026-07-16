"""Serializers module."""
from django.utils import timezone
from rest_framework import serializers

from .models import (
    ApgarScoreDetallado,
    ComplicacionParto,
    Parto,
    PartogramaRegistro,
    RecienNacido,
)


class PartogramaRegistroSerializer(serializers.ModelSerializer):
    """Serializer para registros de partograma"""

    # Campos calculados
    presion_arterial = serializers.SerializerMethodField()
    evaluacion_fcf = serializers.SerializerMethodField()
    evaluacion_contracciones = serializers.SerializerMethodField()
    alertas_activas = serializers.SerializerMethodField()
    resumen_registro = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = PartogramaRegistro
        fields = [
            "id",
            "parto",
            "hora_registro",
            "horas_trabajo_parto",
            "dilatacion_cervical",
            "borramiento_cervical",
            "estacion_fetal",
            "contracciones_10min",
            "duracion_contracciones",
            "intensidad_contracciones",
            "fcf_baseline",
            "variabilidad_fcf",
            "desaceleraciones",
            "presion_arterial_sistolica",
            "presion_arterial_diastolica",
            "temperatura",
            "pulso_materno",
            "oxitocina_dosis",
            "observaciones",
            "alerta_fcf_anormal",
            "alerta_progreso_lento",
            "alerta_signos_vitales",
            "registrado_por_id",
            "fecha_registro",
            # Campos calculados
            "presion_arterial",
            "evaluacion_fcf",
            "evaluacion_contracciones",
            "alertas_activas",
            "resumen_registro",
        ]
        read_only_fields = [
            "id",
            "fecha_registro",
            "alerta_fcf_anormal",
            "alerta_progreso_lento",
            "alerta_signos_vitales",
        ]

    def get_presion_arterial(self, obj):
        """Get presion arterial"""
        return obj.get_presion_arterial()

    def get_evaluacion_fcf(self, obj):
        """Get evaluacion fcf"""
        return obj.get_evaluacion_fcf()

    def get_evaluacion_contracciones(self, obj):
        """Get evaluacion contracciones"""
        return obj.get_evaluacion_contracciones()

    def get_alertas_activas(self, obj):
        """Get alertas activas"""
        return obj.get_alertas_activas()

    def get_resumen_registro(self, obj):
        """Get resumen registro"""
        return obj.get_resumen_registro()


class RecienNacidoSerializer(serializers.ModelSerializer):
    """Serializer para recién nacidos"""

    # Campos calculados
    clasificacion_peso = serializers.SerializerMethodField()
    evaluacion_apgar = serializers.SerializerMethodField()
    evaluacion_estado_general = serializers.SerializerMethodField()
    resumen_completo = serializers.SerializerMethodField()
    parto_numero = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = RecienNacido
        fields = [
            "id",
            "parto",
            "numero_gemelo",
            "fecha_nacimiento",
            "sexo",
            "estado_nacimiento",
            "peso_nacimiento",
            "talla_nacimiento",
            "perimetro_cefalico",
            "apgar_1_minuto",
            "apgar_5_minutos",
            "apgar_10_minutos",
            "requirio_reanimacion",
            "tipo_reanimacion",
            "malformaciones_congenitas",
            "descripcion_malformaciones",
            "destino_rn",
            "llanto_inmediato",
            "respiracion_espontanea",
            "tono_muscular_normal",
            "observaciones_rn",
            "fecha_registro",
            "fecha_modificacion",
            # Campos calculados
            "clasificacion_peso",
            "evaluacion_apgar",
            "evaluacion_estado_general",
            "resumen_completo",
            "parto_numero",
        ]
        read_only_fields = [
            "id",
            "fecha_registro",
            "fecha_modificacion",
        ]

    def get_clasificacion_peso(self, obj):
        """Get clasificacion peso"""
        return obj.get_clasificacion_peso()

    def get_evaluacion_apgar(self, obj):
        """Get evaluacion apgar"""
        return obj.get_evaluacion_apgar()

    def get_evaluacion_estado_general(self, obj):
        """Get evaluacion estado general"""
        return obj.get_evaluacion_estado_general()

    def get_resumen_completo(self, obj):
        """Get resumen completo"""
        return obj.get_resumen_completo()

    def get_parto_numero(self, obj):
        """Get parto numero"""
        return obj.parto.numero_parto

    def validate_peso_nacimiento(self, value):
        """Validar peso del recién nacido"""
        if value < 300:
            raise serializers.ValidationError("El peso debe ser mayor a 300g")
        if value > 6000:
            raise serializers.ValidationError("El peso debe ser menor a 6000g")
        return value

    def validate_apgar_5_minutos(self, value):
        """Validar Apgar a los 5 minutos"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("El Apgar debe estar entre 0 y 10")
        return value

    def validate(self, attrs):
        """Validaciones generales"""
        apgar_1 = attrs.get("apgar_1_minuto")
        apgar_5 = attrs.get("apgar_5_minutos")

        if apgar_1 and apgar_5 and apgar_1 > apgar_5 + 2:
            raise serializers.ValidationError(
                "Es inusual que el Apgar a 1 minuto sea mucho mayor que el de 5 minutos",
            )

        return attrs


class ComplicacionPartoSerializer(serializers.ModelSerializer):
    """Serializer para complicaciones del parto"""

    # Información de relaciones
    parto_numero = serializers.SerializerMethodField()
    medico_responsable_info = serializers.SerializerMethodField()

    # Campos calculados
    icono_severidad = serializers.SerializerMethodField()
    resumen = serializers.SerializerMethodField()
    tipo_display = serializers.SerializerMethodField()
    severidad_display = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ComplicacionParto
        fields = [
            "id",
            "parto",
            "parto_numero",
            "tipo_complicacion",
            "tipo_display",
            "severidad",
            "severidad_display",
            "momento_deteccion",
            "descripcion_detallada",
            "tratamiento_realizado",
            "medicamentos_utilizados",
            "resolucion_complicacion",
            "requirio_cirugia",
            "tipo_cirugia",
            "medico_responsable",
            "medico_responsable_info",
            "observaciones",
            "fecha_registro",
            "fecha_modificacion",
            # Campos calculados
            "icono_severidad",
            "resumen",
        ]
        read_only_fields = ["id", "fecha_registro", "fecha_modificacion"]

    def get_parto_numero(self, obj):
        """Get parto numero"""
        return obj.parto.numero_parto if obj.parto else None

    def get_medico_responsable_info(self, obj):
        """Get medico responsable info"""
        if not obj.medico_responsable:
            return None
        return {
            "id": obj.medico_responsable.id,
            "nombre": obj.medico_responsable.nombre,
            "email": obj.medico_responsable.email,
        }

    def get_icono_severidad(self, obj):
        """Get icono severidad"""
        return obj.get_icono_severidad()

    def get_resumen(self, obj):
        """Get resumen"""
        return obj.get_resumen()

    def get_tipo_display(self, obj):
        """Get tipo display"""
        return obj.get_tipo_complicacion_display()

    def get_severidad_display(self, obj):
        """Get severidad display"""
        return obj.get_severidad_display()

    def validate(self, attrs):
        """Validaciones"""
        requirio_cirugia = attrs.get("requirio_cirugia")
        tipo_cirugia = attrs.get("tipo_cirugia")

        if requirio_cirugia and not tipo_cirugia:
            raise serializers.ValidationError(
                {"tipo_cirugia": "Si requirió cirugía, debe especificar el tipo"},
            )

        return attrs


class ApgarScoreDetalladoSerializer(serializers.ModelSerializer):
    """Serializer para Apgar Score Detallado"""

    # Información del recién nacido
    recien_nacido_info = serializers.SerializerMethodField()
    evaluador_info = serializers.SerializerMethodField()

    # Campos calculados
    score_total = serializers.ReadOnlyField()
    clasificacion = serializers.SerializerMethodField()
    desglose_componentes = serializers.SerializerMethodField()
    componentes_problematicos = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ApgarScoreDetallado
        fields = [
            "id",
            "recien_nacido",
            "recien_nacido_info",
            "minuto_evaluacion",
            "frecuencia_cardiaca",
            "esfuerzo_respiratorio",
            "tono_muscular",
            "irritabilidad_refleja",
            "coloracion",
            "observaciones_evaluador",
            "evaluador",
            "evaluador_info",
            "fecha_registro",
            # Campos calculados
            "score_total",
            "clasificacion",
            "desglose_componentes",
            "componentes_problematicos",
        ]
        read_only_fields = ["id", "fecha_registro", "score_total"]

    def get_recien_nacido_info(self, obj):
        """Get recien nacido info"""
        return {
            "id": obj.recien_nacido.id,
            "peso": obj.recien_nacido.peso_nacimiento,
            "sexo": obj.recien_nacido.get_sexo_display(),
            "parto_numero": obj.recien_nacido.parto.numero_parto,
        }

    def get_evaluador_info(self, obj):
        """Get evaluador info"""
        if not obj.evaluador:
            return None
        return {
            "id": obj.evaluador.id,
            "nombre": obj.evaluador.nombre,
        }

    def get_clasificacion(self, obj):
        """Get clasificacion"""
        return obj.get_clasificacion()

    def get_desglose_componentes(self, obj):
        """Get desglose componentes"""
        return obj.get_desglose_componentes()

    def get_componentes_problematicos(self, obj):
        """Get componentes problematicos"""
        return obj.get_componentes_problematicos()

    def validate(self, attrs):
        """Validaciones"""
        # Verificar que no se duplique evaluación en el mismo minuto
        recien_nacido = attrs.get("recien_nacido")
        minuto = attrs.get("minuto_evaluacion")

        if recien_nacido and minuto:
            exists = ApgarScoreDetallado.objects.filter(
                recien_nacido=recien_nacido, minuto_evaluacion=minuto,
            ).exists()

            if self.instance:
                exists = (
                    exists
                    and ApgarScoreDetallado.objects.filter(
                        recien_nacido=recien_nacido, minuto_evaluacion=minuto,
                    )
                    .exclude(pk=self.instance.pk)
                    .exists()
                )

            if exists:
                raise serializers.ValidationError(
                    f"Ya existe una evaluación Apgar para el minuto {minuto} de este recién nacido",
                )

        return attrs


class PartoSerializer(serializers.ModelSerializer):
    """✅ Serializer COMPLETO para partos con ForeignKey + COMPATIBILIDAD FRONTEND
    """

    #  RELACIONES FOREIGNKEY - Información expandida con SerializerMethodField
    paciente_info = serializers.SerializerMethodField()
    embarazo_info = serializers.SerializerMethodField()
    medico_responsable_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    modified_by_info = serializers.SerializerMethodField()

    # Relaciones anidadas
    recien_nacidos = RecienNacidoSerializer(many=True, read_only=True)
    partograma = PartogramaRegistroSerializer(many=True, read_only=True)
    complicaciones = ComplicacionPartoSerializer(many=True, read_only=True)

    #  CAMPOS DE COMPATIBILIDAD FRONTEND (aliases para nombres diferentes)
    # Estos campos permiten que el frontend use los nombres que está acostumbrado
    fecha_hora_parto = serializers.DateTimeField(
        source="fecha_parto", allow_null=True, required=False,
    )
    semanas_gestacion = (
        serializers.SerializerMethodField()
    )  # Extraído de edad_gestacional_parto
    dias_gestacion = (
        serializers.SerializerMethodField()
    )  # Extraído de edad_gestacional_parto
    via_parto = serializers.CharField(source="tipo_parto", required=False)  # Alias
    inicio_trabajo_parto = serializers.DateTimeField(
        source="fecha_inicio_trabajo_parto", allow_null=True, required=False,
    )
    ruptura_membranas = serializers.CharField(
        source="estado_membranas", required=False, allow_null=True, allow_blank=True,
    )
    liquido_amniotico_caracteristicas = serializers.CharField(
        source="caracteristicas_liquido",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    alumbramiento = serializers.CharField(
        source="tipo_alumbramiento", required=False, allow_null=True, allow_blank=True,
    )
    # ✅ NUEVOS ALIAS PARA COMPATIBILIDAD FRONTEND
    hora_ruptura_membranas = serializers.DateTimeField(
        source="hora_rotura_membranas", allow_null=True, required=False,
    )  # Frontend usa "ruptura"
    grado_desgarro = serializers.CharField(
        source="grado_desgarros", required=False, allow_blank=True, allow_null=True,
    )  # Frontend usa singular
    perimetro_cefalico = serializers.SerializerMethodField()  # Del recién nacido
    perimetro_toracico = serializers.SerializerMethodField()  # Del recién nacido

    # Campos calculados
    evaluacion_perdida_sanguinea = serializers.SerializerMethodField()
    estado_parto = serializers.SerializerMethodField()
    resumen_parto = serializers.SerializerMethodField()
    complicaciones_totales = serializers.SerializerMethodField()
    duracion_trabajo_parto_calculada = serializers.SerializerMethodField()

    # ✅ NUEVOS CAMPOS: Sistema de alertas médicas
    alertas_parto = serializers.SerializerMethodField()
    tiene_alertas = serializers.SerializerMethodField()
    tiene_alertas_criticas = serializers.SerializerMethodField()
    alertas_criticas = serializers.SerializerMethodField()
    alertas_moderadas = serializers.SerializerMethodField()
    tipo_parto_segun_edad = serializers.SerializerMethodField()
    recomendaciones_por_edad = serializers.SerializerMethodField()

    # Estadísticas relacionadas
    total_recien_nacidos = serializers.SerializerMethodField()
    total_registros_partograma = serializers.SerializerMethodField()
    total_complicaciones = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Parto
        fields = [
            "id",
            #  FOREIGNKEY FIELDS
            "paciente",
            "embarazo",
            "medico_responsable",
            "paciente_info",
            "embarazo_info",
            "medico_responsable_info",
            "numero_parto",
            "fecha_ingreso",
            "fecha_inicio_trabajo_parto",
            "fecha_parto",
            "edad_gestacional_parto",
            "tipo_parto",
            "presentacion_fetal",
            "posicion_fetal",
            "estado_membranas",
            "hora_rotura_membranas",
            "caracteristicas_liquido",
            "duracion_trabajo_parto_horas",
            "duracion_periodo_expulsivo_minutos",
            "analgesia_utilizada",
            "tipo_analgesia",
            "episiotomia",
            "tipo_episiotomia",
            "desgarros",
            "grado_desgarros",
            "tipo_alumbramiento",
            "placenta_completa",
            "peso_placenta",
            "perdida_sanguinea_estimada",
            "hemorragia_postparto",
            "complicaciones_maternas",
            "oxitocina_utilizada",
            "dosis_oxitocina",
            "otros_medicamentos",
            "observaciones_parto",
            "indicaciones_cesarea",
            "parto_finalizado",
            "trabajo_parto_espontaneo",
            "induccion_parto",
            "metodo_induccion",
            "monitoreo_fetal_continuo",
            # ✅ CAMPOS DE PROTOCOLO DE ABORTO
            "tipo_aborto",
            "metodo_evacuacion",
            "apoyo_psicologico_realizado",
            "protocolo_duelo_aplicado",
            "observaciones_aborto",
            "fecha_registro",
            "fecha_modificacion",
            # Auditoría
            "created_by",
            "modified_by",
            "created_by_info",
            "modified_by_info",
            # ✅ CAMPOS DE COMPATIBILIDAD FRONTEND (aliases)
            "fecha_hora_parto",  # → fecha_parto
            "semanas_gestacion",  # Extraído de edad_gestacional_parto
            "dias_gestacion",  # Extraído de edad_gestacional_parto
            "via_parto",  # → tipo_parto
            "inicio_trabajo_parto",  # → fecha_inicio_trabajo_parto
            "ruptura_membranas",  # → estado_membranas
            "liquido_amniotico_caracteristicas",  # → caracteristicas_liquido
            "alumbramiento",  # → tipo_alumbramiento
            # ✅ NUEVOS ALIAS FRONTEND
            "hora_ruptura_membranas",  # → hora_rotura_membranas
            "grado_desgarro",  # → grado_desgarros
            "perimetro_cefalico",  # Del recién nacido
            "perimetro_toracico",  # Del recién nacido
            # Campos de escritura para recién nacido
            "sexo_bebe",
            "peso_bebe",
            "talla_bebe",
            "apgar_1min",
            "apgar_5min",
            # Relaciones anidadas
            "recien_nacidos",
            "partograma",
            "complicaciones",
            # Campos calculados
            "evaluacion_perdida_sanguinea",
            "estado_parto",
            "resumen_parto",
            "complicaciones_totales",
            "duracion_trabajo_parto_calculada",
            # ✅ NUEVOS: Sistema de alertas médicas
            "alertas_parto",
            "tiene_alertas",
            "tiene_alertas_criticas",
            "alertas_criticas",
            "alertas_moderadas",
            "tipo_parto_segun_edad",
            "recomendaciones_por_edad",
            # Estadísticas
            "total_recien_nacidos",
            "total_registros_partograma",
            "total_complicaciones",
        ]
        read_only_fields = [
            "id",
            "numero_parto",
            "fecha_registro",
            "fecha_modificacion",
            "created_by",
            "modified_by",
        ]

    # MÉTODOS PARA FOREIGNKEY INFO
    def get_paciente_info(self, obj):
        """Obtiene información del paciente"""
        if not obj.paciente:
            return None
        return {
            "id": obj.paciente.id,
            "nombre": obj.paciente.nombre,
            "apellido_paterno": obj.paciente.apellido_paterno,
            "apellido_materno": obj.paciente.apellido_materno,
            "nombre_completo": f"{obj.paciente.nombre} {obj.paciente.apellido_paterno} {obj.paciente.apellido_materno}".strip(),
            "id_clinico": obj.paciente.id_clinico,
            "cedula_identidad": obj.paciente.ci,  # ✅ Agregar CI
        }

    def get_embarazo_info(self, obj):
        """Obtiene información del embarazo"""
        if not obj.embarazo:
            return None
        return {
            "id": obj.embarazo.id,
            "numero_gesta": obj.embarazo.numero_gesta,
            "numero_para": obj.embarazo.numero_para,
            "numero_abortos": obj.embarazo.numero_abortos,
            "numero_cesareas": obj.embarazo.numero_cesareas,
        }

    def get_medico_responsable_info(self, obj):
        """Obtiene información del médico responsable"""
        if not obj.medico_responsable:
            return None
        return {
            "id": obj.medico_responsable.id,
            "nombre": obj.medico_responsable.nombre,
            "email": obj.medico_responsable.email,
        }

    def get_created_by_info(self, obj):
        """Obtiene información del usuario que creó el parto"""
        if not obj.created_by:
            return None
        return {
            "id": obj.created_by.id,
            "nombre": obj.created_by.nombre,
            "email": obj.created_by.email,
        }

    def get_modified_by_info(self, obj):
        """Obtiene información del usuario que modificó el parto"""
        if not obj.modified_by:
            return None
        return {
            "id": obj.modified_by.id,
            "nombre": obj.modified_by.nombre,
            "email": obj.modified_by.email,
        }

    # MÉTODOS PARA CAMPOS DE COMPATIBILIDAD FRONTEND
    def get_semanas_gestacion(self, obj):
        """Extrae semanas de edad_gestacional_parto (formato: 39+2)"""
        if not obj.edad_gestacional_parto:
            return None
        try:
            return int(obj.edad_gestacional_parto.split("+")[0])
        except (ValueError, IndexError):
            return None

    def get_dias_gestacion(self, obj):
        """Extrae días de edad_gestacional_parto (formato: 39+2)"""
        if not obj.edad_gestacional_parto or "+" not in obj.edad_gestacional_parto:
            return None
        try:
            return int(obj.edad_gestacional_parto.split("+")[1])
        except (ValueError, IndexError):
            return None

    def get_perimetro_cefalico(self, obj):
        """Obtiene perímetro cefálico del primer recién nacido"""
        rn = obj.recien_nacidos.first()
        return rn.perimetro_cefalico if rn else None

    def get_perimetro_toracico(self, obj):
        """Obtiene perímetro torácico del primer recién nacido"""
        rn = obj.recien_nacidos.first()
        # Nota: si el modelo RecienNacido tiene perimetro_toracico, usar ese campo
        return getattr(rn, "perimetro_toracico", None) if rn else None

    # MÉTODOS CALCULADOS
    def get_evaluacion_perdida_sanguinea(self, obj):
        """Get evaluacion perdida sanguinea"""
        return obj.get_evaluacion_perdida_sanguinea()

    def get_estado_parto(self, obj):
        """Get estado parto"""
        return obj.get_estado_parto()

    def get_resumen_parto(self, obj):
        """Get resumen parto"""
        return obj.get_resumen_parto()

    def get_complicaciones_totales(self, obj):
        """Get complicaciones totales"""
        return obj.get_complicaciones_totales()

    def get_duracion_trabajo_parto_calculada(self, obj):
        """Get duracion trabajo parto calculada"""
        return obj.get_duracion_trabajo_parto_horas()

    # ✅ MÉTODOS PARA SISTEMA DE ALERTAS MÉDICAS

    def get_alertas_parto(self, obj):
        """Devuelve todas las alertas médicas del parto"""
        return obj.alertas_parto

    def get_tiene_alertas(self, obj):
        """Indica si el parto tiene alertas"""
        return obj.tiene_alertas

    def get_tiene_alertas_criticas(self, obj):
        """Indica si el parto tiene alertas críticas"""
        return obj.tiene_alertas_criticas

    def get_alertas_criticas(self, obj):
        """Devuelve solo las alertas críticas"""
        return obj.alertas_criticas

    def get_alertas_moderadas(self, obj):
        """Devuelve solo las alertas moderadas"""
        return obj.alertas_moderadas

    def get_tipo_parto_segun_edad(self, obj):
        """Clasificación del parto según edad gestacional"""
        tipo, descripcion = obj.get_tipo_parto_segun_edad()
        return {"tipo": tipo, "descripcion": descripcion}

    def get_recomendaciones_por_edad(self, obj):
        """Devuelve recomendaciones por edad gestacional"""
        return obj.recomendaciones_por_edad

    def get_total_recien_nacidos(self, obj):
        """Get total recien nacidos"""
        return obj.recien_nacidos.count()

    def get_total_registros_partograma(self, obj):
        """Get total registros partograma"""
        return obj.partograma.count()

    def get_total_complicaciones(self, obj):
        """Get total complicaciones"""
        return obj.complicaciones.count()

    # VALIDACIONES
    def validate_perdida_sanguinea_estimada(self, value):
        """Validar pérdida sanguínea"""
        if value and value > 3000:
            raise serializers.ValidationError(
                "Pérdida sanguínea muy alta, revisar valor",
            )
        return value

    def validate_duracion_trabajo_parto_horas(self, value):
        """Validar duración del trabajo de parto"""
        if value and value > 48:
            raise serializers.ValidationError(
                "Duración de trabajo de parto muy prolongada",
            )
        return value

    def validate_edad_gestacional_parto(self, value):
        """Validar edad gestacional con mensaje de ayuda"""
        if value:
            import re

            if not re.match(r"^\d{1,2}(\+\d)$", value):
                raise serializers.ValidationError(
                    "Formato inválido. Use formato: 39 o 39+2 (semanas+días)",
                )

            semanas = int(value.split("+")[0])
            # ✅ Permite desde 0 semanas para abortos muy tempranos
            if semanas < 0 or semanas > 45:
                raise serializers.ValidationError(
                    f"Las semanas deben estar entre 0 y 45. Valor recibido: {semanas}",
                )
        return value

    def validate(self, attrs):
        """Validaciones generales del parto"""
        fecha_ingreso = attrs.get("fecha_ingreso")
        fecha_inicio = attrs.get("fecha_inicio_trabajo_parto")
        fecha_parto = attrs.get("fecha_parto")

        if fecha_ingreso and fecha_inicio and fecha_ingreso > fecha_inicio:
            raise serializers.ValidationError(
                "La fecha de ingreso no puede ser posterior al inicio del trabajo de parto",
            )

        if fecha_inicio and fecha_parto and fecha_inicio > fecha_parto:
            raise serializers.ValidationError(
                "El inicio del trabajo de parto no puede ser posterior al parto",
            )

        # ✅ VALIDACIONES SOLO PARA PARTOS (no para abortos)
        edad_gestacional = attrs.get("edad_gestacional_parto", "")
        es_aborto = False
        if edad_gestacional:
            try:
                semanas = int(edad_gestacional.split("+")[0])
                es_aborto = semanas < 20
            except (ValueError, IndexError):
                pass

        # Solo validar tipo_parto si NO es aborto
        if not es_aborto:
            tipo_parto = attrs.get("tipo_parto")
            indicaciones_cesarea = attrs.get("indicaciones_cesarea")

            if tipo_parto and "cesarea" in tipo_parto and not indicaciones_cesarea:
                raise serializers.ValidationError(
                    "Las cesáreas deben tener indicaciones especificadas",
                )

            episiotomia = attrs.get("episiotomia")
            tipo_episiotomia = attrs.get("tipo_episiotomia")

            if episiotomia and not tipo_episiotomia:
                raise serializers.ValidationError(
                    "Si se realizó episiotomía, debe especificar el tipo",
                )

        return attrs

    # CAMPOS DE ESCRITURA PARA RECIÉN NACIDO (FLATTENED)
    sexo_bebe = serializers.ChoiceField(
        choices=[("masculino", "Masculino"), ("femenino", "Femenino")],
        write_only=True,
        required=False,
    )
    peso_bebe = serializers.IntegerField(write_only=True, required=False)
    talla_bebe = serializers.IntegerField(write_only=True, required=False)
    apgar_1min = serializers.IntegerField(write_only=True, required=False)
    apgar_5min = serializers.IntegerField(write_only=True, required=False)

    def create(self, validated_data):
        """Crear parto y recién nacido asociado"""
        #  MAPEO DE CAMPOS FRONTEND → BACKEND
        # El source='campo' ya maneja la mayoría, pero edad_gestacional_parto necesita construcción
        initial_data = self.initial_data if self.initial_data is not None else {}
        if "semanas_gestacion" in initial_data:
            semanas = initial_data.get("semanas_gestacion", 0)
            dias = initial_data.get("dias_gestacion", 0)
            validated_data["edad_gestacional_parto"] = (
                f"{semanas}+{dias}" if dias else str(semanas)
            )

        # ✅ STRENGTHENED FIX: Remove explicit null paciente to allow auto-assignment
        if "paciente" in validated_data and validated_data["paciente"] is None:
            validated_data.pop("paciente")

        # ✅ FIX: Asignar paciente automáticamente desde el embarazo si no viene explícito
        if "paciente" not in validated_data and "embarazo" in validated_data:
            validated_data["paciente"] = validated_data["embarazo"].paciente

        # ✅ ADDITIONAL SAFETY: Also handle case where embarazo is provided but paciente is missing/None
        if "embarazo" in validated_data and not validated_data.get("paciente"):
            validated_data["paciente"] = validated_data["embarazo"].paciente

        # ✅ FIX: Extraer Y REMOVER datos del recién nacido de validated_data
        # Primero intentar desde validated_data (por si acaso), luego desde initial_data
        _initial = self.initial_data if self.initial_data is not None else {}
        rn_data = {
            "sexo": validated_data.pop("sexo_bebe", None)
            or _initial.get("sexo_bebe"),
            "peso_nacimiento": validated_data.pop("peso_bebe", None)
            or _initial.get("peso_bebe"),
            "talla_nacimiento": validated_data.pop("talla_bebe", None)
            or _initial.get("talla_bebe"),
            "apgar_1_minuto": validated_data.pop("apgar_1min", None)
            or _initial.get("apgar_1min"),
            "apgar_5_minutos": validated_data.pop("apgar_5min", None)
            or _initial.get("apgar_5min"),
        }

        # Crear parto (ahora sin los campos del recién nacido)
        parto = Parto.objects.create(**validated_data)

        # ✅ SOLO crear recién nacido si ES PARTO (tiene tipo_parto) y hay datos del bebé
        # Si tiene tipo_parto, ES UN PARTO (no importa la edad gestacional)
        es_parto = bool(parto.tipo_parto)

        # Solo crear recién nacido para partos (no abortos)
        if es_parto and any(rn_data.values()):

            RecienNacido.objects.create(
                parto=parto,
                numero_gemelo=1,
                fecha_nacimiento=parto.fecha_parto or timezone.now(),
                **{k: v for k, v in rn_data.items() if v is not None},
            )

        return parto

    def update(self, instance, validated_data):
        """Actualizar parto y recién nacido asociado"""
        #  MAPEO DE CAMPOS FRONTEND → BACKEND
        if "semanas_gestacion" in self.initial_data:
            semanas = self.initial_data.get("semanas_gestacion", 0)
            dias = self.initial_data.get("dias_gestacion", 0)
            validated_data["edad_gestacional_parto"] = (
                f"{semanas}+{dias}" if dias else str(semanas)
            )

        # ✅ STRENGTHENED FIX: Remove explicit null paciente to allow auto-assignment
        if "paciente" in validated_data and validated_data["paciente"] is None:
            validated_data.pop("paciente")

        # ✅ FIX: Asegurar que el paciente esté asignado (útil para corregir registros antiguos al editar)
        if not instance.paciente and "embarazo" in validated_data:
            validated_data["paciente"] = validated_data["embarazo"].paciente
        elif not instance.paciente and instance.embarazo:
            validated_data["paciente"] = instance.embarazo.paciente

        # ✅ ADDITIONAL SAFETY: Also handle new embarazo updates
        if "embarazo" in validated_data and not validated_data.get("paciente"):
            validated_data["paciente"] = validated_data["embarazo"].paciente

        # ✅ FIX: Extraer Y REMOVER datos del recién nacido de validated_data
        rn_data = {
            "sexo": validated_data.pop("sexo_bebe", None)
            or self.initial_data.get("sexo_bebe"),
            "peso_nacimiento": validated_data.pop("peso_bebe", None)
            or self.initial_data.get("peso_bebe"),
            "talla_nacimiento": validated_data.pop("talla_bebe", None)
            or self.initial_data.get("talla_bebe"),
            "apgar_1_minuto": validated_data.pop("apgar_1min", None)
            or self.initial_data.get("apgar_1min"),
            "apgar_5_minutos": validated_data.pop("apgar_5min", None)
            or self.initial_data.get("apgar_5min"),
        }

        # Actualizar campos del parto (ahora sin los campos del recién nacido)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ✅ SOLO actualizar/crear recién nacido si ES PARTO (tiene tipo_parto) y hay datos del bebé
        # Si tiene tipo_parto, ES UN PARTO (no importa la edad gestacional)
        es_parto = bool(instance.tipo_parto)

        # Solo manejar recién nacido para partos (no abortos)
        if es_parto and any(rn_data.values()):

            rn, created = RecienNacido.objects.get_or_create(
                parto=instance,
                numero_gemelo=1,
                defaults={
                    "fecha_nacimiento": instance.fecha_parto or timezone.now(),
                    **{k: v for k, v in rn_data.items() if v is not None},
                },
            )
            if not created:
                for attr, value in rn_data.items():
                    if value is not None:
                        setattr(rn, attr, value)
                rn.save()

        return instance


class PartoResumenSerializer(serializers.ModelSerializer):
    """✅ Serializer SIMPLIFICADO para listados de partos
    """

    # Información básica de relaciones
    paciente_nombre = serializers.SerializerMethodField()
    paciente_id_clinico = serializers.SerializerMethodField()
    embarazo_numero = serializers.SerializerMethodField()
    medico_nombre = serializers.SerializerMethodField()

    # Campos calculados
    estado_parto = serializers.SerializerMethodField()
    evaluacion_perdida_sanguinea = serializers.SerializerMethodField()
    total_recien_nacidos = serializers.SerializerMethodField()
    tipo_parto_display = serializers.SerializerMethodField()

    # ✅ NUEVOS: Sistema de alertas médicas
    tiene_alertas = serializers.SerializerMethodField()
    tiene_alertas_criticas = serializers.SerializerMethodField()
    tipo_parto_segun_edad = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Parto
        fields = [
            "id",
            "numero_parto",
            "paciente_nombre",
            "paciente_id_clinico",
            "embarazo_numero",
            "medico_nombre",
            "fecha_parto",
            "tipo_parto",
            "tipo_parto_display",
            "edad_gestacional_parto",
            "parto_finalizado",
            "perdida_sanguinea_estimada",
            "presentacion_fetal",
            "estado_parto",
            "evaluacion_perdida_sanguinea",
            "total_recien_nacidos",
            # ✅ NUEVOS: Alertas médicas
            "tiene_alertas",
            "tiene_alertas_criticas",
            "tipo_parto_segun_edad",
        ]

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        if obj.paciente:
            return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno} {obj.paciente.apellido_materno}".strip()
        return "Sin paciente"

    def get_paciente_id_clinico(self, obj):
        """Get paciente id clinico"""
        return obj.paciente.id_clinico if obj.paciente else None

    def get_embarazo_numero(self, obj):
        """Get embarazo numero"""
        if obj.embarazo:
            return f"G{obj.embarazo.numero_gesta}P{obj.embarazo.numero_para}"
        return None

    def get_medico_nombre(self, obj):
        """Get medico nombre"""
        if obj.medico_responsable:
            return f"{obj.medico_responsable.nombre} {getattr(obj.medico_responsable, 'apellido', '')}".strip()
        return None

    def get_tipo_parto_display(self, obj):
        """Get tipo parto display"""
        return obj.get_tipo_parto_display() if obj.tipo_parto else "No especificado"

    def get_estado_parto(self, obj):
        """Get estado parto"""
        return obj.get_estado_parto()

    def get_evaluacion_perdida_sanguinea(self, obj):
        """Get evaluacion perdida sanguinea"""
        return obj.get_evaluacion_perdida_sanguinea()

    def get_total_recien_nacidos(self, obj):
        """Get total recien nacidos"""
        return obj.recien_nacidos.count()

    # ✅ MÉTODOS PARA SISTEMA DE ALERTAS MÉDICAS

    def get_tiene_alertas(self, obj):
        """Indica si el parto tiene alertas"""
        return obj.tiene_alertas

    def get_tiene_alertas_criticas(self, obj):
        """Indica si el parto tiene alertas críticas"""
        return obj.tiene_alertas_criticas

    def get_tipo_parto_segun_edad(self, obj):
        """Clasificación del parto según edad gestacional"""
        tipo, descripcion = obj.get_tipo_parto_segun_edad()
        return {"tipo": tipo, "descripcion": descripcion}


class RecienNacidoResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de recién nacidos"""

    clasificacion_peso = serializers.SerializerMethodField()
    evaluacion_apgar = serializers.SerializerMethodField()
    parto_numero = serializers.SerializerMethodField()
    sexo_display = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = RecienNacido
        fields = [
            "id",
            "numero_gemelo",
            "fecha_nacimiento",
            "sexo",
            "sexo_display",
            "peso_nacimiento",
            "talla_nacimiento",
            "apgar_1_minuto",
            "apgar_5_minutos",
            "estado_nacimiento",
            "destino_rn",
            "clasificacion_peso",
            "evaluacion_apgar",
            "parto_numero",
        ]

    def get_sexo_display(self, obj):
        """Get sexo display"""
        return obj.get_sexo_display() if obj.sexo else "No especificado"

    def get_clasificacion_peso(self, obj):
        """Get clasificacion peso"""
        return obj.get_clasificacion_peso()

    def get_evaluacion_apgar(self, obj):
        """Get evaluacion apgar"""
        return obj.get_evaluacion_apgar()

    def get_parto_numero(self, obj):
        """Get parto numero"""
        return obj.parto.numero_parto
