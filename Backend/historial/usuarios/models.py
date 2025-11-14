"""
===========================================
MÓDULO: USUARIOS
===========================================
Descripción:
    Sistema completo de gestión de usuarios del sistema de historial médico.
    Incluye autenticación, autorización, y gestión de permisos por roles.

Funcionalidades:
    - CRUD completo de usuarios
    - Autenticación con JWT (JSON Web Tokens)
    - Cambio de contraseña
    - Recuperación de contraseña
    - Gestión de roles y permisos
    - Activación/desactivación de usuarios
    - Auditoría de accesos

Roles disponibles:
    - Administrador: Acceso total al sistema
    - Médico: Gestión de pacientes, embarazos, controles
    - Enfermero: Asistencia en controles, consulta de información

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, date
import uuid


class Usuario(models.Model):
    """
    MODELO PRINCIPAL: Usuario del sistema

    Este modelo representa a todos los usuarios del sistema (médicos, enfermeros, administradores).
    Cada usuario tiene credenciales de acceso, información personal y permisos basados en roles.

    FUNCIONAMIENTO:
        1. El usuario se registra con email y contraseña
        2. La contraseña se hashea automáticamente usando PBKDF2
        3. Se asigna un rol que determina sus permisos
        4. El UUID sirve como identificador inmutable
        5. El campo 'activo' permite desactivar usuarios sin eliminarlos

    RELACIONES:
        - Puede crear/modificar múltiples pacientes
        - Puede registrar múltiples controles prenatales
        - Puede ser responsable de múltiples embarazos
    """

    # ===========================================
    # CHOICES: Opciones predefinidas del sistema
    # ===========================================
    ROLES = (
        ('administrador', 'Administrador del Sistema'),
        ('medico', 'Médico Gineco-Obstetra'),
        ('enfermero', 'Enfermero/a'),
        ('asistente', 'Asistente Médico'),
    )

    ESTADOS_USUARIO = (
        ('activo', 'Usuario Activo'),
        ('inactivo', 'Usuario Inactivo'),
        ('suspendido', 'Usuario Suspendido'),
        ('bloqueado', 'Usuario Bloqueado'),
    )

    # ===========================================
    # CAMPOS DE IDENTIFICACIÓN
    # ===========================================
    # Campo: UUID - Identificador único universal
    # Funcionamiento: Se genera automáticamente al crear el usuario
    # Uso: Identificar usuarios de forma segura en APIs externas
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identificador único universal del usuario (inmutable)"
    )

    # Campo: Email - Correo electrónico (usado para login)
    # Funcionamiento: Debe ser único en todo el sistema
    # Uso: Credencial principal de autenticación
    email = models.EmailField(
        unique=True,
        max_length=255,
        help_text="Correo electrónico del usuario (usado para login)",
        error_messages={
            'unique': 'Ya existe un usuario con este correo electrónico.'
        }
    )

    # ===========================================
    # CAMPOS DE SEGURIDAD
    # ===========================================
    # Campo: Password Hash - Contraseña encriptada
    # Funcionamiento: Almacena la contraseña usando PBKDF2 con SHA256
    # IMPORTANTE: NUNCA almacenar contraseñas en texto plano
    password_hash = models.CharField(
        max_length=255,
        help_text="Hash de la contraseña (PBKDF2-SHA256)"
    )

    # Campo: Último login - Fecha del último acceso
    # Funcionamiento: Se actualiza automáticamente cada vez que el usuario inicia sesión
    ultimo_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora del último inicio de sesión"
    )

    # Campo: Intentos de login fallidos
    # Funcionamiento: Se incrementa con cada login fallido, se resetea al login exitoso
    # Uso: Seguridad - bloquear cuenta después de X intentos fallidos
    intentos_login_fallidos = models.IntegerField(
        default=0,
        help_text="Número de intentos de login fallidos consecutivos"
    )

    # Campo: Fecha de bloqueo
    # Funcionamiento: Se establece cuando se alcanza el límite de intentos fallidos
    fecha_bloqueo = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que la cuenta fue bloqueada por seguridad"
    )

    # ===========================================
    # DATOS PERSONALES
    # ===========================================
    # Campo: Nombre - Nombre(s) del usuario
    # Funcionamiento: Almacena el/los nombre(s) de pila
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre(s) del usuario"
    )

    # Campo: Apellido Paterno
    # Funcionamiento: Primer apellido del usuario
    apellido_paterno = models.CharField(
        max_length=100,
        help_text="Apellido paterno del usuario"
    )

    # Campo: Apellido Materno (opcional)
    # Funcionamiento: Segundo apellido, puede ser nulo
    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Apellido materno del usuario (opcional)"
    )

    # Campo: Fecha de Nacimiento
    # Funcionamiento: Permite calcular edad y validar que sea mayor de edad
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de nacimiento del usuario"
    )

    # Campo: Cédula de Identidad
    # Funcionamiento: Documento de identidad único
    cedula_identidad = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Cédula de identidad del usuario",
        error_messages={
            'unique': 'Ya existe un usuario con esta cédula de identidad.'
        }
    )

    # ===========================================
    # DATOS PROFESIONALES
    # ===========================================
    # Campo: Rol - Rol del usuario en el sistema
    # Funcionamiento: Determina los permisos y accesos del usuario
    # IMPORTANTE: El rol define qué puede hacer el usuario
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='asistente',
        help_text="Rol del usuario en el sistema (determina permisos)"
    )

    # Campo: Especialidad Médica (solo para médicos)
    # Funcionamiento: Detalla la especialidad si aplica
    especialidad = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Especialidad médica (Ej: Ginecología, Obstetricia)"
    )

    # Campo: Número de Registro Profesional
    # Funcionamiento: Matrícula profesional o número de colegiatura
    registro_profesional = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Número de matrícula profesional o colegiatura",
        error_messages={
            'unique': 'Ya existe un usuario con este número de registro.'
        }
    )

    # Campo: Institución
    # Funcionamiento: Hospital o clínica donde trabaja
    institucion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Hospital o clínica donde trabaja el usuario"
    )

    # ===========================================
    # DATOS DE CONTACTO
    # ===========================================
    # Campo: Teléfono Principal
    # Funcionamiento: Número de contacto principal
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono de contacto principal"
    )

    # Campo: Teléfono Alternativo
    # Funcionamiento: Número de contacto secundario
    telefono_alternativo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono alternativo de contacto"
    )

    # Campo: Dirección
    # Funcionamiento: Dirección física del usuario
    direccion = models.TextField(
        blank=True,
        null=True,
        help_text="Dirección física del usuario"
    )

    # ===========================================
    # CONFIGURACIÓN Y PREFERENCIAS
    # ===========================================
    # Campo: Foto de Perfil
    # Funcionamiento: URL o path a la imagen de perfil
    foto_perfil = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de la foto de perfil del usuario"
    )

    # Campo: Firma Digital
    # Funcionamiento: Imagen de la firma para documentos
    firma_digital = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de la firma digital para documentos médicos"
    )

    # ===========================================
    # CONTROL Y ESTADO
    # ===========================================
    # Campo: Estado del Usuario
    # Funcionamiento: Estado actual (activo, inactivo, suspendido, bloqueado)
    # IMPORTANTE: Solo usuarios activos pueden acceder al sistema
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_USUARIO,
        default='activo',
        help_text="Estado actual del usuario en el sistema"
    )

    # Campo: Activo (compatibilidad)
    # Funcionamiento: Boolean que indica si el usuario está activo
    # Uso: Mantener compatibilidad con código existente
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el usuario está activo (True) o inactivo (False)"
    )

    # Campo: Verificado por Email
    # Funcionamiento: Indica si el usuario verificó su correo electrónico
    email_verificado = models.BooleanField(
        default=False,
        help_text="Indica si el usuario verificó su correo electrónico"
    )

    # Campo: Fecha de Verificación Email
    # Funcionamiento: Registra cuándo se verificó el email
    fecha_verificacion_email = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que se verificó el correo electrónico"
    )

    # ===========================================
    # CAMPOS DE AUDITORÍA
    # ===========================================
    # Campo: Fecha de Creación
    # Funcionamiento: Se establece automáticamente al crear el usuario
    # IMPORTANTE: No se puede modificar después
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del usuario (inmutable)"
    )

    # Campo: Fecha de Última Actualización
    # Funcionamiento: Se actualiza automáticamente cada vez que se modifica el usuario
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última modificación del usuario"
    )

    # Campo: Creado Por (usuario que creó este usuario)
    # Funcionamiento: Referencia al administrador que creó la cuenta
    creado_por = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID del usuario administrador que creó esta cuenta"
    )

    # Campo: Observaciones
    # Funcionamiento: Notas adicionales sobre el usuario
    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones o notas sobre el usuario"
    )

    # ===========================================
    # CONFIGURACIÓN DEL MODELO
    # ===========================================
    class Meta:
        db_table = 'usuarios'
        managed = False  # La tabla es administrada externamente
        ordering = ['-fecha_creacion']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        # Índices para mejorar performance en búsquedas
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['rol']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        """
        MÉTODO: Representación en string del usuario

        Funcionamiento:
            Retorna una cadena legible con el nombre completo y rol del usuario

        Retorna:
            str: "Dr. Juan Pérez (Médico Gineco-Obstetra)"
        """
        prefijo = "Dr." if self.rol == 'medico' else "Enf." if self.rol == 'enfermero' else ""
        return f"{prefijo} {self.nombre_completo} ({self.get_rol_display()})"

    # ===========================================
    # PROPERTIES: Campos calculados
    # ===========================================
    @property
    def nombre_completo(self):
        """
        PROPERTY: Nombre completo del usuario

        Funcionamiento:
            Concatena nombre y apellidos en una sola cadena
            Si existe apellido materno lo incluye, si no solo paterno

        Retorna:
            str: "Juan Pérez García" o "Juan Pérez"
        """
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"

    @property
    def edad(self):
        """
        PROPERTY: Edad actual del usuario

        Funcionamiento:
            Calcula la edad en años a partir de la fecha de nacimiento
            Considera si ya cumplió años este año

        Retorna:
            int: Edad en años, o None si no hay fecha de nacimiento
        """
        if not self.fecha_nacimiento:
            return None

        hoy = date.today()
        edad = hoy.year - self.fecha_nacimiento.year

        # Ajustar si aún no ha cumplido años este año
        if hoy.month < self.fecha_nacimiento.month or \
           (hoy.month == self.fecha_nacimiento.month and hoy.day < self.fecha_nacimiento.day):
            edad -= 1

        return edad

    @property
    def is_authenticated(self):
        """
        PROPERTY: Indica si el usuario está autenticado

        Funcionamiento:
            Propiedad requerida por Django para autenticación
            Siempre retorna True para usuarios existentes

        Retorna:
            bool: True (siempre para instancias de Usuario)
        """
        return True

    @property
    def is_anonymous(self):
        """
        PROPERTY: Indica si el usuario es anónimo

        Funcionamiento:
            Propiedad requerida por Django para autenticación
            Siempre retorna False para usuarios existentes

        Retorna:
            bool: False (siempre para instancias de Usuario)
        """
        return False

    @property
    def esta_bloqueado(self):
        """
        PROPERTY: Verifica si el usuario está bloqueado

        Funcionamiento:
            Un usuario está bloqueado si:
            1. Tiene fecha_bloqueo establecida, O
            2. Su estado es 'bloqueado'

        Retorna:
            bool: True si está bloqueado, False si no
        """
        return self.fecha_bloqueo is not None or self.estado == 'bloqueado'

    @property
    def puede_acceder(self):
        """
        PROPERTY: Verifica si el usuario puede acceder al sistema

        Funcionamiento:
            Un usuario puede acceder si:
            1. Está activo (activo=True), Y
            2. Su estado es 'activo', Y
            3. No está bloqueado

        Retorna:
            bool: True si puede acceder, False si no
        """
        return self.activo and self.estado == 'activo' and not self.esta_bloqueado

    # ===========================================
    # MÉTODOS DE CONTRASEÑA
    # ===========================================
    def set_password(self, raw_password):
        """
        MÉTODO: Establecer contraseña de forma segura

        Funcionamiento:
            1. Recibe la contraseña en texto plano
            2. La encripta usando PBKDF2 con SHA256
            3. Guarda el hash en password_hash
            4. NUNCA almacena la contraseña en texto plano

        Proceso de encriptación:
            - Algoritmo: PBKDF2
            - Hash: SHA256
            - Iteraciones: 260,000
            - Salt: Generado automáticamente (único por contraseña)

        Parámetros:
            raw_password (str): Contraseña en texto plano

        Ejemplo:
            usuario.set_password("miContraseña123")
            # password_hash = "pbkdf2_sha256$260000$..."
        """
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """
        MÉTODO: Verificar contraseña

        Funcionamiento:
            1. Recibe la contraseña en texto plano
            2. La compara con el hash almacenado
            3. Retorna True si coincide, False si no

        Proceso de verificación:
            - Extrae el salt del hash almacenado
            - Aplica el mismo algoritmo a la contraseña ingresada
            - Compara los hashes de forma segura (timing-safe)

        Parámetros:
            raw_password (str): Contraseña a verificar

        Retorna:
            bool: True si la contraseña es correcta, False si no

        Ejemplo:
            if usuario.check_password("miContraseña123"):
                # Contraseña correcta
        """
        return check_password(raw_password, self.password_hash)

    # ===========================================
    # MÉTODOS DE GESTIÓN DE ESTADO
    # ===========================================
    def activar(self):
        """
        MÉTODO: Activar usuario

        Funcionamiento:
            1. Establece activo = True
            2. Establece estado = 'activo'
            3. Resetea intentos de login fallidos
            4. Limpia fecha de bloqueo
            5. Guarda los cambios en la base de datos

        Uso:
            Se llama cuando un administrador reactiva un usuario desactivado

        Ejemplo:
            usuario.activar()
            # El usuario ahora puede acceder al sistema
        """
        self.activo = True
        self.estado = 'activo'
        self.intentos_login_fallidos = 0
        self.fecha_bloqueo = None
        self.save()

    def desactivar(self, motivo=None):
        """
        MÉTODO: Desactivar usuario (Soft Delete)

        Funcionamiento:
            1. Establece activo = False
            2. Establece estado = 'inactivo'
            3. Opcionalmente guarda el motivo en observaciones
            4. Guarda los cambios en la base de datos

        IMPORTANTE:
            NO elimina el usuario de la base de datos
            Preserva toda la información e historial
            El usuario no puede acceder pero sus datos persisten

        Parámetros:
            motivo (str, opcional): Razón de la desactivación

        Ejemplo:
            usuario.desactivar(motivo="Término de contrato")
        """
        self.activo = False
        self.estado = 'inactivo'

        if motivo:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            obs = f"\n[{timestamp}] Desactivado: {motivo}"
            self.observaciones = (self.observaciones or "") + obs

        self.save()

    def suspender(self, motivo=None, duracion_dias=None):
        """
        MÉTODO: Suspender usuario temporalmente

        Funcionamiento:
            1. Establece estado = 'suspendido'
            2. Registra el motivo y duración
            3. El usuario no puede acceder durante la suspensión

        Diferencia con desactivar:
            - Suspender: Temporal, con duración definida
            - Desactivar: Indefinido, hasta reactivación manual

        Parámetros:
            motivo (str, opcional): Razón de la suspensión
            duracion_dias (int, opcional): Días de suspensión

        Ejemplo:
            usuario.suspender(motivo="Vacaciones", duracion_dias=15)
        """
        self.estado = 'suspendido'

        if motivo:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            duracion = f" por {duracion_dias} días" if duracion_dias else ""
            obs = f"\n[{timestamp}] Suspendido{duracion}: {motivo}"
            self.observaciones = (self.observaciones or "") + obs

        self.save()

    def bloquear(self, motivo="Seguridad - Múltiples intentos fallidos"):
        """
        MÉTODO: Bloquear usuario por seguridad

        Funcionamiento:
            1. Establece estado = 'bloqueado'
            2. Registra la fecha de bloqueo
            3. Guarda el motivo
            4. El usuario NO puede acceder hasta que un admin lo desbloquee

        Uso típico:
            Se llama automáticamente después de X intentos de login fallidos
            También puede ser manual por razones de seguridad

        Parámetros:
            motivo (str): Razón del bloqueo

        Ejemplo:
            usuario.bloquear(motivo="Actividad sospechosa detectada")
        """
        self.estado = 'bloqueado'
        self.fecha_bloqueo = datetime.now()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        obs = f"\n[{timestamp}] Bloqueado: {motivo}"
        self.observaciones = (self.observaciones or "") + obs

        self.save()

    def desbloquear(self):
        """
        MÉTODO: Desbloquear usuario

        Funcionamiento:
            1. Limpia la fecha de bloqueo
            2. Resetea intentos de login fallidos
            3. Establece estado = 'activo'
            4. Reactiva el usuario

        Uso:
            Solo puede ser ejecutado por un administrador

        Ejemplo:
            usuario.desbloquear()
            # El usuario puede intentar acceder nuevamente
        """
        self.fecha_bloqueo = None
        self.intentos_login_fallidos = 0
        self.estado = 'activo'
        self.activo = True
        self.save()

    # ===========================================
    # MÉTODOS DE SEGURIDAD
    # ===========================================
    def registrar_intento_fallido(self):
        """
        MÉTODO: Registrar intento de login fallido

        Funcionamiento:
            1. Incrementa el contador de intentos fallidos
            2. Si alcanza el límite (5 intentos), bloquea la cuenta
            3. Guarda los cambios

        Seguridad:
            Protege contra ataques de fuerza bruta
            Después de 5 intentos fallidos, la cuenta se bloquea automáticamente

        Ejemplo:
            usuario.registrar_intento_fallido()
            # Si es el 5to intento, la cuenta se bloquea
        """
        self.intentos_login_fallidos += 1

        # Bloquear después de 5 intentos fallidos
        if self.intentos_login_fallidos >= 5:
            self.bloquear(motivo=f"Bloqueado automáticamente por {self.intentos_login_fallidos} intentos fallidos")
        else:
            self.save()

    def resetear_intentos_fallidos(self):
        """
        MÉTODO: Resetear contador de intentos fallidos

        Funcionamiento:
            Se llama automáticamente después de un login exitoso
            Pone el contador en 0

        Ejemplo:
            # Después de login exitoso:
            usuario.resetear_intentos_fallidos()
        """
        self.intentos_login_fallidos = 0
        self.save()

    def registrar_login_exitoso(self):
        """
        MÉTODO: Registrar acceso exitoso al sistema

        Funcionamiento:
            1. Actualiza fecha de último login
            2. Resetea intentos fallidos
            3. Guarda los cambios

        Se llama automáticamente después de autenticación exitosa

        Ejemplo:
            usuario.registrar_login_exitoso()
            # Actualiza ultimo_login y resetea intentos
        """
        self.ultimo_login = datetime.now()
        self.resetear_intentos_fallidos()

    # ===========================================
    # MÉTODOS DE PERMISOS
    # ===========================================
    def tiene_permiso(self, permiso):
        """
        MÉTODO: Verificar si el usuario tiene un permiso específico

        Funcionamiento:
            Verifica permisos basados en el rol del usuario

        Permisos por rol:
            Administrador: Todos los permisos
            Médico: Gestión de pacientes, embarazos, controles, reportes
            Enfermero: Consulta y asistencia en controles
            Asistente: Solo consulta de información

        Parámetros:
            permiso (str): Nombre del permiso a verificar

        Retorna:
            bool: True si tiene el permiso, False si no

        Ejemplo:
            if usuario.tiene_permiso('crear_paciente'):
                # Permitir crear paciente
        """
        # Administrador tiene todos los permisos
        if self.rol == 'administrador':
            return True

        # Definir permisos por rol
        permisos_medico = [
            'ver_pacientes', 'crear_paciente', 'editar_paciente',
            'ver_embarazos', 'crear_embarazo', 'editar_embarazo',
            'ver_controles', 'crear_control', 'editar_control',
            'ver_reportes', 'generar_reporte'
        ]

        permisos_enfermero = [
            'ver_pacientes', 'ver_embarazos', 'ver_controles',
            'crear_control', 'editar_control'
        ]

        permisos_asistente = [
            'ver_pacientes', 'ver_embarazos', 'ver_controles'
        ]

        # Verificar permiso según rol
        if self.rol == 'medico':
            return permiso in permisos_medico
        elif self.rol == 'enfermero':
            return permiso in permisos_enfermero
        elif self.rol == 'asistente':
            return permiso in permisos_asistente

        return False

    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'administrador'

    def es_medico(self):
        """Verifica si el usuario es médico"""
        return self.rol == 'medico'

    def es_enfermero(self):
        """Verifica si el usuario es enfermero"""
        return self.rol == 'enfermero'
