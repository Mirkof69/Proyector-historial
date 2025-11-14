from rest_framework import serializers
from .models import Disponibilidad, Cita, HistorialCita
from pacientes.models import Paciente
from usuarios.models import Usuario
from datetime import datetime, time, timedelta
from django.utils import timezone


class DisponibilidadSerializer(serializers.ModelSerializer):
    """Serializer para Disponibilidades"""
    
    medico_nombre = serializers.SerializerMethodField()
    dia_nombre = serializers.CharField(source='get_dia_semana_display', read_only=True)
    horas_disponibles = serializers.ReadOnlyField()
    total_slots = serializers.ReadOnlyField()
    horario_formateado = serializers.SerializerMethodField()
    
    class Meta:
        model = Disponibilidad
        fields = [
            'id',
            'medico',
            'medico_nombre',
            'dia_semana',
            'dia_nombre',
            'hora_inicio',
            'hora_fin',
            'horario_formateado',
            'duracion_cita',
            'activo',
            'fecha_inicio_vigencia',
            'fecha_fin_vigencia',
            'observaciones',
            'horas_disponibles',
            'total_slots',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_medico_nombre(self, obj):
        return f"Dr(a). {obj.medico.nombre} {obj.medico.apellido_paterno}"
    
    def get_horario_formateado(self, obj):
        return f"{obj.hora_inicio.strftime('%H:%M')} - {obj.hora_fin.strftime('%H:%M')}"
    
    def validate(self, data):
        """Validaciones"""
        
        # Validar que el usuario sea médico
        if data.get('medico'):
            if data['medico'].rol != 'medico':
                raise serializers.ValidationError({
                    'medico': 'El usuario debe tener rol de médico'
                })
        
        # Validar horarios
        if data.get('hora_inicio') and data.get('hora_fin'):
            if data['hora_inicio'] >= data['hora_fin']:
                raise serializers.ValidationError({
                    'hora_fin': 'La hora de fin debe ser mayor que la hora de inicio'
                })
        
        # Validar fechas de vigencia
        if data.get('fecha_inicio_vigencia') and data.get('fecha_fin_vigencia'):
            if data['fecha_inicio_vigencia'] > data['fecha_fin_vigencia']:
                raise serializers.ValidationError({
                    'fecha_fin_vigencia': 'La fecha fin debe ser mayor que la fecha inicio'
                })
        
        return data


class HistorialCitaSerializer(serializers.ModelSerializer):
    """Serializer para Historial de Citas"""
    
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True)
    estado_nuevo_display = serializers.CharField(source='get_estado_nuevo_display', read_only=True)
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = HistorialCita
        fields = [
            'id',
            'cita',
            'estado_anterior',
            'estado_anterior_display',
            'estado_nuevo',
            'estado_nuevo_display',
            'motivo_cambio',
            'usuario',
            'usuario_nombre',
            'fecha_cambio',
        ]
    
    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido_paterno}"
        return "Sistema"


class CitaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de citas"""
    
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True)
    paciente_id_clinico = serializers.CharField(source='paciente.id_clinico', read_only=True)
    medico_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_cita_display = serializers.CharField(source='get_tipo_cita_display', read_only=True)
    fecha_hora_formateada = serializers.SerializerMethodField()
    dias_hasta_cita = serializers.ReadOnlyField()
    esta_pendiente = serializers.ReadOnlyField()
    
    class Meta:
        model = Cita
        fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'paciente_id_clinico',
            'medico',
            'medico_nombre',
            'fecha_cita',
            'hora_cita',
            'fecha_hora_formateada',
            'duracion',
            'tipo_cita',
            'tipo_cita_display',
            'estado',
            'estado_display',
            'dias_hasta_cita',
            'esta_pendiente',
        ]
    
    def get_medico_nombre(self, obj):
        return f"Dr(a). {obj.medico.nombre} {obj.medico.apellido_paterno}"
    
    def get_fecha_hora_formateada(self, obj):
        return f"{obj.fecha_cita.strftime('%d/%m/%Y')} {obj.hora_cita.strftime('%H:%M')}"


class CitaDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para citas"""
    
    paciente_info = serializers.SerializerMethodField()
    medico_info = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_cita_display = serializers.CharField(source='get_tipo_cita_display', read_only=True)
    confirmada_por_nombre = serializers.SerializerMethodField()
    creado_por_nombre = serializers.SerializerMethodField()
    historial = HistorialCitaSerializer(many=True, read_only=True)
    
    # Properties del modelo
    fecha_hora_cita = serializers.ReadOnlyField()
    esta_pendiente = serializers.ReadOnlyField()
    dias_hasta_cita = serializers.ReadOnlyField()
    requiere_recordatorio = serializers.ReadOnlyField()
    
    class Meta:
        model = Cita
        fields = [
            'id',
            'paciente',
            'paciente_info',
            'medico',
            'medico_info',
            'fecha_cita',
            'hora_cita',
            'fecha_hora_cita',
            'duracion',
            'tipo_cita',
            'tipo_cita_display',
            'estado',
            'estado_display',
            'motivo',
            'observaciones',
            'confirmada_por',
            'confirmada_por_nombre',
            'fecha_confirmacion',
            'recordatorio_enviado',
            'fecha_recordatorio',
            'creado_por',
            'creado_por_nombre',
            'fecha_creacion',
            'fecha_actualizacion',
            'esta_pendiente',
            'dias_hasta_cita',
            'requiere_recordatorio',
            'historial',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_paciente_info(self, obj):
        return {
            'id': obj.paciente.id,
            'nombre_completo': obj.paciente.nombre_completo,
            'id_clinico': obj.paciente.id_clinico,
            'telefono': obj.paciente.telefono,
            'email': obj.paciente.email,
            'edad': obj.paciente.edad,
        }
    
    def get_medico_info(self, obj):
        return {
            'id': obj.medico.id,
            'nombre': f"Dr(a). {obj.medico.nombre} {obj.medico.apellido_paterno}",
            'especialidad': obj.medico.especialidad,
            'email': obj.medico.email,
        }
    
    def get_confirmada_por_nombre(self, obj):
        if obj.confirmada_por:
            return f"{obj.confirmada_por.nombre} {obj.confirmada_por.apellido_paterno}"
        return None
    
    def get_creado_por_nombre(self, obj):
        if obj.creado_por:
            return f"{obj.creado_por.nombre} {obj.creado_por.apellido_paterno}"
        return None


class CitaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar citas"""
    
    class Meta:
        model = Cita
        fields = [
            'id',
            'paciente',
            'medico',
            'fecha_cita',
            'hora_cita',
            'duracion',
            'tipo_cita',
            'estado',
            'motivo',
            'observaciones',
            'creado_por',
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validaciones completas"""
        
        # Validar que el médico sea médico
        if data.get('medico'):
            if data['medico'].rol != 'medico':
                raise serializers.ValidationError({
                    'medico': 'El usuario debe tener rol de médico'
                })
        
        # No permitir citas en el pasado
        if data.get('fecha_cita') and data.get('hora_cita'):
            fecha_hora_cita = timezone.make_aware(
                datetime.combine(data['fecha_cita'], data['hora_cita'])
            )
            if fecha_hora_cita < timezone.now():
                raise serializers.ValidationError({
                    'fecha_cita': 'No se pueden agendar citas en el pasado'
                })
        
        # Validar que no exista otra cita en el mismo horario para el médico
        if data.get('medico') and data.get('fecha_cita') and data.get('hora_cita'):
            citas_existentes = Cita.objects.filter(
                medico=data['medico'],
                fecha_cita=data['fecha_cita'],
                hora_cita=data['hora_cita'],
                estado__in=['agendada', 'confirmada']
            )
            
            # Excluir la cita actual si estamos actualizando
            if self.instance:
                citas_existentes = citas_existentes.exclude(pk=self.instance.pk)
            
            if citas_existentes.exists():
                raise serializers.ValidationError({
                    'hora_cita': 'El médico ya tiene una cita agendada en este horario'
                })
        
        # Validar que el horario esté dentro de la disponibilidad del médico
        if data.get('medico') and data.get('fecha_cita') and data.get('hora_cita'):
            dia_semana = data['fecha_cita'].weekday()
            
            disponibilidad = Disponibilidad.objects.filter(
                medico=data['medico'],
                dia_semana=dia_semana,
                activo=True,
                hora_inicio__lte=data['hora_cita'],
                hora_fin__gt=data['hora_cita']
            )
            
            # Verificar vigencia si existe
            if disponibilidad.exists():
                disp = disponibilidad.first()
                if disp.fecha_inicio_vigencia and data['fecha_cita'] < disp.fecha_inicio_vigencia:
                    raise serializers.ValidationError({
                        'fecha_cita': 'La fecha está fuera de la vigencia de disponibilidad del médico'
                    })
                if disp.fecha_fin_vigencia and data['fecha_cita'] > disp.fecha_fin_vigencia:
                    raise serializers.ValidationError({
                        'fecha_cita': 'La fecha está fuera de la vigencia de disponibilidad del médico'
                    })
            else:
                raise serializers.ValidationError({
                    'hora_cita': 'El médico no tiene disponibilidad en este día y horario'
                })
        
        return data
    
    def create(self, validated_data):
        """Crear cita y registrar en historial"""
        cita = super().create(validated_data)
        
        # Crear entrada en historial
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior='',
            estado_nuevo=cita.estado,
            motivo_cambio='Cita creada',
            usuario=validated_data.get('creado_por')
        )
        
        return cita
    
    def update(self, instance, validated_data):
        """Actualizar cita y registrar cambio de estado en historial"""
        estado_anterior = instance.estado
        estado_nuevo = validated_data.get('estado', instance.estado)
        
        cita = super().update(instance, validated_data)
        
        # Si cambió el estado, registrar en historial
        if estado_anterior != estado_nuevo:
            HistorialCita.objects.create(
                cita=cita,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo,
                motivo_cambio='Cambio de estado',
                usuario=self.context.get('request').user if self.context.get('request') else None
            )
        
        return cita


class HorarioDisponibleSerializer(serializers.Serializer):
    """Serializer para mostrar horarios disponibles"""
    
    hora = serializers.TimeField()
    disponible = serializers.BooleanField()
    cita_id = serializers.IntegerField(required=False, allow_null=True)
    paciente_nombre = serializers.CharField(required=False, allow_null=True)


class AgendaMedicoSerializer(serializers.Serializer):
    """Serializer para la agenda del médico por día"""
    
    fecha = serializers.DateField()
    dia_semana = serializers.CharField()
    tiene_disponibilidad = serializers.BooleanField()
    horarios = HorarioDisponibleSerializer(many=True)
    total_citas = serializers.IntegerField()
    total_disponibles = serializers.IntegerField()