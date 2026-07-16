"""Models module."""
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario"""

    def create_user(
        self, email, nombre, apellido_paterno, password=None, **extra_fields,
    ):
        """Create user"""
        if not email:
            raise ValueError("El email es obligatorio")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, nombre, apellido_paterno, password=None, **extra_fields,
    ):
        """Create superuser"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "administrador")
        extra_fields.setdefault("activo", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email, nombre, apellido_paterno, password, **extra_fields,
        )


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Modelo personalizado de Usuario para el sistema de historias clínicas
    Compatible con Django Admin y autenticación JWT
    """

    ROLES = (
        ("medico", "Médico"),
        ("enfermera", "Enfermera"),
        ("laboratorista", "Laboratorista"),
        ("administrador", "Administrador"),
        ("recepcion", "Recepción"),
    )

    # Campos principales
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, verbose_name="Email")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido_paterno = models.CharField(max_length=100, verbose_name="Apellido Paterno")
    apellido_materno = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Apellido Materno",
    )

    # Rol y especialidad
    rol = models.CharField(max_length=20, choices=ROLES, verbose_name="Rol")
    especialidad = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Especialidad",
    )
    telefono = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono",
    )

    # Perfil
    foto = models.ImageField(
        upload_to="usuarios/fotos/",
        blank=True,
        null=True,
        verbose_name="Foto de Perfil",
        help_text="Imagen de perfil del usuario",
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Biografía o descripción del usuario",
    )

    # Estados y permisos
    activo = models.BooleanField(default=True, verbose_name="Activo")
    is_staff = models.BooleanField(default=False, verbose_name="Es staf")
    is_superuser = models.BooleanField(default=False, verbose_name="Es superusuario")

    # Relaciones de permisos (CORREGIDAS)
    groups = models.ManyToManyField(  # type: ignore[assignment]
        "auth.Group",
        verbose_name="grupos",
        blank=True,
        help_text="Los grupos a los que pertenece este usuario.",
        related_name="usuario_set",  # ← CAMBIADO
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(  # type: ignore[assignment]
        "auth.Permission",
        verbose_name="permisos de usuario",
        blank=True,
        help_text="Permisos específicos para este usuario.",
        related_name="usuario_set",  # ← CAMBIADO
        related_query_name="usuario",
    )

    # Fechas
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación",
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Última Modificación",
    )

    # MFA / 2FA (TOTP — Google Authenticator compatible)
    mfa_enabled = models.BooleanField(default=False, verbose_name="MFA Activado")
    mfa_obligatorio = models.BooleanField(
        default=False,
        verbose_name="MFA Obligatorio",
        help_text="True automáticamente para médicos y administradores — no puede desactivarse",
    )
    mfa_secret = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Secreto MFA",
        help_text="Clave TOTP base32 — nunca exponer en APIs públicas",
    )
    intentos_fallidos = models.PositiveSmallIntegerField(
        default=0, verbose_name="Intentos fallidos de login",
    )
    bloqueado_hasta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bloqueado hasta",
        help_text="Cuenta bloqueada después de 5 intentos fallidos",
    )
    ultimo_login_ip = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Última IP de acceso",
    )

    # Configuración del modelo
    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido_paterno"]

    def save(self, *args, **kwargs):
        """MFA obligatorio automático para roles críticos (médico/administrador).
        En DEBUG=True se omite para facilitar el desarrollo/demo.
        """
        from django.conf import settings
        if self.rol in ("medico", "administrador") and not settings.DEBUG:
            self.mfa_obligatorio = True
        super().save(*args, **kwargs)

    class Meta:
        """Meta"""
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        """Str"""
        return f"{self.nombre} {self.apellido_paterno} ({self.get_rol_display()})"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"

    @property
    def iniciales(self):
        """Retorna las iniciales del usuario"""
        try:
            iniciales = ""
            if self.nombre and len(self.nombre) > 0:
                iniciales += self.nombre[0]
            if self.apellido_paterno and len(self.apellido_paterno) > 0:
                iniciales += self.apellido_paterno[0]
            if self.apellido_materno and len(self.apellido_materno) > 0:
                iniciales += self.apellido_materno[0]
            return iniciales.upper() if iniciales else "U"
        except (TypeError, IndexError):
            return "U"

    @property
    def is_active(self):
        """Django espera is_active; lo mapeamos al campo 'activo' del modelo."""
        return getattr(self, "activo", True)

    def has_perm(self, perm, obj=None):
        """Has perm"""
        # activo/is_active es el campo real; AbstractBaseUser.is_active es solo un atributo de clase
        if not self.activo:
            return False
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        """Verifica si el usuario tiene permisos para ver un módulo"""
        return self.is_superuser or self.is_staff

    def get_full_name(self):
        """Requerido por Django Admin"""
        return self.nombre_completo

    def get_short_name(self):
        """Requerido por Django Admin"""
        return self.nombre


class HorarioAtencion(models.Model):
    """Modelo para gestionar los horarios de atención de médicos y enfermeros
    """

    DIAS_SEMANA = (
        ("lunes", "Lunes"),
        ("martes", "Martes"),
        ("miercoles", "Miércoles"),
        ("jueves", "Jueves"),
        ("viernes", "Viernes"),
        ("sabado", "Sábado"),
        ("domingo", "Domingo"),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="horarios_atencion",
        verbose_name="Usuario",
    )
    dia_semana = models.CharField(
        max_length=10, choices=DIAS_SEMANA, verbose_name="Día de la Semana",
    )
    hora_inicio = models.TimeField(verbose_name="Hora de Inicio")
    hora_fin = models.TimeField(verbose_name="Hora de Fin")
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Si está desactivado, no se mostrarán citas en este horario",
    )

    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "usuarios_horarios_atencion"
        verbose_name = "Horario de Atención"
        verbose_name_plural = "Horarios de Atención"
        ordering = ["dia_semana", "hora_inicio"]
        unique_together = [["usuario", "dia_semana", "hora_inicio"]]

    def __str__(self):
        """Str"""
        return f"{self.usuario.nombre_completo} - {self.get_dia_semana_display()}: {self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')}"

    def clean(self):
        """Validar que hora_fin sea mayor a hora_inicio"""
        from django.core.exceptions import ValidationError

        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError("La hora de fin debe ser mayor a la hora de inicio")
