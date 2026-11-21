"""Evoluciones Admin"""

from django.contrib import admin

from .models import EvolucionEmbarazo


@admin.register(EvolucionEmbarazo)
class EvolucionEmbarazoAdmin(admin.ModelAdmin):
    """Evolucionembarazoadmin"""
    list_display = ("embarazo", "paciente", "tipo_evento", "fecha_evento", "medico")
    list_filter = ("tipo_evento", "fecha_evento")
    search_fields = ("paciente__nombre", "descripcion")
    readonly_fields = ("fecha_registro",)
