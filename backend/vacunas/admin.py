"""=============================================================================
MÓDULO: VACUNAS - ADMIN
=============================================================================
Configuración del panel de administración para vacunas
- TipoVacunaAdmin: Administración del catálogo de vacunas
- RegistroVacunaAdmin: Administración de registros de vacunación
=============================================================================
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import RegistroVacuna, TipoVacuna


@admin.register(TipoVacuna)
class TipoVacunaAdmin(admin.ModelAdmin):
    """Administración avanzada para TipoVacuna
    Incluye filtros, búsqueda y visualización mejorada
    """

    list_display = [
        "id",
        "nombre",
        "dosis_requeridas_badge",
        "intervalo_dosis_dias",
        "obligatoria_badge",
        "activo_badge",
        "total_registros_badge",
        "fecha_creacion",
    ]

    list_filter = [
        "activo",
        "obligatoria_embarazo",
        "dosis_requeridas",
        "fecha_creacion",
    ]

    search_fields = [
        "nombre",
        "descripcion",
        "contraindicaciones",
    ]

    readonly_fields = [
        "fecha_creacion",
        "fecha_modificacion",
        "get_estadisticas",
    ]

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "nombre",
                    "descripcion",
                    "activo",
                ),
            },
        ),
        (
            "Esquema de Dosificación",
            {
                "fields": (
                    "dosis_requeridas",
                    "intervalo_dosis_dias",
                    "edad_minima_aplicacion",
                ),
            },
        ),
        (
            "Información Médica",
            {
                "fields": (
                    "contraindicaciones",
                    "efectos_secundarios",
                ),
            },
        ),
        ("Clasificación", {"fields": ("obligatoria_embarazo",)}),
        (
            "Metadatos",
            {
                "fields": (
                    "fecha_creacion",
                    "fecha_modificacion",
                    "get_estadisticas",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    ordering = ["nombre"]

    @admin.display(description="Dosis Requeridas")
    def dosis_requeridas_badge(self, obj):
        """Badge con el número de dosis"""
        color = "green" if obj.dosis_requeridas == 1 else "blue"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} dosis</span>',
            color,
            obj.dosis_requeridas,
        )


    @admin.display(description="Embarazo")
    def obligatoria_badge(self, obj):
        """Badge indicando si es obligatoria"""
        if obj.obligatoria_embarazo:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">OBLIGATORIA</span>',
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Opcional</span>',
        )


    @admin.display(description="Estado")
    def activo_badge(self, obj):
        """Badge de estado activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVO</span>',
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">INACTIVO</span>',
        )


    @admin.display(description="Aplicaciones")
    def total_registros_badge(self, obj):
        """Total de registros de aplicación"""
        total = obj.registros.count()
        color = "green" if total > 0 else "gray"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} aplicaciones</span>',
            color,
            total,
        )


    @admin.display(description="Estadísticas")
    def get_estadisticas(self, obj):
        """Muestra estadísticas del tipo de vacuna"""
        if not obj.pk:
            return "Guarde para ver estadísticas"

        total = obj.registros.count()
        activos = obj.registros.filter(activo=True).count()
        completos = sum(1 for r in obj.registros.all() if r.esquema_completo)

        return format_html(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Estadísticas de Aplicación</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>Total de aplicaciones:</strong> {}</li>
                <li><strong>Registros activos:</strong> {}</li>
                <li><strong>Esquemas completos:</strong> {}</li>
            </ul>
        </div>
        """,
            total, activos, completos,
        )


    actions = ["activar_vacunas", "desactivar_vacunas", "marcar_obligatorias"]

    @admin.action(description="Activar vacunas seleccionadas")
    def activar_vacunas(self, request, queryset):
        """Activa las vacunas seleccionadas"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} vacuna(s) activada(s) exitosamente.")


    @admin.action(description="Desactivar vacunas seleccionadas")
    def desactivar_vacunas(self, request, queryset):
        """Desactiva las vacunas seleccionadas"""
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} vacuna(s) desactivada(s) exitosamente.")


    @admin.action(description="Marcar como obligatorias en embarazo")
    def marcar_obligatorias(self, request, queryset):
        """Marca las vacunas como obligatorias en embarazo"""
        updated = queryset.update(obligatoria_embarazo=True)
        self.message_user(
            request, f"{updated} vacuna(s) marcada(s) como obligatoria(s).",
        )



