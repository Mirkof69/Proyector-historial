"""Admin registration for roles app"""

from django.contrib import admin

from .models import CatRol


@admin.register(CatRol)
class CatRolAdmin(admin.ModelAdmin):
    """Catroladmin"""
    list_display = ("nombre", "descripcion", "activo", "fecha_creacion")
    list_filter = ("nombre", "activo")
    search_fields = ("nombre", "descripcion")
    readonly_fields = ("fecha_creacion",)
