from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    ScoreBishop, RiesgoPreeclampsia, CrecimientoFetal,
    RiesgoCromosomico, DosisMedicamentos, HemorragiaObstetrica,
    SufrimientoFetal
)


@admin.register(ScoreBishop)
class ScoreBishopAdmin(admin.ModelAdmin):
    list_display = (
        'get_paciente_info',
        'fecha_evaluacion',
        'edad_gestacional_semanas',
        'score_badge',
        'interpretacion_badge',
        'probabilidad_badge',
        'get_recomendacion_short',
    )
    
    list_filter = (
        'score_total',
        'interpretacion',
        'consistencia_cervical',
        'posicion_cervical',
        'fecha_evaluacion',
    )
    
    search_fields = (
        'paciente_id',
        'embarazo_id',
    )
    
    readonly_fields = (
        'score_total',
        'interpretacion',
        'probabilidad_parto_espontaneo',
        'fecha_registro',
        'fecha_modificacion',
        'get_recomendacion_clinica_display',
    )
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': (
                ('paciente_id', 'embarazo_id', 'medico_id'),
                ('fecha_evaluacion', 'edad_gestacional_semanas'),
            )
        }),
        ('Evaluación Cervical', {
            'fields': (
                ('dilatacion_cervical', 'borramiento_cervical'),
                ('consistencia_cervical', 'posicion_cervical'),
                ('estacion_fetal',),
            )
        }),
        ('Resultados del Score', {
            'fields': (
                ('score_total', 'interpretacion'),
                ('probabilidad_parto_espontaneo',),
                ('get_recomendacion_clinica_display',),
            )
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>Embarazo ID: {}</small>',
            obj.paciente_id,
            obj.embarazo_id or "No asignado"
        )
    get_paciente_info.short_description = 'Paciente'
    
    def score_badge(self, obj):
        if obj.score_total is None:
            return format_html('<span style="color: #6c757d;">No calculado</span>')
        
        score = obj.score_total
        if score <= 5:
            color = '#e74c3c'
        elif score <= 8:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}/13</span>',
            color, score
        )
    score_badge.short_description = 'Score Bishop'
    
    def interpretacion_badge(self, obj):
        if not obj.interpretacion:
            return format_html('<span style="color: #6c757d;">No calculada</span>')
        
        if "inmaduro" in obj.interpretacion:
            color = '#e74c3c'
        elif "moderadamente" in obj.interpretacion:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.interpretacion
        )
    interpretacion_badge.short_description = 'Interpretación'
    
    def probabilidad_badge(self, obj):
        if not obj.probabilidad_parto_espontaneo:
            return format_html('<span style="color: #6c757d;">No calculada</span>')
        
        prob = float(obj.probabilidad_parto_espontaneo)
        if prob >= 70:
            color = '#27ae60'
        elif prob >= 40:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, prob
        )
    probabilidad_badge.short_description = 'Probabilidad'
    
    def get_recomendacion_short(self, obj):
        recom = obj.get_recomendacion_clinica()
        if len(recom) > 50:
            return f"{recom[:50]}..."
        return recom
    get_recomendacion_short.short_description = 'Recomendación'
    
    def get_recomendacion_clinica_display(self, obj):
        return obj.get_recomendacion_clinica()
    get_recomendacion_clinica_display.short_description = 'Recomendación Clínica Completa'


