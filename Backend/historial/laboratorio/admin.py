# =============================================================================
# ADMIN DE LABORATORIO
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: laboratorio
# Descripción: Configuración del panel de administración para exámenes de laboratorio
# Versión: 1.0.0
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.utils import timezone
from django.contrib import messages

from .models import ExamenLaboratorio
from embarazos.models import Embarazo


# =============================================================================
# ACCIONES PERSONALIZADAS DEL ADMIN
# =============================================================================

@admin.action(description='Marcar como completado')
def marcar_completado(modeladmin, request, queryset):
    """Marca los exámenes como completados."""
    fecha_actual = timezone.now().date()
    updated = queryset.update(estado='completado', fecha_resultado=fecha_actual)
    modeladmin.message_user(
        request,
        f'{updated} examen(es) marcado(s) como completado.',
        messages.SUCCESS
    )


@admin.action(description='Marcar como pendiente')
def marcar_pendiente(modeladmin, request, queryset):
    """Marca los exámenes como pendientes."""
    updated = queryset.update(estado='pendiente', fecha_resultado=None)
    modeladmin.message_user(
        request,
        f'{updated} examen(es) marcado(s) como pendiente.',
        messages.SUCCESS
    )


@admin.action(description='Restaurar exámenes eliminados')
def restaurar_examenes(modeladmin, request, queryset):
    """Restaura exámenes eliminados (soft delete)."""
    updated = queryset.update(activo=True, fecha_eliminacion=None)
    modeladmin.message_user(
        request,
        f'{updated} examen(es) restaurado(s).',
        messages.SUCCESS
    )


@admin.action(description='Eliminar permanentemente')
def eliminar_permanentemente(modeladmin, request, queryset):
    """Eliminación permanente de la BD."""
    count = queryset.count()
    queryset._raw_delete(queryset.db)
    modeladmin.message_user(
        request,
        f'{count} examen(es) eliminado(s) permanentemente.',
        messages.ERROR
    )


# =============================================================================
# FILTROS PERSONALIZADOS
# =============================================================================

class TipoExamenFilter(admin.SimpleListFilter):
    """Filtro por tipo de examen con contadores."""
    title = 'Tipo de Examen'
    parameter_name = 'tipo'

    def lookups(self, request, model_admin):
        counts = {}
        for tipo, nombre in ExamenLaboratorio.TIPOS_EXAMEN:
            count = ExamenLaboratorio.objects.filter(tipo_examen=tipo, activo=True).count()
            counts[tipo] = count

        return [
            (tipo, f"{nombre} ({counts.get(tipo, 0)})")
            for tipo, nombre in ExamenLaboratorio.TIPOS_EXAMEN
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tipo_examen=self.value())
        return queryset


class EstadoExamenFilter(admin.SimpleListFilter):
    """Filtro por estado del examen."""
    title = 'Estado del Examen'
    parameter_name = 'estado_examen'

    def lookups(self, request, model_admin):
        return ExamenLaboratorio.ESTADO_EXAMEN

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(estado=self.value())
        return queryset


