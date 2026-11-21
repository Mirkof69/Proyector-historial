"""=============================================================================
ADMIN: AUDITORÍA
=============================================================================
Registro del modelo de auditoría en el panel de administración de Django.
=============================================================================
"""

from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Administración de registros de auditoría"""

    list_display = [
        "id",
        "fecha",
        "modulo",
        "accion",
        "registro_id",
        "usuario",
        "cambios_resumidos",
    ]
    list_filter = ["modulo", "accion", "fecha"]
    search_fields = ["modulo", "usuario__username", "registro_id"]
    readonly_fields = [
        "modulo",
        "accion",
        "registro_id",
        "usuario",
        "fecha",
        "datos_anteriores",
        "datos_nuevos",
        "ip_address",
        "user_agent",
        "cambios_resumidos",
    ]
    ordering = ["-fecha"]
    date_hierarchy = "fecha"

    def has_add_permission(self, request):
        """No permitir crear registros de auditoría manualmente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar registros de auditoría"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir modificar registros de auditoría"""
        return False