@admin.register(RiesgoPreeclampsia)
class RiesgoPreeclampsiaAdmin(admin.ModelAdmin):
    list_display = (
        'get_paciente_info',
        'fecha_evaluacion',
        'edad_gestacional_semanas',
        'riesgo_badge',
        'clasificacion_badge',
        'get_factores_riesgo',
    )
    
    list_filter = (
        'clasificacion_riesgo',
        'hipertension_cronica',
        'diabetes_tipo1',
        'diabetes_tipo2',
        'antecedente_preeclampsia',
        'embarazo_multiple',
        'raza',
        'fecha_evaluacion',
    )
    
    search_fields = (
        'paciente_id',
        'embarazo_id',
    )
    
    readonly_fields = (
        'riesgo_calculado',
        'riesgo_porcentaje',
        'clasificacion_riesgo',
        'fecha_registro',
        'fecha_modificacion',
        'get_imc_display',
        'get_recomendaciones_display',
    )
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': (
                ('paciente_id', 'embarazo_id'),
                ('fecha_evaluacion', 'edad_gestacional_semanas'),
            )
        }),
        ('Datos Maternos', {
            'fields': (
                ('edad_materna', 'raza'),
                ('peso_materno', 'talla_materna'),
                ('get_imc_display',),
                ('paridad',),
            )
        }),
        ('Antecedentes Médicos', {
            'fields': (
                ('hipertension_cronica', 'diabetes_tipo1', 'diabetes_tipo2'),
                ('lupus', 'antecedente_preeclampsia'),
            )
        }),
        ('Embarazo Actual', {
            'fields': (
                ('embarazo_multiple', 'metodo_concepcion'),
            )
        }),
        ('Biomarcadores', {
            'fields': (
                ('presion_arterial_media',),
            ),
            'classes': ('collapse',)
        }),
        ('Resultados del Cálculo', {
            'fields': (
                ('riesgo_porcentaje', 'riesgo_calculado'),
                ('clasificacion_riesgo',),
                ('get_recomendaciones_display',),
            )
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>{} años - {} sem</small>',
            obj.paciente_id,
            obj.edad_materna,
            obj.edad_gestacional_semanas
        )
    get_paciente_info.short_description = 'Paciente'
    
    def riesgo_badge(self, obj):
        if not obj.riesgo_porcentaje:
            return format_html('<span style="color: #6c757d;">No calculado</span>')
        
        riesgo = float(obj.riesgo_porcentaje)
        if riesgo >= 10:
            color = '#e74c3c'
        elif riesgo >= 5:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}%</span>',
            color, riesgo
        )
    riesgo_badge.short_description = 'Riesgo'
    
    def clasificacion_badge(self, obj):
        if not obj.clasificacion_riesgo:
            return format_html('<span style="color: #6c757d;">No calculada</span>')
        
        if "Alto" in obj.clasificacion_riesgo:
            color = '#e74c3c'
        elif "Intermedio" in obj.clasificacion_riesgo:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.clasificacion_riesgo
        )
    clasificacion_badge.short_description = 'Clasificación'
    
    def get_factores_riesgo(self, obj):
        factores = []
        if obj.hipertension_cronica:
            factores.append("HTA")
        if obj.diabetes_tipo1 or obj.diabetes_tipo2:
            factores.append("DM")
        if obj.antecedente_preeclampsia:
            factores.append("PE previa")
        if obj.embarazo_multiple:
            factores.append("Gemelar")
        if obj.edad_materna >= 35:
            factores.append("Edad >35")
        
        return ", ".join(factores) if factores else "Sin factores mayores"
    get_factores_riesgo.short_description = 'Factores de Riesgo'
    
    def get_imc_display(self, obj):
        return obj.get_imc_calculado()
    get_imc_display.short_description = 'IMC Calculado'
    
    def get_recomendaciones_display(self, obj):
        recom_list = obj.get_recomendaciones()
        return "\n".join([f"• {r}" for r in recom_list])
    get_recomendaciones_display.short_description = 'Recomendaciones Clínicas'


