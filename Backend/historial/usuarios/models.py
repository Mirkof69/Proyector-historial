# =============================================================================
# MODELOS DE USUARIOS Y AUTENTICACIÓN
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: usuarios
# Descripción: Modelos completos para gestión de usuarios del sistema médico,
#              incluyendo roles, permisos, sesiones, recuperación de contraseña,
#              auditoría y soft delete.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 - EXTENDIDO
# Última actualización: 2025-11-14
# =============================================================================

from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta
import uuid
import re

# =============================================================================
# VALIDADORES PERSONALIZADOS
# =============================================================================

def validar_telefono_boliviano(value):
    """
    Validador para teléfonos bolivianos.
    Formatos aceptados:
    - Celulares: 6XXXXXXX, 7XXXXXXX (8 dígitos)
    - Fijos: 2XXXXXXX, 3XXXXXXX, 4XXXXXXX (8 dígitos)
    """
    patron = r'^[2-7]\d{7}$'
    if not re.match(patron, value.replace(' ', '').replace('-', '')):
        raise ValidationError(
            'Ingrese un número de teléfono boliviano válido (8 dígitos comenzando con 2-7)'
        )


def validar_cedula_boliviana(value):
    """
    Validador para cédula de identidad boliviana.
    Formato: XXXXXXXX-XX (departamento-extensión)
    """
    if not value:
        return

    # Eliminar espacios y guiones para validar
    ci_limpia = value.replace(' ', '').replace('-', '')

    # Debe tener entre 6 y 10 dígitos
    if not re.match(r'^\d{6,10}$', ci_limpia):
        raise ValidationError(
            'La cédula de identidad debe tener entre 6 y 10 dígitos'
        )


def validar_matricula_profesional(value):
    """
    Validador para matrícula profesional médica.
    Formato: XXXX/YYYY (número/año)
    """
    if not value:
        return

    patron = r'^\d{3,6}/\d{4}$'
    if not re.match(patron, value):
        raise ValidationError(
            'La matrícula debe tener el formato: XXXX/YYYY (Ej: 1234/2020)'
        )


