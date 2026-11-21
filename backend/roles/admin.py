"""Admin registration for roles app"""

from django.contrib import admin

from .models import Cargo


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rol_base", "activo", "fecha_modificacion")
    list_filter = ("rol_base", "activo")
    search_fields = ("nombre", "descripcion")
    readonly_fields = ("fecha_creacion", "fecha_modificacion")