@admin.register(CrecimientoFetal)
class CrecimientoFetalAdmin(admin.ModelAdmin):
    list_display = (
        'get_paciente_info',
        'fecha_evaluacion',
        'get_edad_gestacional',
        'peso_percentil_badge',
        'clasificacion_badge',
        'get_alertas_crecimiento',
    )
    
    list_filter = (
        'clasificacion_peso',
        'restriccion_crecimiento',
        'macrosomia',
        'fecha_evaluacion',
    )
    
    search_fields = (
        'paciente_id',
        'embarazo_id',
        'ecografia_id',
    )
    
    readonly_fields = (
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
        'get_edad_gestacional_decimal_display',
        'get_recomendaciones_display',
    )
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': (
                ('paciente_id', 'embarazo_id', 'ecografia_id'),
                ('fecha_evaluacion',),
                ('edad_gestacional_semanas', 'edad_gestacional_dias'),
                ('get_edad_gestacional_decimal_display',),
            )
        }),
        ('Biometría Fetal', {
            'fields': (
                ('diametro_biparietal', 'circunferencia_cefalica'),
                ('circunferencia_abdominal', 'longitud_femur'),
                ('peso_fetal_estimado',),
            )
        }),
        ('Percentiles Calculados', {
            'fields': (
                ('percentil_dbp', 'percentil_cc'),
                ('percentil_ca', 'percentil_lf'),
                ('percentil_peso',),
            )
        }),
        ('Evaluación del Crecimiento', {
            'fields': (
                ('clasificacion_peso',),
                ('restriccion_crecimiento', 'macrosomia'),
                ('get_recomendaciones_display',),
            )
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>Ecografía ID: {}</small>',
            obj.paciente_id,
            obj.ecografia_id or "No asociada"
        )
    get_paciente_info.short_description = 'Paciente'
    
    def get_edad_gestacional(self, obj):
        return f"{obj.edad_gestacional_semanas}+{obj.edad_gestacional_dias or 0}"
    get_edad_gestacional.short_description = 'EG'
    
    def peso_percentil_badge(self, obj):
        if not obj.peso_fetal_estimado or not obj.percentil_peso:
            return format_html('<span style="color: #6c757d;">No calculado</span>')
        
        percentil = obj.percentil_peso
        if percentil < 10:
            color = '#e74c3c'
        elif percentil > 90:
            color = '#e67e22'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}g (P{})</span>',
            color, obj.peso_fetal_estimado, percentil
        )
    peso_percentil_badge.short_description = 'Peso (Percentil)'
    
    def clasificacion_badge(self, obj):
        if not obj.clasificacion_peso:
            return format_html('<span style="color: #6c757d;">No calculada</span>')
        
        if "Pequeño" in obj.clasificacion_peso:
            color = '#e74c3c'
        elif "Grande" in obj.clasificacion_peso:
            color = '#e67e22'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.clasificacion_peso
        )
    clasificacion_badge.short_description = 'Clasificación'
    
    def get_alertas_crecimiento(self, obj):
        alertas = []
        if obj.restriccion_crecimiento:
            alertas.append("RCIU")
        if obj.macrosomia:
            alertas.append("Macrosomía")
        
        if alertas:
            return format_html(
                '<span style="color: #e74c3c; font-weight: bold;">{}</span>',
                " | ".join(alertas)
            )
        else:
            return format_html('<span style="color: #27ae60;">Normal</span>')
    get_alertas_crecimiento.short_description = 'Alertas'
    
    def get_edad_gestacional_decimal_display(self, obj):
        return obj.get_edad_gestacional_decimal()
    get_edad_gestacional_decimal_display.short_description = 'EG Decimal'
    
    def get_recomendaciones_display(self, obj):
        recom_list = obj.get_recomendaciones()
        return "\n".join([f"• {r}" for r in recom_list])
    get_recomendaciones_display.short_description = 'Recomendaciones Clínicas'


