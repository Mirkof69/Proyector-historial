from django.db import models
import uuid

class Usuario(models.Model):
    ROLES = (
        ('medico', 'Médico'),
        ('enfermero', 'Enfermero'),
        ('administrador', 'Administrador'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROLES)
    especialidad = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usuarios'
        managed = False
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.rol})"