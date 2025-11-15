# =============================================================================
# ADMIN DE ECOGRAFÍAS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: ecografias
# Descripción: Configuración del panel de administración de Django para ecografías
# Versión: 1.0.0
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.utils import timezone
from django.contrib import messages

from .models import Ecografia
from embarazos.models import Embarazo


# =============================================================================
# ACCIONES PERSONALIZADAS DEL ADMIN
# =============================================================================

@admin.action(description='Marcar como ecografías con anatomía normal')
def marcar_anatomia_normal(modeladmin, request, queryset):
    """
    Marca las ecografías seleccionadas como anatomía normal.

    Args:
        modeladmin: Instancia del ModelAdmin
        request: HttpRequest
        queryset: QuerySet de ecografías seleccionadas
    """
    updated = queryset.update(evaluacion_anatomia='normal')
    modeladmin.message_user(
        request,
        f'{updated} ecografía(s) marcada(s) con anatomía normal.',
        messages.SUCCESS
    )


@admin.action(description='Marcar como ecografías con anatomía alterada')
def marcar_anatomia_alterada(modeladmin, request, queryset):
    """
    Marca las ecografías seleccionadas como anatomía alterada.

    Args:
        modeladmin: Instancia del ModelAdmin
        request: HttpRequest
        queryset: QuerySet de ecografías seleccionadas
    """
    updated = queryset.update(evaluacion_anatomia='alterada')
    modeladmin.message_user(
        request,
        f'{updated} ecografía(s) marcada(s) con anatomía alterada.',
        messages.WARNING
    )


@admin.action(description='Restaurar ecografías eliminadas')
def restaurar_ecografias(modeladmin, request, queryset):
    """
    Restaura ecografías que fueron eliminadas (soft delete).

    Args:
        modeladmin: Instancia del ModelAdmin
        request: HttpRequest
        queryset: QuerySet de ecografías seleccionadas
    """
    updated = queryset.update(activo=True, fecha_eliminacion=None)
    modeladmin.message_user(
        request,
        f'{updated} ecografía(s) restaurada(s).',
        messages.SUCCESS
    )


@admin.action(description='Eliminar permanentemente (hard delete)')
def eliminar_permanentemente(modeladmin, request, queryset):
    """
    Elimina permanentemente las ecografías seleccionadas de la base de datos.

    ADVERTENCIA: Esta acción NO se puede deshacer.

    Args:
        modeladmin: Instancia del ModelAdmin
        request: HttpRequest
        queryset: QuerySet de ecografías seleccionadas
    """
    count = queryset.count()
    queryset._raw_delete(queryset.db)  # Hard delete
    modeladmin.message_user(
        request,
        f'{count} ecografía(s) eliminada(s) permanentemente.',
        messages.ERROR
    )


# =============================================================================
# FILTROS PERSONALIZADOS
# =============================================================================

class TipoEcografiaFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para tipo de ecografía.

    Agrupa las ecografías por tipo con contadores.
    """
    title = 'Tipo de Ecografía'
    parameter_name = 'tipo'

    def lookups(self, request, model_admin):
        """
        Retorna las opciones de filtro con contadores.

        Returns:
            list: Lista de tuplas (valor, etiqueta)
        """
        # Contar ecografías por tipo
        counts = {}
        for tipo, nombre in Ecografia.TIPOS_ECOGRAFIA:
            count = Ecografia.objects.filter(tipo_ecografia=tipo, activo=True).count()
            counts[tipo] = count

        # Retornar opciones con contadores
        return [
            (tipo, f"{nombre} ({counts.get(tipo, 0)})")
            for tipo, nombre in Ecografia.TIPOS_ECOGRAFIA
        ]

    def queryset(self, request, queryset):
        """
        Filtra el queryset según el valor seleccionado.

        Args:
            request: HttpRequest
            queryset: QuerySet original

        Returns:
            QuerySet: QuerySet filtrado
        """
        if self.value():
            return queryset.filter(tipo_ecografia=self.value())
        return queryset


class TrimestreFilter(admin.SimpleListFilter):
    """
    Filtro personalizado por trimestre de embarazo.

    Clasifica las ecografías según la edad gestacional.
    """
    title = 'Trimestre'
    parameter_name = 'trimestre'

    def lookups(self, request, model_admin):
        """
        Retorna las opciones de filtro.

        Returns:
            list: Lista de tuplas (valor, etiqueta)
        """
        return [
            ('1', 'Primer Trimestre (0-13 semanas)'),
            ('2', 'Segundo Trimestre (14-27 semanas)'),
            ('3', 'Tercer Trimestre (28+ semanas)'),
        ]

    def queryset(self, request, queryset):
        """
        Filtra el queryset según el trimestre.

        Args:
            request: HttpRequest
            queryset: QuerySet original

        Returns:
            QuerySet: QuerySet filtrado
        """
        if self.value() == '1':
            return queryset.filter(edad_gestacional_semanas__lte=13)
        elif self.value() == '2':
            return queryset.filter(
                edad_gestacional_semanas__gte=14,
                edad_gestacional_semanas__lte=27
            )
        elif self.value() == '3':
            return queryset.filter(edad_gestacional_semanas__gte=28)
        return queryset


class LiquidoAmnioticaFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para estado del líquido amniótico.
    """
    title = 'Líquido Amniótico'
    parameter_name = 'liquido'

    def lookups(self, request, model_admin):
        """
        Retorna las opciones de filtro.

        Returns:
            list: Lista de tuplas (valor, etiqueta)
        """
        return [
            ('normal', 'Normal'),
            ('oligohidramnios', 'Oligohidramnios (disminuido)'),
            ('polihidramnios', 'Polihidramnios (aumentado)'),
        ]

    def queryset(self, request, queryset):
        """
        Filtra el queryset según el estado del líquido.

        Args:
            request: HttpRequest
            queryset: QuerySet original

        Returns:
            QuerySet: QuerySet filtrado
        """
        if self.value():
            return queryset.filter(liquido_amniotico=self.value())
        return queryset


class AnatomiaFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para evaluación de anatomía fetal.
    """
    title = 'Evaluación Anatómica'
    parameter_name = 'anatomia'

    def lookups(self, request, model_admin):
        """
        Retorna las opciones de filtro.

        Returns:
            list: Lista de tuplas (valor, etiqueta)
        """
        return Ecografia.EVALUACION_ANATOMIA

    def queryset(self, request, queryset):
        """
        Filtra el queryset según la evaluación anatómica.

        Args:
            request: HttpRequest
            queryset: QuerySet original

        Returns:
            QuerySet: QuerySet filtrado
        """
        if self.value():
            return queryset.filter(evaluacion_anatomia=self.value())
        return queryset


class FechaRealizacionFilter(admin.SimpleListFilter):
    """
    Filtro personalizado por rango de fechas de realización.
    """
    title = 'Fecha de Realización'
    parameter_name = 'fecha_rango'

    def lookups(self, request, model_admin):
        """
        Retorna las opciones de filtro.

        Returns:
            list: Lista de tuplas (valor, etiqueta)
        """
        return [
            ('hoy', 'Hoy'),
            ('semana', 'Última semana'),
            ('mes', 'Último mes'),
            ('trimestre', 'Último trimestre'),
            ('anio', 'Último año'),
        ]

    def queryset(self, request, queryset):
        """
        Filtra el queryset según el rango de fechas.

        Args:
            request: HttpRequest
            queryset: QuerySet original

        Returns:
            QuerySet: QuerySet filtrado
        """
        hoy = timezone.now().date()

        if self.value() == 'hoy':
            return queryset.filter(fecha_ecografia=hoy)
        elif self.value() == 'semana':
            fecha_inicio = hoy - timezone.timedelta(days=7)
            return queryset.filter(fecha_ecografia__gte=fecha_inicio)
        elif self.value() == 'mes':
            fecha_inicio = hoy - timezone.timedelta(days=30)
            return queryset.filter(fecha_ecografia__gte=fecha_inicio)
        elif self.value() == 'trimestre':
            fecha_inicio = hoy - timezone.timedelta(days=90)
            return queryset.filter(fecha_ecografia__gte=fecha_inicio)
        elif self.value() == 'anio':
            fecha_inicio = hoy - timezone.timedelta(days=365)
            return queryset.filter(fecha_ecografia__gte=fecha_inicio)

        return queryset


# =============================================================================
# CONFIGURACIÓN DEL ADMIN
# =============================================================================

@admin.register(Ecografia)
class EcografiaAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Ecografia.

    Proporciona una interfaz completa para gestión de ecografías con:
    - Listado con campos clave y búsqueda
    - Filtros personalizados
    - Acciones masivas
    - Formulario detallado con fieldsets organizados
    - Campos de solo lectura calculados
    - Validaciones y permisos
    """

    # =========================================================================
    # CONFIGURACIÓN DEL LISTADO
    # =========================================================================

    list_display = [
        'id',
        'paciente_link',
        'embarazo_link',
        'fecha_ecografia',
        'tipo_ecografia_display',
        'edad_gestacional_display',
        'peso_fetal_display',
        'anatomia_display',
        'liquido_display',
        'activo_display',
    ]

    list_display_links = ['id', 'fecha_ecografia']

    list_filter = [
        'activo',
        TipoEcografiaFilter,
        TrimestreFilter,
        AnatomiaFilter,
        LiquidoAmnioticaFilter,
        FechaRealizacionFilter,
        'latido_cardiaco_presente',
        'movimientos_fetales',
    ]

    search_fields = [
        'id',
        'embarazo__id',
        'embarazo__paciente__nombre',
        'embarazo__paciente__apellido',
        'embarazo__paciente__documento',
        'tipo_ecografia',
        'hallazgos',
        'observaciones',
    ]

    ordering = ['-fecha_ecografia', '-id']

    list_per_page = 25

    actions = [
        marcar_anatomia_normal,
        marcar_anatomia_alterada,
        restaurar_ecografias,
        eliminar_permanentemente,
    ]

    # =========================================================================
    # CONFIGURACIÓN DEL FORMULARIO
    # =========================================================================

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'embarazo',
                'fecha_ecografia',
                'tipo_ecografia',
            ),
            'description': 'Datos básicos de la ecografía'
        }),
        ('Edad Gestacional', {
            'fields': (
                'edad_gestacional_semanas',
                'edad_gestacional_dias',
            ),
            'description': 'Edad gestacional al momento de la ecografía'
        }),
        ('Biometría Fetal', {
            'fields': (
                'longitud_cefalocaudal',
                'diametro_biparietal',
                'circunferencia_cefalica',
                'circunferencia_abdominal',
                'longitud_femur',
                'peso_fetal_estimado',
            ),
            'description': 'Mediciones biométricas del feto'
        }),
        ('Placenta y Líquido Amniótico', {
            'fields': (
                'localizacion_placenta',
                'grado_placentario',
                'liquido_amniotico',
                'indice_liquido_amniotico',
            ),
            'description': 'Evaluación placentaria y líquido amniótico'
        }),
        ('Evaluación Fetal', {
            'fields': (
                'numero_fetos',
                'latido_cardiaco_presente',
                'frecuencia_cardiaca_fetal',
                'movimientos_fetales',
                'evaluacion_anatomia',
            ),
            'description': 'Evaluación del estado fetal'
        }),
        ('Hallazgos y Observaciones', {
            'fields': (
                'hallazgos',
                'observaciones',
                'imagen',
            ),
            'description': 'Hallazgos relevantes y observaciones del ecografista'
        }),
        ('Auditoría', {
            'fields': (
                'activo',
                'fecha_registro',
                'fecha_modificacion',
                'fecha_eliminacion',
            ),
            'classes': ('collapse',),
            'description': 'Información de auditoría y control'
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
        """
        Muestra un link al paciente relacionado.

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: HTML con link al paciente
        """
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
        """
        Muestra un link al embarazo relacionado.

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: HTML con link al embarazo
        """
        if obj.embarazo:
            url = reverse('admin:embarazos_embarazo_change', args=[obj.embarazo.id])
            return format_html(
                '<a href="{}">Embarazo #{}</a>',
                url,
                obj.embarazo.id
            )
        return '-'

    embarazo_link.short_description = 'Embarazo'

    def tipo_ecografia_display(self, obj):
        """
        Muestra el tipo de ecografía con formato.

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: Tipo de ecografía formateado
        """
        return obj.get_tipo_ecografia_display()

    tipo_ecografia_display.short_description = 'Tipo'

    def edad_gestacional_display(self, obj):
        """
        Muestra la edad gestacional en formato "XX+Y semanas".

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: Edad gestacional formateada
        """
        return f"{obj.edad_gestacional_semanas}+{obj.edad_gestacional_dias} sem"

    edad_gestacional_display.short_description = 'Edad Gestacional'

    def peso_fetal_display(self, obj):
        """
        Muestra el peso fetal estimado con formato.

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: Peso fetal formateado o '-'
        """
        if obj.peso_fetal_estimado:
            return f"{int(obj.peso_fetal_estimado)} g"
        return '-'

    peso_fetal_display.short_description = 'Peso Fetal'

    def anatomia_display(self, obj):
        """
        Muestra la evaluación anatómica con color según el estado.

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: HTML con evaluación coloreada
        """
        colors = {
            'normal': 'green',
            'alterada': 'red',
            'no_evaluada': 'gray',
        }
        color = colors.get(obj.evaluacion_anatomia, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_evaluacion_anatomia_display()
        )

    anatomia_display.short_description = 'Anatomía'

    def liquido_display(self, obj):
        """
        Muestra el estado del líquido amniótico con color.

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: HTML con estado coloreado
        """
        if not obj.liquido_amniotico:
            return '-'

        colors = {
            'normal': 'green',
            'oligohidramnios': 'orange',
            'polihidramnios': 'red',
        }
        color = colors.get(obj.liquido_amniotico, 'black')

        texto = obj.get_liquido_amniotico_display()
        if obj.indice_liquido_amniotico:
            texto += f" (ILA: {obj.indice_liquido_amniotico} cm)"

        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            texto
        )

    liquido_display.short_description = 'Líquido Amniótico'

    def activo_display(self, obj):
        """
        Muestra el estado activo/inactivo con iconos.

        Args:
            obj: Instancia de Ecografia

        Returns:
            str: HTML con icono de estado
        """
        if obj.activo:
            return format_html(
                '<span style="color: green;">✓ Activo</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Eliminado</span>'
            )

    activo_display.short_description = 'Estado'

    # =========================================================================
    # MÉTODOS DE PERMISO Y VALIDACIÓN
    # =========================================================================

    def has_delete_permission(self, request, obj=None):
        """
        Controla si el usuario puede eliminar ecografías.

        Por defecto, solo permite soft delete (marcando activo=False).

        Args:
            request: HttpRequest
            obj: Instancia de Ecografia (opcional)

        Returns:
            bool: True si tiene permiso
        """
        # Solo superusuarios pueden hacer hard delete
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        """
        Guarda el modelo con validaciones adicionales.

        Args:
            request: HttpRequest
            obj: Instancia de Ecografia
            form: Form con datos
            change: True si es actualización, False si es creación
        """
        try:
            # Guardar el objeto
            super().save_model(request, obj, form, change)

            # Mensaje de éxito
            if change:
                messages.success(request, f'Ecografía #{obj.id} actualizada correctamente.')
            else:
                messages.success(request, f'Ecografía #{obj.id} creada correctamente.')

        except Exception as e:
            messages.error(request, f'Error al guardar la ecografía: {str(e)}')

    # =========================================================================
    # CONFIGURACIÓN ADICIONAL
    # =========================================================================

    def get_queryset(self, request):
        """
        Optimiza el queryset con select_related.

        Args:
            request: HttpRequest

        Returns:
            QuerySet: QuerySet optimizado
        """
        qs = super().get_queryset(request)
        return qs.select_related('embarazo', 'embarazo__paciente')

    class Media:
        """
        Archivos CSS y JS adicionales para el admin.
        """
        css = {
            'all': ('admin/css/ecografias.css',)
        }
        js = ('admin/js/ecografias.js',)
