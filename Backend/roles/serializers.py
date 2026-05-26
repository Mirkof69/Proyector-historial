"""Roles Serializers"""

from rest_framework import serializers

from .models import CatRol


class CatRolSerializer(serializers.ModelSerializer):
    """Serializer for CatRol model"""

    nombre_display = serializers.CharField(source="get_nombre_display", read_only=True)
    permisos_count = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = CatRol
        fields = "__all__"
        read_only_fields = ("fecha_creacion", "fecha_modificacion")

    def get_permisos_count(self, obj):
        """Count permissions"""
        if obj.permisos:
            return len(obj.permisos)
        return 0


class CatRolListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing"""

    nombre_display = serializers.CharField(source="get_nombre_display", read_only=True)

    class Meta:
        """Meta"""
        model = CatRol
        fields = ["id", "nombre", "nombre_display", "descripcion", "activo"]
        read_only_fields = fields


class CatRolDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with permissions"""

    nombre_display = serializers.CharField(source="get_nombre_display", read_only=True)
    permisos_formatted = serializers.SerializerMethodField()
    usuarios_count = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = CatRol
        fields = "__all__"

    def get_permisos_formatted(self, obj):
        """Format permissions for display"""
        if obj.permisos:
            return {"total": len(obj.permisos), "permisos": obj.permisos}
        return {"total": 0, "permisos": {}}

    def get_usuarios_count(self, obj):
        """Count users with this role"""
        # This assumes Usuario model has a 'rol' field
        try:
            return obj.usuario_set.count()
        except Exception:
            return 0


class CatRolCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating roles"""

    class Meta:
        """Meta"""
        model = CatRol
        fields = ["nombre", "descripcion", "permisos", "activo"]

    def validate_nombre(self, value):
        """Validate role name is from allowed choices"""
        allowed_roles = dict(CatRol.ROLES).keys()
        if value not in allowed_roles:
            raise serializers.ValidationError(
                f"Rol no válido. Permitidos: {', '.join(allowed_roles)}",
            )
        return value

    def validate_permisos(self, value):
        """Validate permissions structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Los permisos deben ser un objeto JSON")
        return value
