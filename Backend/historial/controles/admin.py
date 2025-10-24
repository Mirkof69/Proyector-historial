from django.contrib import admin
from .models import ControlPrenatal

@admin.register(ControlPrenatal)
class ControlPrenatalAdmin(admin.ModelAdmin):
    list_display = ['id', 'paciente', 'numero_control', 'fecha_control', 'semanas_gestacion', 'medico_id']
    list_filter = ['fecha_control']
    search_fields = ['paciente__nombre', 'paciente__apellido_paterno']