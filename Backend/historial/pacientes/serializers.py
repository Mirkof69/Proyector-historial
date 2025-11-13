from rest_framework import serializers
from .models import Paciente
from django.core.validators import EmailValidator
import re

class PacienteSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Paciente"""
    
    # Campos calculados
    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    embarazos_activos = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'uuid',
            'id_clinico',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'fecha_nacimiento',
            'edad',
            'genero',
            'cedula_identidad',
            'telefono_principal',
            'email',
            'direccion',
            'activo',
            'fecha_registro',
            'embarazos_activos',
        ]
        read_only_fields = ['id', 'uuid', 'fecha_registro']
    
    def get_nombre_completo(self, obj):
        """Retorna nombre completo del paciente"""
        apellido_materno = f" {obj.apellido_materno}" if obj.apellido_materno else ""
        return f"{obj.nombre} {obj.apellido_paterno}{apellido_materno}"
    
    def get_edad(self, obj):
        """Calcula edad del paciente"""
        from datetime import date
        today = date.today()
        edad = today.year - obj.fecha_nacimiento.year
        if today.month < obj.fecha_nacimiento.month or \
           (today.month == obj.fecha_nacimiento.month and today.day < obj.fecha_nacimiento.day):
            edad -= 1
        return edad
    
    def get_embarazos_activos(self, obj):
        """Cuenta embarazos activos"""
        return obj.embarazos.filter(estado='activo').count()
    
    def validate_cedula_identidad(self, value):
        """Valida formato de cédula boliviana"""
        if value:
            # Remover espacios y guiones
            ci = re.sub(r'[\s\-]', '', value)
            # Validar que sean solo números
            if not ci.isdigit():
                raise serializers.ValidationError(
                    "La cédula debe contener solo números"
                )
            # Validar longitud (5-10 dígitos en Bolivia)
            if len(ci) < 5 or len(ci) > 10:
                raise serializers.ValidationError(
                    "La cédula debe tener entre 5 y 10 dígitos"
                )
        return value
    
    def validate_telefono_principal(self, value):
        """Valida formato de teléfono boliviano"""
        if value:
            # Remover espacios, guiones y paréntesis
            telefono = re.sub(r'[\s\-\(\)]', '', value)
            # Validar que sean solo números
            if not telefono.isdigit():
                raise serializers.ValidationError(
                    "El teléfono debe contener solo números"
                )
            # Validar longitud (7-8 dígitos)
            if len(telefono) < 7 or len(telefono) > 8:
                raise serializers.ValidationError(
                    "El teléfono debe tener 7 u 8 dígitos"
                )
        return value
    
    def validate_email(self, value):
        """Valida formato de email"""
        if value:
            validator = EmailValidator()
            validator(value)
        return value
    
    def validate(self, data):
        """Validaciones generales"""
        from datetime import date
        
        # Validar fecha de nacimiento no sea futura
        if 'fecha_nacimiento' in data:
            if data['fecha_nacimiento'] > date.today():
                raise serializers.ValidationError({
                    'fecha_nacimiento': 'La fecha de nacimiento no puede ser futura'
                })
            
            # Validar edad mínima (10 años) y máxima (100 años)
            edad = date.today().year - data['fecha_nacimiento'].year
            if edad < 10:
                raise serializers.ValidationError({
                    'fecha_nacimiento': 'El paciente debe tener al menos 10 años'
                })
            if edad > 100:
                raise serializers.ValidationError({
                    'fecha_nacimiento': 'Fecha de nacimiento inválida'
                })
        
        return data


class PacienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    nombre_completo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'uuid',
            'id_clinico',
            'nombre_completo',
            'edad',
            'genero',
            'telefono_principal',
            'activo',
        ]
    
    def get_nombre_completo(self, obj):
        apellido_materno = f" {obj.apellido_materno}" if obj.apellido_materno else ""
        return f"{obj.nombre} {obj.apellido_paterno}{apellido_materno}"
    
    def get_edad(self, obj):
        from datetime import date
        today = date.today()
        edad = today.year - obj.fecha_nacimiento.year
        if today.month < obj.fecha_nacimiento.month or \
           (today.month == obj.fecha_nacimiento.month and today.day < obj.fecha_nacimiento.day):
            edad -= 1
        return edad


class PacienteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar pacientes"""
    
    class Meta:
        model = Paciente
        fields = [
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'fecha_nacimiento',
            'genero',
            'cedula_identidad',
            'telefono_principal',
            'email',
            'direccion',
            'activo',
        ]