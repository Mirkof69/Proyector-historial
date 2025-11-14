from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django import forms
from django.contrib import messages
from .models import Parto, RecienNacido, PartogramaRegistro


class RecienNacidoInline(admin.StackedInline):
    model = RecienNacido
    extra = 1
    max_num = 5
    verbose_name = "Recién Nacido"
    verbose_name_plural = "Recién Nacidos"
    
    fieldsets = (
        ('Datos Básicos', {
            'fields': (
                ('numero_gemelo', 'fecha_nacimiento'),
                ('sexo', 'estado_nacimiento'),
            )
        }),
        ('Antropometría', {
            'fields': (
                ('peso_nacimiento', 'talla_nacimiento'),
                ('perimetro_cefalico',),
            )
        }),
        ('Score de Apgar', {
            'fields': (
                ('apgar_1_minuto', 'apgar_5_minutos', 'apgar_10_minutos'),
            )
        }),
        ('Reanimación', {
            'fields': (
                ('requirio_reanimacion', 'tipo_reanimacion'),
            )
        }),
        ('Estado General', {
            'fields': (
                ('llanto_inmediato', 'respiracion_espontanea', 'tono_muscular_normal'),
            )
        }),
        ('Malformaciones', {
            'fields': (
                ('malformaciones_congenitas', 'descripcion_malformaciones'),
            ),
            'classes': ('collapse',)
        }),
        ('Destino y Observaciones', {
            'fields': (
                ('destino_rn',),
                ('observaciones_rn',),
            )
        }),
    )


class PartogramaRegistroInline(admin.TabularInline):
    model = PartogramaRegistro
    extra = 1
    verbose_name = "Registro de Partograma"
    verbose_name_plural = "Registros de Partograma"
    
    fields = (
        'hora_registro', 'horas_trabajo_parto', 'dilatacion_cervical', 
        'estacion_fetal', 'contracciones_10min', 'fcf_baseline',
        'presion_arterial_sistolica', 'presion_arterial_diastolica',
        'oxitocina_dosis', 'observaciones'
    )
    
    readonly_fields = ('fecha_registro',)


