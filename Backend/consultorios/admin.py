"""CONSULTORIOS - ADMIN"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Consultorio


@admin.register(Consultorio)
class ConsultorioAdmin(admin.ModelAdmin):
    """Consultorioadmin"""
    list_display = (
        "nombre",
        "tipo_consultorio",
        "ubicacion",
        "get_disponibilidad_badge",
        "get_equipamiento_icons",
    )
    list_filter = ("activo", "en_mantenimiento", "tipo_consultorio", "tiene_ecografo")
    search_fields = ("nombre", "codigo", "ubicacion")

    fieldsets = (
        ("Identificación", {"fields": (("nombre", "codigo"),)}),
        ("Ubicación", {"fields": (("ubicacion", "piso"), "edificio")}),
        (
            "Características",
            {
                "fields": (
                    "tipo_consultorio",
                    "capacidad_personas",
                    ("tiene_bano", "tiene_camilla", "tiene_ecografo"),
                    "equipamiento",
                ),
            },
        ),
        ("Estado", {"fields": (("activo", "en_mantenimiento"), "observaciones")}),
    )

    def get_disponibilidad_badge(self, obj):
        """Get disponibilidad badge"""
        if obj.esta_disponible():
            return format_html(
                '<span style="background-color:#27ae60;color:white;padding:3px 8px;border-radius:3px;">✅ DISPONIBLE</span>',
            )
        if obj.en_mantenimiento:
            return format_html(
                '<span style="background-color:#f39c12;color:white;padding:3px 8px;border-radius:3px;"> MANTENIMIENTO</span>',
            )
        return format_html(
            '<span style="background-color:#e74c3c;color:white;padding:3px 8px;border-radius:3px;">❌ INACTIVO</span>',
        )

    get_disponibilidad_badge.short_description = "Disponibilidad"

    def get_equipamiento_icons(self, obj):
        """Get equipamiento icons"""
        icons = []
        if obj.tiene_bano:
            icons.append("")
        if obj.tiene_camilla:
            icons.append("️")
        if obj.tiene_ecografo:
            icons.append("")
        return " ".join(icons) if icons else "-"

    get_equipamiento_icons.short_description = "Equipamiento"
