from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario"""
    
    def create_user(self, email, nombre, apellido_paterno, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nombre, apellido_paterno, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'administrador')
        extra_fields.setdefault('activo', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, nombre, apellido_paterno, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo personalizado de Usuario para el sistema de historias clínicas
    Compatible con Django Admin y autenticación JWT
    """
    
    ROLES = (
        ('medico', 'Médico'),
        ('enfermero', 'Enfermero'),
        ('administrador', 'Administrador'),
    )
    
    # Campos principales
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, verbose_name='Email')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido_paterno = models.CharField(max_length=100, verbose_name='Apellido Paterno')
    apellido_materno = models.CharField(max_length=100, blank=True, null=True, verbose_name='Apellido Materno')
    
    # Rol y especialidad
    rol = models.CharField(max_length=20, choices=ROLES, verbose_name='Rol')
    especialidad = models.CharField(max_length=150, blank=True, null=True, verbose_name='Especialidad')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    
    # Estados y permisos
    activo = models.BooleanField(default=True, verbose_name='Activo')
    is_staff = models.BooleanField(default=False, verbose_name='Es staff')
    is_superuser = models.BooleanField(default=False, verbose_name='Es superusuario')
    
    # Relaciones de permisos (CORREGIDAS)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='grupos',
        blank=True,
        help_text='Los grupos a los que pertenece este usuario.',
        related_name='usuario_set',  # ← CAMBIADO
        related_query_name='usuario',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='permisos de usuario',
        blank=True,
        help_text='Permisos específicos para este usuario.',
        related_name='usuario_set',  # ← CAMBIADO
        related_query_name='usuario',
    )
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última Modificación')
    
    # Configuración del modelo
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido_paterno']
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
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
        iniciales = self.nombre[0] + self.apellido_paterno[0]
        if self.apellido_materno:
            iniciales += self.apellido_materno[0]
        return iniciales.upper()
    
    def has_perm(self, perm, obj=None):
        """Verifica si el usuario tiene un permiso específico"""
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        """Verifica si el usuario tiene permisos para ver un módulo"""
        return self.is_superuser or self.is_staff
    
    def get_full_name(self):
        """Requerido por Django Admin"""
        return self.nombre_completo
    
    def get_short_name(self):
        """Requerido por Django Admin"""
        return self.nombre