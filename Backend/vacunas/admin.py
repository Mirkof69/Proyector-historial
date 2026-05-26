"""=============================================================================
MÓDULO: VACUNAS - ADMIN
=============================================================================
Configuración del panel de administración para vacunas
- TipoVacunaAdmin: Administración del catálogo de vacunas
- RegistroVacunaAdmin: Administración de registros de vacunación
=============================================================================
"""

from django.contrib import admin
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

    def dosis_requeridas_badge(self, obj):
        """Badge con el número de dosis"""
        color = "green" if obj.dosis_requeridas == 1 else "blue"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} dosis</span>',
            color,
            obj.dosis_requeridas,
        )

    dosis_requeridas_badge.short_description = "Dosis Requeridas"

    def obligatoria_badge(self, obj):
        """Badge indicando si es obligatoria"""
        if obj.obligatoria_embarazo:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">OBLIGATORIA</span>',
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Opcional</span>',
        )

    obligatoria_badge.short_description = "Embarazo"

    def activo_badge(self, obj):
        """Badge de estado activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVO</span>',
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">INACTIVO</span>',
        )

    activo_badge.short_description = "Estado"

    def total_registros_badge(self, obj):
        """Total de registros de aplicación"""
        total = obj.registros.count()
        color = "green" if total > 0 else "gray"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} aplicaciones</span>',
            color,
            total,
        )

    total_registros_badge.short_description = "Aplicaciones"

    def get_estadisticas(self, obj):
        """Muestra estadísticas del tipo de vacuna"""
        if not obj.pk:
            return "Guarde para ver estadísticas"

        _total = obj.registros.count()
        _activos = obj.registros.filter(activo=True).count()
        _completos = sum(1 for r in obj.registros.all() if r.esquema_completo)

        html = """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Estadísticas de Aplicación</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>Total de aplicaciones:</strong> {total}</li>
                <li><strong>Registros activos:</strong> {activos}</li>
                <li><strong>Esquemas completos:</strong> {completos}</li>
            </ul>
        </div>
        """
        return format_html(html)

    get_estadisticas.short_description = "Estadísticas"

    actions = ["activar_vacunas", "desactivar_vacunas", "marcar_obligatorias"]

    def activar_vacunas(self, request, queryset):
        """Activa las vacunas seleccionadas"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} vacuna(s) activada(s) exitosamente.")

    activar_vacunas.short_description = "Activar vacunas seleccionadas"

    def desactivar_vacunas(self, request, queryset):
        """Desactiva las vacunas seleccionadas"""
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} vacuna(s) desactivada(s) exitosamente.")

    desactivar_vacunas.short_description = "Desactivar vacunas seleccionadas"

    def marcar_obligatorias(self, request, queryset):
        """Marca las vacunas como obligatorias en embarazo"""
        updated = queryset.update(obligatoria_embarazo=True)
        self.message_user(
            request, f"{updated} vacuna(s) marcada(s) como obligatoria(s).",
        )

    marcar_obligatorias.short_description = "Marcar como obligatorias en embarazo"


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

    def paciente_info(self, obj):
        """Información del paciente"""
        if obj.paciente:
            return format_html(
                "<strong>{}</strong><br/><small>ID: {}</small>",
                obj.paciente.nombre_completo,
                obj.paciente.id_clinico,
            )
        return "-"

    paciente_info.short_description = "Paciente"

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

    dosis_badge.short_description = "Progreso"

    def proxima_dosis_badge(self, obj):
        """Badge con la próxima dosis"""
        if obj.esquema_completo:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">COMPLETO</span>',
            )
        if obj.proxima_dosis_fecha:
            from datetime import date

            dias_restantes = (obj.proxima_dosis_fecha - date.today()).days
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

    proxima_dosis_badge.short_description = "Próxima Dosis"

    def reacciones_badge(self, obj):
        """Badge indicando si hay reacciones adversas"""
        if obj.tiene_reacciones_adversas:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; border-radius: 3px;">CON REACCIONES</span>',
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Sin reacciones</span>',
        )

    reacciones_badge.short_description = "Reacciones"

    def activo_badge(self, obj):
        """Badge de estado activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVO</span>',
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">INACTIVO</span>',
        )

    activo_badge.short_description = "Estado"

    def get_progreso_visual(self, obj):
        """Muestra progreso visual del esquema"""
        if not obj.pk:
            return "Guarde para ver progreso"

        progreso = obj.get_progreso_esquema()
        _porcentaje = progreso["porcentaje"]

        html = """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Progreso del Esquema</h3>
            <div style="background-color: #e9ecef; border-radius: 10px; height: 30px; overflow: hidden;">
                <div style="background-color: {"green" if progreso["completado"] else "blue"};
                            width: {porcentaje}%; height: 100%;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: bold;">
                    {porcentaje}%
                </div>
            </div>
            <p style="margin-top: 10px;">
                <strong>Dosis {progreso["dosis_actual"]} de {progreso["dosis_total"]}</strong>
                {" - COMPLETO" if progreso["completado"] else " - PENDIENTE"}
            </p>
        </div>
        """
        return format_html(html)

    get_progreso_visual.short_description = "Progreso del Esquema"

    def get_info_paciente(self, obj):
        """Información detallada del paciente"""
        if not obj.paciente:
            return "Sin paciente asignado"

        html = """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Información del Paciente</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>Nombre:</strong> {obj.paciente.nombre_completo}</li>
                <li><strong>ID Clínico:</strong> {obj.paciente.id_clinico}</li>
                <li><strong>CI:</strong> {obj.paciente.ci}</li>
                <li><strong>Edad:</strong> {obj.paciente.edad} años</li>
            </ul>
        </div>
        """
        return format_html(html)

    get_info_paciente.short_description = "Información del Paciente"

    def get_info_vacuna(self, obj):
        """Información detallada de la vacuna"""
        if not obj.tipo_vacuna:
            return "Sin vacuna asignada"

        html = """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="margin-top: 0;">Información de la Vacuna</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>Vacuna:</strong> {obj.tipo_vacuna.nombre}</li>
                <li><strong>Dosis requeridas:</strong> {obj.tipo_vacuna.dosis_requeridas}</li>
                <li><strong>Obligatoria:</strong> {"Sí" if obj.tipo_vacuna.obligatoria_embarazo else "No"}</li>
            </ul>
        </div>
        """
        return format_html(html)

    get_info_vacuna.short_description = "Información de la Vacuna"

    actions = ["activar_registros", "desactivar_registros", "calcular_proximas_dosis"]

    def activar_registros(self, request, queryset):
        """Activa los registros seleccionados"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} registro(s) activado(s) exitosamente.")

    activar_registros.short_description = "Activar registros seleccionados"

    def desactivar_registros(self, request, queryset):
        """Desactiva los registros seleccionados"""
        updated = queryset.update(activo=False)
        self.message_user(
            request, f"{updated} registro(s) desactivado(s) exitosamente.",
        )

    desactivar_registros.short_description = "Desactivar registros seleccionados"

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

    calcular_proximas_dosis.short_description = (
        "Calcular próximas dosis automáticamente"
    )
