from django.db import models
from django.core.validators import RegexValidator

class Paciente(models.Model):
    """Modelo de Paciente"""
    
    GENERO_CHOICES = (
        ('femenino', 'Femenino'),
        ('masculino', 'Masculino'),
        ('otro', 'Otro'),
    )
    
    # Identificación
    id_clinico = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='ID Clínico'
    )
    
    # Datos personales
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido_paterno = models.CharField(max_length=100, verbose_name='Apellido Paterno')
    apellido_materno = models.CharField(max_length=100, blank=True, null=True, verbose_name='Apellido Materno')
    fecha_nacimiento = models.DateField(verbose_name='Fecha de Nacimiento')
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, verbose_name='Género')
    
    # Documentos
    ci = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Cédula de Identidad'
    )
    
    # Contacto
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Correo Electrónico'
    )
    
    # Dirección
    direccion = models.TextField(blank=True, null=True, verbose_name='Dirección')
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ciudad')
    pais = models.CharField(max_length=100, default='Bolivia', verbose_name='País')
    
    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    
    # Observaciones
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    
    class Meta:
        db_table = 'pacientes'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['ci']),
            models.Index(fields=['id_clinico']),
            models.Index(fields=['fecha_nacimiento']),
        ]
    
    def save(self, *args, **kwargs):
        """Generar ID clínico automáticamente con UUID para garantizar unicidad"""
        if not self.id_clinico:
            import uuid
            # Usar UUID para garantizar unicidad absoluta
            unique_id = str(uuid.uuid4().hex[:8].upper())
            self.id_clinico = f'PAC-{unique_id}'
        super().save(*args, **kwargs)
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del paciente"""
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"
    
    @property
    def edad(self):
        """Calcula la edad del paciente"""
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.ci}"