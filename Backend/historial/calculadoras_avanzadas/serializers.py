from rest_framework import serializers
from .models import (
    ScoreBishop, RiesgoPreeclampsia, CrecimientoFetal,
    RiesgoCromosomico, DosisMedicamentos, HemorragiaObstetrica,
    SufrimientoFetal
)


class ScoreBishopSerializer(serializers.ModelSerializer):
    """Serializer para Score de Bishop"""
    
    # Campos calculados
    recomendacion_clinica = serializers.SerializerMethodField()
    interpretacion_detallada = serializers.SerializerMethodField()
    
    class Meta:
        model = ScoreBishop
        fields = [
            'id',
            'paciente_id',
            'embarazo_id',
            'medico_id',
            'fecha_evaluacion',
            'edad_gestacional_semanas',
            'dilatacion_cervical',
            'borramiento_cervical',
            'consistencia_cervical',
            'posicion_cervical',
            'estacion_fetal',
            'score_total',
            'interpretacion',
            'probabilidad_parto_espontaneo',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'recomendacion_clinica',
            'interpretacion_detallada',
        ]
        read_only_fields = [
            'id',
            'score_total',
            'interpretacion',
            'probabilidad_parto_espontaneo',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_recomendacion_clinica(self, obj):
        return obj.get_recomendacion_clinica()
    
    def get_interpretacion_detallada(self, obj):
        detalles = {
            'score_total': obj.score_total,
            'interpretacion': obj.interpretacion,
            'probabilidad': float(obj.probabilidad_parto_espontaneo) if obj.probabilidad_parto_espontaneo else 0,
            'componentes': {
                'dilatacion': obj.dilatacion_cervical,
                'borramiento': obj.borramiento_cervical,
                'consistencia': obj.get_consistencia_cervical_display(),
                'posicion': obj.get_posicion_cervical_display(),
                'estacion': obj.estacion_fetal,
            }
        }
        return detalles
    
    def validate_dilatacion_cervical(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("La dilatación debe estar entre 0 y 10 cm")
        return value
    
    def validate_borramiento_cervical(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El borramiento debe estar entre 0 y 100%")
        return value


class RiesgoPreeclampsiaSerializer(serializers.ModelSerializer):
    """Serializer para Riesgo de Preeclampsia"""
    
    # Campos calculados
    imc_calculado = serializers.SerializerMethodField()
    recomendaciones = serializers.SerializerMethodField()
    factores_riesgo_presentes = serializers.SerializerMethodField()
    
    class Meta:
        model = RiesgoPreeclampsia
        fields = [
            'id',
            'paciente_id',
            'embarazo_id',
            'fecha_evaluacion',
            'edad_gestacional_semanas',
            'edad_materna',
            'peso_materno',
            'talla_materna',
            'raza',
            'paridad',
            'hipertension_cronica',
            'diabetes_tipo1',
            'diabetes_tipo2',
            'lupus',
            'antecedente_preeclampsia',
            'embarazo_multiple',
            'metodo_concepcion',
            'presion_arterial_media',
            'riesgo_calculado',
            'riesgo_porcentaje',
            'clasificacion_riesgo',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'imc_calculado',
            'recomendaciones',
            'factores_riesgo_presentes',
        ]
        read_only_fields = [
            'id',
            'riesgo_calculado',
            'riesgo_porcentaje',
            'clasificacion_riesgo',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_imc_calculado(self, obj):
        if obj.peso_materno and obj.talla_materna:
            imc = float(obj.peso_materno) / (float(obj.talla_materna) / 100) ** 2
            return round(imc, 1)
        return None
    
    def get_recomendaciones(self, obj):
        return obj.get_recomendaciones()
    
    def get_factores_riesgo_presentes(self, obj):
        factores = []
        
        if obj.edad_materna >= 35:
            factores.append(f"Edad materna avanzada ({obj.edad_materna} años)")
        
        if obj.hipertension_cronica:
            factores.append("Hipertensión crónica")
        
        if obj.diabetes_tipo1:
            factores.append("Diabetes tipo 1")
        
        if obj.diabetes_tipo2:
            factores.append("Diabetes tipo 2")
        
        if obj.lupus:
            factores.append("Lupus eritematoso sistémico")
        
        if obj.antecedente_preeclampsia:
            factores.append("Antecedente de preeclampsia")
        
        if obj.embarazo_multiple:
            factores.append("Embarazo múltiple")
        
        if obj.paridad == 0:
            factores.append("Nuliparidad")
        
        # IMC
        imc = self.get_imc_calculado(obj)
        if imc and imc >= 30:
            factores.append(f"Obesidad (IMC {imc})")
        elif imc and imc >= 25:
            factores.append(f"Sobrepeso (IMC {imc})")
        
        return factores
    
    def validate_edad_gestacional_semanas(self, value):
        if value < 11 or value > 14:
            raise serializers.ValidationError("La evaluación óptima es entre 11-14 semanas")
        return value
    
    def validate_edad_materna(self, value):
        if value < 15 or value > 50:
            raise serializers.ValidationError("Edad materna fuera del rango válido")
        return value


class CrecimientoFetalSerializer(serializers.ModelSerializer):
    """Serializer para Crecimiento Fetal"""
    
    # Campos calculados
    edad_gestacional_decimal = serializers.SerializerMethodField()
    recomendaciones = serializers.SerializerMethodField()
    resumen_percentiles = serializers.SerializerMethodField()
    
    class Meta:
        model = CrecimientoFetal
        fields = [
            'id',
            'paciente_id',
            'embarazo_id',
            'ecografia_id',
            'fecha_evaluacion',
            'edad_gestacional_semanas',
            'edad_gestacional_dias',
            'diametro_biparietal',
            'circunferencia_cefalica',
            'circunferencia_abdominal',
            'longitud_femur',
            'peso_fetal_estimado',
            'percentil_dbp',
            'percentil_cc',
            'percentil_ca',
            'percentil_lf',
            'percentil_peso',
            'clasificacion_peso',
            'restriccion_crecimiento',
            'macrosomia',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'edad_gestacional_decimal',
            'recomendaciones',
            'resumen_percentiles',
        ]
        read_only_fields = [
            'id',
            'percentil_dbp',
            'percentil_cc',
            'percentil_ca',
            'percentil_lf',
            'percentil_peso',
            'clasificacion_peso',
            'restriccion_crecimiento',
            'macrosomia',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_edad_gestacional_decimal(self, obj):
        return obj.get_edad_gestacional_decimal()
    
    def get_recomendaciones(self, obj):
        return obj.get_recomendaciones()
    
    def get_resumen_percentiles(self, obj):
        return {
            'peso': {
                'valor': obj.peso_fetal_estimado,
                'percentil': obj.percentil_peso,
                'clasificacion': obj.clasificacion_peso,
            },
            'biometria': {
                'dbp': {'valor': float(obj.diametro_biparietal) if obj.diametro_biparietal else None, 'percentil': obj.percentil_dbp},
                'cc': {'valor': float(obj.circunferencia_cefalica) if obj.circunferencia_cefalica else None, 'percentil': obj.percentil_cc},
                'ca': {'valor': float(obj.circunferencia_abdominal) if obj.circunferencia_abdominal else None, 'percentil': obj.percentil_ca},
                'lf': {'valor': float(obj.longitud_femur) if obj.longitud_femur else None, 'percentil': obj.percentil_lf},
            },
            'alertas': {
                'restriccion_crecimiento': obj.restriccion_crecimiento,
                'macrosomia': obj.macrosomia,
            }
        }
    
    def validate_edad_gestacional_semanas(self, value):
        if value < 16 or value > 42:
            raise serializers.ValidationError("Edad gestacional fuera del rango válido para evaluación")
        return value
    
    def validate_peso_fetal_estimado(self, value):
        if value and (value < 100 or value > 6000):
            raise serializers.ValidationError("Peso fetal fuera del rango esperado")
        return value


class RiesgoCromosomicoSerializer(serializers.ModelSerializer):
    """Serializer para Riesgo Cromosómico"""
    
    # Campos calculados
    interpretacion_completa = serializers.SerializerMethodField()
    
    class Meta:
        model = RiesgoCromosomico
        fields = [
            'id',
            'paciente_id',
            'embarazo_id',
            'ecografia_id',
            'fecha_evaluacion',
            'edad_gestacional_semanas',
            'edad_gestacional_dias',
            'edad_materna',
            'peso_materno',
            'translucencia_nucal',
            'hueso_nasal_presente',
            'crl_mm',
            'papp_a',
            'beta_hcg_libre',
            'papp_a_mom',
            'beta_hcg_mom',
            'tn_mom',
            'riesgo_down_basal',
            'riesgo_down_ajustado',
            'riesgo_edwards',
            'riesgo_patau',
            'clasificacion_down',
            'recomendacion',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'interpretacion_completa',
        ]
        read_only_fields = [
            'id',
            'papp_a_mom',
            'beta_hcg_mom',
            'tn_mom',
            'riesgo_down_basal',
            'riesgo_down_ajustado',
            'riesgo_edwards',
            'riesgo_patau',
            'clasificacion_down',
            'recomendacion',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_interpretacion_completa(self, obj):
        return obj.get_interpretacion_completa()
    
    def validate_translucencia_nucal(self, value):
        if value and (value < 0.5 or value > 8.0):
            raise serializers.ValidationError("Translucencia nucal fuera del rango esperado")
        return value


class DosisMedicamentosSerializer(serializers.ModelSerializer):
    """Serializer para Dosis de Medicamentos"""
    
    # Campos calculados
    protocolo_administracion = serializers.SerializerMethodField()
    
    class Meta:
        model = DosisMedicamentos
        fields = [
            'id',
            'paciente_id',
            'embarazo_id',
            'parto_id',
            'fecha_calculo',
            'medicamento',
            'indicacion',
            'peso_materno',
            'edad_gestacional_semanas',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'creatinina_serica',
            'dosis_inicial',
            'dosis_mantenimiento',
            'dosis_maxima',
            'via_administracion',
            'intervalo_dosis',
            'duracion_tratamiento',
            'precauciones',
            'contraindicaciones',
            'monitoreo_requerido',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'protocolo_administracion',
        ]
        read_only_fields = [
            'id',
            'dosis_inicial',
            'dosis_mantenimiento',
            'dosis_maxima',
            'via_administracion',
            'intervalo_dosis',
            'duracion_tratamiento',
            'precauciones',
            'contraindicaciones',
            'monitoreo_requerido',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_protocolo_administracion(self, obj):
        return obj.get_protocolo_administracion()
    
    def validate_peso_materno(self, value):
        if value < 40 or value > 150:
            raise serializers.ValidationError("Peso materno fuera del rango válido")
        return value


class HemorragiaObstetricaSerializer(serializers.ModelSerializer):
    """Serializer para Hemorragia Obstétrica"""
    
    # Campos calculados
    protocolo_manejo = serializers.SerializerMethodField()
    recomendaciones_laboratorio = serializers.SerializerMethodField()
    
    class Meta:
        model = HemorragiaObstetrica
        fields = [
            'id',
            'paciente_id',
            'embarazo_id',
            'parto_id',
            'fecha_evento',
            'tipo_hemorragia',
            'causa_principal',
            'perdida_sanguinea_estimada',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'frecuencia_cardiaca',
            'hemoglobina_inicial',
            'hematocrito_inicial',
            'plaquetas',
            'severidad_hemorragia',
            'indice_shock',
            'deficit_volumen_estimado',
            'paso_protocolo_actual',
            'medidas_implementadas',
            'requiere_transfusion',
            'unidades_globulos_rojos',
            'unidades_plasma_fresco',
            'unidades_plaquetas',
            'hemorragia_controlada',
            'requirio_cirugia',
            'tipo_cirugia',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'protocolo_manejo',
            'recomendaciones_laboratorio',
        ]
        read_only_fields = [
            'id',
            'severidad_hemorragia',
            'indice_shock',
            'deficit_volumen_estimado',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_protocolo_manejo(self, obj):
        return obj.get_protocolo_manejo()
    
    def get_recomendaciones_laboratorio(self, obj):
        return obj.get_recomendaciones_laboratorio()
    
    def validate_perdida_sanguinea_estimada(self, value):
        if value > 5000:
            raise serializers.ValidationError("Pérdida sanguínea excesivamente alta, verificar valor")
        return value


class SufrimientoFetalSerializer(serializers.ModelSerializer):
    """Serializer para Sufrimiento Fetal"""
    
    # Campos calculados
    interpretacion_completa = serializers.SerializerMethodField()
    
    class Meta:
        model = SufrimientoFetal
        fields = [
            'id',
            'paciente_id',
            'embarazo_id',
            'parto_id',
            'fecha_evaluacion',
            'edad_gestacional_semanas',
            'tipo_evaluacion',
            'tipo_monitoreo',
            'fcf_basal',
            'variabilidad_fcf',
            'aceleraciones_presentes',
            'desaceleraciones_tardias',
            'desaceleraciones_variables',
            'desaceleraciones_prolongadas',
            'movimientos_fetales',
            'tono_fetal',
            'liquido_amniotico',
            'indice_pulsatilidad_umbilical',
            'indice_pulsatilidad_cerebral',
            'score_fisher',
            'perfil_biofsico_score',
            'clasificacion_ctg',
            'riesgo_sufrimiento_fetal',
            'conducta_recomendada',
            'requiere_intervencion_inmediata',
            'fecha_registro',
            'fecha_modificacion',
            # Campos calculados
            'interpretacion_completa',
        ]
        read_only_fields = [
            'id',
            'score_fisher',
            'perfil_biofsico_score',
            'clasificacion_ctg',
            'riesgo_sufrimiento_fetal',
            'conducta_recomendada',
            'requiere_intervencion_inmediata',
            'fecha_registro',
            'fecha_modificacion',
        ]
    
    def get_interpretacion_completa(self, obj):
        return obj.get_interpretacion_completa()
    
    def validate_fcf_basal(self, value):
        if value and (value < 80 or value > 200):
            raise serializers.ValidationError("FCF fuera del rango válido")
        return value


# Serializers simplificados para listados
class ScoreBishopResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    recomendacion_clinica = serializers.SerializerMethodField()
    
    class Meta:
        model = ScoreBishop
        fields = [
            'id',
            'paciente_id',
            'fecha_evaluacion',
            'score_total',
            'interpretacion',
            'probabilidad_parto_espontaneo',
            'recomendacion_clinica',
        ]
    
    def get_recomendacion_clinica(self, obj):
        return obj.get_recomendacion_clinica()


class RiesgoPreeclampsiaResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    class Meta:
        model = RiesgoPreeclampsia
        fields = [
            'id',
            'paciente_id',
            'fecha_evaluacion',
            'riesgo_porcentaje',
            'clasificacion_riesgo',
            'edad_materna',
        ]


class CrecimientoFetalResumenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    class Meta:
        model = CrecimientoFetal
        fields = [
            'id',
            'paciente_id',
            'fecha_evaluacion',
            'edad_gestacional_semanas',
            'peso_fetal_estimado',
            'percentil_peso',
            'clasificacion_peso',
        ]