"""
===========================================
MÓDULO: ADMIN DE PARTOS
===========================================
Descripción:
    Configuración del panel de administración de Django para partos.
    Incluye interfaces personalizadas con badges, filtros y acciones masivas.

Funcionalidades:
    - Admin para Parto con recién nacidos y complicaciones inline
    - Admin para RecienNacido con información detallada
    - Admin para ComplicacionParto con gestión de resoluciones
    - Badges de colores para estados y tipos
    - Filtros avanzados por múltiples campos
    - Acciones masivas (finalizar, marcar complicaciones)
    - Búsqueda avanzada

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import Parto, RecienNacido, ComplicacionParto


# ===========================================
# INLINE: RECIÉN NACIDOS
# ===========================================
class RecienNacidoInline(admin.TabularInline):
    """
    INLINE: Inline para mostrar recién nacidos en el admin de Parto

    Funcionamiento:
        Permite agregar/editar recién nacidos directamente desde el formulario de parto
        Muestra los campos principales en formato tabular
    """
    model = RecienNacido
    extra = 1
    fields = [
        'numero_hijo',
        'sexo',
        'peso',
        'talla',
        'perimetro_cefalico',
        'apgar_1min',
        'apgar_5min',
        'estado_al_nacer',
        'reanimacion',
        'malformaciones',
    ]
    readonly_fields = []


# ===========================================
# INLINE: COMPLICACIONES
# ===========================================
class ComplicacionPartoInline(admin.TabularInline):
    """
    INLINE: Inline para mostrar complicaciones en el admin de Parto

    Funcionamiento:
        Permite agregar/editar complicaciones directamente desde el formulario de parto
        Muestra los campos principales en formato tabular
    """
    model = ComplicacionParto
    extra = 0
    fields = [
        'tipo_complicacion',
        'descripcion',
        'tratamiento',
        'resuelto',
    ]
    readonly_fields = []


# ===========================================
# ADMIN: PARTO
# ===========================================
@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    """
    ADMIN: Configuración del administrador para Parto

    Funcionamiento:
        Panel de administración completo para gestión de partos
        Incluye filtros, búsqueda, acciones masivas y visualización detallada

    Características:
        - Lista con información principal y badges de color
        - Filtros por tipo, vía, estado, fecha
        - Búsqueda por paciente
        - Acciones masivas para cambios de estado
        - Inlines para recién nacidos y complicaciones
        - Fieldsets organizados por categorías
    """

    # Configuración de la lista
    list_display = [
        'id',
        'fecha_parto_badge',
        'paciente_info',
        'tipo_parto_badge',
        'via_parto_badge',
        'edad_gestacional_display',
        'recien_nacidos_count',
        'complicaciones_badge',
        'estado_badge',
    ]

    list_filter = [
        'tipo_parto',
        'via_parto',
        'estado',
        'complicaciones',
        'fecha_parto',
        ('medico', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'id',
        'paciente__nombre',
        'paciente__apellido',
        'paciente__ci',
        'observaciones',
    ]

    readonly_fields = [
        'id',
        'uuid',
        'fecha_registro',
        'fecha_actualizacion',
        'duracion_horas_display',
    ]

    # Ordenamiento
    ordering = ['-fecha_parto', '-hora_inicio']

    # Paginación
    list_per_page = 25

    # Inlines
    inlines = [RecienNacidoInline, ComplicacionPartoInline]

    # Campos para autocompletado
    autocomplete_fields = ['paciente', 'embarazo', 'medico']

    # Organización en fieldsets
    fieldsets = (
        ('Información General', {
            'fields': (
                'id',
                'uuid',
                'embarazo',
                'paciente',
                'medico',
            )
        }),
        ('Fecha y Hora', {
            'fields': (
                'fecha_parto',
                'hora_inicio',
                'hora_fin',
                'duracion_trabajo_parto',
                'duracion_horas_display',
            )
        }),
        ('Tipo y Vía de Parto', {
            'fields': (
                'tipo_parto',
                'via_parto',
            )
        }),
        ('Datos del Parto', {
            'fields': (
                'edad_gestacional_semanas',
                'edad_gestacional_dias',
                'indicaciones',
                'anestesia',
                'procedimientos',
            )
        }),
        ('Complicaciones', {
            'fields': (
                'complicaciones',
                'descripcion_complicaciones',
            )
        }),
        ('Estado y Observaciones', {
            'fields': (
                'estado',
                'observaciones',
            )
        }),
        ('Auditoría', {
            'fields': (
                'fecha_registro',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',)
        }),
    )

    # ===========================================
    # MÉTODOS DE VISUALIZACIÓN
    # ===========================================

    def fecha_parto_badge(self, obj):
        """
        MÉTODO: Badge de fecha de parto

        Funcionamiento:
            Muestra la fecha del parto con un badge azul
        """
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            obj.fecha_parto.strftime('%d/%m/%Y') if obj.fecha_parto else 'N/A'
        )
    fecha_parto_badge.short_description = 'Fecha Parto'

    def paciente_info(self, obj):
        """
        MÉTODO: Información del paciente

        Funcionamiento:
            Muestra nombre completo y CI del paciente
        """
        if obj.paciente:
            return format_html(
                '<strong>{}</strong><br><small>CI: {}</small>',
                obj.paciente.nombre_completo,
                obj.paciente.ci if obj.paciente.ci else 'N/A'
            )
        return 'N/A'
    paciente_info.short_description = 'Paciente'

    def tipo_parto_badge(self, obj):
        """
        MÉTODO: Badge de tipo de parto

        Funcionamiento:
            Muestra el tipo de parto con color según el tipo:
            - eutocico: verde (natural)
            - cesarea: naranja (quirúrgico)
            - forceps/ventosa: amarillo (instrumental)
            - inducido: azul
        """
        colores = {
            'eutocico': '#27ae60',  # Verde
            'cesarea': '#e67e22',   # Naranja
            'forceps': '#f39c12',   # Amarillo
            'ventosa': '#f39c12',   # Amarillo
            'inducido': '#3498db',  # Azul
        }
        color = colores.get(obj.tipo_parto, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_parto_display()
        )
    tipo_parto_badge.short_description = 'Tipo'

    def via_parto_badge(self, obj):
        """
        MÉTODO: Badge de vía de parto

        Funcionamiento:
            Muestra la vía del parto con color:
            - vaginal: verde
            - abdominal: naranja
        """
        colores = {
            'vaginal': '#27ae60',    # Verde
            'abdominal': '#e67e22',  # Naranja
        }
        color = colores.get(obj.via_parto, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_via_parto_display()
        )
    via_parto_badge.short_description = 'Vía'

    def edad_gestacional_display(self, obj):
        """
        MÉTODO: Mostrar edad gestacional

        Funcionamiento:
            Muestra la edad gestacional en formato SS+D
        """
        return f"{obj.edad_gestacional_semanas}+{obj.edad_gestacional_dias}"
    edad_gestacional_display.short_description = 'EG'

    def recien_nacidos_count(self, obj):
        """
        MÉTODO: Contador de recién nacidos

        Funcionamiento:
            Muestra la cantidad de recién nacidos con badge
        """
        count = obj.recien_nacidos.count()
        color = '#27ae60' if count > 0 else '#95a5a6'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 50%; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            count
        )
    recien_nacidos_count.short_description = 'RN'

    def complicaciones_badge(self, obj):
        """
        MÉTODO: Badge de complicaciones

        Funcionamiento:
            Muestra si tiene complicaciones con color:
            - Sí: rojo
            - No: verde
        """
        if obj.complicaciones:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">SÍ</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">NO</span>'
            )
    complicaciones_badge.short_description = 'Complicaciones'

    def estado_badge(self, obj):
        """
        MÉTODO: Badge de estado del parto

        Funcionamiento:
            Muestra el estado con color:
            - en_curso: azul
            - finalizado: verde
            - complicado: rojo
        """
        colores = {
            'en_curso': '#3498db',    # Azul
            'finalizado': '#27ae60',  # Verde
            'complicado': '#e74c3c',  # Rojo
        }
        color = colores.get(obj.estado, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display().upper()
        )
    estado_badge.short_description = 'Estado'

    def duracion_horas_display(self, obj):
        """
        MÉTODO: Mostrar duración en horas

        Funcionamiento:
            Convierte la duración de minutos a horas y minutos
        """
        if obj.duracion_trabajo_parto:
            horas = obj.duracion_trabajo_parto // 60
            minutos = obj.duracion_trabajo_parto % 60
            return f"{horas}h {minutos}min"
        return "N/A"
    duracion_horas_display.short_description = 'Duración (H:M)'

    # ===========================================
    # ACCIONES MASIVAS
    # ===========================================

    def finalizar_partos(self, request, queryset):
        """
        ACCIÓN: Finalizar partos seleccionados

        Funcionamiento:
            Marca los partos seleccionados como finalizados
        """
        actualizados = queryset.update(estado='finalizado')
        self.message_user(request, f'{actualizados} parto(s) marcado(s) como finalizado(s).')
    finalizar_partos.short_description = 'Marcar como finalizados'

    def marcar_con_complicaciones(self, request, queryset):
        """
        ACCIÓN: Marcar partos con complicaciones

        Funcionamiento:
            Marca los partos seleccionados como complicados
        """
        actualizados = queryset.update(complicaciones=True, estado='complicado')
        self.message_user(request, f'{actualizados} parto(s) marcado(s) con complicaciones.')
    marcar_con_complicaciones.short_description = 'Marcar con complicaciones'

    def marcar_sin_complicaciones(self, request, queryset):
        """
        ACCIÓN: Marcar partos sin complicaciones

        Funcionamiento:
            Marca los partos seleccionados como sin complicaciones
        """
        actualizados = queryset.update(complicaciones=False)
        self.message_user(request, f'{actualizados} parto(s) marcado(s) sin complicaciones.')
    marcar_sin_complicaciones.short_description = 'Marcar sin complicaciones'

    actions = [
        'finalizar_partos',
        'marcar_con_complicaciones',
        'marcar_sin_complicaciones',
    ]


# ===========================================
# ADMIN: RECIÉN NACIDO
# ===========================================
@admin.register(RecienNacido)
class RecienNacidoAdmin(admin.ModelAdmin):
    """
    ADMIN: Configuración del administrador para Recién Nacido

    Funcionamiento:
        Panel de administración para gestión de recién nacidos
        con información detallada y filtros

    Características:
        - Lista con información principal
        - Filtros por sexo, estado, APGAR
        - Búsqueda por parto
        - Visualización de datos antropométricos
    """

    list_display = [
        'id',
        'parto_info',
        'numero_hijo',
        'sexo_badge',
        'peso_display',
        'talla_display',
        'apgar_badge',
        'estado_badge',
        'reanimacion_badge',
        'malformaciones_badge',
    ]

    list_filter = [
        'sexo',
        'estado_al_nacer',
        'reanimacion',
        'malformaciones',
        'fecha_registro',
    ]

    search_fields = [
        'parto__id',
        'parto__paciente__nombre',
        'parto__paciente__apellido',
    ]

    readonly_fields = [
        'id',
        'fecha_registro',
        'interpretacion_apgar',
    ]

    ordering = ['-fecha_registro']

    list_per_page = 25

    autocomplete_fields = ['parto']

    fieldsets = (
        ('Información del Parto', {
            'fields': (
                'parto',
                'numero_hijo',
            )
        }),
        ('Datos Básicos', {
            'fields': (
                'sexo',
                'estado_al_nacer',
            )
        }),
        ('Datos Antropométricos', {
            'fields': (
                'peso',
                'talla',
                'perimetro_cefalico',
            )
        }),
        ('Evaluación APGAR', {
            'fields': (
                'apgar_1min',
                'apgar_5min',
                'interpretacion_apgar',
            )
        }),
        ('Intervenciones', {
            'fields': (
                'reanimacion',
                'descripcion_reanimacion',
            )
        }),
        ('Malformaciones', {
            'fields': (
                'malformaciones',
                'descripcion_malformaciones',
            )
        }),
        ('Observaciones', {
            'fields': (
                'observaciones',
            )
        }),
        ('Auditoría', {
            'fields': (
                'fecha_registro',
            ),
            'classes': ('collapse',)
        }),
    )

    # ===========================================
    # MÉTODOS DE VISUALIZACIÓN
    # ===========================================

    def parto_info(self, obj):
        """Información del parto"""
        return format_html(
            '<strong>Parto #{}</strong><br><small>{}</small>',
            obj.parto.id,
            obj.parto.fecha_parto.strftime('%d/%m/%Y') if obj.parto.fecha_parto else 'N/A'
        )
    parto_info.short_description = 'Parto'

    def sexo_badge(self, obj):
        """Badge de sexo"""
        colores = {
            'M': '#3498db',  # Azul
            'F': '#e91e63',  # Rosa
            'I': '#95a5a6',  # Gris
        }
        color = colores.get(obj.sexo, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_sexo_display()
        )
    sexo_badge.short_description = 'Sexo'

    def peso_display(self, obj):
        """Mostrar peso"""
        return f"{obj.peso} g"
    peso_display.short_description = 'Peso'

    def talla_display(self, obj):
        """Mostrar talla"""
        return f"{obj.talla} cm" if obj.talla else 'N/A'
    talla_display.short_description = 'Talla'

    def apgar_badge(self, obj):
        """Badge de APGAR"""
        apgar = obj.apgar_5min if obj.apgar_5min else obj.apgar_1min

        if apgar is None:
            return 'N/A'

        # Color según APGAR
        if apgar >= 7:
            color = '#27ae60'  # Verde - Normal
        elif apgar >= 4:
            color = '#f39c12'  # Amarillo - Moderado
        else:
            color = '#e74c3c'  # Rojo - Crítico

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">1min: {} | 5min: {}</span>',
            color,
            obj.apgar_1min if obj.apgar_1min else 'N/A',
            obj.apgar_5min if obj.apgar_5min else 'N/A'
        )
    apgar_badge.short_description = 'APGAR'

    def estado_badge(self, obj):
        """Badge de estado al nacer"""
        colores = {
            'vivo': '#27ae60',      # Verde
            'muerto': '#e74c3c',    # Rojo
            'mortinato': '#95a5a6', # Gris
        }
        color = colores.get(obj.estado_al_nacer, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_al_nacer_display().upper()
        )
    estado_badge.short_description = 'Estado'

    def reanimacion_badge(self, obj):
        """Badge de reanimación"""
        if obj.reanimacion:
            return format_html(
                '<span style="background-color: #e67e22; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">SÍ</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">NO</span>'
            )
    reanimacion_badge.short_description = 'Reanimación'

    def malformaciones_badge(self, obj):
        """Badge de malformaciones"""
        if obj.malformaciones:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">SÍ</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">NO</span>'
            )
    malformaciones_badge.short_description = 'Malformaciones'

    def interpretacion_apgar(self, obj):
        """Interpretación del APGAR"""
        interpretaciones = []

        if obj.apgar_1min is not None:
            if obj.apgar_1min >= 7:
                interp_1 = "Normal"
                color_1 = "#27ae60"
            elif obj.apgar_1min >= 4:
                interp_1 = "Moderadamente anormal"
                color_1 = "#f39c12"
            else:
                interp_1 = "Críticamente bajo"
                color_1 = "#e74c3c"

            interpretaciones.append(
                f'<div style="margin-bottom: 5px;"><strong>1 min ({obj.apgar_1min}):</strong> '
                f'<span style="color: {color_1}; font-weight: bold;">{interp_1}</span></div>'
            )

        if obj.apgar_5min is not None:
            if obj.apgar_5min >= 7:
                interp_5 = "Normal"
                color_5 = "#27ae60"
            elif obj.apgar_5min >= 4:
                interp_5 = "Moderadamente anormal"
                color_5 = "#f39c12"
            else:
                interp_5 = "Críticamente bajo"
                color_5 = "#e74c3c"

            interpretaciones.append(
                f'<div><strong>5 min ({obj.apgar_5min}):</strong> '
                f'<span style="color: {color_5}; font-weight: bold;">{interp_5}</span></div>'
            )

        return mark_safe(''.join(interpretaciones)) if interpretaciones else 'N/A'
    interpretacion_apgar.short_description = 'Interpretación APGAR'


# ===========================================
# ADMIN: COMPLICACIÓN PARTO
# ===========================================
@admin.register(ComplicacionParto)
class ComplicacionPartoAdmin(admin.ModelAdmin):
    """
    ADMIN: Configuración del administrador para Complicación de Parto

    Funcionamiento:
        Panel de administración para gestión de complicaciones
        con filtros y acciones masivas

    Características:
        - Lista con información principal
        - Filtros por tipo y estado de resolución
        - Búsqueda por parto
        - Acciones masivas para marcar como resuelto
    """

    list_display = [
        'id',
        'parto_info',
        'tipo_complicacion_badge',
        'descripcion_corta',
        'resuelto_badge',
        'fecha_registro',
    ]

    list_filter = [
        'tipo_complicacion',
        'resuelto',
        'fecha_registro',
    ]

    search_fields = [
        'parto__id',
        'parto__paciente__nombre',
        'parto__paciente__apellido',
        'descripcion',
        'tratamiento',
    ]

    readonly_fields = [
        'id',
        'fecha_registro',
    ]

    ordering = ['-fecha_registro']

    list_per_page = 25

    autocomplete_fields = ['parto']

    fieldsets = (
        ('Información del Parto', {
            'fields': (
                'parto',
            )
        }),
        ('Complicación', {
            'fields': (
                'tipo_complicacion',
                'descripcion',
            )
        }),
        ('Tratamiento', {
            'fields': (
                'tratamiento',
                'resuelto',
            )
        }),
        ('Auditoría', {
            'fields': (
                'fecha_registro',
            ),
            'classes': ('collapse',)
        }),
    )

    # ===========================================
    # MÉTODOS DE VISUALIZACIÓN
    # ===========================================

    def parto_info(self, obj):
        """Información del parto"""
        return format_html(
            '<strong>Parto #{}</strong><br><small>{}</small>',
            obj.parto.id,
            obj.parto.fecha_parto.strftime('%d/%m/%Y') if obj.parto.fecha_parto else 'N/A'
        )
    parto_info.short_description = 'Parto'

    def tipo_complicacion_badge(self, obj):
        """Badge de tipo de complicación"""
        colores = {
            'hemorragia': '#e74c3c',         # Rojo
            'distocia': '#e67e22',           # Naranja
            'sufrimiento_fetal': '#f39c12',  # Amarillo
            'ruptura_uterina': '#c0392b',    # Rojo oscuro
            'prolapso_cordon': '#e67e22',    # Naranja
            'preeclampsia': '#9b59b6',       # Púrpura
            'otra': '#95a5a6',               # Gris
        }
        color = colores.get(obj.tipo_complicacion, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_complicacion_display()
        )
    tipo_complicacion_badge.short_description = 'Tipo'

    def descripcion_corta(self, obj):
        """Descripción corta"""
        if len(obj.descripcion) > 50:
            return obj.descripcion[:50] + '...'
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'

    def resuelto_badge(self, obj):
        """Badge de resolución"""
        if obj.resuelto:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">RESUELTO</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">PENDIENTE</span>'
            )
    resuelto_badge.short_description = 'Estado'

    # ===========================================
    # ACCIONES MASIVAS
    # ===========================================

    def marcar_como_resuelto(self, request, queryset):
        """Marcar complicaciones como resueltas"""
        actualizados = queryset.update(resuelto=True)
        self.message_user(request, f'{actualizados} complicación(es) marcada(s) como resuelta(s).')
    marcar_como_resuelto.short_description = 'Marcar como resueltas'

    def marcar_como_pendiente(self, request, queryset):
        """Marcar complicaciones como pendientes"""
        actualizados = queryset.update(resuelto=False)
        self.message_user(request, f'{actualizados} complicación(es) marcada(s) como pendiente(s).')
    marcar_como_pendiente.short_description = 'Marcar como pendientes'

    actions = [
        'marcar_como_resuelto',
        'marcar_como_pendiente',
    ]


"""
RESUMEN DE ADMIN DE PARTOS:
============================

1. PartoAdmin:
   - 9 campos en list_display con badges de color
   - 6 filtros (tipo, vía, estado, complicaciones, fecha, médico)
   - Búsqueda por paciente
   - 2 inlines (RecienNacido, ComplicacionParto)
   - 7 fieldsets organizados
   - 3 acciones masivas
   - 8 métodos personalizados de visualización

2. RecienNacidoAdmin:
   - 10 campos en list_display con badges
   - 5 filtros (sexo, estado, reanimación, malformaciones, fecha)
   - Búsqueda por parto y paciente
   - 8 fieldsets organizados
   - 7 métodos personalizados de visualización
   - Interpretación APGAR automática

3. ComplicacionPartoAdmin:
   - 6 campos en list_display con badges
   - 3 filtros (tipo, resuelto, fecha)
   - Búsqueda por parto y descripción
   - 4 fieldsets organizados
   - 2 acciones masivas
   - 4 métodos personalizados de visualización

Total: 3 admins completos con badges, filtros y acciones
Líneas: ~650
============================
"""
