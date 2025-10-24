from django.contrib import admin
from .models import Embarazo

@admin.register(Embarazo)
class EmbarazoAdmin(admin.ModelAdmin):
    list_display = ['id', 'paciente', 'numero_gesta', 'fecha_ultima_menstruacion', 'tipo_embarazo', 'riesgo_embarazo', 'estado']
    list_filter = ['estado', 'riesgo_embarazo', 'tipo_embarazo']
    search_fields = ['paciente__nombre', 'paciente__apellido_paterno']