@admin.register(RegistroVacuna)
class RegistroVacunaAdmin(admin.ModelAdmin):
    """Administración avanzada para RegistroVacuna
    Incluye filtros, búsqueda y visualización mejorada
    """

    list_display = [
        "id",
        "paciente_info",
        "tipo_vacuna",
        "numero_dosis",
        "dosis_badge",
        "fecha_aplicacion",
        "proxima_dosis_badge",
        "via_administracion",
        "reacciones_badge",
        "activo_badge",
    ]

    list_filter = [
        "activo",
        "via_administracion",
        "fecha_aplicacion",
        "tipo_vacuna",
        "numero_dosis",
    ]

    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
        "paciente__id_clinico",
        "tipo_vacuna__nombre",
        "lote",
        "laboratorio",
    ]

    readonly_fields = [
        "fecha_creacion",
        "fecha_modificacion",
        "get_progreso_visual",
        "get_info_paciente",
        "get_info_vacuna",
    ]

    fieldsets = (
        (
            "Paciente y Vacuna",
            {
                "fields": (
                    "paciente",
                    "embarazo",
                    "tipo_vacuna",
                    "get_info_paciente",
                    "get_info_vacuna",
                ),
            },
        ),
        (
            "Información de Aplicación",
            {
                "fields": (
                    "fecha_aplicacion",
                    "numero_dosis",
                    "lote",
                    "laboratorio",
                ),
            },
        ),
        (
            "Detalles de Administración",
            {
                "fields": (
                    "via_administracion",
                    "sitio_aplicacion",
                    "aplicado_por",
                ),
            },
        ),
        (
            "Seguimiento",
            {
                "fields": (
                    "proxima_dosis_fecha",
                    "get_progreso_visual",
                ),
            },
        ),
        (
            "Reacciones y Observaciones",
            {
                "fields": (
                    "reacciones_adversas",
                    "observaciones",
                ),
            },
        ),
        ("Estado", {"fields": ("activo",)}),
        (
            "Metadatos",
            {
                "fields": (
                    "fecha_creacion",
                    "fecha_modificacion",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    autocomplete_fields = ["paciente", "embarazo", "tipo_vacuna", "aplicado_por"]

    date_hierarchy = "fecha_aplicacion"

    ordering = ["-fecha_aplicacion"]

    @admin.display(description="Paciente")
    def paciente_info(self, obj):
        """Información del paciente"""
        if obj.paciente:
            return format_html(
                "<strong>{}</strong><br/><small>ID: {}</small>",
                obj.paciente.nombre_completo,
                obj.paciente.id_clinico,
            )
        return "-"


    @admin.display(description="Progreso")
    def dosis_badge(self, obj):
        """Badge con el número de dosis"""
        progreso = obj.get_progreso_esquema()
        color = "green" if progreso["completado"] else "blue"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}/{}</span>',
            color,
            progreso["dosis_actual"],
            progreso["dosis_total"],
        )


    @admin.display(description="Próxima Dosis")
    def proxima_dosis_badge(self, obj):
        """Badge con la próxima dosis"""
        if obj.esquema_completo:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">COMPLETO</span>',
            )
        if obj.proxima_dosis_fecha:

            dias_restantes = (obj.proxima_dosis_fecha - timezone.localdate()).days
            if dias_restantes < 0:
                color = "red"
                texto = "VENCIDA"
            elif dias_restantes <= 7:
                color = "orange"
                texto = f"{dias_restantes} días"
            else:
                color = "blue"
                texto = f"{dias_restantes} días"
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
                color,
                texto,
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Sin programar</span>',
        )


    @admin.display(description="Reacciones")
    def reacciones_badge(self, obj):
        """Badge indicando si hay reacciones adversas"""
        if obj.tiene_reacciones_adversas:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; border-radius: 3px;">CON REACCIONES</span>',
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Sin reacciones</span>',
        )


    @admin.display(description="Estado")
    def activo_badge(self, obj):
        """Badge de estado activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVO</span>',
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">INACTIVO</span>',
        )


    @admin.display(description="Progreso del Esquema")
    def get_progreso_visual(self, obj):
        """Muestra progreso visual del esquema"""
        if not obj.pk:
            return "Guarde para ver progreso"

        progreso = obj.get_progreso_esquema()
        porcentaje = progreso["porcentaje"]
        color = "green" if progreso["completado"] else "blue"
        estado = " - COMPLETO" if progreso["completado"] else " - PENDIENTE"

        return format_html(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Progreso del Esquema</h3>
            <div style="background-color: #e9ecef; border-radius: 10px; height: 30px; overflow: hidden;">
                <div style="background-color: {}; width: {}%; height: 100%;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: bold;">
                    {}%
                </div>
            </div>
            <p style="margin-top: 10px;">
                <strong>Dosis {} de {}</strong>
                {}
            </p>
        </div>
        """,
            color, porcentaje, porcentaje,
            progreso["dosis_actual"], progreso["dosis_total"], estado,
        )


    @admin.display(description="Información del Paciente")
    def get_info_paciente(self, obj):
        """Información detallada del paciente"""
        if not obj.paciente:
            return "Sin paciente asignado"

        return format_html(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Información del Paciente</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>Nombre:</strong> {}</li>
                <li><strong>ID Clínico:</strong> {}</li>
                <li><strong>CI:</strong> {}</li>
                <li><strong>Edad:</strong> {} años</li>
            </ul>
        </div>
        """,
            obj.paciente.nombre_completo, obj.paciente.id_clinico,
            obj.paciente.ci, obj.paciente.edad,
        )


    @admin.display(description="Información de la Vacuna")
    def get_info_vacuna(self, obj):
        """Información detallada de la vacuna"""
        if not obj.tipo_vacuna:
            return "Sin vacuna asignada"

        obligatoria = "Sí" if obj.tipo_vacuna.obligatoria_embarazo else "No"
        return format_html(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Información de la Vacuna</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>Vacuna:</strong> {}</li>
                <li><strong>Dosis requeridas:</strong> {}</li>
                <li><strong>Obligatoria:</strong> {}</li>
            </ul>
        </div>
        """,
            obj.tipo_vacuna.nombre, obj.tipo_vacuna.dosis_requeridas, obligatoria,
        )


    actions = ["activar_registros", "desactivar_registros", "calcular_proximas_dosis"]

    @admin.action(description="Activar registros seleccionados")
    def activar_registros(self, request, queryset):
        """Activa los registros seleccionados"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} registro(s) activado(s) exitosamente.")


    @admin.action(description="Desactivar registros seleccionados")
    def desactivar_registros(self, request, queryset):
        """Desactiva los registros seleccionados"""
        updated = queryset.update(activo=False)
        self.message_user(
            request, f"{updated} registro(s) desactivado(s) exitosamente.",
        )


    @admin.action(description="Calcular Proximas Dosis")
    def calcular_proximas_dosis(self, request, queryset):
        """Calcula automáticamente las próximas dosis"""
        updated = 0
        for registro in queryset:
            if registro.requiere_siguiente_dosis and not registro.proxima_dosis_fecha:
                fecha = registro.calcular_proxima_dosis_fecha()
                if fecha:
                    registro.proxima_dosis_fecha = fecha
                    registro.save()
                    updated += 1
        self.message_user(
            request, f"{updated} próxima(s) dosis calculada(s) exitosamente.",
        )

        "Calcular próximas dosis automáticamente"
