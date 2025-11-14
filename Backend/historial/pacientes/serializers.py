"""
===========================================
SERIALIZERS - MÓDULO PACIENTES
Descripción: Serializers para gestión de pacientes
Incluye: Validaciones, serializers especializados
===========================================
"""

from rest_framework import serializers
from .models import Paciente
import re
from datetime import date


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer estándar para pacientes.

    Usado en operaciones de creación y actualización.
    Incluye todas las validaciones necesarias.
    """

    # Campo adicional para compatibilidad
    telefono = serializers.CharField(
        source='telefono_principal',
        required=False,
        allow_blank=True
    )

    # Campos calculados
    nombre_completo = serializers.ReadOnlyField()
    edad = serializers.ReadOnlyField()

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
            'estado_civil',
            'grupo_sanguineo',
            'cedula_identidad',
            'telefono_principal',
            'telefono',  # Campo alias
            'telefono_alternativo',
            'email',
            'direccion',
            'ciudad',
            'contacto_emergencia_nombre',
            'contacto_emergencia_telefono',
            'contacto_emergencia_relacion',
            'activo',
            'fecha_registro',
            'fecha_ultima_actualizacion',
            'observaciones',
        ]
        read_only_fields = ['uuid', 'fecha_registro', 'fecha_ultima_actualizacion', 'nombre_completo', 'edad']

    # ===========================================
    # VALIDACIONES DE CAMPOS INDIVIDUALES
    # ===========================================

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
        """Validar que el apellido materno solo contenga letras (opcional)"""
        if value and not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido materno solo puede contener letras.")
        return value.strip() if value else None

    def validate_id_clinico(self, value):
        """Validar formato de ID clínico: HC-001"""
        if not value:
            return value
        if not re.match(r'^HC-\d{3,}$', value):
            raise serializers.ValidationError("El ID Clínico debe tener el formato HC-001 (mínimo 3 dígitos).")
        return value

    def validate_cedula_identidad(self, value):
        """Validar que la CI solo contenga números y guiones, y no esté duplicada"""
        if value:
            # Validar formato
            if not re.match(r'^[0-9\-]+$', value):
                raise serializers.ValidationError(
                    "La Cédula de Identidad solo puede contener números y guiones."
                )

            # Validar duplicados en creación
            if not self.instance:
                if Paciente.objects.filter(cedula_identidad=value).exists():
                    raise serializers.ValidationError("Ya existe un paciente con esta Cédula de Identidad.")
            # Validar duplicados en actualización
            else:
                if Paciente.objects.filter(cedula_identidad=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("Ya existe un paciente con esta Cédula de Identidad.")
        return value

    def validate_telefono_principal(self, value):
        """Validar que el teléfono solo contenga caracteres válidos"""
        if value and not re.match(r'^[0-9\+\-\s\(\)]+$', value):
            raise serializers.ValidationError(
                "El teléfono solo puede contener números, espacios y los caracteres: + - ( )"
            )
        return value

    def validate_telefono_alternativo(self, value):
        """Validar teléfono alternativo"""
        if value and not re.match(r'^[0-9\+\-\s\(\)]+$', value):
            raise serializers.ValidationError(
                "El teléfono solo puede contener números, espacios y los caracteres: + - ( )"
            )
        return value

    def validate_email(self, value):
        """Validar formato de email"""
        if value:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise serializers.ValidationError("El formato del correo electrónico no es válido.")
        return value

    def validate_fecha_nacimiento(self, value):
        """Validar que la fecha de nacimiento sea válida"""
        if value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")

        # Calcular edad
        edad = date.today().year - value.year
        if edad > 120:
            raise serializers.ValidationError("La fecha de nacimiento parece incorrecta (edad mayor a 120 años).")

        return value

    # ===========================================
    # VALIDACIÓN GENERAL
    # ===========================================

    def validate(self, data):
        """Validaciones a nivel de objeto completo"""

        # Validar ID Clínico duplicado
        id_clinico = data.get('id_clinico')
        if id_clinico:
            if not self.instance:  # Creación
                if Paciente.objects.filter(id_clinico=id_clinico).exists():
                    raise serializers.ValidationError({
                        'id_clinico': "Ya existe un paciente con este ID Clínico."
                    })
            else:  # Actualización
                if Paciente.objects.filter(id_clinico=id_clinico).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError({
                        'id_clinico': "Ya existe un paciente con este ID Clínico."
                    })

        return data

    # ===========================================
    # MÉTODOS DE CREACIÓN Y ACTUALIZACIÓN
    # ===========================================

    def create(self, validated_data):
        """Crear nuevo paciente con manejo del campo 'telefono'"""
        # Mapear 'telefono' a 'telefono_principal' si existe
        if 'telefono' in validated_data and 'telefono_principal' not in validated_data:
            validated_data['telefono_principal'] = validated_data.pop('telefono')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Actualizar paciente con manejo del campo 'telefono'"""
        # Mapear 'telefono' a 'telefono_principal' si existe
        if 'telefono' in validated_data and 'telefono_principal' not in validated_data:
            validated_data['telefono_principal'] = validated_data.pop('telefono')
        return super().update(instance, validated_data)


class PacienteListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de pacientes.

    Optimizado para performance en listas grandes.
    Solo incluye campos esenciales.
    """

    nombre_completo = serializers.ReadOnlyField()
    edad = serializers.ReadOnlyField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'uuid',
            'id_clinico',
            'nombre_completo',
            'edad',
            'cedula_identidad',
            'telefono_principal',
            'genero',
            'grupo_sanguineo',
            'activo',
            'fecha_registro',
        ]


class PacienteDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para vista individual de paciente.

    Incluye campos calculados y relaciones.
    Usado en endpoints de detalle e historial completo.
    """

    nombre_completo = serializers.ReadOnlyField()
    edad = serializers.ReadOnlyField()

    # Estadísticas relacionadas
    total_embarazos = serializers.SerializerMethodField()
    embarazos_activos = serializers.SerializerMethodField()
    total_controles = serializers.SerializerMethodField()

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
            'estado_civil',
            'grupo_sanguineo',
            'cedula_identidad',
            'telefono_principal',
            'telefono_alternativo',
            'email',
            'direccion',
            'ciudad',
            'contacto_emergencia_nombre',
            'contacto_emergencia_telefono',
            'contacto_emergencia_relacion',
            'activo',
            'fecha_registro',
            'fecha_ultima_actualizacion',
            'observaciones',
            # Estadísticas
            'total_embarazos',
            'embarazos_activos',
            'total_controles',
        ]

    def get_total_embarazos(self, obj):
        """Retorna el total de embarazos del paciente"""
        try:
            return obj.embarazos.count()
        except:
            return 0

    def get_embarazos_activos(self, obj):
        """Retorna el número de embarazos activos"""
        try:
            return obj.embarazos.filter(estado='activo').count()
        except:
            return 0

    def get_total_controles(self, obj):
        """Retorna el total de controles prenatales"""
        try:
            return obj.controles.count()
        except:
            return 0