@admin.register(RiesgoCromosomico)
class RiesgoCromosomicoAdmin(admin.ModelAdmin):
    list_display = (
        'get_paciente_info',
        'fecha_evaluacion',
        'edad_gestacional_semanas',
        'edad_materna',
        'riesgo_down_badge',
        'clasificacion_badge',
        'get_tn_valor',
    )
    
    list_filter = (
        'clasificacion_down',
        'hueso_nasal_presente',
        'fecha_evaluacion',
    )
    
    search_fields = (
        'paciente_id',
        'embarazo_id',
    )
    
    readonly_fields = (
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
        'get_interpretacion_completa_display',
    )
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': (
                ('paciente_id', 'embarazo_id', 'ecografia_id'),
                ('fecha_evaluacion', 'edad_gestacional_semanas', 'edad_gestacional_dias'),
                ('edad_materna', 'peso_materno'),
            )
        }),
        ('Ecografía del Primer Trimestre', {
            'fields': (
                ('translucencia_nucal', 'hueso_nasal_presente'),
                ('crl_mm',),
            )
        }),
        ('Marcadores Bioquímicos', {
            'fields': (
                ('papp_a', 'beta_hcg_libre'),
                ('papp_a_mom', 'beta_hcg_mom', 'tn_mom'),
            )
        }),
        ('Resultados del Screening', {
            'fields': (
                ('riesgo_down_basal', 'riesgo_down_ajustado'),
                ('riesgo_edwards', 'riesgo_patau'),
                ('clasificacion_down',),
                ('recomendacion',),
                ('get_interpretacion_completa_display',),
            )
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>{} años - {}+{} sem</small>',
            obj.paciente_id,
            obj.edad_materna,
            obj.edad_gestacional_semanas,
            obj.edad_gestacional_dias
        )
    get_paciente_info.short_description = 'Paciente'
    
    def riesgo_down_badge(self, obj):
        if not obj.riesgo_down_ajustado:
            return format_html('<span style="color: #6c757d;">No calculado</span>')
        
        # Extraer el número del riesgo (ej: "1:250" -> 250)
        try:
            riesgo_num = int(obj.riesgo_down_ajustado.split(':')[1])
            if riesgo_num <= 250:
                color = '#e74c3c'  # Alto riesgo
            elif riesgo_num <= 1000:
                color = '#f39c12'  # Riesgo intermedio
            else:
                color = '#27ae60'  # Bajo riesgo
        except:
            color = '#6c757d'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.riesgo_down_ajustado
        )
    riesgo_down_badge.short_description = 'Riesgo Down'
    
    def clasificacion_badge(self, obj):
        if not obj.clasificacion_down:
            return format_html('<span style="color: #6c757d;">No calculada</span>')
        
        if obj.clasificacion_down == 'alto':
            color = '#e74c3c'
            texto = 'ALTO RIESGO'
        elif obj.clasificacion_down == 'intermedio':
            color = '#f39c12'
            texto = 'RIESGO INTERMEDIO'
        else:
            color = '#27ae60'
            texto = 'BAJO RIESGO'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, texto
        )
    clasificacion_badge.short_description = 'Clasificación'
    
    def get_tn_valor(self, obj):
        if obj.translucencia_nucal:
            tn = float(obj.translucencia_nucal)
            if tn >= 3.5:
                color = '#e74c3c'
            elif tn >= 2.5:
                color = '#f39c12'
            else:
                color = '#27ae60'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} mm</span>',
                color, tn
            )
        return format_html('<span style="color: #6c757d;">No medida</span>')
    get_tn_valor.short_description = 'TN'
    
    def get_interpretacion_completa_display(self, obj):
        interp = obj.get_interpretacion_completa()
        result = []
        for key, value in interp.items():
            result.append(f"{key}: {value}")
        return "\n".join(result)
    get_interpretacion_completa_display.short_description = 'Interpretación Completa'


