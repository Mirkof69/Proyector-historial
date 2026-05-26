"""Serializers module."""
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import HorarioAtencion, Usuario

# ======================================================================================
# HORARIO SERIALIZERS
# ======================================================================================


class HorarioAtencionSerializer(serializers.ModelSerializer):
    """Serializer para horarios de atención"""

    dia_semana_display = serializers.CharField(
        source="get_dia_semana_display", read_only=True,
    )

    class Meta:
        """Meta"""
        model = HorarioAtencion
        fields = [
            "id",
            "usuario",
            "dia_semana",
            "dia_semana_display",
            "hora_inicio",
            "hora_fin",
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = ["id", "fecha_creacion", "fecha_modificacion"]

    def validate(self, attrs):
        """Validar que hora_fin sea mayor a hora_inicio"""
        if attrs.get("hora_inicio") and attrs.get("hora_fin"):
            if attrs["hora_inicio"] >= attrs["hora_fin"]:
                raise serializers.ValidationError(
                    {"hora_fin": "La hora de fin debe ser mayor a la hora de inicio"},
                )
        return attrs


# ======================================================================================
# PERMISOS SERIALIZERS
# ======================================================================================


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos de Django"""

    app_label = serializers.CharField(source="content_type.app_label", read_only=True)
    model = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        """Meta"""
        model = Permission
        fields = ["id", "name", "codename", "app_label", "model"]


# ======================================================================================
# USUARIO SERIALIZERS
# ======================================================================================


class UsuarioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""

    nombre_completo = serializers.ReadOnlyField()
    rol_display = serializers.CharField(source="get_rol_display", read_only=True)
    foto_url = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Usuario
        fields = [
            "id",
            "email",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "nombre_completo",
            "rol",
            "rol_display",
            "especialidad",
            "telefono",
            "foto",
            "foto_url",
            "activo",
            "is_staff",
            "is_superuser",
            "fecha_creacion",
        ]

    def get_foto_url(self, obj):
        """Obtener URL completa de la foto"""
        if obj.foto:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para ver un usuario"""

    nombre_completo = serializers.ReadOnlyField()
    iniciales = serializers.ReadOnlyField()
    rol_display = serializers.CharField(source="get_rol_display", read_only=True)
    foto_url = serializers.SerializerMethodField()
    horarios_atencion = HorarioAtencionSerializer(many=True, read_only=True)
    permisos = serializers.SerializerMethodField()
    grupos = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Usuario
        fields = [
            "id",
            "uuid",
            "email",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "nombre_completo",
            "iniciales",
            "rol",
            "rol_display",
            "especialidad",
            "telefono",
            "foto",
            "foto_url",
            "descripcion",
            "activo",
            "is_staff",
            "is_superuser",
            "horarios_atencion",
            "permisos",
            "grupos",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = ["id", "uuid", "fecha_creacion", "fecha_modificacion"]

    def get_foto_url(self, obj):
        """Obtener URL completa de la foto"""
        if obj.foto:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None

    def get_permisos(self, obj):
        """Obtener lista de permisos del usuario (directos + grupos)"""
        if obj.is_superuser:
            # Superusuarios tienen todos los permisos implícitamente
            # Retornamos una lista vacía o todos Para frontend es mejor retornar todos los codenames
            # o manejar is_superuser en frontend.
            # Como authService ya chequea is_superuser, podemos retornar los asignados o vacio.
            # Pero para consistencia con "Asignados", devolvemos la unión.
            pass

        # Obtener permisos directos y de grupos
        from django.db.models import Q

        permisos = Permission.objects.filter(
            Q(usuario=obj) | Q(group__usuario=obj),
        ).distinct()
        return PermissionSerializer(permisos, many=True).data

    def get_grupos(self, obj):
        """Obtener lista de grupos del usuario"""
        return [{"id": g.id, "name": g.name} for g in obj.groups.all()]


class UsuarioCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar usuarios"""

    password = serializers.CharField(
        write_only=True,
        required=False,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"},
    )
    permisos_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Lista de IDs de permisos a asignar",
    )
    grupos_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Lista de IDs de grupos a asignar",
    )

    class Meta:
        """Meta"""
        model = Usuario
        fields = [
            "id",
            "email",
            "password",
            "password_confirm",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "rol",
            "especialidad",
            "telefono",
            "foto",
            "descripcion",
            "activo",
            "is_staff",
            "is_superuser",
            "permisos_ids",
            "grupos_ids",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Validaciones personalizadas"""
        # Si se está creando un usuario, la contraseña es obligatoria
        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "La contraseña es obligatoria al crear un usuario"},
            )

        # Si se proporciona contraseña, validar confirmación
        if attrs.get("password"):
            if attrs.get("password") != attrs.get("password_confirm"):
                raise serializers.ValidationError(
                    {"password_confirm": "Las contraseñas no coinciden"},
                )

        return attrs

    def create(self, validated_data):
        """Crear usuario con contraseña encriptada y permisos"""
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        permisos_ids = validated_data.pop("permisos_ids", [])
        grupos_ids = validated_data.pop("grupos_ids", [])

        # Crear usuario
        usuario = Usuario.objects.create(**validated_data)
        usuario.set_password(password)
        usuario.save()

        # Asignar permisos
        if permisos_ids:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            usuario.user_permissions.set(permisos)

        # Asignar grupos
        if grupos_ids:

            grupos = Group.objects.filter(id__in=grupos_ids)
            usuario.groups.set(grupos)

        return usuario

    def update(self, instance, validated_data):
        """Actualizar usuario"""
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password", None)
        permisos_ids = validated_data.pop("permisos_ids", None)
        grupos_ids = validated_data.pop("grupos_ids", None)

        # Actualizar campos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Actualizar contraseña si se proporcionó
        if password:
            instance.set_password(password)

        instance.save()

        # Actualizar permisos si se proporcionaron
        if permisos_ids is not None:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            instance.user_permissions.set(permisos)

        # Actualizar grupos si se proporcionaron
        if grupos_ids is not None:

            grupos = Group.objects.filter(id__in=grupos_ids)
            instance.groups.set(grupos)

        return instance


