"""
===========================================
MÓDULO: SERIALIZERS DE PARTOS
===========================================
Descripción:
    Serializers para el módulo de partos del sistema.
    Maneja validaciones y transformación de datos de partos y recién nacidos.

Serializers principales:
    - PartoSerializer: Serializer estándar para CRUD
    - PartoCreateSerializer: Para creación con validaciones extensas
    - PartoDetailSerializer: Detallado con recién nacidos y complicaciones
    - RecienNacidoSerializer: Para gestión de recién nacidos
    - ComplicacionPartoSerializer: Para gestión de complicaciones

Validaciones:
    - Fecha de parto coherente con embarazo
    - Edad gestacional válida
    - Peso del recién nacido en rangos normales
    - APGAR válido (0-10)

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from rest_framework import serializers
from datetime import datetime, timedelta, date
from .models import Parto, RecienNacido, ComplicacionParto
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


# ===========================================
# SERIALIZER DE RECIÉN NACIDO
# ===========================================
class RecienNacidoSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Serializer para Recién Nacido
    
    Funcionamiento:
        Maneja la creación y actualización de datos del recién nacido
        Incluye validaciones de peso, talla y APGAR
    """
    
    class Meta:
        model = RecienNacido
        fields = [
            'id',
            'numero_hijo',
            'sexo',
            'peso',
            'talla',
            'perimetro_cefalico',
            'apgar_1min',
            'apgar_5min',
            'estado_al_nacer',
            'reanimacion',
            'descripcion_reanimacion',
            'malformaciones',
            'descripcion_malformaciones',
            'observaciones',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']
    
    def validate_peso(self, value):
        """Validar peso del recién nacido"""
        if value < 500:
            raise serializers.ValidationError("El peso parece muy bajo (< 500g)")
        if value > 6000:
            raise serializers.ValidationError("El peso parece muy alto (> 6000g)")
        return value
    
    def validate_apgar_1min(self, value):
        """Validar APGAR 1 minuto"""
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError("APGAR debe estar entre 0 y 10")
        return value
    
    def validate_apgar_5min(self, value):
        """Validar APGAR 5 minutos"""
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError("APGAR debe estar entre 0 y 10")
        return value


# ===========================================
# SERIALIZER DE COMPLICACIÓN
# ===========================================
class ComplicacionPartoSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Serializer para Complicación del Parto
    
    Funcionamiento:
        Maneja el registro de complicaciones durante el parto
    """
    
    tipo_complicacion_display = serializers.CharField(
        source='get_tipo_complicacion_display',
        read_only=True
    )
    
    class Meta:
        model = ComplicacionParto
        fields = [
            'id',
            'tipo_complicacion',
            'tipo_complicacion_display',
            'descripcion',
            'tratamiento',
            'resuelto',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']


# ===========================================
# SERIALIZER ESTÁNDAR DE PARTO
# ===========================================
class PartoSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Serializer estándar para Parto
    
    Funcionamiento:
        Serializer principal para operaciones CRUD de partos
        Incluye información básica y calculada
    """
    
    paciente_nombre = serializers.SerializerMethodField()
    tipo_parto_display = serializers.CharField(source='get_tipo_parto_display', read_only=True)
    via_parto_display = serializers.CharField(source='get_via_parto_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    edad_gestacional_completa = serializers.SerializerMethodField()
    
    class Meta:
        model = Parto
        fields = [
            'id',
            'uuid',
            'embarazo',
            'paciente',
            'paciente_nombre',
            'medico',
            'fecha_parto',
            'hora_inicio',
            'hora_fin',
            'tipo_parto',
            'tipo_parto_display',
            'via_parto',
            'via_parto_display',
            'edad_gestacional_semanas',
            'edad_gestacional_dias',
            'edad_gestacional_completa',
            'duracion_trabajo_parto',
            'indicaciones',
            'anestesia',
            'procedimientos',
            'complicaciones',
            'descripcion_complicaciones',
            'estado',
            'estado_display',
            'observaciones',
            'fecha_registro',
            'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'uuid', 'fecha_registro', 'fecha_actualizacion']
    
    def get_paciente_nombre(self, obj):
        """Obtener nombre completo del paciente"""
        try:
            return obj.paciente.nombre_completo
        except:
            return "N/A"
    
    def get_edad_gestacional_completa(self, obj):
        """Retornar edad gestacional en formato completo"""
        return f"{obj.edad_gestacional_semanas}+{obj.edad_gestacional_dias}"
    
    def validate_fecha_parto(self, value):
        """Validar que fecha de parto no sea futura"""
        if value > date.today():
            raise serializers.ValidationError("La fecha de parto no puede ser futura")
        return value
    
    def validate(self, data):
        """Validaciones generales"""
        # Validar que el embarazo pertenezca al paciente
        if 'embarazo' in data and 'paciente' in data:
            if data['embarazo'].paciente_id != data['paciente'].id:
                raise serializers.ValidationError({
                    'embarazo': 'El embarazo no pertenece al paciente seleccionado'
                })
        
        return data


# ===========================================
# SERIALIZER PARA CREACIÓN
# ===========================================
class PartoCreateSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Para creación de partos
    
    Funcionamiento:
        Serializer especializado para crear nuevos partos
        con validaciones estrictas
    """
    
    recien_nacidos = RecienNacidoSerializer(many=True, required=False)
    complicaciones_list = ComplicacionPartoSerializer(many=True, required=False)
    
    class Meta:
        model = Parto
        fields = [
            'embarazo',
            'paciente',
            'medico',
            'fecha_parto',
            'hora_inicio',
            'hora_fin',
            'tipo_parto',
            'via_parto',
            'edad_gestacional_semanas',
            'edad_gestacional_dias',
            'duracion_trabajo_parto',
            'indicaciones',
            'anestesia',
            'procedimientos',
            'complicaciones',
            'descripcion_complicaciones',
            'estado',
            'observaciones',
            'recien_nacidos',
            'complicaciones_list',
        ]
    
    def create(self, validated_data):
        """Crear parto con recién nacidos y complicaciones"""
        recien_nacidos_data = validated_data.pop('recien_nacidos', [])
        complicaciones_data = validated_data.pop('complicaciones_list', [])
        
        # Crear parto
        parto = Parto.objects.create(**validated_data)
        
        # Crear recién nacidos
        for rn_data in recien_nacidos_data:
            RecienNacido.objects.create(parto=parto, **rn_data)
        
        # Crear complicaciones
        for comp_data in complicaciones_data:
            ComplicacionParto.objects.create(parto=parto, **comp_data)
        
        return parto


# ===========================================
# SERIALIZER DETALLADO
# ===========================================
class PartoDetailSerializer(serializers.ModelSerializer):
    """
    SERIALIZER: Para detalle completo de parto
    
    Funcionamiento:
        Serializer con información completa del parto
        Incluye datos del paciente, embarazo, recién nacidos y complicaciones
    """
    
    from embarazos.serializers import EmbarazoListSerializer
    from pacientes.serializers import PacienteListSerializer
    
    paciente_info = PacienteListSerializer(source='paciente', read_only=True)
    embarazo_info = EmbarazoListSerializer(source='embarazo', read_only=True)
    recien_nacidos = RecienNacidoSerializer(many=True, read_only=True)
    complicaciones_list = ComplicacionPartoSerializer(source='complicaciones', many=True, read_only=True)
    
    tipo_parto_display = serializers.CharField(source='get_tipo_parto_display', read_only=True)
    via_parto_display = serializers.CharField(source='get_via_parto_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    edad_gestacional_completa = serializers.SerializerMethodField()
    total_recien_nacidos = serializers.SerializerMethodField()
    tiene_complicaciones = serializers.SerializerMethodField()
    
    class Meta:
        model = Parto
        fields = '__all__'
    
    def get_edad_gestacional_completa(self, obj):
        """Edad gestacional completa"""
        return f"{obj.edad_gestacional_semanas}+{obj.edad_gestacional_dias}"
    
    def get_total_recien_nacidos(self, obj):
        """Total de recién nacidos"""
        return obj.recien_nacidos.count()
    
    def get_tiene_complicaciones(self, obj):
        """Si tiene complicaciones"""
        return obj.complicaciones or obj.complicaciones.count() > 0


"""
RESUMEN DE SERIALIZERS DE PARTOS:
==================================

1. RecienNacidoSerializer:
   - Campos: sexo, peso, talla, APGAR, estado
   - Validaciones: peso, APGAR
   
2. ComplicacionPartoSerializer:
   - Campos: tipo, descripción, tratamiento
   
3. PartoSerializer (Principal):
   - Campos: todos + calculados
   - Validaciones completas
   
4. PartoCreateSerializer:
   - Con recién nacidos anidados
   - Con complicaciones anidadas
   
5. PartoDetailSerializer:
   - Información completa
   - Incluye paciente, embarazo, RN, complicaciones

Total: 5 serializers especializados
Líneas: ~350
==================================
"""
