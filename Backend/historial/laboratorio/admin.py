from django.contrib import admin
from django.utils.html import format_html
from .models import TipoExamen, ExamenLaboratorio, ValorReferencia, ResultadoLaboratorio


@admin.register(TipoExamen)
class TipoExamenAdmin(admin.ModelAdmin):
    """Administración de Tipos de Exámenes"""
    
    list_display = [
        'codigo',
        'nombre',
        'categoria_badge',
        'precio_formatted',
        'tiempo_resultado',
        'activo_badge',
        'total_examenes_realizados',
        'examenes_mes_actual',
        'tiempo_promedio_badge',
        'porcentaje_urgentes_badge',
    ]
    
    list_filter = ['categoria', 'activo', 'fecha_creacion']
    
    search_fields = ['nombre', 'codigo', 'descripcion']
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'categoria', 'activo')
        }),
        ('Detalles del Examen', {
            'fields': ('descripcion', 'preparacion', 'tiempo_resultado', 'precio')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activar_examenes', 'desactivar_examenes']
    
    def categoria_badge(self, obj):
        colors = {
            'hematologia': '#e74c3c',
            'bioquimica': '#3498db',
            'inmunologia': '#9b59b6',
            'microbiologia': '#e67e22',
            'urinalisis': '#f39c12',
            'serologia': '#1abc9c',
            'hormonal': '#34495e',
            'genetica': '#2ecc71',
        }
        color = colors.get(obj.categoria, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoría'
    
    def precio_formatted(self, obj):
        return f"Bs. {obj.precio}"
    precio_formatted.short_description = 'Precio'
    precio_formatted.admin_order_field = 'precio'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>'
        )
    activo_badge.short_description = 'Estado'
    
    def total_examenes_realizados(self, obj):
        total = obj.examenes.count()
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
            total
        )
    total_examenes_realizados.short_description = 'Total Realizados'
    
    def examenes_mes_actual(self, obj):
        mes_actual = obj.get_examenes_realizados_mes()
        return format_html(
            '<span style="background-color: #2ecc71; color: white; padding: 2px 8px; border-radius: 10px;">{} este mes</span>',
            mes_actual
        )
    examenes_mes_actual.short_description = 'Este Mes'
    
    def tiempo_promedio_badge(self, obj):
        tiempo = obj.get_tiempo_promedio_resultado()
        if tiempo is None:
            return format_html('<span style="color: gray;">Sin datos</span>')
        
        color = '#27ae60' if tiempo <= 2 else '#f39c12' if tiempo <= 5 else '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} días</span>',
            color,
            tiempo
        )
    tiempo_promedio_badge.short_description = 'Tiempo Promedio'
    
    def porcentaje_urgentes_badge(self, obj):
        porcentaje = obj.get_porcentaje_urgentes()
        color = '#27ae60' if porcentaje <= 20 else '#f39c12' if porcentaje <= 50 else '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}% urgentes</span>',
            color,
            porcentaje
        )
    porcentaje_urgentes_badge.short_description = '% Urgentes'
    
    def activar_examenes(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} exámenes activados correctamente.')
    activar_examenes.short_description = 'Activar exámenes seleccionados'
    
    def desactivar_examenes(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} exámenes desactivados correctamente.')
    desactivar_examenes.short_description = 'Desactivar exámenes seleccionados'


class ValorReferenciaInline(admin.TabularInline):
    """Inline para valores de referencia"""
    model = ValorReferencia
    extra = 1
    fields = ['parametro', 'valor_minimo', 'valor_maximo', 'valor_normal', 'unidad', 'condicion', 'es_critico_bajo', 'es_critico_alto']


class ResultadoLaboratorioInline(admin.TabularInline):
    """Inline para resultados de laboratorio"""
    model = ResultadoLaboratorio
    extra = 0
    fields = ['valor_referencia', 'valor_numerico', 'valor_texto', 'es_normal', 'es_critico', 'observaciones']
    readonly_fields = ['es_normal', 'es_critico']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('valor_referencia')


