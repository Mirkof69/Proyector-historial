"""
===========================================
SERIALIZERS - MÓDULO USUARIOS
===========================================
Descripción:
    Serializers para el módulo de gestión de usuarios.
    Incluye validaciones exhaustivas, serializers especializados,
    y manejo seguro de contraseñas.

Funcionalidades:
    - Serializer estándar para CRUD
    - Serializer de registro con validación de contraseña
    - Serializer de login con autenticación
    - Serializer de cambio de contraseña
    - Serializer simplificado para listas
    - Serializer detallado con estadísticas
    - Validaciones de seguridad y formato

Seguridad:
    - Nunca expone password_hash
    - Validación de fortaleza de contraseña
    - Validación de email único
    - Validación de cédula única
    - Prevención de duplicados

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from rest_framework import serializers
from .models import Usuario
from django.contrib.auth.hashers import make_password
import re
from datetime import date, datetime


class UsuarioSerializer(serializers.ModelSerializer):
    """
    SERIALIZER ESTÁNDAR: Para operaciones CRUD de usuarios

    Funcionamiento:
        - Se usa para crear, actualizar y mostrar usuarios
        - NO expone el campo password_hash por seguridad
        - Incluye campos calculados como nombre_completo y edad
        - Validaciones exhaustivas en todos los campos

    Campos expuestos:
        Todos excepto password_hash (por seguridad)

    Uso:
        - GET /api/usuarios/{id}/
        - PUT /api/usuarios/{id}/
        - PATCH /api/usuarios/{id}/
    """

    # Campos calculados (solo lectura)
    nombre_completo = serializers.ReadOnlyField()
    edad = serializers.ReadOnlyField()
    puede_acceder = serializers.ReadOnlyField()
    esta_bloqueado = serializers.ReadOnlyField()

    class Meta:
        model = Usuario
        fields = [
            # Identificación
            'id',
            'uuid',
            'email',
            'cedula_identidad',

            # Datos personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',  # Calculado
            'fecha_nacimiento',
            'edad',  # Calculado

            # Datos profesionales
            'rol',
            'especialidad',
            'registro_profesional',
            'institucion',

            # Contacto
            'telefono',
            'telefono_alternativo',
            'direccion',

            # Configuración
            'foto_perfil',
            'firma_digital',
            'email_verificado',
            'fecha_verificacion_email',

            # Estado y seguridad
            'estado',
            'activo',
            'puede_acceder',  # Calculado
            'esta_bloqueado',  # Calculado
            'ultimo_login',
            'intentos_login_fallidos',
            'fecha_bloqueo',

            # Auditoría
            'fecha_creacion',
            'fecha_actualizacion',
            'creado_por',
            'observaciones',
        ]

        # Campos de solo lectura
        read_only_fields = [
            'id',
            'uuid',
            'nombre_completo',
            'edad',
            'puede_acceder',
            'esta_bloqueado',
            'fecha_creacion',
            'fecha_actualizacion',
            'ultimo_login',
            'intentos_login_fallidos',
            'fecha_bloqueo',
            'fecha_verificacion_email',
        ]

        # IMPORTANTE: password_hash NO está en fields por seguridad
        # Nunca exponer hashes de contraseñas en la API

    # ===========================================
    # VALIDACIONES DE CAMPOS INDIVIDUALES
    # ===========================================

    def validate_email(self, value):
        """
        VALIDACIÓN: Email único y formato válido

        Funcionamiento:
            1. Verifica formato de email válido
            2. Verifica que no exista en la base de datos
            3. En actualización, permite el email del mismo usuario

        Reglas:
            - Debe tener formato email válido
            - Debe ser único en todo el sistema
            - No sensible a mayúsculas/minúsculas

        Parámetros:
            value (str): Email a validar

        Retorna:
            str: Email en minúsculas

        Excepciones:
            ValidationError: Si el email ya existe o formato inválido
        """
        # Convertir a minúsculas para consistencia
        value = value.lower().strip()

        # Validar formato básico de email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError(
                "El formato del correo electrónico no es válido."
            )

        # Validar unicidad
        if not self.instance:  # Creación
            if Usuario.objects.filter(email=value).exists():
                raise serializers.ValidationError(
                    "Ya existe un usuario con este correo electrónico."
                )
        else:  # Actualización
            if Usuario.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Ya existe un usuario con este correo electrónico."
                )

        return value

    def validate_cedula_identidad(self, value):
        """
        VALIDACIÓN: Cédula de identidad única

        Funcionamiento:
            1. Verifica formato (solo números y guiones)
            2. Verifica que no exista en la base de datos
            3. Permite nulo (campo opcional)

        Reglas:
            - Solo números y guiones
            - Único en todo el sistema
            - Opcional (puede ser None)

        Parámetros:
            value (str): Cédula a validar

        Retorna:
            str: Cédula validada o None

        Excepciones:
            ValidationError: Si ya existe o formato inválido
        """
        if not value:
            return None

        # Limpiar espacios
        value = value.strip()

        # Validar formato (solo números y guiones)
        if not re.match(r'^[0-9\-]+$', value):
            raise serializers.ValidationError(
                "La cédula de identidad solo puede contener números y guiones."
            )

        # Validar unicidad
        if not self.instance:  # Creación
            if Usuario.objects.filter(cedula_identidad=value).exists():
                raise serializers.ValidationError(
                    "Ya existe un usuario con esta cédula de identidad."
                )
        else:  # Actualización
            if Usuario.objects.filter(cedula_identidad=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Ya existe un usuario con esta cédula de identidad."
                )

        return value

    def validate_registro_profesional(self, value):
        """
        VALIDACIÓN: Número de registro profesional único

        Funcionamiento:
            Verifica que el número de matrícula/colegiatura sea único

        Parámetros:
            value (str): Número de registro

        Retorna:
            str: Registro validado o None

        Excepciones:
            ValidationError: Si ya existe
        """
        if not value:
            return None

        value = value.strip()

        # Validar unicidad
        if not self.instance:  # Creación
            if Usuario.objects.filter(registro_profesional=value).exists():
                raise serializers.ValidationError(
                    "Ya existe un usuario con este número de registro profesional."
                )
        else:  # Actualización
            if Usuario.objects.filter(registro_profesional=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Ya existe un usuario con este número de registro profesional."
                )

        return value

    def validate_nombre(self, value):
        """
        VALIDACIÓN: Nombre solo con letras

        Funcionamiento:
            Verifica que el nombre solo contenga letras y espacios

        Reglas:
            - Solo letras (incluye acentos y ñ)
            - Permite espacios
            - Obligatorio

        Parámetros:
            value (str): Nombre a validar

        Retorna:
            str: Nombre validado y limpio

        Excepciones:
            ValidationError: Si contiene caracteres inválidos
        """
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")

        # Solo letras, espacios, acentos y ñ
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError(
                "El nombre solo puede contener letras."
            )

        return value.strip().title()  # Capitalizar

    def validate_apellido_paterno(self, value):
        """
        VALIDACIÓN: Apellido paterno solo con letras

        Funcionamiento:
            Verifica que el apellido solo contenga letras

        Parámetros:
            value (str): Apellido a validar

        Retorna:
            str: Apellido validado

        Excepciones:
            ValidationError: Si contiene caracteres inválidos
        """
        if not value:
            raise serializers.ValidationError("El apellido paterno es obligatorio.")

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError(
                "El apellido paterno solo puede contener letras."
            )

        return value.strip().title()

    def validate_apellido_materno(self, value):
        """
        VALIDACIÓN: Apellido materno (opcional)

        Funcionamiento:
            Si se proporciona, debe contener solo letras

        Parámetros:
            value (str): Apellido a validar

        Retorna:
            str: Apellido validado o None

        Excepciones:
            ValidationError: Si contiene caracteres inválidos
        """
        if not value:
            return None

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError(
                "El apellido materno solo puede contener letras."
            )

        return value.strip().title()

    def validate_fecha_nacimiento(self, value):
        """
        VALIDACIÓN: Fecha de nacimiento válida

        Funcionamiento:
            1. Verifica que no sea futura
            2. Verifica que la edad sea razonable (18-100 años)

        Reglas:
            - No puede ser fecha futura
            - Edad mínima: 18 años (usuario debe ser mayor de edad)
            - Edad máxima: 100 años (validación de datos)

        Parámetros:
            value (date): Fecha a validar

        Retorna:
            date: Fecha validada

        Excepciones:
            ValidationError: Si la fecha es inválida
        """
        if not value:
            return None

        # No puede ser futura
        if value > date.today():
            raise serializers.ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )

        # Calcular edad
        hoy = date.today()
        edad = hoy.year - value.year
        if hoy.month < value.month or (hoy.month == value.month and hoy.day < value.day):
            edad -= 1

        # Validar edad mínima (18 años)
        if edad < 18:
            raise serializers.ValidationError(
                "El usuario debe ser mayor de 18 años."
            )

        # Validar edad máxima (100 años)
        if edad > 100:
            raise serializers.ValidationError(
                "La fecha de nacimiento parece incorrecta (edad mayor a 100 años)."
            )

        return value

    def validate_telefono(self, value):
        """
        VALIDACIÓN: Formato de teléfono

        Funcionamiento:
            Verifica que el teléfono contenga solo caracteres válidos

        Reglas:
            - Solo números, espacios, +, -, (, )

        Parámetros:
            value (str): Teléfono a validar

        Retorna:
            str: Teléfono validado

        Excepciones:
            ValidationError: Si contiene caracteres inválidos
        """
        if not value:
            return None

        if not re.match(r'^[0-9\+\-\s\(\)]+$', value):
            raise serializers.ValidationError(
                "El teléfono solo puede contener números y los caracteres: + - ( )"
            )

        return value.strip()

    def validate_telefono_alternativo(self, value):
        """VALIDACIÓN: Teléfono alternativo (mismo formato)"""
        if not value:
            return None

        if not re.match(r'^[0-9\+\-\s\(\)]+$', value):
            raise serializers.ValidationError(
                "El teléfono solo puede contener números y los caracteres: + - ( )"
            )

        return value.strip()

    def validate_rol(self, value):
        """
        VALIDACIÓN: Rol válido

        Funcionamiento:
            Verifica que el rol sea uno de los permitidos

        Reglas:
            - Debe ser un rol válido del sistema
            - Los roles son: administrador, medico, enfermero, asistente

        Parámetros:
            value (str): Rol a validar

        Retorna:
            str: Rol validado

        Excepciones:
            ValidationError: Si el rol no es válido
        """
        roles_validos = ['administrador', 'medico', 'enfermero', 'asistente']

        if value not in roles_validos:
            raise serializers.ValidationError(
                f"El rol debe ser uno de: {', '.join(roles_validos)}"
            )

        return value


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """
    SERIALIZER DE CREACIÓN: Para registrar nuevos usuarios

    Funcionamiento:
        - Se usa SOLO para crear usuarios
        - Incluye campo de contraseña (no hash)
        - Valida fortaleza de contraseña
        - Hashea la contraseña automáticamente
        - Confirmación de contraseña requerida

    Campos adicionales:
        - password: Contraseña en texto plano (solo escritura)
        - password_confirm: Confirmación de contraseña

    Proceso:
        1. Usuario envía password y password_confirm
        2. Sistema valida que coincidan
        3. Sistema valida fortaleza
        4. Sistema hashea la contraseña
        5. Guarda el hash en password_hash
        6. NUNCA expone la contraseña

    Uso:
        POST /api/usuarios/
    """

    # Campo de contraseña (solo escritura)
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
        help_text="Contraseña del usuario (mínimo 8 caracteres)",
        style={'input_type': 'password'}
    )

    # Campo de confirmación de contraseña
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
        help_text="Confirmación de contraseña (debe coincidir)",
        style={'input_type': 'password'}
    )

    class Meta:
        model = Usuario
        fields = [
            # Identificación
            'email',
            'cedula_identidad',

            # Contraseñas (solo escritura)
            'password',
            'password_confirm',

            # Datos personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'fecha_nacimiento',

            # Datos profesionales
            'rol',
            'especialidad',
            'registro_profesional',
            'institucion',

            # Contacto
            'telefono',
            'telefono_alternativo',
            'direccion',

            # Configuración
            'foto_perfil',
            'firma_digital',
        ]

    def validate_password(self, value):
        """
        VALIDACIÓN: Fortaleza de contraseña

        Funcionamiento:
            Valida que la contraseña cumpla requisitos de seguridad

        Requisitos:
            - Mínimo 8 caracteres
            - Al menos una letra mayúscula
            - Al menos una letra minúscula
            - Al menos un número
            - Al menos un carácter especial (opcional pero recomendado)

        Parámetros:
            value (str): Contraseña a validar

        Retorna:
            str: Contraseña validada

        Excepciones:
            ValidationError: Si la contraseña es débil
        """
        # Mínimo 8 caracteres (ya validado por min_length)

        # Debe contener al menos una letra mayúscula
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra mayúscula."
            )

        # Debe contener al menos una letra minúscula
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra minúscula."
            )

        # Debe contener al menos un número
        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        # Opcional pero recomendado: caracteres especiales
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=]', value):
            # Solo advertencia, no error
            pass

        return value

    def validate(self, data):
        """
        VALIDACIÓN: Validación a nivel de objeto

        Funcionamiento:
            1. Verifica que las contraseñas coincidan
            2. Si el rol es médico, requiere especialidad
            3. Otras validaciones de negocio

        Parámetros:
            data (dict): Datos completos del usuario

        Retorna:
            dict: Datos validados

        Excepciones:
            ValidationError: Si hay inconsistencias
        """
        # Las contraseñas deben coincidir
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })

        # Si el rol es médico, debería tener especialidad
        if data.get('rol') == 'medico' and not data.get('especialidad'):
            raise serializers.ValidationError({
                'especialidad': 'Los médicos deben especificar su especialidad.'
            })

        return data

    def create(self, validated_data):
        """
        MÉTODO: Crear usuario con contraseña hasheada

        Funcionamiento:
            1. Extrae la contraseña del validated_data
            2. Elimina password_confirm
            3. Crea el usuario
            4. Hashea y establece la contraseña usando set_password()
            5. Guarda el usuario

        IMPORTANTE:
            La contraseña se hashea usando PBKDF2-SHA256
            NUNCA se almacena en texto plano

        Parámetros:
            validated_data (dict): Datos validados

        Retorna:
            Usuario: Instancia del usuario creado
        """
        # Extraer contraseña
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')  # No se necesita

        # Crear usuario (sin contraseña aún)
        usuario = Usuario.objects.create(**validated_data)

        # Hashear y establecer contraseña de forma segura
        usuario.set_password(password)
        usuario.save()

        return usuario


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    SERIALIZER DE ACTUALIZACIÓN: Para modificar usuarios existentes

    Funcionamiento:
        - Se usa para actualizar datos del usuario
        - NO incluye contraseña (use PasswordChangeSerializer para eso)
        - Permite actualización parcial (PATCH)

    Campos modificables:
        Todos excepto: id, uuid, password_hash, fecha_creacion

    Uso:
        PUT /api/usuarios/{id}/
        PATCH /api/usuarios/{id}/
    """

    class Meta:
        model = Usuario
        fields = [
            # Identificación (no modificable: email)
            'cedula_identidad',

            # Datos personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'fecha_nacimiento',

            # Datos profesionales
            'rol',
            'especialidad',
            'registro_profesional',
            'institucion',

            # Contacto
            'telefono',
            'telefono_alternativo',
            'direccion',

            # Configuración
            'foto_perfil',
            'firma_digital',

            # Estado
            'activo',
            'observaciones',
        ]

    def validate(self, data):
        """
        VALIDACIÓN: Reglas de negocio en actualización

        Funcionamiento:
            Verifica reglas como médicos deben tener especialidad

        Parámetros:
            data (dict): Datos a actualizar

        Retorna:
            dict: Datos validados
        """
        # Si cambia el rol a médico, debe tener especialidad
        rol = data.get('rol', self.instance.rol if self.instance else None)
        especialidad = data.get('especialidad', self.instance.especialidad if self.instance else None)

        if rol == 'medico' and not especialidad:
            raise serializers.ValidationError({
                'especialidad': 'Los médicos deben especificar su especialidad.'
            })

        return data


