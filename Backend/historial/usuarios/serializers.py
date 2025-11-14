from rest_framework import serializers
from .models import Usuario
from django.contrib.auth.password_validation import validate_password

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer completo para Usuario"""
    nombre_completo = serializers.ReadOnlyField()
    iniciales = serializers.ReadOnlyField()
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'uuid',
            'email',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'iniciales',
            'rol',
            'especialidad',
            'telefono',
            'activo',
            'is_staff',
            'is_superuser',
            'fecha_creacion',
            'fecha_modificacion'
        ]
        read_only_fields = ['id', 'uuid', 'fecha_creacion', 'fecha_modificacion']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Crear usuario con contraseña encriptada"""
        password = validated_data.pop('password', None)
        usuario = Usuario.objects.create(**validated_data)
        
        if password:
            usuario.set_password(password)
            usuario.save()
        
        return usuario
    
    def update(self, instance, validated_data):
        """Actualizar usuario"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios con validación de contraseña"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = Usuario
        fields = [
            'email',
            'password',
            'password_confirm',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'rol',
            'especialidad',
            'telefono'
        ]
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs
    
    def create(self, validated_data):
        """Crear usuario con contraseña encriptada"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        usuario = Usuario.objects.create(**validated_data)
        usuario.set_password(password)
        usuario.save()
        
        return usuario


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    password_actual = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_nueva = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_nueva_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validar que las contraseñas nuevas coincidan"""
        if attrs['password_nueva'] != attrs['password_nueva_confirm']:
            raise serializers.ValidationError({
                'password_nueva_confirm': 'Las contraseñas no coinciden'
            })
        return attrs


class UsuarioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    nombre_completo = serializers.ReadOnlyField()
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'nombre_completo',
            'rol',
            'especialidad',
            'activo'
        ]