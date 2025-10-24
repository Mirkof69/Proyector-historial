from django.contrib import admin
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['id_clinico', 'nombre', 'apellido_paterno', 'cedula_identidad', 'fecha_nacimiento', 'activo']
    search_fields = ['id_clinico', 'nombre', 'apellido_paterno', 'cedula_identidad']
    list_filter = ['genero', 'activo']