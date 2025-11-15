"""Admin para módulo de Partos"""
from django.contrib import admin
from .models import Parto, RecienNacido, ComplicacionParto

@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    list_display = ['id', 'paciente', 'fecha_parto', 'tipo_parto', 'via_parto', 'estado']
    list_filter = ['tipo_parto', 'via_parto', 'estado', 'complicaciones']
    search_fields = ['paciente__nombre', 'paciente__apellido_paterno']
    ordering = ['-fecha_parto']

@admin.register(RecienNacido)
class RecienNacidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'parto', 'numero_hijo', 'sexo', 'peso', 'apgar_5min', 'estado_al_nacer']
    list_filter = ['sexo', 'estado_al_nacer', 'reanimacion', 'malformaciones']

@admin.register(ComplicacionParto)
class ComplicacionPartoAdmin(admin.ModelAdmin):
    list_display = ['id', 'parto', 'tipo_complicacion', 'resuelto']
    list_filter = ['tipo_complicacion', 'resuelto']
