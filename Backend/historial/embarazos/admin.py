# =============================================================================
# ADMIN DE EMBARAZOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: embarazos
# Descripción: Configuración del panel administrativo de Django para gestión
#              de embarazos y complicaciones. Incluye filtros avanzados,
#              acciones masivas, badges visuales y búsqueda optimizada.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 COMPLETO
# Última actualización: 2025-11-14
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Embarazo, ComplicacionEmbarazo


# =============================================================================
# INLINE ADMIN: COMPLICACIONES EN EMBARAZO
# =============================================================================

class ComplicacionEmbarazoInline(admin.TabularInline):
    """
    Inline para mostrar y editar complicaciones directamente desde el embarazo.
    """
    model = ComplicacionEmbarazo
    extra = 0
    fields = [
        'tipo_complicacion',
        'fecha_diagnostico',
        'edad_gestacional_diagnostico',
        'severidad',
        'resuelto',
        'descripcion'
    ]
    readonly_fields = []
    can_delete = True


# =============================================================================
# ADMIN PRINCIPAL: EMBARAZOS
# =============================================================================

@admin.register(Embarazo)
class EmbarazoAdmin(admin.ModelAdmin):
    """
    Administración completa de embarazos en Django Admin.

    Características:
    - Listado optimizado con información clave
    - Filtros laterales por múltiples criterios
    - Búsqueda por paciente y médico
    - Acciones masivas (marcar alto riesgo, finalizar, etc.)
    - Badges de estado visual
    - Inline de complicaciones
    - Fieldsets organizados
    - Cálculos automáticos
    """

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE LISTADO
    # -------------------------------------------------------------------------

    list_display = [
        'id',
        'paciente_info',
        'numero_gesta_display',
        'edad_gestacional_display',
        'trimestre_badge',
        'tipo_embarazo_display',
        'estado_badge',
        'riesgo_badge',
        'complicaciones_count',
        'fecha_registro_short'
    ]

    list_display_links = ['id', 'paciente_info']

    list_filter = [
        'estado',
        'nivel_riesgo',
        'embarazo_alto_riesgo',
        'tipo_embarazo',
        'tiene_complicaciones',
        ('fecha_ultima_menstruacion', admin.DateFieldListFilter),
        ('fecha_probable_parto', admin.DateFieldListFilter),
        'activo'
    ]

    search_fields = [
        'paciente__nombres',
        'paciente__apellidos',
        'paciente__cedula_identidad',
        'medico_responsable',
        'numero_gesta'
    ]

    ordering = ['-fecha_registro']

    list_per_page = 25

    # -------------------------------------------------------------------------
    # FIELDSETS - ORGANIZACIÓN DE FORMULARIOS
    # -------------------------------------------------------------------------

    fieldsets = (
        ('INFORMACIÓN BÁSICA', {
            'fields': (
                'paciente',
                'numero_gesta',
                'es_planeado',
                'metodo_concepcion'
            )
        }),

        ('FECHAS CLAVE', {
            'fields': (
                'fecha_ultima_menstruacion',
                'fur_confiable',
                'fecha_probable_parto',
                'fecha_primera_ecografia',
                'edad_gestacional_primera_eco',
                'fpp_corregida_eco'
            )
        }),

        ('TIPO DE EMBARAZO', {
            'fields': (
                'tipo_embarazo',
                'numero_fetos',
                'corionicidad'
            )
        }),

        ('DATOS PRE-GESTACIONALES', {
            'fields': (
                'peso_pregestacional',
                'talla_madre',
                'imc_pregestacional',
                'clasificacion_imc',
                'semanas_al_diagnostico'
            ),
            'classes': ('collapse',)
        }),

        ('NIVEL DE RIESGO', {
            'fields': (
                'embarazo_alto_riesgo',
                'nivel_riesgo',
                'factores_riesgo'
            )
        }),

        ('COMPLICACIONES PRINCIPALES', {
            'fields': (
                'tiene_complicaciones',
                ('diabetes_gestacional', 'diabetes_gestacional_fecha'),
                ('hipertension_gestacional', 'hipertension_gestacional_fecha'),
                ('preeclampsia', 'preeclampsia_fecha', 'preeclampsia_severidad'),
                ('eclampsia', 'eclampsia_fecha'),
                ('sindrome_hellp', 'sindrome_hellp_fecha'),
                ('amenaza_parto_prematuro', 'amenaza_parto_prematuro_fecha'),
                ('ruptura_prematura_membranas', 'ruptura_prematura_membranas_fecha')
            ),
            'classes': ('collapse',)
        }),

        ('COMPLICACIONES PLACENTARIAS', {
            'fields': (
                ('placenta_previa', 'placenta_previa_tipo'),
                ('desprendimiento_placenta', 'desprendimiento_placenta_fecha'),
                'placenta_accreta',
                ('restriccion_crecimiento', 'restriccion_crecimiento_fecha', 'restriccion_crecimiento_tipo')
            ),
            'classes': ('collapse',)
        }),

        ('OTRAS COMPLICACIONES', {
            'fields': (
                ('polihidramnios', 'polihidramnios_fecha'),
                ('oligohidramnios', 'oligohidramnios_fecha'),
                ('colestasis_intrahepatica', 'colestasis_intrahepatica_fecha'),
                ('anemia_gestacional', 'hemoglobina_minima'),
                ('infeccion_urinaria_recurrente', 'numero_itus'),
                ('amenaza_aborto', 'amenaza_aborto_semanas'),
                ('incompetencia_cervical_actual', 'cerclaje_realizado', 'cerclaje_fecha')
            ),
            'classes': ('collapse',)
        }),

        ('HOSPITALIZACIÓN', {
            'fields': (
                'requirio_hospitalizacion',
                'numero_hospitalizaciones',
                'dias_hospitalizacion_total',
                'hospitalizacion_uci'
            ),
            'classes': ('collapse',)
        }),

        ('RESULTADO DEL EMBARAZO', {
            'fields': (
                'estado',
                'fecha_finalizacion',
                'edad_gestacional_finalizacion',
                'via_finalizacion',
                'indicacion_cesarea',
                'resultado_embarazo'
            ),
            'classes': ('collapse',)
        }),

        ('MÉDICO Y OBSERVACIONES', {
            'fields': (
                'medico_responsable',
                'medico_responsable_fk',
                'notas',
                'plan_parto'
            ),
            'classes': ('collapse',)
        }),

        ('AUDITORÍA', {
            'fields': (
                'activo',
                'fecha_registro',
                'creado_por',
                'fecha_modificacion',
                'modificado_por'
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'fecha_registro',
        'fecha_modificacion',
        'imc_pregestacional',
        'clasificacion_imc',
        'fecha_probable_parto'
    ]

    # -------------------------------------------------------------------------
    # INLINES
    # -------------------------------------------------------------------------

    inlines = [ComplicacionEmbarazoInline]

    # -------------------------------------------------------------------------
    # MÉTODOS DE DISPLAY PERSONALIZADOS
    # -------------------------------------------------------------------------

    def paciente_info(self, obj):
        """Muestra información de la paciente con enlace."""
        if obj.paciente:
            url = reverse('admin:pacientes_paciente_change', args=[obj.paciente.id])
            return format_html(
                '<a href="{}">{}</a><br><small>{}</small>',
                url,
                f"{obj.paciente.nombres} {obj.paciente.apellidos}",
                obj.paciente.cedula_identidad
            )
        return '-'
    paciente_info.short_description = 'Paciente'

    def numero_gesta_display(self, obj):
        """Muestra número de gesta con formato."""
        return f"G{obj.numero_gesta}"
    numero_gesta_display.short_description = 'Gesta'
    numero_gesta_display.admin_order_field = 'numero_gesta'

    def edad_gestacional_display(self, obj):
        """Muestra edad gestacional actual."""
        if obj.estado == 'en_curso':
            eg = obj.get_edad_gestacional_actual()
            if eg:
                semanas = int(eg)
                dias = int((eg - semanas) * 7)
                return format_html(
                    '<strong>{}</strong> sem + {} días',
                    semanas, dias
                )
        elif obj.edad_gestacional_finalizacion:
            return format_html(
                '{} sem <small>(final)</small>',
                int(obj.edad_gestacional_finalizacion)
            )
        return '-'
    edad_gestacional_display.short_description = 'Edad Gestacional'

    def trimestre_badge(self, obj):
        """Badge del trimestre actual."""
        if obj.estado == 'en_curso':
            trimestre = obj.get_trimestre_actual()
            if trimestre:
                colors = {1: '#3498db', 2: '#e74c3c', 3: '#2ecc71'}
                color = colors.get(trimestre, '#95a5a6')
                return format_html(
                    '<span style="background-color: {}; color: white; padding: 3px 8px; '
                    'border-radius: 3px; font-weight: bold; font-size: 11px;">{}° TRIM</span>',
                    color, trimestre
                )
        return format_html('<span style="color: #999;">-</span>')
    trimestre_badge.short_description = 'Trimestre'

    def tipo_embarazo_display(self, obj):
        """Tipo de embarazo formateado."""
        return obj.get_tipo_embarazo_display()
    tipo_embarazo_display.short_description = 'Tipo'
    tipo_embarazo_display.admin_order_field = 'tipo_embarazo'

    def estado_badge(self, obj):
        """Badge visual del estado del embarazo."""
        colors = {
            'en_curso': '#2ecc71',
            'finalizado_parto': '#3498db',
            'finalizado_cesarea': '#9b59b6',
            'finalizado_aborto': '#e74c3c',
            'finalizado_muerte_fetal': '#c0392b',
            'finalizado_otro': '#95a5a6'
        }
        color = colors.get(obj.estado, '#34495e')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 3px; font-weight: bold; font-size: 10px; text-transform: uppercase;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'estado'

    def riesgo_badge(self, obj):
        """Badge visual del nivel de riesgo."""
        colors = {
            'bajo': '#27ae60',
            'medio': '#f39c12',
            'alto': '#e67e22',
            'muy_alto': '#c0392b'
        }
        color = colors.get(obj.nivel_riesgo, '#95a5a6')

        icon = ''
        if obj.nivel_riesgo in ['alto', 'muy_alto']:
            icon = '⚠️ '

        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; '
            'border-radius: 3px; font-weight: bold; font-size: 10px;">{}{}</span>',
            color, icon, obj.get_nivel_riesgo_display().upper()
        )
    riesgo_badge.short_description = 'Riesgo'
    riesgo_badge.admin_order_field = 'nivel_riesgo'

    def complicaciones_count(self, obj):
        """Contador de complicaciones."""
        count = obj.complicaciones_detalladas.count()
        if count > 0:
            color = '#e74c3c' if count >= 3 else '#f39c12'
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 50%; font-weight: bold; font-size: 11px;">{}</span>',
                color, count
            )
        return format_html('<span style="color: #27ae60;">✓</span>')
    complicaciones_count.short_description = 'Compl.'

    def fecha_registro_short(self, obj):
        """Fecha de registro formateada."""
        return obj.fecha_registro.strftime('%d/%m/%Y') if obj.fecha_registro else '-'
    fecha_registro_short.short_description = 'Fecha Registro'
    fecha_registro_short.admin_order_field = 'fecha_registro'

    # -------------------------------------------------------------------------
    # ACCIONES MASIVAS
    # -------------------------------------------------------------------------

    actions = ['marcar_alto_riesgo', 'marcar_bajo_riesgo', 'finalizar_embarazos', 'activar_embarazos']

    def marcar_alto_riesgo(self, request, queryset):
        """Marca embarazos seleccionados como alto riesgo."""
        updated = queryset.update(embarazo_alto_riesgo=True, nivel_riesgo='alto')
        self.message_user(request, f'{updated} embarazo(s) marcado(s) como alto riesgo.')
    marcar_alto_riesgo.short_description = "Marcar como ALTO RIESGO"

    def marcar_bajo_riesgo(self, request, queryset):
        """Marca embarazos seleccionados como bajo riesgo."""
        updated = queryset.update(embarazo_alto_riesgo=False, nivel_riesgo='bajo')
        self.message_user(request, f'{updated} embarazo(s) marcado(s) como bajo riesgo.')
    marcar_bajo_riesgo.short_description = "Marcar como BAJO RIESGO"

    def finalizar_embarazos(self, request, queryset):
        """Finaliza embarazos en curso (requiere confirmación)."""
        en_curso = queryset.filter(estado='en_curso')
        count = en_curso.count()
        if count > 0:
            self.message_user(
                request,
                f'ATENCIÓN: {count} embarazo(s) en curso. Finalizar manualmente cada uno.',
                level='warning'
            )
        else:
            self.message_user(request, 'Ningún embarazo en curso seleccionado.', level='info')
    finalizar_embarazos.short_description = "Verificar embarazos para finalizar"

    def activar_embarazos(self, request, queryset):
        """Reactiva embarazos eliminados."""
        updated = queryset.update(activo=True, eliminado=False)
        self.message_user(request, f'{updated} embarazo(s) reactivado(s).')
    activar_embarazos.short_description = "Reactivar embarazos eliminados"

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN ADICIONAL
    # -------------------------------------------------------------------------

    def get_queryset(self, request):
        """Optimiza queryset con select_related y prefetch_related."""
        qs = super().get_queryset(request)
        return qs.select_related('paciente', 'medico_responsable_fk').prefetch_related('complicaciones_detalladas')


# =============================================================================
# ADMIN: COMPLICACIONES DE EMBARAZO
# =============================================================================

@admin.register(ComplicacionEmbarazo)
class ComplicacionEmbarazoAdmin(admin.ModelAdmin):
    """
    Administración de complicaciones de embarazos.
    """

    list_display = [
        'id',
        'embarazo_link',
        'tipo_complicacion_display',
        'fecha_diagnostico',
        'severidad_badge',
        'resuelto_badge',
        'requirio_hospitalizacion'
    ]

    list_filter = [
        'tipo_complicacion',
        'severidad',
        'resuelto',
        'requirio_hospitalizacion',
        'requirio_uci',
        ('fecha_diagnostico', admin.DateFieldListFilter)
    ]

    search_fields = [
        'embarazo__paciente__nombres',
        'embarazo__paciente__apellidos',
        'descripcion',
        'tratamiento'
    ]

    ordering = ['-fecha_diagnostico']

    fieldsets = (
        ('INFORMACIÓN BÁSICA', {
            'fields': (
                'embarazo',
                'tipo_complicacion',
                'fecha_diagnostico',
                'edad_gestacional_diagnostico',
                'severidad'
            )
        }),

        ('DETALLES CLÍNICOS', {
            'fields': (
                'descripcion',
                'sintomas',
                'hallazgos_clinicos',
                'tratamiento',
                'medicamentos'
            )
        }),

        ('HOSPITALIZACIÓN', {
            'fields': (
                'requirio_hospitalizacion',
                'fecha_hospitalizacion',
                'dias_hospitalizacion',
                'requirio_uci'
            ),
            'classes': ('collapse',)
        }),

        ('RESOLUCIÓN', {
            'fields': (
                'resuelto',
                'fecha_resolucion',
                'secuelas'
            )
        }),

        ('AUDITORÍA', {
            'fields': (
                'creado_por',
                'fecha_creacion',
                'modificado_por',
                'fecha_modificacion'
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['fecha_creacion', 'fecha_modificacion']

    # -------------------------------------------------------------------------
    # MÉTODOS DE DISPLAY
    # -------------------------------------------------------------------------

    def embarazo_link(self, obj):
        """Enlace al embarazo."""
        if obj.embarazo:
            url = reverse('admin:embarazos_embarazo_change', args=[obj.embarazo.id])
            return format_html(
                '<a href="{}">Embarazo #{} - {}</a>',
                url,
                obj.embarazo.id,
                f"{obj.embarazo.paciente.nombres} {obj.embarazo.paciente.apellidos}"
            )
        return '-'
    embarazo_link.short_description = 'Embarazo'

    def tipo_complicacion_display(self, obj):
        """Tipo de complicación."""
        return obj.get_tipo_complicacion_display()
    tipo_complicacion_display.short_description = 'Tipo'
    tipo_complicacion_display.admin_order_field = 'tipo_complicacion'

    def severidad_badge(self, obj):
        """Badge de severidad."""
        colors = {
            'leve': '#27ae60',
            'moderada': '#f39c12',
            'grave': '#e67e22',
            'critica': '#c0392b'
        }
        color = colors.get(obj.severidad, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 10px;">{}</span>',
            color, obj.get_severidad_display().upper()
        )
    severidad_badge.short_description = 'Severidad'
    severidad_badge.admin_order_field = 'severidad'

    def resuelto_badge(self, obj):
        """Badge de resolución."""
        if obj.resuelto:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Resuelto</span>'
            )
        return format_html(
            '<span style="color: #e74c3c; font-weight: bold;">⚠ Activa</span>'
        )
    resuelto_badge.short_description = 'Estado'
    resuelto_badge.admin_order_field = 'resuelto'


# =============================================================================
# FIN DEL ARCHIVO - embarazos/admin.py
# =============================================================================
