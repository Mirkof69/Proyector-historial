"""
===========================================
MÓDULO: ADMIN DE PACIENTES
===========================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from datetime import date
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Admin completo para Pacientes"""

    # Lista de campos a mostrar
    list_display = [
        'id_clinico_badge',
        'nombre_completo_display',
        'ci_display',
        'edad_display',
        'genero_badge',
        'grupo_sanguineo_badge',
        'estado_civil_display',
        'activo_badge',
        'fecha_registro_display',
    ]

    list_filter = [
        'genero',
        'activo',
        'grupo_sanguineo',
        'estado_civil',
        'ciudad',
        'fecha_registro',
    ]

    search_fields = [
        'id_clinico',
        'nombre',
        'apellido_paterno',
        'apellido_materno',
        'cedula_identidad',
        'telefono_principal',
        'email',
    ]

    readonly_fields = [
        'uuid',
        'fecha_registro',
        'fecha_ultima_actualizacion',
        'edad_display',
    ]

    ordering = ['-fecha_registro']
    list_per_page = 25

    fieldsets = (
        ('Identificación', {
            'fields': (
                'uuid',
                'id_clinico',
                'cedula_identidad',
            )
        }),
        ('Datos Personales', {
            'fields': (
                'nombre',
                'apellido_paterno',
                'apellido_materno',
                'fecha_nacimiento',
                'edad_display',
                'genero',
                'estado_civil',
            )
        }),
        ('Datos Clínicos', {
            'fields': (
                'grupo_sanguineo',
            )
        }),
        ('Contacto', {
            'fields': (
                'telefono_principal',
                'telefono_alternativo',
                'email',
                'direccion',
                'ciudad',
            )
        }),
        ('Contacto de Emergencia', {
            'fields': (
                'contacto_emergencia_nombre',
                'contacto_emergencia_telefono',
                'contacto_emergencia_relacion',
            ),
            'classes': ('collapse',)
        }),
        ('Estado y Observaciones', {
            'fields': (
                'activo',
                'observaciones',
            )
        }),
        ('Auditoría', {
            'fields': (
                'fecha_registro',
                'fecha_ultima_actualizacion',
            ),
            'classes': ('collapse',)
        }),
    )

    # Métodos de visualización con badges
    def id_clinico_badge(self, obj):
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            obj.id_clinico
        )
    id_clinico_badge.short_description = 'ID Clínico'

    def nombre_completo_display(self, obj):
        return format_html('<strong>{}</strong>', obj.nombre_completo)
    nombre_completo_display.short_description = 'Nombre Completo'

    def ci_display(self, obj):
        return obj.cedula_identidad if obj.cedula_identidad else 'N/A'
    ci_display.short_description = 'CI'

    def edad_display(self, obj):
        edad = obj.edad
        if not edad:
            return 'N/A'
        
        if edad < 18:
            color = '#e67e22'  # Naranja
        elif edad > 35:
            color = '#9b59b6'  # Púrpura
        else:
            color = '#27ae60'  # Verde

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} años</span>',
            color, edad
        )
    edad_display.short_description = 'Edad'

    def genero_badge(self, obj):
        colores = {
            'femenino': '#e91e63',
            'masculino': '#3498db',
            'otro': '#95a5a6',
        }
        color = colores.get(obj.genero, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_genero_display()
        )
    genero_badge.short_description = 'Género'

    def grupo_sanguineo_badge(self, obj):
        if not obj.grupo_sanguineo:
            return 'N/A'

        if '-' in obj.grupo_sanguineo:
            color = '#e74c3c'  # Rojo para RH negativo
        else:
            color = '#27ae60'  # Verde para RH positivo

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.grupo_sanguineo
        )
    grupo_sanguineo_badge.short_description = 'Grupo Sanguíneo'

    def estado_civil_display(self, obj):
        return obj.get_estado_civil_display() if obj.estado_civil else 'N/A'
    estado_civil_display.short_description = 'Estado Civil'

    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">ACTIVO</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">INACTIVO</span>'
            )
    activo_badge.short_description = 'Estado'

    def fecha_registro_display(self, obj):
        return obj.fecha_registro.strftime('%d/%m/%Y')
    fecha_registro_display.short_description = 'Registro'

    # Acciones masivas
    def activar_pacientes(self, request, queryset):
        actualizados = queryset.update(activo=True)
        self.message_user(request, f'{actualizados} paciente(s) activado(s).')
    activar_pacientes.short_description = 'Activar pacientes seleccionados'

    def desactivar_pacientes(self, request, queryset):
        actualizados = queryset.update(activo=False)
        self.message_user(request, f'{actualizados} paciente(s) desactivado(s).')
    desactivar_pacientes.short_description = 'Desactivar pacientes seleccionados'

    actions = [
        'activar_pacientes',
        'desactivar_pacientes',
    ]
