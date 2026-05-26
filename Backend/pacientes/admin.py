"""Admin module."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Administración de Pacientes"""

    list_display = [
        "id",
        "id_clinico",
        "nombre_completo_display",
        "ci",
        "edad_display",
        "telefono",
        "email",
        "activo_badge",
    ]

    list_filter = [
        "activo",
        "genero",
        "ciudad",
        "fecha_registro",
    ]

    search_fields = [
        "nombre",
        "apellido_paterno",
        "apellido_materno",
        "ci",
        "id_clinico",
        "email",
        "telefono",
    ]

    readonly_fields = [
        "id_clinico",
        "fecha_registro",
        "fecha_actualizacion",
        "edad_display",
    ]

    fieldsets = (
        (
            "Información Personal",
            {
                "fields": (
                    "nombre",
                    "apellido_paterno",
                    "apellido_materno",
                    "fecha_nacimiento",
                    "genero",
                ),
            },
        ),
        ("Documentos", {"fields": ("ci", "id_clinico")}),
        (
            "Contacto",
            {
                "fields": (
                    "telefono",
                    "email",
                    "direccion",
                    "ciudad",
                    "pais",
                ),
            },
        ),
        (
            "Información Adicional",
            {"fields": ("observaciones",), "classes": ("collapse",)},
        ),
        (
            "Metadatos",
            {
                "fields": (
                    "activo",
                    "fecha_registro",
                    "fecha_actualizacion",
                    "edad_display",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    date_hierarchy = "fecha_registro"
    list_per_page = 25

    def nombre_completo_display(self, obj):
        """Muestra el nombre completo"""
        return obj.nombre_completo

    nombre_completo_display.short_description = "Nombre Completo"

    def edad_display(self, obj):
        """Muestra la edad"""
        return f"{obj.edad} años"

    edad_display.short_description = "Edad"

    def activo_badge(self, obj):
        """Badge visual para el estado activo"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ Activo</span>',
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✗ Inactivo</span>',
        )

    activo_badge.short_description = "Estado"

    def get_queryset(self, request):
        """Muestra todos los pacientes (activos e inactivos)"""
        qs = super().get_queryset(request)
        return qs

    actions = ["activar_pacientes", "desactivar_pacientes"]

    @admin.action(description="✓ Activar pacientes seleccionados")
    def activar_pacientes(self, request, queryset):
        """Activar pacientes"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} paciente(s) activado(s) exitosamente.")

    @admin.action(description="✗ Desactivar pacientes seleccionados")
    def desactivar_pacientes(self, request, queryset):
        """Desactivar pacientes"""
        updated = queryset.update(activo=False)
        self.message_user(
            request, f"{updated} paciente(s) desactivado(s) exitosamente.",
        )