@admin.register(ExamenLaboratorio)
class ExamenLaboratorioAdmin(admin.ModelAdmin):
    """Administración de Exámenes de Laboratorio"""
    
    list_display = [
        'id',
        'paciente_link',
        'tipo_examen_nombre',
        'categoria_badge',
        'fecha_solicitud_formatted',
        'estado_badge',
        'prioridad_badge',
        'tiene_resultados',
        'resultados_criticos_badge',
        'dias_transcurridos',
        'costo_estimado',
    ]
    
    list_filter = [
        'estado',
        'prioridad',
        'tipo_examen__categoria',
        'fecha_solicitud',
    ]
    
    search_fields = [
        'paciente__nombre',
        'paciente__apellido_paterno',
        'paciente__id_clinico',
        'tipo_examen__nombre',
    ]
    
    readonly_fields = [
        'fecha_solicitud',
        'fecha_creacion',
        'fecha_actualizacion',
        'dias_desde_solicitud',
        'esta_pendiente',
        'esta_vencido',
        'tiempo_total_proceso',
        'costo_total_estimado',
    ]
    
    autocomplete_fields = ['paciente', 'control_prenatal', 'tipo_examen', 'medico_solicitante']
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': ('paciente', 'control_prenatal')
        }),
        ('Datos del Examen', {
            'fields': ('tipo_examen', 'medico_solicitante', 'prioridad')
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_muestra', 'fecha_resultado')
        }),
        ('Estado', {
            'fields': ('estado', 'indicaciones', 'observaciones')
        }),
        ('Información del Sistema', {
            'fields': ('dias_desde_solicitud', 'esta_pendiente', 'esta_vencido', 'tiempo_total_proceso', 'costo_total_estimado', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ResultadoLaboratorioInline]
    
    actions = ['marcar_en_proceso', 'marcar_completado', 'marcar_cancelado']
    
    def paciente_link(self, obj):
        return format_html(
            '<a href="/admin/pacientes/paciente/{}/change/">{}</a>',
            obj.paciente.id,
            obj.paciente.nombre_completo
        )
    paciente_link.short_description = 'Paciente'
    
    def tipo_examen_nombre(self, obj):
        return obj.tipo_examen.nombre
    tipo_examen_nombre.short_description = 'Tipo de Examen'
    tipo_examen_nombre.admin_order_field = 'tipo_examen__nombre'
    
    def categoria_badge(self, obj):
        colors = {
            'hematologia': '#e74c3c',
            'bioquimica': '#3498db',
            'inmunologia': '#9b59b6',
            'microbiologia': '#e67e22',
            'urinalisis': '#f39c12',
            'serologia': '#1abc9c',
            'hormonal': '#34495e',
            'genetica': '#2ecc71',
        }
        color = colors.get(obj.tipo_examen.categoria, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.tipo_examen.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoría'
    
    def fecha_solicitud_formatted(self, obj):
        return obj.fecha_solicitud.strftime('%d/%m/%Y %H:%M')
    fecha_solicitud_formatted.short_description = 'Fecha Solicitud'
    fecha_solicitud_formatted.admin_order_field = 'fecha_solicitud'
    
    def estado_badge(self, obj):
        colors = {
            'solicitado': '#f39c12',
            'en_proceso': '#3498db',
            'completado': '#27ae60',
            'cancelado': '#e74c3c',
        }
        color = colors.get(obj.estado, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def prioridad_badge(self, obj):
        colors = {
            'normal': '#95a5a6',
            'urgente': '#e67e22',
            'stat': '#e74c3c',
        }
        color = colors.get(obj.prioridad, '#95a5a6')
        icon = '🔴' if obj.prioridad == 'stat' else '🟠' if obj.prioridad == 'urgente' else '⚪'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_prioridad_display()
        )
    prioridad_badge.short_description = 'Prioridad'
    
    def tiene_resultados(self, obj):
        count = obj.resultados.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {} resultados</span>',
                count
            )
        return format_html('<span style="color: gray;">Sin resultados</span>')
    tiene_resultados.short_description = 'Resultados'
    
    def resultados_criticos_badge(self, obj):
        criticos = obj.get_resultados_criticos_count()
        anormales = obj.get_resultados_anormales_count()
        
        if criticos > 0:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">🚨 {} críticos</span>',
                criticos
            )
        elif anormales > 0:
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 2px 8px; border-radius: 3px;">⚠️ {} anormales</span>',
                anormales
            )
        else:
            return format_html('<span style="color: green;">✓ Normales</span>')
    resultados_criticos_badge.short_description = 'Alertas'
    
    def dias_transcurridos(self, obj):
        dias = obj.dias_desde_solicitud
        if obj.esta_vencido:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} días (VENCIDO)</span>',
                dias
            )
        return f"{dias} días"
    dias_transcurridos.short_description = 'Días'
    
    def costo_estimado(self, obj):
        costo = obj.get_costo_total_estimado()
        color = '#e74c3c' if obj.prioridad == 'stat' else '#f39c12' if obj.prioridad == 'urgente' else '#27ae60'
        return format_html(
            '<span style="color: {}; font-weight: bold;">Bs. {}</span>',
            color,
            costo
        )
    costo_estimado.short_description = 'Costo'
    
    def marcar_en_proceso(self, request, queryset):
        updated = queryset.update(estado='en_proceso')
        self.message_user(request, f'{updated} exámenes marcados como "En Proceso".')
    marcar_en_proceso.short_description = 'Marcar como "En Proceso"'
    
    def marcar_completado(self, request, queryset):
        from django.utils import timezone
        queryset.update(estado='completado', fecha_resultado=timezone.now())
        self.message_user(request, f'{queryset.count()} exámenes marcados como "Completado".')
    marcar_completado.short_description = 'Marcar como "Completado"'
    
    def marcar_cancelado(self, request, queryset):
        updated = queryset.update(estado='cancelado')
        self.message_user(request, f'{updated} exámenes marcados como "Cancelado".')
    marcar_cancelado.short_description = 'Marcar como "Cancelado"'