# ======================================================================================
# AUTH SERIALIZERS
# ======================================================================================


class LoginSerializer(serializers.Serializer):
    """Serializer para login — paso 1 (email + password)"""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"},
    )

    def create(self, validated_data):
        """Create"""
        raise NotImplementedError

    def update(self, instance, validated_data):
        """Update"""
        raise NotImplementedError


class MfaVerifySerializer(serializers.Serializer):
    """Serializer para verificación MFA — paso 2 (temp_token + totp_code)"""

    temp_token = serializers.CharField(
        required=True,
        help_text="Token temporal recibido en el paso 1 cuando mfa_required=true",
    )
    totp_code = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text="Código de 6 dígitos del autenticador TOTP",
    )

    def validate_totp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El código TOTP debe contener solo dígitos.")
        return value

    def create(self, validated_data):
        raise NotImplementedError

    def update(self, instance, validated_data):
        raise NotImplementedError


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""

    password_actual = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"},
    )
    password_nueva = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_nueva_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"},
    )

    def validate(self, attrs):
        """Validar que las contraseñas nuevas coincidan"""
        if attrs["password_nueva"] != attrs["password_nueva_confirm"]:
            raise serializers.ValidationError(
                {"password_nueva_confirm": "Las contraseñas no coinciden"},
            )
        return attrs

    def create(self, validated_data):
        """Create"""
        raise NotImplementedError

    def update(self, instance, validated_data):
        """Update"""
        raise NotImplementedError


class AdminChangePasswordSerializer(serializers.Serializer):
    """Serializer para que admin cambie contraseña de usuario"""

    password_nueva = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_nueva_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"},
    )

    def validate(self, attrs):
        """Validar que las contraseñas nuevas coincidan"""
        if attrs["password_nueva"] != attrs["password_nueva_confirm"]:
            raise serializers.ValidationError(
                {"password_nueva_confirm": "Las contraseñas no coinciden"},
            )
        return attrs

    def create(self, validated_data):
        """Create"""
        raise NotImplementedError

    def update(self, instance, validated_data):
        """Update"""
        raise NotImplementedError


# ======================================================================================
# ALIAS PARA COMPATIBILIDAD
# ======================================================================================

# Mantener compatibilidad con código existente que use UsuarioSerializer
UsuarioSerializer = UsuarioDetailSerializer
