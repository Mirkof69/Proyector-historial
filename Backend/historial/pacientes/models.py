from django.db import models
import uuid

class Paciente(models.Model):
    GENEROS = (
        ('femenino', 'Femenino'),
        ('masculino', 'Masculino'),
        ('otro', 'Otro'),
    )
    
    ESTADOS_CIVILES = (
        ('soltera', 'Soltera'),
        ('casada', 'Casada'),
        ('divorciada', 'Divorciada'),
        ('viuda', 'Viuda'),
        ('union_libre', 'Unión Libre'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    id_clinico = models.CharField(
        max_length=50, 
        unique=True,
        error_messages={
            'unique': 'ID Clínico duplicado'
        }
    )
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=20, choices=GENEROS)
    cedula_identidad = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        error_messages={
            'unique': 'Cédula de Identidad duplicada'
        }
    )
    telefono_principal = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pacientes'
        managed = False
    
    def __str__(self):
        return f"{self.id_clinico} - {self.nombre} {self.apellido_paterno}"