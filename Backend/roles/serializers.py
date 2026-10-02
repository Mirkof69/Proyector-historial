"""Serializadores de cargos."""
from rest_framework import serializers

from usuarios.permisos_por_rol import modulos_del_cargo, validar_cargo

from .models import Cargo


class CargoSerializer(serializers.ModelSerializer):
    rol_base_display = serializers.CharField(source="get_rol_base_display", read_only=True)
    nombres_modulos = serializers.ListField(child=serializers.CharField(), read_only=True)
    usuarios_count = serializers.SerializerMethodField()

    class Meta:
        model = Cargo
        fields = ["id", "nombre", "descripcion", "rol_base", "rol_base_display", "modulos", "nombres_modulos",
                  "activo", "usuarios_count", "fecha_creacion", "fecha_modificacion"]
        read_only_fields = ["fecha_creacion", "fecha_modificacion"]

    def get_usuarios_count(self, obj) -> int:
        n = getattr(obj, "n_usuarios", None)
        return n if n is not None else obj.usuarios.count()

    def validate(self, attrs):
        rol_base = attrs.get("rol_base", getattr(self.instance, "rol_base", None))
        modulos = attrs.get("modulos", getattr(self.instance, "modulos", []))
        errores = validar_cargo(rol_base, modulos)
        if errores:
            raise serializers.ValidationError(errores)
        attrs["modulos"] = modulos_del_cargo(rol_base, modulos)
        return attrs
