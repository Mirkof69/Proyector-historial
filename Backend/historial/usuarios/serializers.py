# =============================================================================
# SERIALIZERS DE USUARIOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: usuarios
# Descripción: Serializers completos para gestión de usuarios, autenticación,
#              perfiles, cambio de contraseña, recuperación, sesiones, etc.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 - EXTENDIDO
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from datetime import timedelta
import re

from .models import (
    Usuario,
    HistorialSesion,
    TokenRecuperacion,
    TokenVerificacionEmail
)


# =============================================================================
# SERIALIZERS BÁSICOS DE LECTURA
# =============================================================================

class UsuarioBasicoSerializer(serializers.ModelSerializer):
    """
    Serializer básico de usuario para listados y referencias.
    Solo información esencial.
    """
    nombre_completo = serializers.CharField(read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)

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
            'rol',
            'rol_display',
            'especialidad',
            'especialidad_display',
            'activo',
        ]
        read_only_fields = ['id', 'uuid']


class UsuarioListaSerializer(serializers.ModelSerializer):
    """
    Serializer para listado de usuarios.
    Más información que el básico pero menos que el completo.
    """
    nombre_completo = serializers.CharField(read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    edad = serializers.IntegerField(read_only=True)
    es_medico = serializers.BooleanField(read_only=True)
    es_personal_salud = serializers.BooleanField(read_only=True)

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
            'rol',
            'rol_display',
            'especialidad',
            'especialidad_display',
            'matricula_profesional',
            'telefono',
            'estado',
            'estado_display',
            'activo',
            'fecha_nacimiento',
            'edad',
            'es_medico',
            'es_personal_salud',
            'foto_perfil',
            'fecha_creacion',
            'ultimo_login',
        ]
        read_only_fields = ['id', 'uuid', 'fecha_creacion']


class UsuarioDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalle de usuario.
    Incluye toda la información excepto datos sensibles.
    """
    nombre_completo = serializers.CharField(read_only=True)
    nombre_completo_formateado = serializers.CharField(read_only=True)
    iniciales = serializers.CharField(read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    departamento_ci_display = serializers.CharField(source='get_departamento_ci_display', read_only=True)
    genero_display = serializers.CharField(source='get_genero_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    edad = serializers.IntegerField(read_only=True)
    es_medico = serializers.BooleanField(read_only=True)
    es_personal_salud = serializers.BooleanField(read_only=True)
    es_administrador = serializers.BooleanField(read_only=True)
    esta_bloqueado = serializers.BooleanField(read_only=True)
    dias_desde_ultimo_cambio_password = serializers.IntegerField(read_only=True)
    password_expirado = serializers.BooleanField(read_only=True)

    # Permisos
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            # Identificación
            'id',
            'uuid',
            'email',
            'email_verificado',

            # Datos Personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'nombre_completo_formateado',
            'iniciales',
            'fecha_nacimiento',
            'edad',
            'genero',
            'genero_display',

            # Identificación Oficial
            'cedula_identidad',
            'departamento_ci',
            'departamento_ci_display',

            # Contacto
            'telefono',
            'telefono_secundario',
            'direccion',
            'ciudad',

            # Profesional
            'rol',
            'rol_display',
            'especialidad',
            'especialidad_display',
            'matricula_profesional',
            'institucion',
            'cargo',
            'anos_experiencia',

            # Estado
            'estado',
            'estado_display',
            'activo',
            'esta_bloqueado',
            'razon_bloqueo',

            # Seguridad
            'requiere_cambio_password',
            'dias_desde_ultimo_cambio_password',
            'password_expirado',

            # Sesiones
            'ultimo_login',
            'ip_ultimo_login',

            # Preferencias
            'idioma',
            'zona_horaria',
            'notificaciones_email',
            'notificaciones_sms',

            # Media
            'foto_perfil',
            'firma_digital',

            # Propiedades computadas
            'es_medico',
            'es_personal_salud',
            'es_administrador',

            # Permisos
            'permisos',

            # Auditoría
            'fecha_creacion',
            'fecha_modificacion',
        ]
        read_only_fields = [
            'id', 'uuid', 'fecha_creacion', 'fecha_modificacion',
            'ultimo_login', 'ip_ultimo_login'
        ]

    def get_permisos(self, obj):
        """Retorna todos los permisos del usuario"""
        return {
            'puede_crear_pacientes': obj.puede_crear_pacientes,
            'puede_editar_pacientes': obj.puede_editar_pacientes,
            'puede_eliminar_pacientes': obj.puede_eliminar_pacientes,
            'puede_ver_historial_completo': obj.puede_ver_historial_completo,
            'puede_registrar_controles': obj.puede_registrar_controles,
            'puede_solicitar_laboratorios': obj.puede_solicitar_laboratorios,
            'puede_registrar_resultados_lab': obj.puede_registrar_resultados_lab,
            'puede_agendar_citas': obj.puede_agendar_citas,
            'puede_generar_reportes': obj.puede_generar_reportes,
            'es_superusuario': obj.es_superusuario,
        }


# =============================================================================
# SERIALIZERS DE CREACIÓN Y ACTUALIZACIÓN
# =============================================================================

class UsuarioCrearSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevos usuarios.
    Incluye validaciones de contraseña y confirmación.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Contraseña (mínimo 8 caracteres)"
    )
    password_confirmacion = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirmar contraseña"
    )

    class Meta:
        model = Usuario
        fields = [
            # Autenticación
            'email',
            'password',
            'password_confirmacion',

            # Datos Personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'fecha_nacimiento',
            'genero',

            # Identificación
            'cedula_identidad',
            'departamento_ci',

            # Contacto
            'telefono',
            'telefono_secundario',
            'direccion',
            'ciudad',

            # Profesional
            'rol',
            'especialidad',
            'matricula_profesional',
            'institucion',
            'cargo',
            'anos_experiencia',

            # Preferencias
            'idioma',
            'zona_horaria',
        ]

    def validate_email(self, value):
        """Validar que el email no exista"""
        if Usuario.objects.filter(email__iexact=value, eliminado=False).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value.lower()

    def validate_cedula_identidad(self, value):
        """Validar que la CI no exista"""
        if value and Usuario.objects.filter(cedula_identidad=value, eliminado=False).exists():
            raise serializers.ValidationError("Esta cédula de identidad ya está registrada")
        return value

    def validate_password(self, value):
        """Validar la contraseña con los validadores de Django"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        """Validaciones generales"""
        # Validar que las contraseñas coincidan
        if data['password'] != data['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden'
            })

        # Validar que médicos tengan especialidad
        if data['rol'] in ['medico', 'enfermero', 'doctor_laboratorio']:
            if not data.get('especialidad'):
                raise serializers.ValidationError({
                    'especialidad': f"Los usuarios con rol '{data['rol']}' deben tener especialidad"
                })

        # Validar que médicos tengan matrícula
        if data['rol'] in ['medico', 'doctor_laboratorio']:
            if not data.get('matricula_profesional'):
                raise serializers.ValidationError({
                    'matricula_profesional': "Los médicos deben tener matrícula profesional"
                })

        # Validar CI con departamento
        if data.get('cedula_identidad') and not data.get('departamento_ci'):
            raise serializers.ValidationError({
                'departamento_ci': "Debe especificar el departamento de expedición de CI"
            })

        return data

    def create(self, validated_data):
        """Crear usuario con contraseña hasheada"""
        # Remover campos extra
        validated_data.pop('password_confirmacion')
        password = validated_data.pop('password')

        # Crear usuario
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.estado = 'pendiente'  # Pendiente de activación
        usuario.save()

        # Generar token de verificación de email
        TokenVerificacionEmail.generar_token(usuario)

        return usuario


class UsuarioActualizarSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar datos de usuario.
    No permite cambiar email ni contraseña (endpoints separados).
    """

    class Meta:
        model = Usuario
        fields = [
            # Datos Personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'fecha_nacimiento',
            'genero',

            # Identificación
            'cedula_identidad',
            'departamento_ci',

            # Contacto
            'telefono',
            'telefono_secundario',
            'direccion',
            'ciudad',

            # Profesional (algunos campos)
            'especialidad',
            'institucion',
            'cargo',
            'anos_experiencia',

            # Preferencias
            'idioma',
            'zona_horaria',
            'notificaciones_email',
            'notificaciones_sms',

            # Media
            'foto_perfil',
            'firma_digital',
        ]

    def validate(self, data):
        """Validaciones de actualización"""
        instance = self.instance

        # Validar CI con departamento
        cedula = data.get('cedula_identidad', instance.cedula_identidad)
        departamento = data.get('departamento_ci', instance.departamento_ci)

        if cedula and not departamento:
            raise serializers.ValidationError({
                'departamento_ci': "Debe especificar el departamento de expedición de CI"
            })

        return data

    def update(self, instance, validated_data):
        """Actualizar usuario"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class UsuarioAdminActualizarSerializer(serializers.ModelSerializer):
    """
    Serializer para que administradores actualicen usuarios.
    Incluye campos adicionales como rol, permisos, estado.
    """

    class Meta:
        model = Usuario
        fields = [
            # Datos Personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'fecha_nacimiento',
            'genero',

            # Identificación
            'cedula_identidad',
            'departamento_ci',

            # Contacto
            'telefono',
            'telefono_secundario',
            'direccion',
            'ciudad',

            # Profesional
            'rol',
            'especialidad',
            'matricula_profesional',
            'institucion',
            'cargo',
            'anos_experiencia',

            # Estado
            'estado',
            'activo',

            # Permisos
            'puede_crear_pacientes',
            'puede_editar_pacientes',
            'puede_eliminar_pacientes',
            'puede_ver_historial_completo',
            'puede_registrar_controles',
            'puede_solicitar_laboratorios',
            'puede_registrar_resultados_lab',
            'puede_agendar_citas',
            'puede_generar_reportes',
            'es_superusuario',

            # Preferencias
            'idioma',
            'zona_horaria',

            # Notas
            'notas_internas',
        ]

    def validate(self, data):
        """Validaciones de administrador"""
        instance = self.instance

        # Validar rol con especialidad
        rol = data.get('rol', instance.rol)
        especialidad = data.get('especialidad', instance.especialidad)

        if rol in ['medico', 'enfermero', 'doctor_laboratorio'] and not especialidad:
            raise serializers.ValidationError({
                'especialidad': f"Los usuarios con rol '{rol}' deben tener especialidad"
            })

        return data


# =============================================================================
# SERIALIZERS DE AUTENTICACIÓN
# =============================================================================

class LoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuario.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    recordarme = serializers.BooleanField(default=False, required=False)

    def validate_email(self, value):
        """Normalizar email a minúsculas"""
        return value.lower()


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de login exitoso.
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    usuario = UsuarioDetalleSerializer()
    mensaje = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para logout.
    """
    refresh = serializers.CharField(required=True)


