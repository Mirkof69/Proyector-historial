from rest_framework import serializers
from .models import Embarazo
from pacientes.models import Paciente
from datetime import datetime, timedelta

class EmbarazoSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    semanas_gestacion = serializers.SerializerMethodField()
    
    class Meta:
        model = Embarazo
        fields = [
            'id',
            'uuid',
            'paciente',
            'paciente_nombre',
            'numero_gesta',
            'fecha_ultima_menstruacion',
            'fecha_probable_parto',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',
            'notas',
            'medico_responsable',
            'fecha_registro',
            'semanas_gestacion'
        ]
        read_only_fields = ['uuid', 'fecha_registro', 'semanas_gestacion']
    
    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        paciente = obj.paciente
        return f"{paciente.id_clinico} - {paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno or ''}"
    
    def get_semanas_gestacion(self, obj):
        """Calcular semanas de gestación"""
        if obj.fecha_ultima_menstruacion:
            hoy = datetime.now().date()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas}+{dias}"
        return None
    
    def validate_paciente(self, value):
        """Validar que el paciente exista"""
        if not Paciente.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("El paciente seleccionado no existe")
        return value
    
    def validate_numero_gesta(self, value):
        """Validar número de gesta"""
        if value < 1:
            raise serializers.ValidationError("El número de gesta debe ser mayor a 0")
        if value > 20:
            raise serializers.ValidationError("El número de gesta parece incorrecto (máximo 20)")
        return value
    
    def validate_fecha_ultima_menstruacion(self, value):
        """Validar FUM - SIN RESTRICCIONES DE FECHA"""
        if not value:
            raise serializers.ValidationError("La Fecha de Última Menstruación es obligatoria")
        
        # Solo validar que no sea fecha futura
        if value > datetime.now().date():
            raise serializers.ValidationError("La FUM no puede ser una fecha futura")
        
        # QUITÉ LA VALIDACIÓN DE 42 SEMANAS - AHORA ACEPTA CUALQUIER FECHA PASADA
        
        return value
    
    def validate(self, data):
        """Validaciones generales"""
        # Calcular FPP automáticamente si no viene
        if 'fecha_ultima_menstruacion' in data and not data.get('fecha_probable_parto'):
            fum = data['fecha_ultima_menstruacion']
            data['fecha_probable_parto'] = fum + timedelta(days=280)
        
        # Validar que no haya embarazo activo duplicado para la misma paciente
        paciente = data.get('paciente')
        if paciente and not self.instance:  # Solo en creación
            embarazos_activos = Embarazo.objects.filter(
                paciente=paciente,
                estado='activo'
            )
            if embarazos_activos.exists():
                raise serializers.ValidationError({
                    'paciente': 'Esta paciente ya tiene un embarazo activo registrado'
                })
        
        return data
    
    def create(self, validated_data):
        """Crear embarazo"""
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualizar embarazo"""
        # Recalcular FPP si se actualiza FUM y no se envía FPP
        if 'fecha_ultima_menstruacion' in validated_data and 'fecha_probable_parto' not in validated_data:
            validated_data['fecha_probable_parto'] = validated_data['fecha_ultima_menstruacion'] + timedelta(days=280)
        
        return super().update(instance, validated_data)