@admin.register(DosisMedicamentos)
class DosisMedicamentosAdmin(admin.ModelAdmin):
    list_display = (
        'get_paciente_info',
        'fecha_calculo',
        'medicamento_badge',
        'indicacion_badge',
        'peso_materno',
        'get_dosis_inicial',
    )
    
    list_filter = (
        'medicamento',
        'indicacion',
        'fecha_calculo',
    )
    
    search_fields = (
        'paciente_id',
        'embarazo_id',
    )
    
    readonly_fields = (
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
        'get_protocolo_administracion_display',
    )
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': (
                ('paciente_id', 'embarazo_id', 'parto_id'),
                ('fecha_calculo',),
            )
        }),
        ('Medicamento e Indicación', {
            'fields': (
                ('medicamento', 'indicacion'),
                ('peso_materno', 'edad_gestacional_semanas'),
            )
        }),
        ('Parámetros Clínicos', {
            'fields': (
                ('presion_arterial_sistolica', 'presion_arterial_diastolica'),
                ('creatinina_serica',),
            ),
            'classes': ('collapse',)
        }),
        ('Protocolo de Dosificación', {
            'fields': (
                ('dosis_inicial', 'dosis_mantenimiento', 'dosis_maxima'),
                ('via_administracion', 'intervalo_dosis'),
                ('duracion_tratamiento',),
            )
        }),
        ('Seguridad y Monitoreo', {
            'fields': (
                ('precauciones',),
                ('contraindicaciones',),
                ('monitoreo_requerido',),
                ('get_protocolo_administracion_display',),
            )
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>Peso: {}kg</small>',
            obj.paciente_id,
            obj.peso_materno
        )
    get_paciente_info.short_description = 'Paciente'
    
    def medicamento_badge(self, obj):
        colors = {
            'oxitocina': '#e74c3c',
            'sulfato_magnesio': '#9b59b6',
            'betametasona': '#3498db',
            'nifedipino': '#f39c12',
            'labetalol': '#27ae60',
        }
        color = colors.get(obj.medicamento, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_medicamento_display()
        )
    medicamento_badge.short_description = 'Medicamento'
    
    def indicacion_badge(self, obj):
        colors = {
            'induccion_parto': '#3498db',
            'hemorragia_postparto': '#e74c3c',
            'preeclampsia_severa': '#9b59b6',
            'maduracin_pulmonar': '#27ae60',
        }
        color = colors.get(obj.indicacion, '#6c757d')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_indicacion_display()
        )
    indicacion_badge.short_description = 'Indicación'
    
    def get_dosis_inicial(self, obj):
        return obj.dosis_inicial or "No calculada"
    get_dosis_inicial.short_description = 'Dosis Inicial'
    
    def get_protocolo_administracion_display(self, obj):
        protocolo = obj.get_protocolo_administracion()
        result = []
        for key, value in protocolo.items():
            result.append(f"{key}: {value}")
        return "\n".join(result)
    get_protocolo_administracion_display.short_description = 'Protocolo Completo'