# =============================================================================
# MODELO PRINCIPAL: USUARIO
# =============================================================================
class Usuario(models.Model):
    """
    Modelo extendido para usuarios del sistema de historial médico.

    Funcionalidades completas:
    - Gestión de roles (paciente, médico, enfermero, doctor_laboratorio, admin)
    - Sistema de permisos granular
    - Autenticación JWT
    - Soft delete (borrado lógico)
    - Auditoría completa (creación, modificación, eliminación)
    - Perfil completo de usuario
    - Recuperación de contraseña
    - Historial de sesiones
    - Validaciones exhaustivas
    - Seguridad mejorada

    Relaciones:
    - Tiene múltiples sesiones (HistorialSesion)
    - Puede tener múltiples tokens de recuperación (TokenRecuperacion)
    - Puede atender pacientes (relacionado con Paciente)
    - Puede realizar controles (relacionado con ControlPrenatal)
    """

    # =========================================================================
    # OPCIONES Y CHOICES
    # =========================================================================

    # Roles del sistema - EXTENDIDO con paciente y doctor_laboratorio
    ROLES = (
        ('paciente', 'Paciente'),                      # Paciente del sistema
        ('medico', 'Médico'),                          # Médico obstetra/ginecólogo
        ('enfermero', 'Enfermero'),                    # Enfermero/a
        ('doctor_laboratorio', 'Doctor de Laboratorio'), # Médico de laboratorio
        ('administrador', 'Administrador'),             # Administrador del sistema
    )

    # Especialidades médicas obstétricas
    ESPECIALIDADES = (
        ('obstetricia', 'Obstetricia'),
        ('ginecologia', 'Ginecología'),
        ('gineco_obstetricia', 'Ginecología y Obstetricia'),
        ('medicina_fetal', 'Medicina Materno Fetal'),
        ('perinatologia', 'Perinatología'),
        ('medicina_general', 'Medicina General'),
        ('enfermeria_obstetrica', 'Enfermería Obstétrica'),
        ('laboratorio_clinico', 'Laboratorio Clínico'),
        ('bioquimica', 'Bioquímica'),
        ('imagenologia', 'Imagenología'),
        ('ecografia', 'Ecografía'),
        ('otra', 'Otra Especialidad'),
    )

    # Departamentos de Bolivia (para CI)
    DEPARTAMENTOS = (
        ('LP', 'La Paz'),
        ('CB', 'Cochabamba'),
        ('SC', 'Santa Cruz'),
        ('OR', 'Oruro'),
        ('PT', 'Potosí'),
        ('TJ', 'Tarija'),
        ('CH', 'Chuquisaca'),
        ('BE', 'Beni'),
        ('PD', 'Pando'),
    )

    # Géneros
    GENEROS = (
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro'),
        ('prefiero_no_decir', 'Prefiero no decir'),
    )

    # Estados del usuario
    ESTADOS = (
        ('activo', 'Activo'),                # Usuario activo
        ('inactivo', 'Inactivo'),            # Usuario temporalmente inactivo
        ('bloqueado', 'Bloqueado'),          # Usuario bloqueado por seguridad
        ('pendiente', 'Pendiente activación'), # Pendiente de activación
        ('eliminado', 'Eliminado'),          # Soft delete
    )

    # =========================================================================
    # CAMPOS PRINCIPALES
    # =========================================================================

    # --- Identificación ---
    id = models.AutoField(
        primary_key=True,
        help_text="Identificador único autoincremental"
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Identificador único universal (UUID)"
    )

    # --- Autenticación ---
    email = models.EmailField(
        unique=True,
        db_index=True,
        validators=[EmailValidator(message="Ingrese un email válido")],
        error_messages={
            'unique': 'Este email ya está registrado en el sistema'
        },
        help_text="Email único del usuario (usado para login)"
    )

    password_hash = models.CharField(
        max_length=255,
        verbose_name="Contraseña (hash)",
        help_text="Hash de la contraseña del usuario"
    )

    # --- Datos Personales ---
    nombre = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2, message="El nombre debe tener al menos 2 caracteres")],
        help_text="Nombre(s) del usuario"
    )

    apellido_paterno = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2, message="El apellido debe tener al menos 2 caracteres")],
        help_text="Apellido paterno del usuario"
    )

    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Apellido materno del usuario (opcional)"
    )

    nombre_completo = models.CharField(
        max_length=300,
        blank=True,
        editable=False,
        help_text="Nombre completo concatenado (generado automáticamente)"
    )

    # --- Identificación Oficial ---
    cedula_identidad = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        validators=[validar_cedula_boliviana],
        error_messages={
            'unique': 'Esta cédula de identidad ya está registrada'
        },
        help_text="Cédula de Identidad boliviana"
    )

    departamento_ci = models.CharField(
        max_length=2,
        choices=DEPARTAMENTOS,
        blank=True,
        null=True,
        help_text="Departamento de expedición de CI"
    )

    fecha_nacimiento = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de nacimiento del usuario"
    )

    genero = models.CharField(
        max_length=20,
        choices=GENEROS,
        blank=True,
        null=True,
        help_text="Género del usuario"
    )

    # --- Datos de Contacto ---
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validar_telefono_boliviano],
        help_text="Teléfono principal (Bolivia: 8 dígitos)"
    )

    telefono_secundario = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validar_telefono_boliviano],
        help_text="Teléfono secundario (opcional)"
    )

    direccion = models.TextField(
        blank=True,
        null=True,
        help_text="Dirección completa del usuario"
    )

    ciudad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Ciudad de residencia"
    )

    # --- Rol y Permisos ---
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        db_index=True,
        help_text="Rol del usuario en el sistema"
    )

    especialidad = models.CharField(
        max_length=150,
        choices=ESPECIALIDADES,
        blank=True,
        null=True,
        help_text="Especialidad médica (para médicos y enfermeros)"
    )

    matricula_profesional = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        validators=[validar_matricula_profesional],
        error_messages={
            'unique': 'Esta matrícula profesional ya está registrada'
        },
        help_text="Matrícula profesional (para médicos y enfermeros)"
    )

    # --- Información Profesional ---
    institucion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Institución donde trabaja"
    )

    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Cargo que desempeña"
    )

    anos_experiencia = models.IntegerField(
        blank=True,
        null=True,
        help_text="Años de experiencia profesional"
    )

    # --- Permisos Granulares ---
    puede_crear_pacientes = models.BooleanField(
        default=False,
        help_text="Permiso para crear nuevos pacientes"
    )

    puede_editar_pacientes = models.BooleanField(
        default=False,
        help_text="Permiso para editar pacientes"
    )

    puede_eliminar_pacientes = models.BooleanField(
        default=False,
        help_text="Permiso para eliminar pacientes"
    )

    puede_ver_historial_completo = models.BooleanField(
        default=False,
        help_text="Permiso para ver historial completo de pacientes"
    )

    puede_registrar_controles = models.BooleanField(
        default=False,
        help_text="Permiso para registrar controles prenatales"
    )

    puede_solicitar_laboratorios = models.BooleanField(
        default=False,
        help_text="Permiso para solicitar exámenes de laboratorio"
    )

    puede_registrar_resultados_lab = models.BooleanField(
        default=False,
        help_text="Permiso para registrar resultados de laboratorio"
    )

    puede_agendar_citas = models.BooleanField(
        default=False,
        help_text="Permiso para agendar citas"
    )

    puede_generar_reportes = models.BooleanField(
        default=False,
        help_text="Permiso para generar reportes"
    )

    es_superusuario = models.BooleanField(
        default=False,
        help_text="Usuario con permisos de superusuario"
    )

    # --- Estado y Activación ---
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente',
        db_index=True,
        help_text="Estado actual del usuario"
    )

    activo = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Usuario activo en el sistema"
    )

    email_verificado = models.BooleanField(
        default=False,
        help_text="Email ha sido verificado"
    )

    fecha_verificacion_email = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de verificación del email"
    )

    # --- Seguridad ---
    intentos_login_fallidos = models.IntegerField(
        default=0,
        help_text="Contador de intentos fallidos de login"
    )

    fecha_bloqueo = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de bloqueo del usuario"
    )

    razon_bloqueo = models.TextField(
        blank=True,
        null=True,
        help_text="Razón del bloqueo del usuario"
    )

    requiere_cambio_password = models.BooleanField(
        default=False,
        help_text="Usuario debe cambiar contraseña en próximo login"
    )

    ultimo_cambio_password = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha del último cambio de contraseña"
    )

    # --- Sesiones ---
    ultimo_login = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha y hora del último login exitoso"
    )

    ip_ultimo_login = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP del último login"
    )

    user_agent_ultimo_login = models.TextField(
        blank=True,
        null=True,
        help_text="User agent del último login"
    )

    # --- Preferencias ---
    idioma = models.CharField(
        max_length=10,
        default='es',
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
        ],
        help_text="Idioma preferido del usuario"
    )

    zona_horaria = models.CharField(
        max_length=50,
        default='America/La_Paz',
        help_text="Zona horaria del usuario"
    )

    notificaciones_email = models.BooleanField(
        default=True,
        help_text="Recibir notificaciones por email"
    )

    notificaciones_sms = models.BooleanField(
        default=False,
        help_text="Recibir notificaciones por SMS"
    )

    # --- Foto de Perfil ---
    foto_perfil = models.ImageField(
        upload_to='usuarios/fotos_perfil/',
        blank=True,
        null=True,
        help_text="Foto de perfil del usuario"
    )

    # --- Firma Digital (para médicos) ---
    firma_digital = models.ImageField(
        upload_to='usuarios/firmas/',
        blank=True,
        null=True,
        help_text="Firma digital para documentos médicos"
    )

    # --- Auditoría ---
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del registro"
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha de última modificación"
    )

    creado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_creados',
        help_text="Usuario que creó este registro"
    )

    modificado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_modificados',
        help_text="Usuario que modificó este registro por última vez"
    )

    # --- Soft Delete ---
    eliminado = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Registro eliminado lógicamente"
    )

    fecha_eliminacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de eliminación lógica"
    )

    eliminado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_eliminados',
        help_text="Usuario que eliminó este registro"
    )

    razon_eliminacion = models.TextField(
        blank=True,
        null=True,
        help_text="Razón de la eliminación"
    )

    # --- Notas ---
    notas_internas = models.TextField(
        blank=True,
        null=True,
        help_text="Notas internas sobre el usuario (solo visible para admins)"
    )

    # =========================================================================
    # META
    # =========================================================================

    class Meta:
        db_table = 'usuarios'
        managed = False
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['cedula_identidad']),
            models.Index(fields=['rol']),
            models.Index(fields=['estado']),
            models.Index(fields=['activo', 'eliminado']),
            models.Index(fields=['apellido_paterno', 'nombre']),
        ]

    # =========================================================================
    # PROPIEDADES COMPUTADAS
    # =========================================================================

    @property
    def is_authenticated(self):
        """Siempre retorna True para usuarios autenticados"""
        return True

    @property
    def is_anonymous(self):
        """Siempre retorna False para usuarios autenticados"""
        return False

    @property
    def nombre_completo_formateado(self):
        """Retorna el nombre completo en formato: Apellidos, Nombres"""
        apellidos = f"{self.apellido_paterno}"
        if self.apellido_materno:
            apellidos += f" {self.apellido_materno}"
        return f"{apellidos}, {self.nombre}"

    @property
    def iniciales(self):
        """Retorna las iniciales del usuario (ej: JDP)"""
        iniciales = self.nombre[0] if self.nombre else ''
        iniciales += self.apellido_paterno[0] if self.apellido_paterno else ''
        iniciales += self.apellido_materno[0] if self.apellido_materno else ''
        return iniciales.upper()

    @property
    def edad(self):
        """Calcula la edad del usuario"""
        if not self.fecha_nacimiento:
            return None

        hoy = timezone.now().date()
        edad = hoy.year - self.fecha_nacimiento.year

        # Ajustar si no ha cumplido años este año
        if hoy.month < self.fecha_nacimiento.month or \
           (hoy.month == self.fecha_nacimiento.month and hoy.day < self.fecha_nacimiento.day):
            edad -= 1

        return edad

    @property
    def es_medico(self):
        """Verifica si el usuario es médico"""
        return self.rol in ['medico', 'doctor_laboratorio']

    @property
    def es_personal_salud(self):
        """Verifica si el usuario es personal de salud"""
        return self.rol in ['medico', 'enfermero', 'doctor_laboratorio']

    @property
    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'administrador' or self.es_superusuario

    @property
    def esta_bloqueado(self):
        """Verifica si el usuario está bloqueado"""
        return self.estado == 'bloqueado' or self.fecha_bloqueo is not None

    @property
    def dias_desde_ultimo_cambio_password(self):
        """Calcula días desde el último cambio de contraseña"""
        if not self.ultimo_cambio_password:
            return None

        diferencia = timezone.now() - self.ultimo_cambio_password
        return diferencia.days

    @property
    def password_expirado(self):
        """Verifica si la contraseña ha expirado (90 días)"""
        if not self.ultimo_cambio_password:
            return False

        dias = self.dias_desde_ultimo_cambio_password
        return dias and dias > 90

    # =========================================================================
    # VALIDACIONES
    # =========================================================================

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        errors = {}

        # Validar que médicos y enfermeros tengan especialidad
        if self.rol in ['medico', 'enfermero', 'doctor_laboratorio']:
            if not self.especialidad:
                errors['especialidad'] = f"Los usuarios con rol '{self.get_rol_display()}' deben tener una especialidad"

            if self.rol in ['medico', 'doctor_laboratorio'] and not self.matricula_profesional:
                errors['matricula_profesional'] = "Los médicos deben tener matrícula profesional"

        # Validar edad mínima (18 años para personal médico)
        if self.fecha_nacimiento and self.es_personal_salud:
            edad = self.edad
            if edad and edad < 18:
                errors['fecha_nacimiento'] = "El personal de salud debe ser mayor de 18 años"

        # Validar email único (insensible a mayúsculas)
        if self.email:
            email_lower = self.email.lower()
            existe = Usuario.objects.filter(
                email__iexact=email_lower,
                eliminado=False
            ).exclude(pk=self.pk).exists()

            if existe:
                errors['email'] = "Este email ya está registrado"

        # Validar formato de CI completo (con departamento si está presente)
        if self.cedula_identidad and not self.departamento_ci:
            errors['departamento_ci'] = "Debe especificar el departamento de expedición de CI"

        if errors:
            raise ValidationError(errors)

    # =========================================================================
    # MÉTODOS DE AUTENTICACIÓN
    # =========================================================================

    def set_password(self, raw_password):
        """
        Establece la contraseña del usuario (la hashea).

        Args:
            raw_password (str): Contraseña en texto plano
        """
        self.password_hash = make_password(raw_password)
        self.ultimo_cambio_password = timezone.now()
        self.requiere_cambio_password = False

    def check_password(self, raw_password):
        """
        Verifica si la contraseña es correcta.

        Args:
            raw_password (str): Contraseña en texto plano

        Returns:
            bool: True si la contraseña es correcta
        """
        return check_password(raw_password, self.password_hash)

    def verificar_puede_login(self):
        """
        Verifica si el usuario puede hacer login.

        Returns:
            tuple: (puede_login, mensaje_error)
        """
        if self.eliminado:
            return False, "Usuario eliminado"

        if not self.activo:
            return False, "Usuario inactivo"

        if self.estado == 'bloqueado':
            return False, f"Usuario bloqueado. Razón: {self.razon_bloqueo or 'No especificada'}"

        if self.estado == 'pendiente':
            return False, "Usuario pendiente de activación"

        if self.intentos_login_fallidos >= 5:
            return False, "Usuario bloqueado por múltiples intentos fallidos"

        return True, None

    def registrar_login_exitoso(self, ip_address=None, user_agent=None):
        """
        Registra un login exitoso.

        Args:
            ip_address (str): Dirección IP del login
            user_agent (str): User agent del navegador
        """
        self.ultimo_login = timezone.now()
        self.intentos_login_fallidos = 0
        self.ip_ultimo_login = ip_address
        self.user_agent_ultimo_login = user_agent

        if self.estado == 'pendiente':
            self.estado = 'activo'

        self.save()

    def registrar_login_fallido(self):
        """Registra un intento de login fallido"""
        self.intentos_login_fallidos += 1

        # Bloquear después de 5 intentos
        if self.intentos_login_fallidos >= 5:
            self.estado = 'bloqueado'
            self.fecha_bloqueo = timezone.now()
            self.razon_bloqueo = "Bloqueado automáticamente por 5 intentos fallidos de login"

        self.save()

    def desbloquear(self, razon=None):
        """
        Desbloquea un usuario bloqueado.

        Args:
            razon (str): Razón del desbloqueo
        """
        self.estado = 'activo'
        self.intentos_login_fallidos = 0
        self.fecha_bloqueo = None
        self.razon_bloqueo = None
        if razon:
            self.notas_internas = f"{self.notas_internas or ''}\n[{timezone.now()}] Desbloqueado: {razon}"
        self.save()

    def bloquear(self, razon):
        """
        Bloquea un usuario.

        Args:
            razon (str): Razón del bloqueo
        """
        self.estado = 'bloqueado'
        self.fecha_bloqueo = timezone.now()
        self.razon_bloqueo = razon
        self.save()

    # =========================================================================
    # MÉTODOS DE PERMISOS
    # =========================================================================

    def tiene_permiso(self, permiso):
        """
        Verifica si el usuario tiene un permiso específico.

        Args:
            permiso (str): Nombre del permiso a verificar

        Returns:
            bool: True si tiene el permiso
        """
        if self.es_superusuario:
            return True

        # Mapeo de permisos
        permisos_map = {
            'crear_pacientes': self.puede_crear_pacientes,
            'editar_pacientes': self.puede_editar_pacientes,
            'eliminar_pacientes': self.puede_eliminar_pacientes,
            'ver_historial_completo': self.puede_ver_historial_completo,
            'registrar_controles': self.puede_registrar_controles,
            'solicitar_laboratorios': self.puede_solicitar_laboratorios,
            'registrar_resultados_lab': self.puede_registrar_resultados_lab,
            'agendar_citas': self.puede_agendar_citas,
            'generar_reportes': self.puede_generar_reportes,
        }

        return permisos_map.get(permiso, False)

    def asignar_permisos_por_rol(self):
        """Asigna permisos automáticos basados en el rol"""
        if self.rol == 'administrador':
            self.puede_crear_pacientes = True
            self.puede_editar_pacientes = True
            self.puede_eliminar_pacientes = True
            self.puede_ver_historial_completo = True
            self.puede_registrar_controles = True
            self.puede_solicitar_laboratorios = True
            self.puede_registrar_resultados_lab = True
            self.puede_agendar_citas = True
            self.puede_generar_reportes = True
            self.es_superusuario = True

        elif self.rol == 'medico':
            self.puede_crear_pacientes = True
            self.puede_editar_pacientes = True
            self.puede_eliminar_pacientes = False
            self.puede_ver_historial_completo = True
            self.puede_registrar_controles = True
            self.puede_solicitar_laboratorios = True
            self.puede_registrar_resultados_lab = False
            self.puede_agendar_citas = True
            self.puede_generar_reportes = True

        elif self.rol == 'enfermero':
            self.puede_crear_pacientes = True
            self.puede_editar_pacientes = True
            self.puede_eliminar_pacientes = False
            self.puede_ver_historial_completo = True
            self.puede_registrar_controles = True
            self.puede_solicitar_laboratorios = False
            self.puede_registrar_resultados_lab = False
            self.puede_agendar_citas = True
            self.puede_generar_reportes = False

        elif self.rol == 'doctor_laboratorio':
            self.puede_crear_pacientes = False
            self.puede_editar_pacientes = False
            self.puede_eliminar_pacientes = False
            self.puede_ver_historial_completo = False
            self.puede_registrar_controles = False
            self.puede_solicitar_laboratorios = False
            self.puede_registrar_resultados_lab = True
            self.puede_agendar_citas = False
            self.puede_generar_reportes = True

        elif self.rol == 'paciente':
            # Pacientes no tienen permisos administrativos
            self.puede_crear_pacientes = False
            self.puede_editar_pacientes = False
            self.puede_eliminar_pacientes = False
            self.puede_ver_historial_completo = False
            self.puede_registrar_controles = False
            self.puede_solicitar_laboratorios = False
            self.puede_registrar_resultados_lab = False
            self.puede_agendar_citas = True  # Pueden agendar sus propias citas
            self.puede_generar_reportes = False

    # =========================================================================
    # MÉTODOS DE MODELO
    # =========================================================================

    def save(self, *args, **kwargs):
        """Sobrescribir save para cálculos automáticos"""
        # Generar nombre completo
        self.nombre_completo = f"{self.nombre} {self.apellido_paterno}"
        if self.apellido_materno:
            self.nombre_completo += f" {self.apellido_materno}"

        # Normalizar email a minúsculas
        if self.email:
            self.email = self.email.lower()

        # Asignar permisos si es un usuario nuevo
        if not self.pk:
            self.asignar_permisos_por_rol()

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Soft delete - No eliminar realmente"""
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.activo = False
        self.estado = 'eliminado'
        self.save()

    def hard_delete(self):
        """Eliminación física del registro"""
        super().delete()

    def restaurar(self):
        """Restaurar un usuario eliminado lógicamente"""
        self.eliminado = False
        self.fecha_eliminacion = None
        self.eliminado_por = None
        self.razon_eliminacion = None
        self.activo = True
        self.estado = 'activo'
        self.save()

    # =========================================================================
    # REPRESENTACIÓN
    # =========================================================================

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.get_rol_display()})"

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', rol='{self.rol}')>"


# =============================================================================
# MODELO: HISTORIAL DE SESIONES
# =============================================================================
class HistorialSesion(models.Model):
    """
    Modelo para rastrear todas las sesiones de usuario.
    Útil para auditoría y seguridad.
    """

    ACCIONES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_fallido', 'Login Fallido'),
        ('cambio_password', 'Cambio de Contraseña'),
        ('recuperacion_password', 'Recuperación de Contraseña'),
        ('sesion_expirada', 'Sesión Expirada'),
    )

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='sesiones',
        help_text="Usuario de la sesión"
    )

    accion = models.CharField(
        max_length=50,
        choices=ACCIONES,
        help_text="Tipo de acción realizada"
    )

    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de la acción"
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="Dirección IP"
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent del navegador"
    )

    dispositivo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Tipo de dispositivo (desktop, mobile, tablet)"
    )

    navegador = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Navegador utilizado"
    )

    sistema_operativo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Sistema operativo"
    )

    ubicacion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Ubicación geográfica aproximada"
    )

    exitoso = models.BooleanField(
        default=True,
        help_text="Indica si la acción fue exitosa"
    )

    razon_fallo = models.TextField(
        blank=True,
        null=True,
        help_text="Razón del fallo (si aplica)"
    )

    token_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ID del token JWT (para invalidar sesiones)"
    )

    duracion_sesion = models.DurationField(
        blank=True,
        null=True,
        help_text="Duración de la sesión (para logouts)"
    )

    class Meta:
        db_table = 'historial_sesiones'
        managed = False
        ordering = ['-fecha_hora']
        verbose_name = 'Historial de Sesión'
        verbose_name_plural = 'Historial de Sesiones'

        indexes = [
            models.Index(fields=['usuario', 'fecha_hora']),
            models.Index(fields=['accion']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.usuario.email} - {self.get_accion_display()} - {self.fecha_hora}"


# =============================================================================
# MODELO: TOKEN DE RECUPERACIÓN DE CONTRASEÑA
# =============================================================================
class TokenRecuperacion(models.Model):
    """
    Modelo para tokens de recuperación de contraseña.
    Los tokens expiran en 24 horas por seguridad.
    """

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_recuperacion',
        help_text="Usuario que solicita recuperación"
    )

    token = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Token único de recuperación"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del token"
    )

    fecha_expiracion = models.DateTimeField(
        help_text="Fecha de expiración del token (24 horas)"
    )

    usado = models.BooleanField(
        default=False,
        help_text="Indica si el token ya fue usado"
    )

    fecha_uso = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha en que se usó el token"
    )

    ip_solicitud = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP desde donde se solicitó"
    )

    ip_uso = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP desde donde se usó"
    )

    class Meta:
        db_table = 'tokens_recuperacion'
        managed = False
        ordering = ['-fecha_creacion']
        verbose_name = 'Token de Recuperación'
        verbose_name_plural = 'Tokens de Recuperación'

        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['usuario', 'usado']),
            models.Index(fields=['fecha_expiracion']),
        ]

    @classmethod
    def generar_token(cls, usuario, ip_address=None):
        """
        Genera un nuevo token de recuperación para un usuario.

        Args:
            usuario (Usuario): Usuario para el que se genera el token
            ip_address (str): IP desde donde se solicita

        Returns:
            TokenRecuperacion: Token generado
        """
        # Invalidar tokens anteriores no usados
        cls.objects.filter(
            usuario=usuario,
            usado=False
        ).update(usado=True)

        # Generar token aleatorio de 60 caracteres
        token_str = get_random_string(length=60)

        # Crear token con expiración de 24 horas
        token = cls.objects.create(
            usuario=usuario,
            token=token_str,
            fecha_expiracion=timezone.now() + timedelta(hours=24),
            ip_solicitud=ip_address
        )

        return token

    def esta_vigente(self):
        """Verifica si el token está vigente"""
        return (
            not self.usado and
            timezone.now() < self.fecha_expiracion
        )

    def marcar_como_usado(self, ip_address=None):
        """Marca el token como usado"""
        self.usado = True
        self.fecha_uso = timezone.now()
        self.ip_uso = ip_address
        self.save()

    def __str__(self):
        return f"Token para {self.usuario.email} - {'Vigente' if self.esta_vigente() else 'Expirado/Usado'}"


# =============================================================================
# MODELO: VERIFICACIÓN DE EMAIL
# =============================================================================
class TokenVerificacionEmail(models.Model):
    """
    Modelo para tokens de verificación de email.
    Los tokens expiran en 7 días.
    """

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_verificacion_email',
        help_text="Usuario que verifica email"
    )

    token = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Token único de verificación"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del token"
    )

    fecha_expiracion = models.DateTimeField(
        help_text="Fecha de expiración del token (7 días)"
    )

    verificado = models.BooleanField(
        default=False,
        help_text="Email verificado"
    )

    fecha_verificacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de verificación"
    )

    class Meta:
        db_table = 'tokens_verificacion_email'
        managed = False
        ordering = ['-fecha_creacion']
        verbose_name = 'Token de Verificación de Email'
        verbose_name_plural = 'Tokens de Verificación de Email'

    @classmethod
    def generar_token(cls, usuario):
        """Genera un nuevo token de verificación de email"""
        # Invalidar tokens anteriores no verificados
        cls.objects.filter(
            usuario=usuario,
            verificado=False
        ).delete()

        # Generar token aleatorio
        token_str = get_random_string(length=60)

        # Crear token con expiración de 7 días
        token = cls.objects.create(
            usuario=usuario,
            token=token_str,
            fecha_expiracion=timezone.now() + timedelta(days=7)
        )

        return token

    def esta_vigente(self):
        """Verifica si el token está vigente"""
        return (
            not self.verificado and
            timezone.now() < self.fecha_expiracion
        )

    def marcar_como_verificado(self):
        """Marca el email como verificado"""
        self.verificado = True
        self.fecha_verificacion = timezone.now()
        self.save()

        # Actualizar usuario
        self.usuario.email_verificado = True
        self.usuario.fecha_verificacion_email = timezone.now()
        self.usuario.save()

    def __str__(self):
        return f"Token verificación para {self.usuario.email}"


# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
