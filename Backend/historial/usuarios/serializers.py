from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'uuid', 'email', 'nombre', 'apellido_paterno', 'apellido_materno', 'rol', 'especialidad', 'telefono', 'activo']
        read_only_fields = ['id', 'uuid']