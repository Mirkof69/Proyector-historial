"""Ecografias Archivos Admin"""

from django.contrib import admin

from .models import EcografiaArchivo


@admin.register(EcografiaArchivo)
class EcografiaArchivoAdmin(admin.ModelAdmin):
    """Ecografiaarchivoadmin"""
    list_display = (
        "nombre_archivo",
        "ecografia",
        "tipo_archivo",
        "tamano_bytes",
        "fecha_subida",
        "subido_por",
    )
    list_filter = ("tipo_archivo", "fecha_subida")
    search_fields = ("nombre_archivo", "descripcion")
    readonly_fields = ("fecha_subida", "tamano_bytes")
