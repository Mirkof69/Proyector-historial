from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Administración de Usuarios del Sistema"""
    
    list_display = [
        'email',
        'nombre_completo',
        'rol_badge',
        'especialidad',
        'telefono',
        'activo_badge',
        'is_staff_badge',
        'is_superuser_badge',
    ]
    
    list_filter = ['rol', 'is_staff', 'is_superuser', 'activo', 'fecha_creacion']
    
    search_fields = ['email', 'nombre', 'apellido_paterno', 'apellido_materno']
    
    ordering = ['-fecha_creacion']
    
    readonly_fields = ['fecha_creacion', 'fecha_modificacion', 'last_login']
    
    fieldsets = (
        ('Información de Acceso', {
            'fields': ('email', 'password')
        }),
        ('Información Personal', {
            'fields': ('nombre', 'apellido_paterno', 'apellido_materno', 'telefono')
        }),
        ('Información Profesional', {
            'fields': ('rol', 'especialidad')
        }),
        ('Permisos y Estado', {
            'fields': ('activo', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Crear Nuevo Usuario', {
            'classes': ('wide',),
            'fields': (
                'email',
                'nombre',
                'apellido_paterno',
                'apellido_materno',
                'password1',
                'password2',
                'rol',
                'especialidad',
                'telefono',
                'activo',
                'is_staff',
                'is_superuser'
            ),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions')
    
    actions = ['activar_usuarios', 'desactivar_usuarios', 'hacer_staff']
    
    # Métodos personalizados para mejorar la visualización
    def nombre_completo(self, obj):
        return obj.get_full_name()
    nombre_completo.short_description = 'Nombre Completo'
    
    def rol_badge(self, obj):
        colors = {
            'medico': '#3498db',
            'enfermero': '#2ecc71',
            'administrador': '#e74c3c',
        }
        color = colors.get(obj.rol, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_rol_display()
        )
    rol_badge.short_description = 'Rol'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>'
        )
    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'
    
    def is_staff_badge(self, obj):
        if obj.is_staff:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    is_staff_badge.short_description = 'Staff'
    is_staff_badge.admin_order_field = 'is_staff'
    
    def is_superuser_badge(self, obj):
        if obj.is_superuser:
            return format_html('<span style="color: green; font-weight: bold;">✓ Admin</span>')
        return format_html('<span style="color: gray;">-</span>')
    is_superuser_badge.short_description = 'Superusuario'
    is_superuser_badge.admin_order_field = 'is_superuser'
    
    # Acciones personalizadas
    def activar_usuarios(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} usuarios activados correctamente.')
    activar_usuarios.short_description = 'Activar usuarios seleccionados'
    
    def desactivar_usuarios(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} usuarios desactivados correctamente.')
    desactivar_usuarios.short_description = 'Desactivar usuarios seleccionados'
    
    def hacer_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} usuarios ahora tienen acceso al admin.')
    hacer_staff.short_description = 'Dar acceso al admin (Staff)'