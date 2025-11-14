# =============================================================================
# ADMINISTRACIÓN DE PACIENTES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: pacientes
# Descripción: Configuración del panel de administración para pacientes.
#              Incluye listas personalizadas, filtros, búsqueda, acciones masivas
#              y visualización detallada de registros.
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from django.utils import timezone
from .models import Paciente


# =============================================================================
# FILTROS PERSONALIZADOS
# =============================================================================

class EdadListFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para edad de pacientes.
    """
    title = 'Edad'
    parameter_name = 'edad'

    def lookups(self, request, model_admin):
        return (
            ('adolescente', 'Adolescente (< 18 años)'),
            ('adulta_joven', 'Adulta Joven (18-35 años)'),
            ('adulta_mayor', 'Adulta Mayor (> 35 años)'),
        )

    def queryset(self, request, queryset):
        from datetime import timedelta
        hoy = timezone.now().date()

        if self.value() == 'adolescente':
            fecha_min = hoy - timedelta(days=18*365)
            return queryset.filter(fecha_nacimiento__gte=fecha_min)
        elif self.value() == 'adulta_joven':
            fecha_min_18 = hoy - timedelta(days=18*365)
            fecha_max_35 = hoy - timedelta(days=35*365)
            return queryset.filter(
                fecha_nacimiento__lte=fecha_min_18,
                fecha_nacimiento__gte=fecha_max_35
            )
        elif self.value() == 'adulta_mayor':
            fecha_max = hoy - timedelta(days=35*365)
            return queryset.filter(fecha_nacimiento__lte=fecha_max)


class RiesgoListFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para nivel de riesgo.
    """
    title = 'Nivel de Riesgo'
    parameter_name = 'riesgo'

    def lookups(self, request, model_admin):
        return (
            ('alto', 'Alto Riesgo (≥ 50)'),
            ('medio', 'Riesgo Medio (25-49)'),
            ('bajo', 'Bajo Riesgo (< 25)'),
        )

    def queryset(self, request, queryset):
        # Este filtro puede ser lento, considera cachear resultados
        if self.value() == 'alto':
            pacientes_alto = [p.id for p in queryset if p.get_indice_riesgo() >= 50]
            return queryset.filter(id__in=pacientes_alto)
        elif self.value() == 'medio':
            pacientes_medio = [p.id for p in queryset if 25 <= p.get_indice_riesgo() < 50]
            return queryset.filter(id__in=pacientes_medio)
        elif self.value() == 'bajo':
            pacientes_bajo = [p.id for p in queryset if p.get_indice_riesgo() < 25]
            return queryset.filter(id__in=pacientes_bajo)


class ParidadListFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para paridad.
    """
    title = 'Paridad'
    parameter_name = 'paridad'

    def lookups(self, request, model_admin):
        return (
            ('nulipara', 'Nulípara (0 partos)'),
            ('primipara', 'Primípara (1 parto)'),
            ('multipara', 'Multípara (2-4 partos)'),
            ('gran_multipara', 'Gran Multípara (≥ 5 partos)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'nulipara':
            return queryset.filter(partos=0)
        elif self.value() == 'primipara':
            return queryset.filter(partos=1)
        elif self.value() == 'multipara':
            return queryset.filter(partos__gte=2, partos__lte=4)
        elif self.value() == 'gran_multipara':
            return queryset.filter(partos__gte=5)


# =============================================================================
# ADMIN PRINCIPAL DE PACIENTES
# =============================================================================

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """
    Configuración del administrador de pacientes.

    Características:
    - Lista detallada con información clave
    - Búsqueda por múltiples campos
    - Filtros personalizados
    - Acciones masivas
    - Visualización con colores según riesgo
    - Readonly fields para auditoría
    """

    # =========================================================================
    # CONFIGURACIÓN DE LISTADO
    # =========================================================================

    list_display = [
        'id_clinico_badge',
        'nombre_completo',
        'cedula_identidad',
        'edad_display',
        'gpac_display',
        'riesgo_badge',
        'telefono',
        'estado_badge',
    ]

    list_display_links = ['id_clinico_badge', 'nombre_completo']

    list_filter = [
        'activo',
        EdadListFilter,
        RiesgoListFilter,
        ParidadListFilter,
        'genero',
        'estado_civil',
        'diabetes_previa',
        'hipertension_previa',
        'preeclampsia_previa',
        'fuma',
        'tiene_seguro',
        'fecha_creacion',
    ]

    search_fields = [
        'id_clinico',
        'nombres',
        'apellidos',
        'cedula_identidad',
        'telefono',
        'email',
    ]

    ordering = ['-fecha_creacion']

    list_per_page = 25

    # =========================================================================
    # CONFIGURACIÓN DE FORMULARIO
    # =========================================================================

    fieldsets = (
        ('Identificación', {
            'fields': (
                'id_clinico',
                'cedula_identidad',
                'nombres',
                'apellidos',
                'fecha_nacimiento',
                'genero',
            )
        }),
        ('Contacto', {
            'fields': (
                'telefono',
                'email',
                'direccion',
                'ciudad',
                'pais',
            )
        }),
        ('Antecedentes Personales', {
            'fields': (
                'antecedentes_personales',
                'antecedentes_familiares',
                'alergias',
                'medicamentos_actuales',
                'inmunizaciones',
            ),
            'classes': ('collapse',)
        }),
        ('Antecedentes Gineco-Obstétricos', {
            'fields': (
                'fecha_primera_menstruacion',
                'ciclos_regulares',
                'duracion_ciclo',
                'duracion_menstruacion',
                'dismenorrea',
                'metodo_anticonceptivo_previo',
                'tiempo_uso_anticonceptivo',
            ),
            'classes': ('collapse',)
        }),
        ('Fórmula Obstétrica (GPAC)', {
            'fields': (
                'gestas',
                'partos',
                'abortos',
                'cesareas',
                'ectopicos',
                'molas',
                'hijos_vivos',
                'hijos_muertos',
            )
        }),
        ('Detalles Embarazos Previos', {
            'fields': (
                'complicaciones_embarazos_previos',
                'peso_maximo_recien_nacido',
                'peso_minimo_recien_nacido',
            ),
            'classes': ('collapse',)
        }),
        ('Factores de Riesgo', {
            'fields': (
                'diabetes_previa',
                'hipertension_previa',
                'preeclampsia_previa',
                'eclampsia_previa',
                'hemorragia_postparto_previa',
                'cirugia_uterina_previa',
                'incompetencia_cervical',
                'malformaciones_uterinas',
            ),
            'description': 'Marque los factores de riesgo presentes'
        }),
        ('Hábitos', {
            'fields': (
                'fuma',
                'cigarrillos_dia',
                'consume_alcohol',
                'frecuencia_alcohol',
                'consume_drogas',
                'tipo_drogas',
            ),
            'classes': ('collapse',)
        }),
        ('Contactos de Emergencia', {
            'fields': (
                'contacto_emergencia_nombre',
                'contacto_emergencia_telefono',
                'contacto_emergencia_relacion',
                'contacto_emergencia2_nombre',
                'contacto_emergencia2_telefono',
                'contacto_emergencia2_relacion',
            ),
            'classes': ('collapse',)
        }),
        ('Datos Socioeconómicos', {
            'fields': (
                'nivel_educativo',
                'ocupacion',
                'estado_civil',
                'vive_con',
                'situacion_vivienda',
                'acceso_agua_potable',
                'acceso_alcantarillado',
            ),
            'classes': ('collapse',)
        }),
        ('Seguro Médico', {
            'fields': (
                'tiene_seguro',
                'tipo_seguro',
                'numero_seguro',
            ),
            'classes': ('collapse',)
        }),
        ('Estado del Registro', {
            'fields': (
                'activo',
                'eliminado',
                'motivo_inactivacion',
            )
        }),
        ('Auditoría', {
            'fields': (
                'creado_por',
                'fecha_creacion',
                'modificado_por',
                'fecha_modificacion',
                'eliminado_por',
                'fecha_eliminacion',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'fecha_creacion',
        'fecha_modificacion',
        'fecha_eliminacion',
    ]

    # =========================================================================
    # ACCIONES MASIVAS
    # =========================================================================

    actions = [
        'activar_pacientes',
        'desactivar_pacientes',
        'marcar_alto_riesgo',
        'exportar_seleccionados',
    ]

    @admin.action(description='Activar pacientes seleccionados')
    def activar_pacientes(self, request, queryset):
        """Activa los pacientes seleccionados."""
        actualizados = queryset.update(activo=True, eliminado=False)
        self.message_user(
            request,
            f'{actualizados} paciente(s) activado(s) exitosamente.'
        )

    @admin.action(description='Desactivar pacientes seleccionados')
    def desactivar_pacientes(self, request, queryset):
        """Desactiva los pacientes seleccionados (soft delete)."""
        queryset.update(
            activo=False,
            eliminado=True,
            fecha_eliminacion=timezone.now(),
            motivo_inactivacion='Desactivación masiva desde admin'
        )
        self.message_user(
            request,
            f'{queryset.count()} paciente(s) desactivado(s).'
        )

    @admin.action(description='Identificar alto riesgo')
    def marcar_alto_riesgo(self, request, queryset):
        """Muestra pacientes de alto riesgo."""
        alto_riesgo = [p for p in queryset if p.get_indice_riesgo() >= 50]
        if alto_riesgo:
            nombres = ', '.join([f"{p.nombres} {p.apellidos}" for p in alto_riesgo])
            self.message_user(
                request,
                f'Pacientes de ALTO RIESGO: {nombres}',
                level='warning'
            )
        else:
            self.message_user(request, 'No hay pacientes de alto riesgo en la selección.')

    @admin.action(description='Exportar a CSV')
    def exportar_seleccionados(self, request, queryset):
        """Exporta los pacientes seleccionados a CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="pacientes_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID Clínico', 'Cédula', 'Nombres', 'Apellidos', 'Edad',
            'GPAC', 'Índice Riesgo', 'Teléfono', 'Email'
        ])

        for paciente in queryset:
            writer.writerow([
                paciente.id_clinico,
                paciente.cedula_identidad,
                paciente.nombres,
                paciente.apellidos,
                paciente.calcular_edad(),
                paciente.get_gpac_formatted(),
                paciente.get_indice_riesgo(),
                paciente.telefono,
                paciente.email or ''
            ])

        self.message_user(request, f'{queryset.count()} paciente(s) exportado(s).')
        return response

    # =========================================================================
    # MÉTODOS DE VISUALIZACIÓN PERSONALIZADOS
    # =========================================================================

    def id_clinico_badge(self, obj):
        """Muestra el ID clínico con badge."""
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            obj.id_clinico
        )
    id_clinico_badge.short_description = 'ID Clínico'

    def nombre_completo(self, obj):
        """Muestra el nombre completo."""
        return f"{obj.nombres} {obj.apellidos}"
    nombre_completo.short_description = 'Nombre Completo'

    def edad_display(self, obj):
        """Muestra la edad calculada."""
        edad = obj.calcular_edad()
        if edad:
            if edad < 18:
                color = '#e74c3c'  # Rojo para adolescentes
            elif edad > 35:
                color = '#f39c12'  # Naranja para >35
            else:
                color = '#27ae60'  # Verde para rango normal
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} años</span>',
                color, edad
            )
        return '-'
    edad_display.short_description = 'Edad'

    def gpac_display(self, obj):
        """Muestra la fórmula obstétrica GPAC."""
        return format_html(
            '<span style="font-family: monospace; background-color: #ecf0f1; '
            'padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.get_gpac_formatted()
        )
    gpac_display.short_description = 'GPAC'

    def riesgo_badge(self, obj):
        """Muestra el nivel de riesgo con colores."""
        indice = obj.get_indice_riesgo()

        if indice >= 50:
            color = '#e74c3c'
            texto = 'ALTO'
        elif indice >= 25:
            color = '#f39c12'
            texto = 'MEDIO'
        else:
            color = '#27ae60'
            texto = 'BAJO'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} ({})</span>',
            color, texto, indice
        )
    riesgo_badge.short_description = 'Riesgo'

    def estado_badge(self, obj):
        """Muestra el estado activo/inactivo."""
        if obj.activo:
            return format_html(
                '<span style="color: #27ae60;">✓ Activo</span>'
            )
        else:
            return format_html(
                '<span style="color: #e74c3c;">✗ Inactivo</span>'
            )
    estado_badge.short_description = 'Estado'