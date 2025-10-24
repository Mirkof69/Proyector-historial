from rest_framework import serializers
from .models import Paciente
import re

class PacienteSerializer(serializers.ModelSerializer):
    telefono = serializers.CharField(source='telefono_principal', required=False, allow_blank=True)
    
    class Meta:
        model = Paciente
        fields = [
            'id', 
            'uuid', 
            'id_clinico', 
            'nombre', 
            'apellido_paterno', 
            'apellido_materno',
            'fecha_nacimiento', 
            'genero', 
            'cedula_identidad', 
            'telefono_principal',
            'telefono',
            'email', 
            'direccion', 
            'activo', 
            'fecha_registro'
        ]
        read_only_fields = ['uuid', 'fecha_registro']
    
    def validate_nombre(self, value):
        """Validar que el nombre solo contenga letras y espacios"""
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El nombre solo puede contener letras.")
        return value.strip()
    
    def validate_apellido_paterno(self, value):
        """Validar que el apellido paterno solo contenga letras"""
        if not value:
            raise serializers.ValidationError("El apellido paterno es obligatorio.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido paterno solo puede contener letras.")
        return value.strip()
    
    def validate_apellido_materno(self, value):
        """Validar que el apellido materno solo contenga letras"""
        if value and not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido materno solo puede contener letras.")
        return value.strip() if value else None
    
    def validate_id_clinico(self, value):
        """Validar formato de ID clínico"""
        if not value:
            return value
        if not re.match(r'^HC-\d{3,}$', value):
            raise serializers.ValidationError("El ID Clínico debe tener el formato HC-001.")
        return value
    
    def validate_cedula_identidad(self, value):
        """Validar que la CI solo contenga números y guiones"""
        if value:
            if not re.match(r'^[0-9\-]+$', value):
                raise serializers.ValidationError("La Cédula de Identidad solo puede contener números y guiones.")
            # Validar duplicados en create
            if not self.instance:  # Solo en creación
                if Paciente.objects.filter(cedula_identidad=value).exists():
                    raise serializers.ValidationError("Cédula de Identidad duplicada")
            # Validar duplicados en update
            else:
                if Paciente.objects.filter(cedula_identidad=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("Cédula de Identidad duplicada")
        return value
    
    def validate_telefono_principal(self, value):
        """Validar que el teléfono solo contenga números"""
        if value and not re.match(r'^[0-9\+\-\s\(\)]+$', value):
            raise serializers.ValidationError("El teléfono solo puede contener números.")
        return value
    
    def validate_email(self, value):
        """Validar formato de email"""
        if value:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise serializers.ValidationError("El formato del correo electrónico no es válido.")
        return value
    
    def validate(self, data):
        """Validaciones generales"""
        # Validar ID Clínico duplicado
        id_clinico = data.get('id_clinico')
        if id_clinico:
            if not self.instance:  # Creación
                if Paciente.objects.filter(id_clinico=id_clinico).exists():
                    raise serializers.ValidationError({
                        'id_clinico': "ID Clínico duplicado"
                    })
            else:  # Actualización
                if Paciente.objects.filter(id_clinico=id_clinico).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError({
                        'id_clinico': "ID Clínico duplicado"
                    })
        
        return data
    
    def create(self, validated_data):
        if 'telefono' in validated_data and 'telefono_principal' not in validated_data:
            validated_data['telefono_principal'] = validated_data.pop('telefono')
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'telefono' in validated_data and 'telefono_principal' not in validated_data:
            validated_data['telefono_principal'] = validated_data.pop('telefono')
        return super().update(instance, validated_data)