@admin.register(ValorReferencia)
class ValorReferenciaAdmin(admin.ModelAdmin):
    """Administración de Valores de Referencia"""
    
    list_display = [
        'tipo_examen_nombre',
        'parametro',
        'rango_normal',
        'unidad',
        'condicion',
        'valores_criticos_badge',
    ]
    
    list_filter = ['tipo_examen__categoria', 'unidad']
    
    search_fields = ['parametro', 'tipo_examen__nombre']
    
    autocomplete_fields = ['tipo_examen']
    
    fieldsets = (
        ('Examen', {
            'fields': ('tipo_examen',)
        }),
        ('Parámetro', {
            'fields': ('parametro', 'unidad', 'condicion')
        }),
        ('Valores de Referencia', {
            'fields': ('valor_minimo', 'valor_maximo', 'valor_normal')
        }),
        ('Valores Críticos', {
            'fields': ('es_critico_bajo', 'es_critico_alto'),
            'classes': ('collapse',)
        }),
    )
    
    def tipo_examen_nombre(self, obj):
        return obj.tipo_examen.nombre
    tipo_examen_nombre.short_description = 'Tipo de Examen'
    tipo_examen_nombre.admin_order_field = 'tipo_examen__nombre'
    
    def rango_normal(self, obj):
        return obj.get_rango_completo()
    rango_normal.short_description = 'Rango Normal'
    
    def valores_criticos_badge(self, obj):
        if obj.es_critico_bajo or obj.es_critico_alto:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px;">🚨 Críticos definidos</span>'
            )
        return format_html('<span style="color: gray;">Sin valores críticos</span>')
    valores_criticos_badge.short_description = 'Valores Críticos'


