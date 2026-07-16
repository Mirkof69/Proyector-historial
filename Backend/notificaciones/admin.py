"""=============================================================================
MÓDULO: NOTIFICACIONES - ADMIN
=============================================================================
Configuración del Django Admin para notificaciones
=============================================================================
"""

from django.contrib import admin

from .models import ConfiguracionNotificaciones, HistorialNotificaciones, Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """Admin para Notificaciones"""

    list_display = [
        "id",
        "usuario",
        "tipo",
        "prioridad",
        "titulo_corto",
        "leida",
        "archivada",
        "fecha_creacion",
        "icono_color",
    ]

    list_filter = [
        "tipo",
        "prioridad",
        "leida",
        "archivada",
        "fecha_creacion",
        "enviada_push",
        "enviada_email",
    ]

    search_fields = ["usuario__nombre", "usuario__apellido", "titulo", "mensaje"]

    readonly_fields = [
        "fecha_creacion",
        "fecha_leida",
        "get_tiempo_transcurrido",
        "esta_vigente",
    ]

    fieldsets = (
        ("Destinatario", {"fields": ("usuario",)}),
        ("Tipo y Prioridad", {"fields": ("tipo", "prioridad")}),
        ("Contenido", {"fields": ("titulo", "mensaje", "icono", "color")}),
        ("Acción", {"fields": ("url", "url_texto")}),
        ("Estado", {"fields": ("leida", "fecha_leida", "archivada")}),
        (
            "Metadatos",
            {
                "fields": ("metadata", "entidad_tipo", "entidad_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    "fecha_creacion",
                    "fecha_expiracion",
                    "get_tiempo_transcurrido",
                    "esta_vigente",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Envío",
            {
                "fields": ("enviada_push", "enviada_email", "enviada_sms"),
                "classes": ("collapse",),
            },
        ),
    )

    date_hierarchy = "fecha_creacion"
    ordering = ["-fecha_creacion"]

    actions = ["marcar_como_leidas", "archivar_seleccionadas"]

    @admin.display(description="Título")
    def titulo_corto(self, obj):
        """Muestra título acortado"""
        if len(obj.titulo) > 50:
            return obj.titulo[:50] + "..."
        return obj.titulo


    @admin.display(description="Icono/Color")
    def icono_color(self, obj):
        """Muestra icono y color"""
        return f"{obj.icono} ({obj.color})"


    @admin.display(description="Tiempo transcurrido")
    def get_tiempo_transcurrido(self, obj):
        """Tiempo transcurrido"""
        return obj.get_tiempo_transcurrido()


    @admin.action(description="Marcar seleccionadas como leídas")
    def marcar_como_leidas(self, request, queryset):
        """Acción: Marcar como leídas"""
        from django.utils import timezone

        count = queryset.update(leida=True, fecha_leida=timezone.now())
        self.message_user(request, f"{count} notificaciones marcadas como leídas.")


    @admin.action(description="Archivar seleccionadas")
    def archivar_seleccionadas(self, request, queryset):
        """Acción: Archivar"""
        count = queryset.update(archivada=True)
        self.message_user(request, f"{count} notificaciones archivadas.")



@admin.register(ConfiguracionNotificaciones)
class ConfiguracionNotificacionesAdmin(admin.ModelAdmin):
    """Admin para Configuración de Notificaciones"""

    list_display = [
        "usuario",
        "recibir_push",
        "recibir_email",
        "recibir_sms",
        "notificar_citas",
        "notificar_examenes",
        "recordatorio_citas_horas",
    ]

    list_filter = [
        "recibir_push",
        "recibir_email",
        "recibir_sms",
        "notificar_citas",
        "notificar_examenes",
        "notificar_alertas",
    ]

    search_fields = ["usuario__nombre", "usuario__apellido", "usuario__email"]

    fieldsets = (
        ("Usuario", {"fields": ("usuario",)}),
        (
            "Canales Activos",
            {"fields": ("recibir_push", "recibir_email", "recibir_sms")},
        ),
        (
            "Tipos de Notificaciones",
            {
                "fields": (
                    "notificar_citas",
                    "notificar_examenes",
                    "notificar_alertas",
                    "notificar_mensajes",
                    "notificar_documentos",
                ),
            },
        ),
        (
            "Recordatorios",
            {"fields": ("recordatorio_citas_horas", "recordatorio_controles")},
        ),
        (
            "Horario No Molestar",
            {
                "fields": ("no_molestar_inicio", "no_molestar_fin"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(HistorialNotificaciones)
class HistorialNotificacionesAdmin(admin.ModelAdmin):
    """Admin para Historial de Notificaciones"""

    list_display = ["id", "notificacion", "accion", "fecha"]

    list_filter = ["accion", "fecha"]

    search_fields = ["notificacion__titulo", "notificacion__usuario__nombre"]

    readonly_fields = ["fecha"]

    date_hierarchy = "fecha"
    ordering = ["-fecha"]