class AnemiaSevFilter(admin.SimpleListFilter):
    """Filtro por anemia severa."""
    title = 'Anemia Severa'
    parameter_name = 'anemia_severa'

    def lookups(self, request, model_admin):
        return [
            ('si', 'Sí (Hb <10 g/dL)'),
            ('no', 'No (Hb ≥10 g/dL)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'si':
            return queryset.filter(hemoglobina__lt=10.0)
        elif self.value() == 'no':
            return queryset.filter(hemoglobina__gte=10.0)
        return queryset


class DiabetesFilter(admin.SimpleListFilter):
    """Filtro por diabetes (glucosa alta)."""
    title = 'Diabetes/Glucosa Alta'
    parameter_name = 'diabetes'

    def lookups(self, request, model_admin):
        return [
            ('si', 'Sí (Glucosa >126 mg/dL)'),
            ('probable', 'Probable (95-126 mg/dL)'),
            ('normal', 'Normal (<95 mg/dL)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'si':
            return queryset.filter(glucosa__gt=126.0)
        elif self.value() == 'probable':
            return queryset.filter(glucosa__gte=95.0, glucosa__lte=126.0)
        elif self.value() == 'normal':
            return queryset.filter(glucosa__lt=95.0)
        return queryset


class SerologiaReactivaFilter(admin.SimpleListFilter):
    """Filtro por serología reactiva."""
    title = 'Serología Reactiva'
    parameter_name = 'serologia_reactiva'

    def lookups(self, request, model_admin):
        return [
            ('vdrl', 'VDRL Reactivo'),
            ('vih', 'VIH Reactivo'),
            ('hepatitis_b', 'Hepatitis B Reactivo'),
            ('cualquiera', 'Cualquiera Reactivo'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'vdrl':
            return queryset.filter(vdrl='reactivo')
        elif self.value() == 'vih':
            return queryset.filter(vih='reactivo')
        elif self.value() == 'hepatitis_b':
            return queryset.filter(hepatitis_b='reactivo')
        elif self.value() == 'cualquiera':
            from django.db.models import Q
            return queryset.filter(
                Q(vdrl='reactivo') | Q(vih='reactivo') | Q(hepatitis_b='reactivo')
            )
        return queryset


class InfeccionUrinariaFilter(admin.SimpleListFilter):
    """Filtro por probable infección urinaria."""
    title = 'Infección Urinaria Probable'
    parameter_name = 'infeccion_urinaria'

    def lookups(self, request, model_admin):
        return [
            ('si', 'Sí (Leucocitos >5)'),
            ('no', 'No (Leucocitos ≤5)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'si':
            return queryset.filter(orina_leucocitos__gt=5)
        elif self.value() == 'no':
            return queryset.filter(orina_leucocitos__lte=5)
        return queryset


class FechaExamenFilter(admin.SimpleListFilter):
    """Filtro por fecha del examen."""
    title = 'Fecha del Examen'
    parameter_name = 'fecha_examen_rango'

    def lookups(self, request, model_admin):
        return [
            ('hoy', 'Hoy'),
            ('semana', 'Última semana'),
            ('mes', 'Último mes'),
            ('trimestre', 'Último trimestre'),
        ]

    def queryset(self, request, queryset):
        hoy = timezone.now().date()

        if self.value() == 'hoy':
            return queryset.filter(fecha_examen=hoy)
        elif self.value() == 'semana':
            fecha_inicio = hoy - timezone.timedelta(days=7)
            return queryset.filter(fecha_examen__gte=fecha_inicio)
        elif self.value() == 'mes':
            fecha_inicio = hoy - timezone.timedelta(days=30)
            return queryset.filter(fecha_examen__gte=fecha_inicio)
        elif self.value() == 'trimestre':
            fecha_inicio = hoy - timezone.timedelta(days=90)
            return queryset.filter(fecha_examen__gte=fecha_inicio)

        return queryset


# =============================================================================
# CONFIGURACIÓN DEL ADMIN
# =============================================================================

@admin.register(ExamenLaboratorio)
class ExamenLaboratorioAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para ExamenLaboratorio.
    """

    # =========================================================================
    # CONFIGURACIÓN DEL LISTADO
    # =========================================================================

    list_display = [
        'id',
        'paciente_link',
        'embarazo_link',
        'fecha_examen',
        'tipo_examen_display',
        'estado_display',
        'valores_principales',
        'alertas_display',
        'activo_display',
    ]

    list_display_links = ['id', 'fecha_examen']

    list_filter = [
        'activo',
        TipoExamenFilter,
        EstadoExamenFilter,
        FechaExamenFilter,
        AnemiaSevFilter,
        DiabetesFilter,
        SerologiaReactivaFilter,
        InfeccionUrinariaFilter,
    ]

    search_fields = [
        'id',
        'embarazo__id',
        'embarazo__paciente__nombre',
        'embarazo__paciente__apellido',
        'embarazo__paciente__documento',
        'tipo_examen',
        'laboratorio',
        'observaciones',
    ]

    ordering = ['-fecha_examen', '-id']

    list_per_page = 25

    actions = [
        marcar_completado,
        marcar_pendiente,
        restaurar_examenes,
        eliminar_permanentemente,
    ]

    # =========================================================================
    # CONFIGURACIÓN DEL FORMULARIO
    # =========================================================================

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'embarazo',
                'fecha_examen',
                'fecha_resultado',
                'tipo_examen',
                'estado',
                'laboratorio',
            ),
        }),
        ('Hemograma Completo', {
            'fields': (
                'hemoglobina',
                'hematocrito',
                'leucocitos',
                'plaquetas',
            ),
            'classes': ('collapse',),
        }),
        ('Química Sanguínea', {
            'fields': (
                'glucosa',
                'urea',
                'creatinina',
                'acido_urico',
                'proteinas_totales',
                'albumina',
                'globulina',
                'bilirrubina_total',
                'tgo',
                'tgp',
                'fosfatasa_alcalina',
            ),
            'classes': ('collapse',),
        }),
        ('Grupo Sanguíneo y Serología', {
            'fields': (
                'grupo_sanguineo',
                'factor_rh',
                'vdrl',
                'vih',
                'hepatitis_b',
                'toxoplasmosis_igg',
                'toxoplasmosis_igm',
                'rubeola_igg',
            ),
            'classes': ('collapse',),
        }),
        ('Examen de Orina', {
            'fields': (
                'orina_color',
                'orina_aspecto',
                'orina_ph',
                'orina_densidad',
                'orina_glucosa',
                'orina_proteinas',
                'orina_leucocitos',
                'orina_hematies',
                'orina_celulas_epiteliales',
                'orina_bacterias',
            ),
            'classes': ('collapse',),
        }),
        ('Cultivos', {
            'fields': (
                'urocultivo',
                'antibiograma',
            ),
            'classes': ('collapse',),
        }),
        ('Observaciones y Archivo', {
            'fields': (
                'observaciones',
                'archivo_resultado',
            ),
        }),
        ('Auditoría', {
            'fields': (
                'activo',
                'fecha_registro',
                'fecha_modificacion',
                'fecha_eliminacion',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = [
        'fecha_registro',
        'fecha_modificacion',
        'fecha_eliminacion',
    ]

    # =========================================================================
    # MÉTODOS PERSONALIZADOS PARA EL LISTADO
    # =========================================================================

    def paciente_link(self, obj):
        """Link al paciente."""
        if obj.embarazo and obj.embarazo.paciente:
            paciente = obj.embarazo.paciente
            url = reverse('admin:pacientes_paciente_change', args=[paciente.id])
            return format_html(
                '<a href="{}">{} {}</a>',
                url,
                paciente.nombre,
                paciente.apellido
            )
        return '-'

    paciente_link.short_description = 'Paciente'

    def embarazo_link(self, obj):
        """Link al embarazo."""
        if obj.embarazo:
            url = reverse('admin:embarazos_embarazo_change', args=[obj.embarazo.id])
            return format_html(
                '<a href="{}">Embarazo #{}</a>',
                url,
                obj.embarazo.id
            )
        return '-'

    embarazo_link.short_description = 'Embarazo'

    def tipo_examen_display(self, obj):
        """Muestra el tipo de examen."""
        return obj.get_tipo_examen_display()

    tipo_examen_display.short_description = 'Tipo'

    def estado_display(self, obj):
        """Muestra el estado con color."""
        colors = {
            'pendiente': 'orange',
            'completado': 'green',
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )

    estado_display.short_description = 'Estado'

    def valores_principales(self, obj):
        """Muestra valores principales según tipo de examen."""
        valores = []

        if obj.hemoglobina:
            valores.append(f'Hb: {obj.hemoglobina} g/dL')
        if obj.glucosa:
            valores.append(f'Glucosa: {obj.glucosa} mg/dL')
        if obj.plaquetas:
            valores.append(f'Plaq: {obj.plaquetas}/mm³')

        return format_html('<br>'.join(valores)) if valores else '-'

    valores_principales.short_description = 'Valores'

    def alertas_display(self, obj):
        """Muestra alertas importantes."""
        alertas = []

        # Anemia
        if obj.hemoglobina and float(obj.hemoglobina) < 10.0:
            alertas.append('⚠️ Anemia severa')

        # Diabetes
        if obj.glucosa and float(obj.glucosa) > 126.0:
            alertas.append('⚠️ Diabetes')

        # Plaquetas bajas
        if obj.plaquetas and obj.plaquetas < 150000:
            alertas.append('⚠️ Plaquetas bajas')

        # Serología reactiva
        if obj.vdrl == 'reactivo':
            alertas.append('🔴 VDRL+')
        if obj.vih == 'reactivo':
            alertas.append('🔴 VIH+')
        if obj.hepatitis_b == 'reactivo':
            alertas.append('🔴 HBsAg+')

        # Infección urinaria
        if obj.orina_leucocitos and obj.orina_leucocitos > 10:
            alertas.append('⚠️ ITU probable')

        # Proteinuria
        if obj.orina_proteinas in ['positivo_2', 'positivo_3']:
            alertas.append('⚠️ Proteinuria')

        if alertas:
            return format_html('<br>'.join(alertas))
        else:
            return format_html('<span style="color: green;">✓ Sin alertas</span>')

    alertas_display.short_description = 'Alertas'

    def activo_display(self, obj):
        """Muestra estado activo/inactivo."""
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        else:
            return format_html('<span style="color: red;">✗ Eliminado</span>')

    activo_display.short_description = 'Estado'

    # =========================================================================
    # MÉTODOS DE PERMISO Y VALIDACIÓN
    # =========================================================================

    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden hacer hard delete."""
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        """Guarda con validaciones."""
        try:
            super().save_model(request, obj, form, change)

            if change:
                messages.success(request, f'Examen #{obj.id} actualizado correctamente.')
            else:
                messages.success(request, f'Examen #{obj.id} creado correctamente.')

        except Exception as e:
            messages.error(request, f'Error al guardar el examen: {str(e)}')

    # =========================================================================
    # CONFIGURACIÓN ADICIONAL
    # =========================================================================

    def get_queryset(self, request):
        """Optimiza con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('embarazo', 'embarazo__paciente')

    class Media:
        css = {
            'all': ('admin/css/laboratorio.css',)
        }
        js = ('admin/js/laboratorio.js',)
