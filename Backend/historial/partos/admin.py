# =============================================================================
# ADMIN DE PARTOS
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages

from .models import Parto


@admin.action(description='Restaurar partos eliminados')
def restaurar_partos(modeladmin, request, queryset):
    updated = queryset.update(activo=True, fecha_eliminacion=None)
    modeladmin.message_user(request, f'{updated} parto(s) restaurado(s).', messages.SUCCESS)


class TipoPartoFilter(admin.SimpleListFilter):
    title = 'Tipo de Parto'
    parameter_name = 'tipo'

    def lookups(self, request, model_admin):
        counts = {}
        for tipo, nombre in Parto.TIPOS_PARTO:
            count = Parto.objects.filter(tipo_parto=tipo, activo=True).count()
            counts[tipo] = count
        return [(tipo, f"{nombre} ({counts.get(tipo, 0)})") for tipo, nombre in Parto.TIPOS_PARTO]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tipo_parto=self.value())
        return queryset


class RiesgoRNFilter(admin.SimpleListFilter):
    title = 'Riesgo RN'
    parameter_name = 'riesgo'

    def lookups(self, request, model_admin):
        return [
            ('alto', 'Alto Riesgo (APGAR<7 o peso<2500g)'),
            ('normal', 'Normal'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'alto':
            from django.db.models import Q
            return queryset.filter(Q(apgar_5_min__lt=7) | Q(peso_rn_gramos__lt=2500))
        elif self.value() == 'normal':
            return queryset.filter(apgar_5_min__gte=7, peso_rn_gramos__gte=2500)
        return queryset


class EdadGestacionalFilter(admin.SimpleListFilter):
    title = 'Edad Gestacional'
    parameter_name = 'edad_gestacional'

    def lookups(self, request, model_admin):
        return [
            ('prematuro', 'Prematuro (<37 sem)'),
            ('termino', 'A término (37-42 sem)'),
            ('postermino', 'Postérmino (>42 sem)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'prematuro':
            return queryset.filter(edad_gestacional_parto_semanas__lt=37)
        elif self.value() == 'termino':
            return queryset.filter(edad_gestacional_parto_semanas__gte=37, edad_gestacional_parto_semanas__lte=42)
        elif self.value() == 'postermino':
            return queryset.filter(edad_gestacional_parto_semanas__gt=42)
        return queryset


@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    """Configuración del admin para Partos."""

    list_display = [
        'id',
        'paciente_link',
        'fecha_hora_parto',
        'tipo_parto_display',
        'datos_rn',
        'apgar_display',
        'complicaciones_display',
        'activo_display',
    ]

    list_display_links = ['id', 'fecha_hora_parto']

    list_filter = [
        'activo',
        TipoPartoFilter,
        RiesgoRNFilter,
        EdadGestacionalFilter,
        'hemorragia_postparto',
        'reanimacion_neonatal',
        'episiotomia',
        'desgarros',
    ]

    search_fields = [
        'id',
        'paciente__nombre',
        'paciente__apellido',
        'paciente__documento',
        'tipo_parto',
        'medico_atencion',
        'lugar_parto',
    ]

    ordering = ['-fecha_hora_parto', '-id']
    list_per_page = 25
    actions = [restaurar_partos]

    fieldsets = (
        ('Información Básica', {
            'fields': ('embarazo', 'paciente', 'fecha_hora_parto', 'lugar_parto'),
        }),
        ('Datos del Parto', {
            'fields': ('tipo_parto', 'presentacion', 'duracion_trabajo_parto_horas', 
                      'edad_gestacional_parto_semanas'),
        }),
        ('Recién Nacido', {
            'fields': ('apgar_1_min', 'apgar_5_min', 'peso_rn_gramos', 'talla_rn_cm',
                      'perimetro_cefalico_rn_cm', 'perimetro_toracico_rn_cm', 'sexo_rn',
                      'reanimacion_neonatal'),
        }),
        ('Procedimientos', {
            'fields': ('anestesia', 'episiotomia', 'desgarros', 'grado_desgarro'),
            'classes': ('collapse',),
        }),
        ('Placenta y Alumbramiento', {
            'fields': ('alumbramiento', 'peso_placenta_gramos', 'anomalias_placenta'),
            'classes': ('collapse',),
        }),
        ('Complicaciones', {
            'fields': ('complicaciones_maternas', 'complicaciones_neonatales',
                      'hemorragia_postparto', 'sangrado_ml'),
        }),
        ('Cesárea', {
            'fields': ('indicacion_cesarea', 'tipo_incision'),
            'classes': ('collapse',),
        }),
        ('Personal y Observaciones', {
            'fields': ('medico_atencion', 'medico', 'observaciones'),
        }),
        ('Auditoría', {
            'fields': ('activo', 'creado_por', 'fecha_registro', 'modificado_por',
                      'fecha_modificacion', 'fecha_eliminacion'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['creado_por', 'fecha_registro', 'modificado_por', 'fecha_modificacion', 'fecha_eliminacion']

    def paciente_link(self, obj):
        if obj.paciente:
            url = reverse('admin:pacientes_paciente_change', args=[obj.paciente.id])
            return format_html('<a href="{}">{}</a>', url, obj.paciente.get_nombre_completo())
        return '-'
    paciente_link.short_description = 'Paciente'

    def tipo_parto_display(self, obj):
        return obj.get_tipo_parto_display()
    tipo_parto_display.short_description = 'Tipo'

    def datos_rn(self, obj):
        datos = []
        if obj.peso_rn_gramos:
            datos.append(f'Peso: {obj.peso_rn_gramos}g')
        if obj.sexo_rn:
            datos.append(f'Sexo: {obj.get_sexo_rn_display()}')
        if obj.edad_gestacional_parto_semanas:
            datos.append(f'EG: {obj.edad_gestacional_parto_semanas} sem')
        return format_html('<br>'.join(datos)) if datos else '-'
    datos_rn.short_description = 'Datos RN'

    def apgar_display(self, obj):
        if obj.apgar_5_min is not None:
            color = 'green' if obj.apgar_5_min >= 7 else 'red'
            return format_html('<span style="color: {};">APGAR 5min: {}</span>', color, obj.apgar_5_min)
        return '-'
    apgar_display.short_description = 'APGAR'

    def complicaciones_display(self, obj):
        comps = []
        if obj.complicaciones_maternas:
            comps.append('⚠️ Maternas')
        if obj.complicaciones_neonatales:
            comps.append('⚠️ Neonatales')
        if obj.hemorragia_postparto:
            comps.append('🔴 Hemorragia')
        if obj.apgar_5_min and obj.apgar_5_min < 7:
            comps.append('⚠️ APGAR bajo')
        if comps:
            return format_html('<br>'.join(comps))
        return format_html('<span style="color: green;">✓ Sin complicaciones</span>')
    complicaciones_display.short_description = 'Complicaciones'

    def activo_display(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Eliminado</span>')
    activo_display.short_description = 'Estado'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        try:
            if not change:
                obj.creado_por = request.user
            obj.modificado_por = request.user
            super().save_model(request, obj, form, change)
            messages.success(request, f'Parto #{obj.id} {"actualizado" if change else "creado"} correctamente.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('paciente', 'embarazo', 'medico')

    class Media:
        css = {'all': ('admin/css/partos.css',)}
        js = ('admin/js/partos.js',)
