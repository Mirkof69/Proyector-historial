"""Admin module."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import HorarioAtencion, Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Administración de Usuarios del Sistema"""

    list_display = [
        "email",
        "nombre_completo",
        "rol_badge",
        "especialidad",
        "telefono",
        "activo_badge",
        "is_stafff_badge",
        "is_superuser_badge",
    ]

    list_filter = ["rol", "is_staff", "is_superuser", "activo", "fecha_creacion"]

    search_fields = ["email", "nombre", "apellido_paterno", "apellido_materno"]

    ordering = ["-fecha_creacion"]

    readonly_fields = ["fecha_creacion", "fecha_modificacion", "last_login"]

    fieldsets = (
        ("Información de Acceso", {"fields": ("email", "password")}),
        (
            "Información Personal",
            {
                "fields": (
                    "nombre",
                    "apellido_paterno",
                    "apellido_materno",
                    "telefono",
                    "foto",
                    "descripcion",
                ),
            },
        ),
        ("Información Profesional", {"fields": ("rol", "especialidad")}),
        (
            "Permisos y Estado",
            {
                "fields": (
                    "activo",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Fechas Importantes",
            {
                "fields": ("last_login", "fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            "Crear Nuevo Usuario",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nombre",
                    "apellido_paterno",
                    "apellido_materno",
                    "password1",
                    "password2",
                    "rol",
                    "especialidad",
                    "telefono",
                    "activo",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")

    actions = ["activar_usuarios", "desactivar_usuarios", "hacer_staf"]

    # Métodos personalizados para mejorar la visualización
    def nombre_completo(self, obj):
        """Nombre completo"""
        return obj.get_full_name()

    nombre_completo.short_description = "Nombre Completo"

    def rol_badge(self, obj):
        """Rol badge"""
        colors = {
            "medico": "#3498db",
            "enfermero": "#2ecc71",
            "administrador": "#e74c3c",
        }
        color = colors.get(obj.rol, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_rol_display(),
        )

    rol_badge.short_description = "Rol"

    def activo_badge(self, obj):
        """Activo badge"""
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>',
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>',
        )

    activo_badge.short_description = "Estado"
    activo_badge.admin_order_field = "activo"

    def is_stafff_badge(self, obj):
        """Is stafff badge"""
        if obj.is_stafff:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')

    is_stafff_badge.short_description = "Staf"
    is_stafff_badge.admin_order_field = "is_stafff"

    def is_superuser_badge(self, obj):
        """Is superuser badge"""
        if obj.is_superuser:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Admin</span>',
            )
        return format_html('<span style="color: gray;">-</span>')

    is_superuser_badge.short_description = "Superusuario"
    is_superuser_badge.admin_order_field = "is_superuser"

    # Acciones personalizadas
    def activar_usuarios(self, request, queryset):
        """Activar usuarios"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} usuarios activados correctamente.")

    activar_usuarios.short_description = "Activar usuarios seleccionados"

    def desactivar_usuarios(self, request, queryset):
        """Desactivar usuarios"""
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} usuarios desactivados correctamente.")

    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"

    def hacer_staff(self, request, queryset):
        """Hacer staff"""
        updated = queryset.update(is_stafff=True)
        self.message_user(request, f"{updated} usuarios ahora tienen acceso al admin.")

    hacer_staff.short_description = "Dar acceso al admin (Staff)"


@admin.register(HorarioAtencion)
class HorarioAtencionAdmin(admin.ModelAdmin):
    """Administración de Horarios de Atención"""

    list_display = [
        "usuario",
        "dia_semana_badge",
        "hora_inicio",
        "hora_fin",
        "activo_badge",
        "fecha_creacion",
    ]

    list_filter = ["dia_semana", "activo", "usuario__rol"]

    search_fields = ["usuario__nombre", "usuario__apellido_paterno", "usuario__email"]

    ordering = ["usuario", "dia_semana", "hora_inicio"]

    readonly_fields = ["fecha_creacion", "fecha_modificacion"]

    fieldsets = (
        (
            "Información del Horario",
            {"fields": ("usuario", "dia_semana", "hora_inicio", "hora_fin", "activo")},
        ),
        (
            "Metadata",
            {
                "fields": ("fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )

    # Métodos personalizados
    def dia_semana_badge(self, obj):
        """Dia semana badge"""
        colors = {
            "lunes": "#3498db",
            "martes": "#2ecc71",
            "miercoles": "#9b59b6",
            "jueves": "#f39c12",
            "viernes": "#e74c3c",
            "sabado": "#1abc9c",
            "domingo": "#95a5a6",
        }
        color = colors.get(obj.dia_semana, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_dia_semana_display(),
        )

    dia_semana_badge.short_description = "Día"

    def activo_badge(self, obj):
        """Activo badge"""
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>',
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>',
        )

    activo_badge.short_description = "Estado"

    actions = ["activar_horarios", "desactivar_horarios"]

    def activar_horarios(self, request, queryset):
        """Activar horarios"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} horarios activados correctamente.")

    activar_horarios.short_description = "Activar horarios seleccionados"

    def desactivar_horarios(self, request, queryset):
        """Desactivar horarios"""
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} horarios desactivados correctamente.")

    desactivar_horarios.short_description = "Desactivar horarios seleccionados"