@admin.register(ResultadoLaboratorio)
class ResultadoLaboratorioAdmin(admin.ModelAdmin):
    """Administración de Resultados de Laboratorio"""
    
    list_display = [
        'examen_info',
        'parametro',
        'valor_formatted',
        'rango_referencia',
        'estado_badge_mejorado',
        'interpretacion_badge',
        'tendencia_badge',
    ]
    
    list_filter = ['es_normal', 'es_critico', 'fecha_registro', 'valor_referencia__parametro']
    
    search_fields = [
        'examen__paciente__nombre',
        'examen__paciente__apellido_paterno',
        'valor_referencia__parametro',
    ]
    
    readonly_fields = [
        'es_normal', 
        'es_critico', 
        'fecha_registro',
        'interpretacion_medica_completa',
        'protocolo_medico',
        'recomendaciones_paciente',
        'tendencia_historica',
    ]
    
    autocomplete_fields = ['examen', 'valor_referencia']
    
    fieldsets = (
        ('Información del Examen', {
            'fields': ('examen', 'valor_referencia')
        }),
        ('Valores del Resultado', {
            'fields': ('valor_numerico', 'valor_texto', 'observaciones')
        }),
        ('Evaluación Automática', {
            'fields': ('es_normal', 'es_critico', 'fecha_registro'),
            'classes': ('collapse',)
        }),
        ('Interpretación Médica', {
            'fields': ('interpretacion_medica_completa', 'protocolo_medico', 'recomendaciones_paciente'),
            'classes': ('collapse',)
        }),
        ('Análisis Histórico', {
            'fields': ('tendencia_historica',),
            'classes': ('collapse',)
        }),
    )
    
    def examen_info(self, obj):
        return f"{obj.examen.tipo_examen.nombre} - {obj.examen.paciente.nombre_completo}"
    examen_info.short_description = 'Examen - Paciente'
    
    def parametro(self, obj):
        return obj.valor_referencia.parametro
    parametro.short_description = 'Parámetro'
    
    def valor_formatted(self, obj):
        if obj.valor_numerico:
            return f"{obj.valor_numerico} {obj.valor_referencia.unidad}"
        return obj.valor_texto or "N/A"
    valor_formatted.short_description = 'Valor'
    
    def rango_referencia(self, obj):
        return obj.valor_referencia.get_rango_completo()
    rango_referencia.short_description = 'Rango Normal'
    
    def estado_badge_mejorado(self, obj):
        if obj.es_critico:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">🚨 CRÍTICO</span>'
            )
        elif not obj.es_normal:
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">⚠️ ANORMAL</span>'
            )
        return format_html(
            '<span style="background-color: #27ae60; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✅ NORMAL</span>'
        )
    estado_badge_mejorado.short_description = 'Estado'
    
    def interpretacion_badge(self, obj):
        interpretacion = obj.get_interpretacion_medica()
        if '🔴' in interpretacion:
            color = '#e74c3c'
        elif '🟠' in interpretacion:
            color = '#e67e22'
        elif '🟡' in interpretacion:
            color = '#f39c12'
        else:
            color = '#27ae60'
            
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; max-width: 200px; display: inline-block; overflow: hidden; text-overflow: ellipsis;" title="{}">{}</span>',
            color,
            interpretacion,
            interpretacion[:30] + '...' if len(interpretacion) > 30 else interpretacion
        )
    interpretacion_badge.short_description = 'Interpretación'
    
    def tendencia_badge(self, obj):
        tendencia = obj.calcular_tendencia()
        if 'MEJORANDO' in tendencia:
            color = '#27ae60'
        elif 'EMPEORANDO' in tendencia:
            color = '#e74c3c'
        else:
            color = '#95a5a6'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            tendencia
        )
    tendencia_badge.short_description = 'Tendencia'
    
    def interpretacion_medica_completa(self, obj):
        return obj.get_interpretacion_medica()
    interpretacion_medica_completa.short_description = 'Interpretación Médica Completa'
    
    def protocolo_medico(self, obj):
        return obj.get_protocolo_sugerido()
    protocolo_medico.short_description = 'Protocolo Médico Sugerido'
    
    def recomendaciones_paciente(self, obj):
        return obj.get_recomendaciones_paciente()
    recomendaciones_paciente.short_description = 'Recomendaciones para el Paciente'
    
    def tendencia_historica(self, obj):
        valores = obj.get_valores_seguimiento()
        if len(valores) <= 1:
            return "Sin datos históricos suficientes"
        
        historial = []
        for i, valor in enumerate(valores[:5]):
            fecha = valor.fecha_registro.strftime('%d/%m/%Y')
            val = valor.valor_numerico if valor.valor_numerico else valor.valor_texto
            estado = "🔴 CRÍTICO" if valor.es_critico else "⚠️ ANORMAL" if not valor.es_normal else "✅ NORMAL"
            historial.append(f"{i+1}. {fecha}: {val} {valor.valor_referencia.unidad} - {estado}")
        
        return "\n".join(historial)
    tendencia_historica.short_description = 'Historial de Valores'


# Personalizar el título del admin
admin.site.site_header = "Sistema de Historias Clínicas - Administración"
admin.site.site_title = "Admin Fetal Medical"
admin.site.index_title = "Panel de Administración"