# =============================================================================
# SERIALIZERS DE CONTRASEÑA
# =============================================================================

class CambiarPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña (usuario autenticado).
    """
    password_actual = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_nuevo = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_confirmacion = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_password_actual(self, value):
        """Validar que la contraseña actual sea correcta"""
        usuario = self.context['request'].user
        if not usuario.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta")
        return value

    def validate_password_nuevo(self, value):
        """Validar la nueva contraseña"""
        try:
            validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        if data['password_nuevo'] != data['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden'
            })

        # Validar que la nueva contraseña sea diferente de la actual
        if data['password_actual'] == data['password_nuevo']:
            raise serializers.ValidationError({
                'password_nuevo': 'La nueva contraseña debe ser diferente de la actual'
            })

        return data

    def save(self):
        """Guardar la nueva contraseña"""
        usuario = self.context['request'].user
        usuario.set_password(self.validated_data['password_nuevo'])
        usuario.save()

        # Registrar en historial
        HistorialSesion.objects.create(
            usuario=usuario,
            accion='cambio_password',
            ip_address=self.context.get('ip_address'),
            exitoso=True
        )

        return usuario


class SolicitarRecuperacionPasswordSerializer(serializers.Serializer):
    """
    Serializer para solicitar recuperación de contraseña.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validar que el email exista"""
        value = value.lower()
        if not Usuario.objects.filter(email=value, activo=True, eliminado=False).exists():
            # No revelar si el email existe o no (seguridad)
            pass
        return value


class RecuperarPasswordSerializer(serializers.Serializer):
    """
    Serializer para recuperar contraseña con token.
    """
    token = serializers.CharField(required=True)
    password_nuevo = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_confirmacion = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_token(self, value):
        """Validar que el token sea válido"""
        try:
            token = TokenRecuperacion.objects.get(token=value)
            if not token.esta_vigente():
                raise serializers.ValidationError("El token ha expirado o ya fue usado")
            self.context['token_obj'] = token
        except TokenRecuperacion.DoesNotExist:
            raise serializers.ValidationError("Token inválido")
        return value

    def validate_password_nuevo(self, value):
        """Validar la nueva contraseña"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        if data['password_nuevo'] != data['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden'
            })
        return data

    def save(self):
        """Guardar la nueva contraseña"""
        token = self.context['token_obj']
        usuario = token.usuario

        # Establecer nueva contraseña
        usuario.set_password(self.validated_data['password_nuevo'])
        usuario.save()

        # Marcar token como usado
        token.marcar_como_usado(self.context.get('ip_address'))

        # Registrar en historial
        HistorialSesion.objects.create(
            usuario=usuario,
            accion='recuperacion_password',
            ip_address=self.context.get('ip_address'),
            exitoso=True
        )

        return usuario


