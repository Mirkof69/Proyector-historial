"""Admin module."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Cita, Disponibilidad, HistorialCita


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    """Administración de Disponibilidades"""

    list_display = [
        "medico_nombre",
        "dia_badge",
        "horario_formateado",
        "duracion_cita",
        "total_slots",
        "activo_badge",
        "vigencia",
    ]

    list_filter = ["dia_semana", "activo", "medico"]

    search_fields = ["medico__nombre", "medico__apellido_paterno"]

    readonly_fields = [
        "fecha_creacion",
        "fecha_actualizacion",
        "total_slots",
        "horas_disponibles",
    ]

    autocomplete_fields = ["medico"]

    fieldsets = (
        ("Médico", {"fields": ("medico",)}),
        (
            "Horario",
            {"fields": ("dia_semana", "hora_inicio", "hora_fin", "duracion_cita")},
        ),
        (
            "Vigencia",
            {"fields": ("fecha_inicio_vigencia", "fecha_fin_vigencia", "activo")},
        ),
        (
            "Información",
            {"fields": ("observaciones", "total_slots", "horas_disponibles")},
        ),
        (
            "Metadatos",
            {
                "fields": ("fecha_creacion", "fecha_actualizacion"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["activar_disponibilidades", "desactivar_disponibilidades"]

    @admin.display(description="Médico")
    def medico_nombre(self, obj):
        """Medico nombre"""
        return format_html(
            "<strong>Dr(a). {} {}</strong>",
            obj.medico.nombre,
            obj.medico.apellido_paterno,
        )


    @admin.display(description="Día")
    def dia_badge(self, obj):
        """Dia badge"""
        colors = {
            0: "#3498db",  # Lunes
            1: "#2ecc71",  # Martes
            2: "#9b59b6",  # Miércoles
            3: "#e67e22",  # Jueves
            4: "#e74c3c",  # Viernes
            5: "#34495e",  # Sábado
            6: "#95a5a6",  # Domingo
        }
        color = colors.get(obj.dia_semana, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            getattr(obj, 'get_dia_semana_display')(),
        )


    @admin.display(description="Horario")
    def horario_formateado(self, obj):
        """Horario formateado"""
        return f"{obj.hora_inicio.strftime('%H:%M')} - {obj.hora_fin.strftime('%H:%M')}"


    @admin.display(description="Estado")
    def activo_badge(self, obj):
        """Activo badge"""
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>',
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>',
        )


    @admin.display(description="Vigencia")
    def vigencia(self, obj):
        """Vigencia"""
        if obj.fecha_inicio_vigencia or obj.fecha_fin_vigencia:
            inicio = (
                obj.fecha_inicio_vigencia.strftime("%d/%m/%Y")
                if obj.fecha_inicio_vigencia
                else "Sin inicio"
            )
            fin = (
                obj.fecha_fin_vigencia.strftime("%d/%m/%Y")
                if obj.fecha_fin_vigencia
                else "Sin fin"
            )
            return f"{inicio} - {fin}"
        return "Sin restricción"


    @admin.action(description="Activar disponibilidades seleccionadas")
    def activar_disponibilidades(self, request, queryset):
        """Activar disponibilidades"""
        updated = queryset.update(activo=True)
        self.message_user(
            request, f"{updated} disponibilidades activadas correctamente.",
        )

    @admin.action(description="Desactivar disponibilidades seleccionadas")
    def desactivar_disponibilidades(self, request, queryset):
        """Desactivar disponibilidades"""
        updated = queryset.update(activo=False)
        self.message_user(
            request, f"{updated} disponibilidades desactivadas correctamente.",
        )


class HistorialCitaInline(admin.TabularInline):
    """Inline para historial de citas"""

    model = HistorialCita
    extra = 0
    readonly_fields = [
        "estado_anterior",
        "estado_nuevo",
        "motivo_cambio",
        "usuario",
        "fecha_cambio",
    ]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Has add permission"""
        return False


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    """Administración de Citas"""

    list_display = [
        "id",
        "fecha_hora_badge",
        "paciente_link",
        "medico_nombre",
        "tipo_badge",
        "estado_badge",
        "dias_hasta",
        "confirmada",
    ]

    list_filter = [
        "estado",
        "tipo_cita",
        "fecha_cita",
        "recordatorio_enviado",
    ]

    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__id_clinico",
        "medico__nombre",
        "medico__apellido_paterno",
    ]

    readonly_fields = [
        "fecha_creacion",
        "fecha_actualizacion",
        "fecha_hora_cita",
        "esta_pendiente",
        "dias_hasta_cita",
        "requiere_recordatorio",
    ]

    autocomplete_fields = ["paciente", "medico", "confirmada_por", "creado_por"]

    date_hierarchy = "fecha_cita"

    fieldsets = (
        (
            "Información de la Cita",
            {"fields": ("paciente", "medico", "fecha_cita", "hora_cita", "duracion")},
        ),
        ("Detalles", {"fields": ("tipo_cita", "estado", "motivo", "observaciones")}),
        (
            "Confirmación",
            {
                "fields": ("confirmada_por", "fecha_confirmacion"),
                "classes": ("collapse",),
            },
        ),
        (
            "Recordatorio",
            {
                "fields": ("recordatorio_enviado", "fecha_recordatorio"),
                "classes": ("collapse",),
            },
        ),
        (
            "Información del Sistema",
            {
                "fields": (
                    "creado_por",
                    "fecha_creacion",
                    "fecha_actualizacion",
                    "fecha_hora_cita",
                    "esta_pendiente",
                    "dias_hasta_cita",
                    "requiere_recordatorio",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [HistorialCitaInline]

    actions = ["confirmar_citas", "cancelar_citas", "completar_citas"]

    @admin.display(description="Fecha y Hora")
    def fecha_hora_badge(self, obj):
        """Fecha hora badge"""
        hoy = obj.fecha_cita.today()
        color = (
            "#e74c3c"
            if obj.fecha_cita < hoy
            else "#3498db"
            if obj.fecha_cita == hoy
            else "#95a5a6"
        )
        return format_html(
            '<div style="text-align: center;"><div style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; margin-bottom: 2px; font-size: 11px;">{}</div><div style="font-weight: bold;">{}</div></div>',
            color,
            obj.fecha_cita.strftime("%d/%m/%Y"),
            obj.hora_cita.strftime("%H:%M"),
        )


    @admin.display(description="Paciente")
    def paciente_link(self, obj):
        """Paciente link"""
        return format_html(
            '<a href="/admin/pacientes/paciente/{}/change/">{}</a><br><small style="color: #666;">{}</small>',
            obj.paciente.id,
            obj.paciente.nombre_completo,
            obj.paciente.id_clinico,
        )


    @admin.display(description="Médico")
    def medico_nombre(self, obj):
        """Medico nombre"""
        return f"Dr(a). {obj.medico.nombre} {obj.medico.apellido_paterno}"


    @admin.display(description="Tipo")
    def tipo_badge(self, obj):
        """Tipo badge"""
        colors = {
            "primera_vez": "#3498db",
            "control": "#2ecc71",
            "urgencia": "#e74c3c",
            "seguimiento": "#f39c12",
        }
        color = colors.get(obj.tipo_cita, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            getattr(obj, 'get_tipo_cita_display')(),
        )


    @admin.display(description="Estado")
    def estado_badge(self, obj):
        """Estado badge"""
        colors = {
            "agendada": "#f39c12",
            "confirmada": "#3498db",
            "completada": "#27ae60",
            "cancelada": "#e74c3c",
            "no_asistio": "#95a5a6",
        }
        icons = {
            "agendada": "",
            "confirmada": "✅",
            "completada": "✔️",
            "cancelada": "❌",
            "no_asistio": "⚠️",
        }
        color = colors.get(obj.estado, "#95a5a6")
        icon = icons.get(obj.estado, "•")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            getattr(obj, 'get_estado_display')(),
        )


    @admin.display(description="Días")
    def dias_hasta(self, obj):
        """Dias hasta"""
        dias = obj.dias_hasta_cita
        if dias is None:
            return "-"

        if dias < 0:
            return format_html(
                '<span style="color: red;">Hace {} días</span>', abs(dias),
            )
        if dias == 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">HOY</span>',
            )
        color = "#e74c3c" if dias <= 3 else "#95a5a6"
        return format_html(
            '<span style="color: {};">En {} días</span>', color, dias,
        )


    @admin.display(description="Confirmada")
    def confirmada(self, obj):
        """Confirmada"""
        if obj.fecha_confirmacion:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">-</span>')


    @admin.action(description="Confirmar citas seleccionadas")
    def confirmar_citas(self, request, queryset):
        """Confirmar citas"""
        from django.utils import timezone

        updated = queryset.filter(estado="agendada").update(
            estado="confirmada",
            fecha_confirmacion=timezone.now(),
            confirmada_por=request.user,
        )
        self.message_user(request, f"{updated} citas confirmadas correctamente.")


    @admin.action(description="Cancelar citas seleccionadas")
    def cancelar_citas(self, request, queryset):
        """Cancelar citas"""
        updated = queryset.filter(estado__in=["agendada", "confirmada"]).update(
            estado="cancelada",
        )
        self.message_user(request, f"{updated} citas canceladas correctamente.")


    @admin.action(description="Marcar como completadas")
    def completar_citas(self, request, queryset):
        """Completar citas"""
        updated = queryset.filter(estado__in=["agendada", "confirmada"]).update(
            estado="completada",
        )
        self.message_user(request, f"{updated} citas completadas correctamente.")



@admin.register(HistorialCita)
class HistorialCitaAdmin(admin.ModelAdmin):
    """Administración de Historial de Citas"""

    list_display = [
        "cita_info",
        "cambio_estado",
        "usuario_nombre",
        "fecha_cambio_formateada",
    ]

    list_filter = ["estado_anterior", "estado_nuevo", "fecha_cambio"]

    search_fields = [
        "cita__paciente__nombre",
        "cita__paciente__apellido_paterno",
        "usuario__nombre",
    ]

    readonly_fields = [
        "cita",
        "estado_anterior",
        "estado_nuevo",
        "motivo_cambio",
        "usuario",
        "fecha_cambio",
    ]

    def has_add_permission(self, request):
        """Has add permission"""
        return False

    def has_change_permission(self, request, obj=None):
        """Has change permission"""
        return False

    @admin.display(description="Cita")
    def cita_info(self, obj):
        """Cita info"""
        return format_html(
            "<strong>Cita #{}</strong><br>{}<br><small>{}</small>",
            obj.cita.id,
            obj.cita.paciente.nombre_completo,
            obj.cita.fecha_cita.strftime("%d/%m/%Y %H:%M"),
        )


    @admin.display(description="Cambio de Estado")
    def cambio_estado(self, obj):
        """Cambio estado"""
        return format_html(
            '<span style="color: #e74c3c;">{}</span> → <span style="color: #27ae60;">{}</span>',
            getattr(obj, 'get_estado_anterior_display')() if obj.estado_anterior else "Creación",
            getattr(obj, 'get_estado_nuevo_display')(),
        )


    @admin.display(description="Usuario")
    def usuario_nombre(self, obj):
        """Usuario nombre"""
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido_paterno}"
        return "Sistema"


    @admin.display(description="Fecha")
    def fecha_cambio_formateada(self, obj):
        """Fecha cambio formateada"""
        return obj.fecha_cambio.strftime("%d/%m/%Y %H:%M:%S")



# Personalizar título del admin
admin.site.site_header = "Sistema de Historias Clínicas - Administración"
admin.site.site_title = "Admin Fetal Medical"
admin.site.index_title = "Panel de Administración"
