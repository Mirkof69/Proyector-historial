from rest_framework import serializers
from .models import Ecografia, BiometriaFetal, AnatomiaFetal, AnexosFetales, ImagenEcografia
from embarazos.models import Embarazo
from pacientes.models import Paciente

class BiometriaFetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometriaFetal
        fields = [
            'id',
            'diametro_biparietal',
            'circunferencia_cefalica',
            'circunferencia_abdominal',
            'longitud_femur',
            'longitud_humero',
            'peso_fetal_estimado',
            'percentil_peso'
        ]


class AnatomiaFetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnatomiaFetal
        fields = [
            'id',
            'craneo_normal',
            'cerebro_normal',
            'cerebelo_normal',
            'perfil_facial_normal',
            'labios_normales',
            'corazon_normal',
            'pulmones_normales',
            'estomago_normal',
            'rinones_normales',
            'vejiga_normal',
            'columna_normal',
            'extremidades_superiores_normales',
            'extremidades_inferiores_normales',
            'hallazgos_anormales'
        ]


class AnexosFetalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnexosFetales
        fields = [
            'id',
            'placenta_localizacion',
            'placenta_grosor',
            'placenta_inserccion_cordon',
            'numero_vasos_cordon',
            'circular_cordon',
            'liquido_amniotico_normal',
            'polihidramnios',
            'oligohidramnios'
        ]


class ImagenEcografiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenEcografia
        fields = ['id', 'archivo', 'tipo_imagen', 'descripcion', 'fecha_subida']
        read_only_fields = ['fecha_subida']


class EcografiaSerializer(serializers.ModelSerializer):
    # Campos de solo lectura
    paciente_nombre = serializers.SerializerMethodField()
    medico_nombre = serializers.SerializerMethodField()
    edad_gestacional_completa = serializers.ReadOnlyField()
    
    # Relaciones anidadas
    biometria = BiometriaFetalSerializer(required=False, allow_null=True)
    anatomia = AnatomiaFetalSerializer(required=False, allow_null=True)
    anexos = AnexosFetalesSerializer(required=False, allow_null=True)
    imagenes = ImagenEcografiaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Ecografia
        fields = [
            'id',
            'embarazo',
            'paciente',
            'paciente_nombre',
            'medico',
            'medico_nombre',
            'fecha_ecografia',
            'tipo_ecografia',
            'indicacion',
            'edad_gestacional_semanas',
            'edad_gestacional_dias',
            'edad_gestacional_completa',
            'numero_fetos',
            'vitalidad_fetal',
            'frecuencia_cardiaca_fetal',
            'indice_liquido_amniotico',
            'bolsillo_maximo',
            'localizacion_placenta',
            'grado_madurez_placenta',
            'diagnostico',
            'observaciones',
            'biometria',
            'anatomia',
            'anexos',
            'imagenes',
            'fecha_registro',
            'fecha_modificacion'
        ]
        read_only_fields = ['fecha_registro', 'fecha_modificacion']
    
    def get_paciente_nombre(self, obj):
        if obj.paciente:
            return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno}"
        return None
    
    def get_medico_nombre(self, obj):
        if obj.medico:
            return f"{obj.medico.nombre} {obj.medico.apellido}"
        return None
    
    def create(self, validated_data):
        # Extraer datos anidados
        biometria_data = validated_data.pop('biometria', None)
        anatomia_data = validated_data.pop('anatomia', None)
        anexos_data = validated_data.pop('anexos', None)
        
        # Crear ecografía principal
        ecografia = Ecografia.objects.create(**validated_data)
        
        # Crear relaciones si existen
        if biometria_data:
            BiometriaFetal.objects.create(ecografia=ecografia, **biometria_data)
        
        if anatomia_data:
            AnatomiaFetal.objects.create(ecografia=ecografia, **anatomia_data)
        
        if anexos_data:
            AnexosFetales.objects.create(ecografia=ecografia, **anexos_data)
        
        return ecografia
    
    def update(self, instance, validated_data):
        # Extraer datos anidados
        biometria_data = validated_data.pop('biometria', None)
        anatomia_data = validated_data.pop('anatomia', None)
        anexos_data = validated_data.pop('anexos', None)
        
        # Actualizar ecografía principal
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar o crear biometría
        if biometria_data:
            BiometriaFetal.objects.update_or_create(
                ecografia=instance,
                defaults=biometria_data
            )
        
        # Actualizar o crear anatomía
        if anatomia_data:
            AnatomiaFetal.objects.update_or_create(
                ecografia=instance,
                defaults=anatomia_data
            )
        
        # Actualizar o crear anexos
        if anexos_data:
            AnexosFetales.objects.update_or_create(
                ecografia=instance,
                defaults=anexos_data
            )
        
        return instance
    
    def validate(self, data):
        # Validar que el embarazo esté activo
        if 'embarazo' in data:
            embarazo = data['embarazo']
            if embarazo.estado != 'activo':
                raise serializers.ValidationError({
                    'embarazo': 'Solo se pueden registrar ecografías en embarazos activos'
                })
        
        # Validar edad gestacional
        if 'edad_gestacional_semanas' in data:
            semanas = data['edad_gestacional_semanas']
            if semanas < 4 or semanas > 42:
                raise serializers.ValidationError({
                    'edad_gestacional_semanas': 'Las semanas deben estar entre 4 y 42'
                })
        
        return data


class EcografiaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    paciente_nombre = serializers.SerializerMethodField()
    edad_gestacional = serializers.SerializerMethodField()
    
    class Meta:
        model = Ecografia
        fields = [
            'id',
            'paciente_nombre',
            'fecha_ecografia',
            'tipo_ecografia',
            'edad_gestacional',
            'numero_fetos',
            'vitalidad_fetal',
            'diagnostico'
        ]
    
    def get_paciente_nombre(self, obj):
        if obj.paciente:
            return f"{obj.paciente.nombre} {obj.paciente.apellido_paterno}"
        return None
    
    def get_edad_gestacional(self, obj):
        return f"{obj.edad_gestacional_semanas}+{obj.edad_gestacional_dias}"