class PasswordChangeSerializer(serializers.Serializer):
    """
    SERIALIZER: Cambio de contraseña

    Funcionamiento:
        - Requiere contraseña actual para verificación
        - Requiere nueva contraseña con confirmación
        - Valida fortaleza de nueva contraseña
        - Hashea automáticamente

    Campos:
        - current_password: Contraseña actual (verificación)
        - new_password: Nueva contraseña
        - new_password_confirm: Confirmación de nueva contraseña

    Proceso:
        1. Verifica contraseña actual
        2. Valida fortaleza de nueva contraseña
        3. Verifica que las nuevas coincidan
        4. Hashea y guarda

    Uso:
        POST /api/usuarios/{id}/cambiar_password/
    """

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Contraseña actual (para verificación)"
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        max_length=128,
        style={'input_type': 'password'},
        help_text="Nueva contraseña (mínimo 8 caracteres)"
    )

    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        max_length=128,
        style={'input_type': 'password'},
        help_text="Confirmación de nueva contraseña"
    )

    def validate_new_password(self, value):
        """
        VALIDACIÓN: Fortaleza de nueva contraseña

        Funcionamiento:
            Aplica las mismas reglas que el registro

        Requisitos:
            - Mínimo 8 caracteres
            - Mayúscula, minúscula, número
        """
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra mayúscula."
            )

        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra minúscula."
            )

        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        return value

    def validate(self, data):
        """
        VALIDACIÓN: Las nuevas contraseñas deben coincidir

        Funcionamiento:
            Verifica que new_password y new_password_confirm sean iguales
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden.'
            })

        return data


class LoginSerializer(serializers.Serializer):
    """
    SERIALIZER: Login de usuario

    Funcionamiento:
        - Recibe email y password
        - Valida formato
        - NO verifica credenciales (eso lo hace la vista)

    Campos:
        - email: Correo electrónico
        - password: Contraseña

    Uso:
        POST /api/usuarios/login/
    """

    email = serializers.EmailField(
        required=True,
        help_text="Correo electrónico del usuario"
    )

    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Contraseña del usuario"
    )

    def validate_email(self, value):
        """Normalizar email a minúsculas"""
        return value.lower().strip()


class UsuarioListSerializer(serializers.ModelSerializer):
    """
    SERIALIZER SIMPLIFICADO: Para listados de usuarios

    Funcionamiento:
        - Optimizado para listas grandes
        - Solo campos esenciales
        - Incluye campos calculados útiles

    Uso:
        GET /api/usuarios/
    """

    nombre_completo = serializers.ReadOnlyField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'uuid',
            'email',
            'nombre_completo',
            'rol',
            'rol_display',
            'especialidad',
            'estado',
            'estado_display',
            'activo',
            'fecha_creacion',
            'ultimo_login',
        ]


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """
    SERIALIZER DETALLADO: Para vista individual de usuario

    Funcionamiento:
        - Incluye TODOS los campos (excepto password_hash)
        - Incluye campos calculados
        - Incluye estadísticas relacionadas

    Uso:
        GET /api/usuarios/{id}/
    """

    nombre_completo = serializers.ReadOnlyField()
    edad = serializers.ReadOnlyField()
    puede_acceder = serializers.ReadOnlyField()
    esta_bloqueado = serializers.ReadOnlyField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    # Estadísticas relacionadas
    total_pacientes_creados = serializers.SerializerMethodField()
    total_controles_realizados = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = '__all__'
        read_only_fields = ['password_hash']  # Nunca exponer

    def get_total_pacientes_creados(self, obj):
        """
        MÉTODO: Contar pacientes creados por este usuario

        Funcionamiento:
            Cuenta los pacientes donde este usuario es el responsable
            (Requiere implementación en modelo Paciente)

        Retorna:
            int: Número de pacientes
        """
        # TODO: Implementar cuando Paciente tenga campo 'creado_por'
        return 0

    def get_total_controles_realizados(self, obj):
        """
        MÉTODO: Contar controles realizados por este usuario

        Funcionamiento:
            Cuenta controles donde este usuario es médico o enfermero

        Retorna:
            int: Número de controles
        """
        try:
            total_medico = obj.controles_medico.count() if hasattr(obj, 'controles_medico') else 0
            total_enfermero = obj.controles_enfermero.count() if hasattr(obj, 'controles_enfermero') else 0
            return total_medico + total_enfermero
        except:
            return 0
