from rest_framework import serializers
from .models import Parto, RecienNacido, PartogramaRegistro


class PartogramaRegistroSerializer(serializers.ModelSerializer):
    """Serializer para registros de partograma"""
    
    # Campos calculados
    presion_arterial = serializers.SerializerMethodField()
    evaluacion_fcf = serializers.SerializerMethodField()
    evaluacion_contracciones = serializers.SerializerMethodField()
    alertas_activas = serializers.SerializerMethodField()
    resumen_registro = serializers.SerializerMethodField()
    
    class Meta:
        model = PartogramaRegistro
        fields = [
            'id',
            'parto',
            'hora_registro',
            'horas_trabajo_parto',
            'dilatacion_cervical',
            'borramiento_cervical',
            'estacion_fetal',
            'contracciones_10min',
            'duracion_contracciones',
            'intensidad_contracciones',
            'fcf_baseline',
            'variabilidad_fcf',
            'desaceleraciones',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'temperatura',
            'pulso_materno',
            'oxitocina_dosis',
            'observaciones',
            'alerta_fcf_anormal',
            'alerta_progreso_lento',
            'alerta_signos_vitales',
            'registrado_por_id',
            'fecha_registro',
            # Campos calculados
            'presion_arterial',
            'evaluacion_fcf',
            'evaluacion_contracciones',
            'alertas_activas',
            'resumen_registro',
        ]
        read_only_fields = [
            'id',
            'fecha_registro',
            'alerta_fcf_anormal',
            'alerta_progreso_lento',
            'alerta_signos_vitales',
        ]
    
    def get_presion_arterial(self, obj):
        return obj.get_presion_arterial()
    
    def get_evaluacion_fcf(self, obj):
        return obj.get_evaluacion_fcf()
    
    def get_evaluacion_contracciones(self, obj):
        return obj.get_evaluacion_contracciones()
    
    def get_alertas_activas(self, obj):
        return obj.get_alertas_activas()
    
    def get_resumen_registro(self, obj):
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
        model = RecienNacido
        fields = [
            'id',
            'parto',
            'numero_gemelo',
            'fecha_nacimiento',
            'sexo',
            'estado_nacimiento',
            'peso_nacimiento',
            'talla_nacimiento',
            'perimetro_cefalico',
            'apgar_1_minuto',
            'apgar_5_minutos',
            'apgar_10_minutos',
            'requirio_reanimacion',
            'tipo_reanimacion',
            'malformaciones_congenitas',
            'descripcion_malformaciones',
            'destino_rn',
            'llanto_inmediato',
            'respiracion_espontanea',
            'tono_muscular_normal',
            'observaciones_rn',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'clasificacion_peso',
            'evaluacion_apgar',
            'evaluacion_estado_general',
            'resumen_completo',
            'parto_numero',
        ]
        read_only_fields = [
            'id',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_clasificacion_peso(self, obj):
        return obj.get_clasificacion_peso()
    
    def get_evaluacion_apgar(self, obj):
        return obj.get_evaluacion_apgar()
    
    def get_evaluacion_estado_general(self, obj):
        return obj.get_evaluacion_estado_general()
    
    def get_resumen_completo(self, obj):
        return obj.get_resumen_completo()
    
    def get_parto_numero(self, obj):
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
    
    def validate(self, data):
        """Validaciones generales"""
        # Validar que Apgar 1 min <= Apgar 5 min (generalmente)
        apgar_1 = data.get('apgar_1_minuto')
        apgar_5 = data.get('apgar_5_minutos')
        
        if apgar_1 and apgar_5 and apgar_1 > apgar_5 + 2:
            raise serializers.ValidationError(
                "Es inusual que el Apgar a 1 minuto sea mucho mayor que el de 5 minutos"
            )
        
        return data


class PartoSerializer(serializers.ModelSerializer):
    """Serializer para partos"""
    
    # Relaciones anidadas
    recien_nacidos = RecienNacidoSerializer(many=True, read_only=True)
    partograma = PartogramaRegistroSerializer(many=True, read_only=True)
    
    # Campos calculados
    evaluacion_perdida_sanguinea = serializers.SerializerMethodField()
    estado_parto = serializers.SerializerMethodField()
    resumen_parto = serializers.SerializerMethodField()
    complicaciones_totales = serializers.SerializerMethodField()
    duracion_trabajo_parto_calculada = serializers.SerializerMethodField()
    
    # Estadísticas relacionadas
    total_recien_nacidos = serializers.SerializerMethodField()
    total_registros_partograma = serializers.SerializerMethodField()
    
    class Meta:
        model = Parto
        fields = [
            'id',
            'embarazo_id',
            'paciente_id',
            'medico_responsable_id',
            'numero_parto',
            'fecha_ingreso',
            'fecha_inicio_trabajo_parto',
            'fecha_parto',
            'edad_gestacional_parto',
            'tipo_parto',
            'presentacion_fetal',
            'posicion_fetal',
            'estado_membranas',
            'hora_rotura_membranas',
            'caracteristicas_liquido',
            'duracion_trabajo_parto_horas',
            'duracion_periodo_expulsivo_minutos',
            'analgesia_utilizada',
            'tipo_analgesia',
            'episiotomia',
            'tipo_episiotomia',
            'desgarros',
            'grado_desgarros',
            'tipo_alumbramiento',
            'placenta_completa',
            'peso_placenta',
            'perdida_sanguinea_estimada',
            'hemorragia_postparto',
            'complicaciones_maternas',
            'oxitocina_utilizada',
            'dosis_oxitocina',
            'otros_medicamentos',
            'observaciones_parto',
            'indicaciones_cesarea',
            'parto_finalizado',
            'trabajo_parto_espontaneo',
            'induccion_parto',
            'metodo_induccion',
            'monitoreo_fetal_continuo',
            'fecha_registro',
            'fecha_modificacion',
            # Relaciones
            'recien_nacidos',
            'partograma',
            # Campos calculados
            'evaluacion_perdida_sanguinea',
            'estado_parto',
            'resumen_parto',
            'complicaciones_totales',
            'duracion_trabajo_parto_calculada',
            'total_recien_nacidos',
            'total_registros_partograma',
        ]
        read_only_fields = [
            'id',
            'numero_parto',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_evaluacion_perdida_sanguinea(self, obj):
        return obj.get_evaluacion_perdida_sanguinea()
    
    def get_estado_parto(self, obj):
        return obj.get_estado_parto()
    
    def get_resumen_parto(self, obj):
        return obj.get_resumen_parto()
    
    def get_complicaciones_totales(self, obj):
        return obj.get_complicaciones_totales()
    
    def get_duracion_trabajo_parto_calculada(self, obj):
        return obj.get_duracion_trabajo_parto_horas()
    
    def get_total_recien_nacidos(self, obj):
        return obj.recien_nacidos.count()
    
    def get_total_registros_partograma(self, obj):
        return obj.partograma.count()
    
    def validate_perdida_sanguinea_estimada(self, value):
        """Validar pérdida sanguínea"""
        if value and value > 3000:
            raise serializers.ValidationError(
                "Pérdida sanguínea muy alta, revisar valor"
            )
        return value
    
    def validate_duracion_trabajo_parto_horas(self, value):
        """Validar duración del trabajo de parto"""
        if value and value > 48:
            raise serializers.ValidationError(
                "Duración de trabajo de parto muy prolongada"
            )
        return value
    
    def validate(self, data):
        """Validaciones generales del parto"""
        # Validar fechas
        fecha_ingreso = data.get('fecha_ingreso')
        fecha_inicio = data.get('fecha_inicio_trabajo_parto')
        fecha_parto = data.get('fecha_parto')
        
        if fecha_ingreso and fecha_inicio and fecha_ingreso > fecha_inicio:
            raise serializers.ValidationError(
                "La fecha de ingreso no puede ser posterior al inicio del trabajo de parto"
            )
        
        if fecha_inicio and fecha_parto and fecha_inicio > fecha_parto:
            raise serializers.ValidationError(
                "El inicio del trabajo de parto no puede ser posterior al parto"
            )
        
        # Validar campos relacionados con cesárea
        tipo_parto = data.get('tipo_parto')
        indicaciones_cesarea = data.get('indicaciones_cesarea')
        
        if tipo_parto and 'cesarea' in tipo_parto and not indicaciones_cesarea:
            raise serializers.ValidationError(
                "Las cesáreas deben tener indicaciones especificadas"
            )
        
        # Validar episiotomía
        episiotomia = data.get('episiotomia')
        tipo_episiotomia = data.get('tipo_episiotomia')
        
        if episiotomia and not tipo_episiotomia:
            raise serializers.ValidationError(
                "Si se realizó episiotomía, debe especificar el tipo"
            )
        
        return data


class PartoResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de partos"""
    
    estado_parto = serializers.SerializerMethodField()
    evaluacion_perdida_sanguinea = serializers.SerializerMethodField()
    total_recien_nacidos = serializers.SerializerMethodField()
    
    class Meta:
        model = Parto
        fields = [
            'id',
            'numero_parto',
            'paciente_id',
            'fecha_parto',
            'tipo_parto',
            'edad_gestacional_parto',
            'parto_finalizado',
            'perdida_sanguinea_estimada',
            'estado_parto',
            'evaluacion_perdida_sanguinea',
            'total_recien_nacidos',
        ]
    
    def get_estado_parto(self, obj):
        return obj.get_estado_parto()
    
    def get_evaluacion_perdida_sanguinea(self, obj):
        return obj.get_evaluacion_perdida_sanguinea()
    
    def get_total_recien_nacidos(self, obj):
        return obj.recien_nacidos.count()


class RecienNacidoResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de recién nacidos"""
    
    clasificacion_peso = serializers.SerializerMethodField()
    evaluacion_apgar = serializers.SerializerMethodField()
    parto_numero = serializers.SerializerMethodField()
    
    class Meta:
        model = RecienNacido
        fields = [
            'id',
            'numero_gemelo',
            'fecha_nacimiento',
            'sexo',
            'peso_nacimiento',
            'apgar_5_minutos',
            'estado_nacimiento',
            'destino_rn',
            'clasificacion_peso',
            'evaluacion_apgar',
            'parto_numero',
        ]
    
    def get_clasificacion_peso(self, obj):
        return obj.get_clasificacion_peso()
    
    def get_evaluacion_apgar(self, obj):
        return obj.get_evaluacion_apgar()
    
    def get_parto_numero(self, obj):
        return obj.parto.numero_parto