@admin.register(HemorragiaObstetrica)
class HemorragiaObstetricaAdmin(admin.ModelAdmin):
    list_display = (
        'get_paciente_info',
        'fecha_evento',
        'tipo_hemorragia',
        'severidad_badge',
        'perdida_sanguinea_badge',
        'get_signos_vitales',
        'hemorragia_controlada',
    )
    
    list_filter = (
        'tipo_hemorragia',
        'causa_principal',
        'severidad_hemorragia',
        'requiere_transfusion',
        'hemorragia_controlada',
        'fecha_evento',
    )
    
    search_fields = (
        'paciente_id',
        'embarazo_id',
        'parto_id',
    )
    
    readonly_fields = (
        'severidad_hemorragia',
        'indice_shock',
        'deficit_volumen_estimado',
        'fecha_registro',
        'fecha_modificacion',
        'get_protocolo_manejo_display',
        'get_recomendaciones_laboratorio_display',
    )
    
    fieldsets = (
        ('Información del Evento', {
            'fields': (
                ('paciente_id', 'embarazo_id', 'parto_id'),
                ('fecha_evento', 'tipo_hemorragia'),
                ('causa_principal',),
            )
        }),
        ('Evaluación Inicial', {
            'fields': (
                ('perdida_sanguinea_estimada', 'severidad_hemorragia'),
                ('presion_arterial_sistolica', 'presion_arterial_diastolica'),
                ('frecuencia_cardiaca', 'indice_shock'),
            )
        }),
        ('Laboratorio Inicial', {
            'fields': (
                ('hemoglobina_inicial', 'hematocrito_inicial'),
                ('plaquetas',),
            )
        }),
        ('Protocolo de Manejo', {
            'fields': (
                ('paso_protocolo_actual',),
                ('medidas_implementadas',),
                ('get_protocolo_manejo_display',),
            )
        }),
        ('Transfusión', {
            'fields': (
                ('requiere_transfusion',),
                ('unidades_globulos_rojos', 'unidades_plasma_fresco', 'unidades_plaquetas'),
            )
        }),
        ('Resultado', {
            'fields': (
                ('hemorragia_controlada', 'requirio_cirugia'),
                ('tipo_cirugia',),
            )
        }),
        ('Laboratorio y Recomendaciones', {
            'fields': (
                ('get_recomendaciones_laboratorio_display',),
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>{}</small>',
            obj.paciente_id,
            obj.get_tipo_hemorragia_display()
        )
    get_paciente_info.short_description = 'Paciente'
    
    def severidad_badge(self, obj):
        colors = {
            'Leve': '#27ae60',
            'Moderada': '#f39c12',
            'Severa': '#e67e22',
            'Masiva': '#e74c3c',
        }
        color = colors.get(obj.severidad_hemorragia, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.severidad_hemorragia or "No calculada"
        )
    severidad_badge.short_description = 'Severidad'
    
    def perdida_sanguinea_badge(self, obj):
        if not obj.perdida_sanguinea_estimada:
            return format_html('<span style="color: #6c757d;">No registrada</span>')
        
        perdida = obj.perdida_sanguinea_estimada
        if perdida >= 1500:
            color = '#e74c3c'
        elif perdida >= 1000:
            color = '#e67e22'
        elif perdida >= 500:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} mL</span>',
            color, perdida
        )
    perdida_sanguinea_badge.short_description = 'Pérdida Sanguínea'
    
    def get_signos_vitales(self, obj):
        return f"PA: {obj.presion_arterial_sistolica}/{obj.presion_arterial_diastolica} - FC: {obj.frecuencia_cardiaca}"
    get_signos_vitales.short_description = 'Signos Vitales'
    
    def get_protocolo_manejo_display(self, obj):
        protocolo = obj.get_protocolo_manejo()
        result = [f"PASO {obj.paso_protocolo_actual}: {protocolo['titulo']}"]
        result.extend([f"• {accion}" for accion in protocolo['acciones']])
        return "\n".join(result)
    get_protocolo_manejo_display.short_description = 'Protocolo de Manejo'
    
    def get_recomendaciones_laboratorio_display(self, obj):
        recom_list = obj.get_recomendaciones_laboratorio()
        return "\n".join([f"• {r}" for r in recom_list])
    get_recomendaciones_laboratorio_display.short_description = 'Recomendaciones de Laboratorio'


@admin.register(SufrimientoFetal)
class SufrimientoFetalAdmin(admin.ModelAdmin):
    list_display = (
        'get_paciente_info',
        'fecha_evaluacion',
        'tipo_evaluacion',
        'fcf_badge',
        'clasificacion_ctg_badge',
        'riesgo_badge',
        'requiere_intervencion_inmediata',
    )
    
    list_filter = (
        'tipo_evaluacion',
        'tipo_monitoreo',
        'clasificacion_ctg',
        'riesgo_sufrimiento_fetal',
        'requiere_intervencion_inmediata',
        'variabilidad_fcf',
        'fecha_evaluacion',
    )
    
    search_fields = (
        'paciente_id',
        'embarazo_id',
        'parto_id',
    )
    
    readonly_fields = (
        'score_fisher',
        'perfil_biofsico_score',
        'clasificacion_ctg',
        'riesgo_sufrimiento_fetal',
        'conducta_recomendada',
        'requiere_intervencion_inmediata',
        'fecha_registro',
        'fecha_modificacion',
        'get_interpretacion_completa_display',
    )
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': (
                ('paciente_id', 'embarazo_id', 'parto_id'),
                ('fecha_evaluacion', 'edad_gestacional_semanas'),
                ('tipo_evaluacion', 'tipo_monitoreo'),
            )
        }),
        ('Cardiotocografía', {
            'fields': (
                ('fcf_basal', 'variabilidad_fcf'),
                ('aceleraciones_presentes',),
                ('desaceleraciones_tardias', 'desaceleraciones_variables', 'desaceleraciones_prolongadas'),
            )
        }),
        ('Perfil Biofísico', {
            'fields': (
                ('movimientos_fetales', 'tono_fetal'),
                ('liquido_amniotico',),
            ),
            'classes': ('collapse',)
        }),
        ('Doppler Fetal', {
            'fields': (
                ('indice_pulsatilidad_umbilical', 'indice_pulsatilidad_cerebral'),
            ),
            'classes': ('collapse',)
        }),
        ('Evaluación y Scores', {
            'fields': (
                ('score_fisher', 'perfil_biofsico_score'),
                ('clasificacion_ctg', 'riesgo_sufrimiento_fetal'),
                ('requiere_intervencion_inmediata',),
            )
        }),
        ('Conducta Clínica', {
            'fields': (
                ('conducta_recomendada',),
                ('get_interpretacion_completa_display',),
            )
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>{} sem - {}</small>',
            obj.paciente_id,
            obj.edad_gestacional_semanas,
            obj.get_tipo_evaluacion_display()
        )
    get_paciente_info.short_description = 'Paciente'
    
    def fcf_badge(self, obj):
        if not obj.fcf_basal:
            return format_html('<span style="color: #6c757d;">No registrada</span>')
        
        fcf = obj.fcf_basal
        if 110 <= fcf <= 160:
            color = '#27ae60'  # Normal
        elif 100 <= fcf < 110 or 160 < fcf <= 180:
            color = '#f39c12'  # Límite
        else:
            color = '#e74c3c'  # Anormal
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} lpm</span>',
            color, fcf
        )
    fcf_badge.short_description = 'FCF Basal'
    
    def clasificacion_ctg_badge(self, obj):
        if not obj.clasificacion_ctg:
            return format_html('<span style="color: #6c757d;">No clasificado</span>')
        
        colors = {
            'categoria_1': '#27ae60',
            'categoria_2': '#f39c12',
            'categoria_3': '#e74c3c',
        }
        
        nombres = {
            'categoria_1': 'CAT I',
            'categoria_2': 'CAT II',
            'categoria_3': 'CAT III',
        }
        
        color = colors.get(obj.clasificacion_ctg, '#6c757d')
        nombre = nombres.get(obj.clasificacion_ctg, obj.clasificacion_ctg)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, nombre
        )
    clasificacion_ctg_badge.short_description = 'CTG'
    
    def riesgo_badge(self, obj):
        if not obj.riesgo_sufrimiento_fetal:
            return format_html('<span style="color: #6c757d;">No evaluado</span>')
        
        colors = {
            'bajo': '#27ae60',
            'intermedio': '#f39c12',
            'alto': '#e74c3c',
        }
        
        nombres = {
            'bajo': 'BAJO',
            'intermedio': 'MEDIO',
            'alto': 'ALTO',
        }
        
        color = colors.get(obj.riesgo_sufrimiento_fetal, '#6c757d')
        nombre = nombres.get(obj.riesgo_sufrimiento_fetal, obj.riesgo_sufrimiento_fetal)
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, nombre
        )
    riesgo_badge.short_description = 'Riesgo'
    
    def get_interpretacion_completa_display(self, obj):
        interp = obj.get_interpretacion_completa()
        result = []
        for key, value in interp.items():
            result.append(f"{key}: {value}")
        return "\n".join(result)
    get_interpretacion_completa_display.short_description = 'Interpretación Completa'


# Personalizar títulos del admin
admin.site.site_header = "Sistema de Historias Clínicas - Calculadoras Médicas Avanzadas"
admin.site.site_title = "Calculadoras Médicas"
admin.site.index_title = "Gestión de Calculadoras Obstétricas Especializadas"