class RestablecerPasswordAdminSerializer(serializers.Serializer):
    """
    Serializer para que administradores restablezcan contraseñas.
    """
    usuario_id = serializers.IntegerField(required=True)
    password_nuevo = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_confirmacion = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    requiere_cambio = serializers.BooleanField(default=True)

    def validate_usuario_id(self, value):
        """Validar que el usuario exista"""
        try:
            usuario = Usuario.objects.get(id=value, eliminado=False)
            self.context['usuario_obj'] = usuario
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")
        return value

    def validate_password_nuevo(self, value):
        """Validar la nueva contraseña"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        if data['password_nuevo'] != data['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden'
            })
        return data

    def save(self):
        """Restablecer contraseña"""
        usuario = self.context['usuario_obj']
        usuario.set_password(self.validated_data['password_nuevo'])
        usuario.requiere_cambio_password = self.validated_data['requiere_cambio']
        usuario.save()

        return usuario


# =============================================================================
# SERIALIZERS DE VERIFICACIÓN
# =============================================================================

class VerificarEmailSerializer(serializers.Serializer):
    """
    Serializer para verificar email con token.
    """
    token = serializers.CharField(required=True)

    def validate_token(self, value):
        """Validar que el token sea válido"""
        try:
            token = TokenVerificacionEmail.objects.get(token=value)
            if not token.esta_vigente():
                raise serializers.ValidationError("El token ha expirado o ya fue usado")
            self.context['token_obj'] = token
        except TokenVerificacionEmail.DoesNotExist:
            raise serializers.ValidationError("Token inválido")
        return value

    def save(self):
        """Marcar email como verificado"""
        token = self.context['token_obj']
        token.marcar_como_verificado()
        return token.usuario


class ReenviarVerificacionEmailSerializer(serializers.Serializer):
    """
    Serializer para reenviar email de verificación.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validar que el usuario exista y no esté verificado"""
        value = value.lower()
        try:
            usuario = Usuario.objects.get(email=value, eliminado=False)
            if usuario.email_verificado:
                raise serializers.ValidationError("El email ya está verificado")
            self.context['usuario_obj'] = usuario
        except Usuario.DoesNotExist:
            # No revelar si el email existe o no
            pass
        return value


# =============================================================================
# SERIALIZERS DE HISTORIAL Y SESIONES
# =============================================================================

class HistorialSesionSerializer(serializers.ModelSerializer):
    """
    Serializer para historial de sesiones.
    """
    accion_display = serializers.CharField(source='get_accion_display', read_only=True)
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)

    class Meta:
        model = HistorialSesion
        fields = [
            'id',
            'uuid',
            'usuario',
            'usuario_email',
            'accion',
            'accion_display',
            'fecha_hora',
            'ip_address',
            'dispositivo',
            'navegador',
            'sistema_operativo',
            'ubicacion',
            'exitoso',
            'razon_fallo',
            'duracion_sesion',
        ]
        read_only_fields = ['id', 'uuid', 'fecha_hora']


class TokenRecuperacionSerializer(serializers.ModelSerializer):
    """
    Serializer para tokens de recuperación (solo admin).
    """
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    esta_vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = TokenRecuperacion
        fields = [
            'id',
            'uuid',
            'usuario',
            'usuario_email',
            'token',
            'fecha_creacion',
            'fecha_expiracion',
            'usado',
            'fecha_uso',
            'ip_solicitud',
            'ip_uso',
            'esta_vigente',
        ]
        read_only_fields = ['id', 'uuid', 'fecha_creacion']


# =============================================================================
# SERIALIZERS DE BLOQUEO Y DESBLOQUEO
# =============================================================================

class BloquearUsuarioSerializer(serializers.Serializer):
    """
    Serializer para bloquear un usuario.
    """
    usuario_id = serializers.IntegerField(required=True)
    razon = serializers.CharField(required=True, max_length=500)

    def validate_usuario_id(self, value):
        """Validar que el usuario exista"""
        try:
            usuario = Usuario.objects.get(id=value, eliminado=False)
            self.context['usuario_obj'] = usuario
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")
        return value

    def save(self):
        """Bloquear usuario"""
        usuario = self.context['usuario_obj']
        usuario.bloquear(self.validated_data['razon'])
        return usuario


class DesbloquearUsuarioSerializer(serializers.Serializer):
    """
    Serializer para desbloquear un usuario.
    """
    usuario_id = serializers.IntegerField(required=True)
    razon = serializers.CharField(required=False, max_length=500)

    def validate_usuario_id(self, value):
        """Validar que el usuario exista y esté bloqueado"""
        try:
            usuario = Usuario.objects.get(id=value, eliminado=False)
            if not usuario.esta_bloqueado:
                raise serializers.ValidationError("El usuario no está bloqueado")
            self.context['usuario_obj'] = usuario
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")
        return value

    def save(self):
        """Desbloquear usuario"""
        usuario = self.context['usuario_obj']
        razon = self.validated_data.get('razon')
        usuario.desbloquear(razon)
        return usuario


# =============================================================================
# SERIALIZERS ESPECIALES
# =============================================================================

class PerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del usuario actual.
    Incluye información completa y permisos.
    """
    nombre_completo = serializers.CharField(read_only=True)
    edad = serializers.IntegerField(read_only=True)
    es_medico = serializers.BooleanField(read_only=True)
    es_personal_salud = serializers.BooleanField(read_only=True)
    permisos = serializers.SerializerMethodField()
    estadisticas = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            # Identificación
            'id',
            'uuid',
            'email',
            'email_verificado',

            # Datos Personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'fecha_nacimiento',
            'edad',
            'genero',

            # Contacto
            'telefono',
            'direccion',

            # Profesional
            'rol',
            'especialidad',
            'matricula_profesional',
            'institucion',

            # Media
            'foto_perfil',

            # Preferencias
            'idioma',
            'zona_horaria',
            'notificaciones_email',

            # Propiedades
            'es_medico',
            'es_personal_salud',

            # Extra
            'permisos',
            'estadisticas',

            # Fecha
            'ultimo_login',
        ]
        read_only_fields = ['id', 'uuid', 'email', 'rol', 'ultimo_login']

    def get_permisos(self, obj):
        """Retorna permisos del usuario"""
        return {
            'puede_crear_pacientes': obj.puede_crear_pacientes,
            'puede_editar_pacientes': obj.puede_editar_pacientes,
            'puede_registrar_controles': obj.puede_registrar_controles,
            'puede_agendar_citas': obj.puede_agendar_citas,
            'puede_generar_reportes': obj.puede_generar_reportes,
        }

    def get_estadisticas(self, obj):
        """Retorna estadísticas del usuario"""
        # TODO: Calcular estadísticas reales
        return {
            'total_pacientes_atendidos': 0,
            'total_controles_realizados': 0,
            'total_citas_pendientes': 0,
        }


class EstadisticasUsuarioSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de un usuario.
    """
    total_usuarios = serializers.IntegerField()
    usuarios_activos = serializers.IntegerField()
    usuarios_inactivos = serializers.IntegerField()
    usuarios_bloqueados = serializers.IntegerField()
    por_rol = serializers.DictField()
    nuevos_este_mes = serializers.IntegerField()
    logins_hoy = serializers.IntegerField()


# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