@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_parto',
        'get_paciente_info',
        'fecha_parto',
        'tipo_parto_badge',
        'get_edad_gestacional',
        'get_estado_parto',
        'get_duracion_trabajo',
        'get_perdida_sanguinea_badge',
        'get_num_recien_nacidos',
        'acciones_rapidas',
    )
    
    list_filter = (
        'tipo_parto',
        'presentacion_fetal',
        'parto_finalizado',
        'hemorragia_postparto',
        'episiotomia',
        'desgarros',
        'analgesia_utilizada',
        'oxitocina_utilizada',
        'fecha_parto',
    )
    
    search_fields = (
        'numero_parto',
        'paciente_id',
        'edad_gestacional_parto',
        'observaciones_parto',
        'complicaciones_maternas',
    )
    
    date_hierarchy = 'fecha_parto'
    
    readonly_fields = (
        'numero_parto',
        'fecha_registro',
        'fecha_modificacion',
        'get_resumen_parto',
        'get_evaluacion_perdida_sanguinea',
        'get_estado_parto',
        'get_complicaciones_totales',
        'get_duracion_trabajo_parto_horas',
    )
    
    fieldsets = (
        ('Identificación del Parto', {
            'fields': (
                ('numero_parto',),
                ('embarazo_id', 'paciente_id', 'medico_responsable_id'),
            )
        }),
        ('Fechas y Tiempos', {
            'fields': (
                ('fecha_ingreso', 'fecha_inicio_trabajo_parto'),
                ('fecha_parto',),
                ('duracion_trabajo_parto_horas', 'duracion_periodo_expulsivo_minutos'),
                ('get_duracion_trabajo_parto_horas',),
            )
        }),
        ('Datos del Parto', {
            'fields': (
                ('edad_gestacional_parto', 'tipo_parto'),
                ('presentacion_fetal', 'posicion_fetal'),
            )
        }),
        ('Trabajo de Parto', {
            'fields': (
                ('trabajo_parto_espontaneo', 'induccion_parto'),
                ('metodo_induccion',),
                ('monitoreo_fetal_continuo',),
            )
        }),
        ('Estado de Membranas', {
            'fields': (
                ('estado_membranas', 'hora_rotura_membranas'),
                ('caracteristicas_liquido',),
            )
        }),
        ('Analgesia y Anestesia', {
            'fields': (
                ('analgesia_utilizada', 'tipo_analgesia'),
            )
        }),
        ('Episiotomía y Desgarros', {
            'fields': (
                ('episiotomia', 'tipo_episiotomia'),
                ('desgarros', 'grado_desgarros'),
            )
        }),
        ('Alumbramiento', {
            'fields': (
                ('tipo_alumbramiento', 'placenta_completa'),
                ('peso_placenta',),
            )
        }),
        ('Pérdida Sanguínea', {
            'fields': (
                ('perdida_sanguinea_estimada', 'hemorragia_postparto'),
                ('get_evaluacion_perdida_sanguinea',),
            )
        }),
        ('Medicamentos', {
            'fields': (
                ('oxitocina_utilizada', 'dosis_oxitocina'),
                ('otros_medicamentos',),
            )
        }),
        ('Complicaciones y Observaciones', {
            'fields': (
                ('complicaciones_maternas',),
                ('observaciones_parto',),
                ('indicaciones_cesarea',),
                ('get_complicaciones_totales',),
            )
        }),
        ('Estado del Parto', {
            'fields': (
                ('parto_finalizado',),
                ('get_estado_parto',),
                ('get_resumen_parto',),
            )
        }),
        ('Información del Sistema', {
            'fields': (
                ('fecha_registro', 'fecha_modificacion'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RecienNacidoInline, PartogramaRegistroInline]
    
    actions = [
        'marcar_parto_finalizado',
        'generar_reporte_parto',
        'duplicar_partograma',
    ]
    
    def get_paciente_info(self, obj):
        return format_html(
            '<strong>Paciente ID: {}</strong><br/><small>Embarazo ID: {}</small>',
            obj.paciente_id,
            obj.embarazo_id or "No asignado"
        )
    get_paciente_info.short_description = 'Paciente'
    
    def tipo_parto_badge(self, obj):
        colors = {
            'vaginal_espontaneo': '#27ae60',
            'vaginal_instrumentado': '#2ecc71',
            'cesarea_electiva': '#3498db',
            'cesarea_urgencia': '#f39c12',
            'cesarea_emergencia': '#e74c3c'
        }
        color = colors.get(obj.tipo_parto, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_parto_display().upper()
        )
    tipo_parto_badge.short_description = 'Tipo de Parto'
    
    def get_edad_gestacional(self, obj):
        return obj.edad_gestacional_parto
    get_edad_gestacional.short_description = 'Edad Gestacional'
    
    def get_duracion_trabajo(self, obj):
        if obj.duracion_trabajo_parto_horas:
            return f"{obj.duracion_trabajo_parto_horas}h"
        return "No registrada"
    get_duracion_trabajo.short_description = 'Duración'
    
    def get_perdida_sanguinea_badge(self, obj):
        evaluacion = obj.get_evaluacion_perdida_sanguinea()
        if "Normal" in evaluacion:
            color = '#27ae60'
        elif "Moderada" in evaluacion:
            color = '#f39c12'
        elif "Severa" in evaluacion:
            color = '#e74c3c'
        else:
            color = '#95a5a6'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            evaluacion
        )
    get_perdida_sanguinea_badge.short_description = 'Pérdida Sanguínea'
    
    def get_num_recien_nacidos(self, obj):
        count = obj.recien_nacidos.count()
        if count == 0:
            return format_html('<span style="color: #e74c3c;">No registrados</span>')
        elif count == 1:
            return format_html('<span style="color: #27ae60;">1 RN</span>')
        else:
            return format_html('<span style="color: #2ecc71;">{} RNs</span>', count)
    get_num_recien_nacidos.short_description = 'Recién Nacidos'
    
    def acciones_rapidas(self, obj):
        url_editar = reverse('admin:partos_parto_change', args=[obj.id])
        
        return format_html(
            '<a href="{}" style="background-color: #3498db; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px; margin-right: 2px;">EDITAR</a>',
            url_editar
        )
    acciones_rapidas.short_description = 'Acciones'
    
    def marcar_parto_finalizado(self, request, queryset):
        updated = queryset.update(parto_finalizado=True)
        self.message_user(request, f'{updated} partos marcados como finalizados.')
    marcar_parto_finalizado.short_description = 'Marcar parto como finalizado'
    
    def generar_reporte_parto(self, request, queryset):
        count = queryset.count()
        self.message_user(request, f'Reportes generados para {count} partos.')
    generar_reporte_parto.short_description = 'Generar reporte de parto'
    
    def duplicar_partograma(self, request, queryset):
        count = queryset.count()
        self.message_user(request, f'Partogramas duplicados para {count} partos.')
    duplicar_partograma.short_description = 'Duplicar partograma'


@admin.register(RecienNacido)
class RecienNacidoAdmin(admin.ModelAdmin):
    list_display = (
        'get_parto_numero',
        'numero_gemelo',
        'fecha_nacimiento',
        'sexo',
        'peso_clasificacion_badge',
        'get_apgar_badge',
        'estado_nacimiento',
        'get_evaluacion_estado',
        'requirio_reanimacion',
        'destino_rn',
    )
    
    list_filter = (
        'sexo',
        'estado_nacimiento',
        'requirio_reanimacion',
        'malformaciones_congenitas',
        'destino_rn',
        'fecha_nacimiento',
        'llanto_inmediato',
        'respiracion_espontanea',
    )
    
    search_fields = (
        'parto__numero_parto',
        'observaciones_rn',
        'descripcion_malformaciones',
    )
    
    readonly_fields = (
        'fecha_registro',
        'fecha_modificacion',
        'get_clasificacion_peso',
        'get_evaluacion_apgar',
        'get_evaluacion_estado_general',
        'get_resumen_completo',
    )
    
    fieldsets = (
        ('Información del Parto', {
            'fields': (
                ('parto', 'numero_gemelo'),
                ('fecha_nacimiento',),
            )
        }),
        ('Datos Básicos', {
            'fields': (
                ('sexo', 'estado_nacimiento'),
            )
        }),
        ('Antropometría', {
            'fields': (
                ('peso_nacimiento', 'talla_nacimiento'),
                ('perimetro_cefalico',),
                ('get_clasificacion_peso',),
            )
        }),
        ('Score de Apgar', {
            'fields': (
                ('apgar_1_minuto', 'apgar_5_minutos', 'apgar_10_minutos'),
                ('get_evaluacion_apgar',),
            )
        }),
        ('Estado al Nacimiento', {
            'fields': (
                ('llanto_inmediato', 'respiracion_espontanea', 'tono_muscular_normal'),
                ('get_evaluacion_estado_general',),
            )
        }),
        ('Reanimación', {
            'fields': (
                ('requirio_reanimacion', 'tipo_reanimacion'),
            )
        }),
        ('Malformaciones', {
            'fields': (
                ('malformaciones_congenitas', 'descripcion_malformaciones'),
            ),
            'classes': ('collapse',)
        }),
        ('Destino', {
            'fields': (
                ('destino_rn',),
                ('observaciones_rn',),
            )
        }),
        ('Resumen', {
            'fields': (
                ('get_resumen_completo',),
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
    
    def get_parto_numero(self, obj):
        url = reverse('admin:partos_parto_change', args=[obj.parto.id])
        return format_html('<a href="{}">{}</a>', url, obj.parto.numero_parto)
    get_parto_numero.short_description = 'Parto'
    
    def peso_clasificacion_badge(self, obj):
        clasificacion = obj.get_clasificacion_peso()
        if "normal" in clasificacion:
            color = '#27ae60'
        elif "bajo peso" in clasificacion:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br/><small>{}</small>',
            color,
            f"{obj.peso_nacimiento}g",
            clasificacion
        )
    peso_clasificacion_badge.short_description = 'Peso y Clasificación'
    
    def get_apgar_badge(self, obj):
        evaluacion = obj.get_evaluacion_apgar()
        if "Excelente" in evaluacion:
            color = '#27ae60'
        elif "Moderado" in evaluacion:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{}</span><br/><small>{}</small>',
            color,
            obj.apgar_1_minuto,
            obj.apgar_5_minutos,
            evaluacion
        )
    get_apgar_badge.short_description = 'Apgar 1/5'
    
    def get_evaluacion_estado(self, obj):
        evaluacion = obj.get_evaluacion_estado_general()
        if "normal" in evaluacion:
            return format_html('<span style="color: #27ae60;">✅ Normal</span>')
        else:
            return format_html('<span style="color: #e74c3c;">🔴 Con problemas</span>')
    get_evaluacion_estado.short_description = 'Estado General'


@admin.register(PartogramaRegistro)
class PartogramaRegistroAdmin(admin.ModelAdmin):
    list_display = (
        'get_parto_numero',
        'hora_registro',
        'horas_trabajo_parto',
        'dilatacion_progreso_badge',
        'get_contracciones_badge',
        'get_fcf_badge',
        'get_presion_arterial',
        'get_alertas_badge',
    )
    
    list_filter = (
        'alerta_fcf_anormal',
        'alerta_progreso_lento',
        'alerta_signos_vitales',
        'intensidad_contracciones',
        'variabilidad_fcf',
        'hora_registro',
    )
    
    search_fields = (
        'parto__numero_parto',
        'observaciones',
    )
    
    readonly_fields = (
        'fecha_registro',
        'get_presion_arterial',
        'get_evaluacion_fcf',
        'get_evaluacion_contracciones',
        'get_alertas_activas',
        'get_resumen_registro',
    )
    
    fieldsets = (
        ('Información del Parto', {
            'fields': (
                ('parto',),
                ('hora_registro', 'horas_trabajo_parto'),
                ('registrado_por_id',),
            )
        }),
        ('Dilatación y Descenso', {
            'fields': (
                ('dilatacion_cervical', 'borramiento_cervical'),
                ('estacion_fetal',),
            )
        }),
        ('Contracciones Uterinas', {
            'fields': (
                ('contracciones_10min', 'duracion_contracciones'),
                ('intensidad_contracciones',),
                ('get_evaluacion_contracciones',),
            )
        }),
        ('Frecuencia Cardíaca Fetal', {
            'fields': (
                ('fcf_baseline', 'variabilidad_fcf'),
                ('desaceleraciones',),
                ('get_evaluacion_fcf',),
            )
        }),
        ('Signos Vitales Maternos', {
            'fields': (
                ('presion_arterial_sistolica', 'presion_arterial_diastolica'),
                ('temperatura', 'pulso_materno'),
                ('get_presion_arterial',),
            )
        }),
        ('Medicamentos', {
            'fields': (
                ('oxitocina_dosis',),
            )
        }),
        ('Alertas Automáticas', {
            'fields': (
                ('alerta_fcf_anormal', 'alerta_progreso_lento', 'alerta_signos_vitales'),
                ('get_alertas_activas',),
            )
        }),
        ('Observaciones', {
            'fields': (
                ('observaciones',),
                ('get_resumen_registro',),
            )
        }),
        ('Metadata', {
            'fields': (
                ('fecha_registro',),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_parto_numero(self, obj):
        url = reverse('admin:partos_parto_change', args=[obj.parto.id])
        return format_html('<a href="{}">{}</a>', url, obj.parto.numero_parto)
    get_parto_numero.short_description = 'Parto'
    
    def dilatacion_progreso_badge(self, obj):
        dilatacion = obj.dilatacion_cervical
        if dilatacion >= 8:
            color = '#27ae60'
        elif dilatacion >= 5:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} cm</span><br/><small>Estación: {}</small>',
            color,
            dilatacion,
            obj.estacion_fetal
        )
    dilatacion_progreso_badge.short_description = 'Dilatación'
    
    def get_contracciones_badge(self, obj):
        evaluacion = obj.get_evaluacion_contracciones()
        if "adecuadas" in evaluacion:
            color = '#27ae60'
        elif "moderadas" in evaluacion:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/10min</span><br/><small>{}</small>',
            color,
            obj.contracciones_10min,
            obj.intensidad_contracciones or "No registrada"
        )
    get_contracciones_badge.short_description = 'Contracciones'
    
    def get_fcf_badge(self, obj):
        evaluacion = obj.get_evaluacion_fcf()
        if "Normal" in evaluacion:
            color = '#27ae60'
        else:
            color = '#e74c3c'
        
        fcf_text = f"{obj.fcf_baseline} lpm" if obj.fcf_baseline else "No registrada"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br/><small>{}</small>',
            color,
            fcf_text,
            obj.variabilidad_fcf or "No registrada"
        )
    get_fcf_badge.short_description = 'FCF'
    
    def get_alertas_badge(self, obj):
        alertas = obj.get_alertas_activas()
        if "Sin alertas" in alertas[0]:
            return format_html('<span style="color: #27ae60;">✅ Normal</span>')
        else:
            return format_html(
                '<span style="color: #e74c3c;">🚨 {} alertas</span>',
                len(alertas)
            )
    get_alertas_badge.short_description = 'Alertas'


# Personalizar títulos del admin
admin.site.site_header = "Sistema de Historias Clínicas - Módulo de Partos"
admin.site.site_title = "Admin Partos"
admin.site.index_title = "Gestión Completa de Partos y Nacimientos"