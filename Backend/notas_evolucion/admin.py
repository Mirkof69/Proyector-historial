"""=============================================================================
ADMIN - NOTAS DE EVOLUCIÓN
=============================================================================
Configuración del panel de administración Django para notas médicas
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import NotaEvolucion


@admin.register(NotaEvolucion)
class NotaEvolucionAdmin(admin.ModelAdmin):
    """Administración de Notas de Evolución en Django Admin
    """

    # Lista de registros
    list_display = [
        "id",
        "paciente_display",
        "medico_display",
        "fecha_consulta_display",
        "tipo_consulta_badge",
        "presion_arterial_display",
        "temperatura_display",
        "edad_gestacional_display",
        "estado_revision",
        "activo_badge",
    ]

    list_filter = [
        "tipo_consulta",
        "activo",
        "fecha_consulta",
        "embarazo__riesgo_embarazo",
        ("revisado_por", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__ci",
        "paciente__id_clinico",
        "motivo_consulta",
        "diagnosticos",
        "medico__nombre",
        "medico__apellido_paterno",
    ]

    readonly_fields = [
        "fecha_creacion",
        "fecha_modificacion",
        "presion_arterial",
        "edad_gestacional_completa",
    ]

    autocomplete_fields = [
        "paciente",
        "embarazo",
        "control_prenatal",
        "medico",
        "revisado_por",
    ]

    # Organización por fieldsets
    fieldsets = (
        (
            "Información General",
            {
                "fields": (
                    "paciente",
                    "embarazo",
                    "control_prenatal",
                    "medico",
                    "fecha_consulta",
                    "tipo_consulta",
                    "activo",
                ),
            },
        ),
        ("Motivo de Consulta", {"fields": ("motivo_consulta",)}),
        (
            "Signos Vitales",
            {
                "fields": (
                    (
                        "presion_arterial_sistolica",
                        "presion_arterial_diastolica",
                        "presion_arterial",
                    ),
                    ("frecuencia_cardiaca", "frecuencia_respiratoria"),
                    ("temperatura", "saturacion_oxigeno"),
                ),
            },
        ),
        (
            "Datos Obstétricos",
            {
                "fields": (
                    (
                        "edad_gestacional_semanas",
                        "edad_gestacional_dias",
                        "edad_gestacional_completa",
                    ),
                    "altura_uterina",
                    "frecuencia_cardiaca_fetal",
                    "presentacion_fetal",
                    "movimientos_fetales",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Examen Físico",
            {
                "fields": (
                    "examen_fisico",
                    "examen_obstetrico",
                ),
            },
        ),
        (
            "Diagnóstico y Plan",
            {
                "fields": (
                    "diagnosticos",
                    "plan_tratamiento",
                    "indicaciones",
                ),
            },
        ),
        ("Observaciones", {"fields": ("observaciones",), "classes": ("collapse",)}),
        (
            "Control de Calidad",
            {
                "fields": (
                    "revisado_por",
                    "fecha_revision",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Trazabilidad",
            {
                "fields": (
                    "fecha_creacion",
                    "fecha_modificacion",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    # Ordenamiento
    ordering = ["-fecha_consulta"]

    # Acciones masivas
    actions = [
        "marcar_como_activo",
        "marcar_como_inactivo",
    ]

    # Paginación
    list_per_page = 25

    # Display methods personalizados
    @admin.display(description="Paciente", ordering="paciente__apellido_paterno")
    def paciente_display(self, obj):
        """Muestra el nombre completo del paciente con su ID clínico"""
        return format_html(
            "<strong>{}</strong><br/><small>ID: {}</small>",
            obj.paciente.nombre_completo,
            obj.paciente.id_clinico,
        )

    @admin.display(description="Médico", ordering="medico__apellido_paterno")
    def medico_display(self, obj):
        """Muestra el nombre del médico con su especialidad"""
        medico = getattr(obj, 'medico', None)
        if medico is None:
            return format_html("<em>Sin médico asignado</em>")
        especialidad = (
            f" - {getattr(medico, 'especialidad', '')}" if getattr(medico, 'especialidad', None) else ""
        )
        return format_html(
            "<strong>{}</strong><br/><small>{}{}</small>",
            getattr(medico, 'nombre_completo', ''),
            getattr(medico, 'get_rol_display', lambda: '')(),
            especialidad,
        )

    @admin.display(description="Fecha Consulta", ordering="fecha_consulta")
    def fecha_consulta_display(self, obj):
        """Muestra la fecha de consulta formateada"""
        return obj.fecha_consulta.strftime("%d/%m/%Y %H:%M")

    @admin.display(description="Tipo")
    def tipo_consulta_badge(self, obj):
        """Muestra el tipo de consulta con color"""
        colors = {
            "control_prenatal": "#28a745",
            "urgencia": "#dc3545",
            "seguimiento": "#17a2b8",
            "interconsulta": "#ffc107",
            "puerperio": "#6c757d",
            "otro": "#6c757d",
        }
        color = colors.get(obj.tipo_consulta, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            getattr(obj, 'get_tipo_consulta_display')(),
        )

    @admin.display(description="Presión Arterial")
    def presion_arterial_display(self, obj):
        """Muestra la presión arterial"""
        if obj.presion_arterial:
            # Colorear según valores
            sistolica = obj.presion_arterial_sistolica
            if sistolica >= 140:
                color = "#dc3545"  # Rojo
            elif sistolica >= 130:
                color = "#ffc107"  # Amarillo
            else:
                color = "#28a745"  # Verde
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                obj.presion_arterial,
            )
        return "-"

    @admin.display(description="Temperatura")
    def temperatura_display(self, obj):
        """Muestra la temperatura con color según valor"""
        if obj.temperatura:
            if obj.temperatura >= 38:
                color = "#dc3545"  # Rojo - Fiebre
            elif obj.temperatura >= 37.5:
                color = "#ffc107"  # Amarillo - Febrícula
            else:
                color = "#28a745"  # Verde - Normal
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} °C</span>',
                color,
                obj.temperatura,
            )
        return "-"

    @admin.display(description="Edad Gestacional")
    def edad_gestacional_display(self, obj):
        """Muestra la edad gestacional"""
        if obj.edad_gestacional_completa:
            return obj.edad_gestacional_completa
        return "-"

    @admin.display(description="Revisión")
    def estado_revision(self, obj):
        """Muestra el estado de revisión de la nota"""
        if obj.revisado_por:
            return format_html(
                '<span style="color: #28a745;">✓ Revisada</span><br/>'
                "<small>por {}</small>",
                obj.revisado_por.nombre_completo,
            )
        return format_html('<span style="color: #ffc107;">⏳ Pendiente</span>')

    @admin.display(description="Estado", boolean=True)
    def activo_badge(self, obj):
        """Muestra el estado activo/inactivo"""
        return obj.activo

    # Acciones masivas
    @admin.action(description="Marcar notas seleccionadas como activas")
    def marcar_como_activo(self, request, queryset):
        """Marca las notas seleccionadas como activas"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} nota(s) marcada(s) como activa(s).")

    @admin.action(description="Marcar notas seleccionadas como inactivas")
    def marcar_como_inactivo(self, request, queryset):
        """Marca las notas seleccionadas como inactivas"""
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} nota(s) marcada(s) como inactiva(s).")

    def get_queryset(self, request):
        """Optimiza las consultas usando select_related
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "paciente", "embarazo", "control_prenatal", "medico", "revisado_por",
        )
