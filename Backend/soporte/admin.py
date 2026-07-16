"""Admin module."""
from django.contrib import admin

from .models import TicketSoporte


@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    """Admin para tickets de soporte"""
    list_display = ["id", "asunto", "usuario", "modulo", "prioridad", "estado", "fecha_creacion"]
    list_filter = ["estado", "prioridad", "modulo"]
    search_fields = ["asunto", "descripcion"]
