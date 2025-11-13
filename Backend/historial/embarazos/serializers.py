from rest_framework import serializers
from .models import Embarazo
from pacientes.models import Paciente
from datetime import datetime, timedelta, date


class EmbarazoSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Embarazo"""
    
    paciente_info = serializers.SerializerMethodField()
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    semanas_gestacion = serializers.SerializerMethodField()
    semanas_restantes = serializers.SerializerMethodField()
    
    class Meta:
        model = Embarazo
        fields = [
            'id',
            'uuid',
            'paciente',
            'paciente_info',
            'paciente_nombre',
            'numero_gesta',
            'fecha_ultima_menstruacion',
            'fecha_probable_parto',
            'edad_gestacional',
            'semanas_gestacion',
            'semanas_restantes',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',
            'notas',
            'medico_responsable',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'uuid', 'fecha_registro']
    
    def get_paciente_info(self, obj):
        """Información básica del paciente"""
        return {
            'id': obj.paciente.id,
            'id_clinico': obj.paciente.id_clinico,
            'nombre_completo': f"{obj.paciente.nombre} {obj.paciente.apellido_paterno}",
        }
    
    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        paciente = obj.paciente
        apellido_materno = f" {paciente.apellido_materno}" if paciente.apellido_materno else ""
        return f"{paciente.id_clinico} - {paciente.nombre} {paciente.apellido_paterno}{apellido_materno}"
    
    def get_edad_gestacional(self, obj):
        """Calcula edad gestacional actual"""
        if not obj.fecha_ultima_menstruacion:
            return None
        
        today = date.today()
        diferencia = (today - obj.fecha_ultima_menstruacion).days
        semanas = diferencia // 7
        dias = diferencia % 7
        
        return {
            'semanas': semanas,
            'dias': dias,
            'texto': f"{semanas} semanas + {dias} días"
        }
    
    def get_semanas_gestacion(self, obj):
        """Calcular semanas de gestación (formato corto)"""
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas}+{dias}"
        return None
    
    def get_semanas_restantes(self, obj):
        """Calcula semanas restantes hasta FPP"""
        if not obj.fecha_probable_parto:
            return None
        
        today = date.today()
        if today >= obj.fecha_probable_parto:
            return 0
        
        diferencia = (obj.fecha_probable_parto - today).days
        semanas = diferencia // 7
        
        return semanas
    
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
        if value > date.today():
            raise serializers.ValidationError("La FUM no puede ser una fecha futura")
        
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


class EmbarazoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    paciente_nombre = serializers.SerializerMethodField()
    semanas_gestacion = serializers.SerializerMethodField()
    
    class Meta:
        model = Embarazo
        fields = [
            'id',
            'uuid',
            'paciente_nombre',
            'numero_gesta',
            'semanas_gestacion',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',
            'fecha_registro',
        ]
    
    def get_paciente_nombre(self, obj):
        return f"{obj.paciente.id_clinico} - {obj.paciente.nombre} {obj.paciente.apellido_paterno}"
    
    def get_semanas_gestacion(self, obj):
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            diferencia = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = diferencia // 7
            dias = diferencia % 7
            return f"{semanas}+{dias}"
        return None


class EmbarazoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar embarazos"""
    
    class Meta:
        model = Embarazo
        fields = [
            'paciente',
            'numero_gesta',
            'fecha_ultima_menstruacion',
            'fecha_probable_parto',
            'tipo_embarazo',
            'riesgo_embarazo',
            'estado',
            'notas',
            'medico_responsable',
        ]