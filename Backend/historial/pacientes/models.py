"""
===========================================
MÓDULO: PACIENTES
Descripción: Gestión de pacientes del sistema de historial gineco-obstétrico
Autor: Sistema Historial Médico
Fecha: 2025
===========================================
"""

from django.db import models
from datetime import date
import uuid


class Paciente(models.Model):
    """
    Modelo de Paciente para el sistema de historial gineco-obstétrico.

    Almacena información demográfica, de contacto y estado del paciente.
    Cada paciente puede tener múltiples embarazos y controles asociados.
    """

    # ===========================================
    # CHOICES - Opciones predefinidas
    # ===========================================
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

    GRUPOS_SANGUINEOS = (
        ('A+', 'A Positivo'),
        ('A-', 'A Negativo'),
        ('B+', 'B Positivo'),
        ('B-', 'B Negativo'),
        ('AB+', 'AB Positivo'),
        ('AB-', 'AB Negativo'),
        ('O+', 'O Positivo'),
        ('O-', 'O Negativo'),
    )

    # ===========================================
    # CAMPOS DE IDENTIFICACIÓN
    # ===========================================
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identificador único universal del paciente"
    )

    id_clinico = models.CharField(
        max_length=50,
        unique=True,
        help_text="ID clínico del paciente (formato: HC-001)",
        error_messages={'unique': 'ID Clínico duplicado'}
    )

    cedula_identidad = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Cédula de identidad del paciente",
        error_messages={'unique': 'Cédula de Identidad duplicada'}
    )

    # ===========================================
    # DATOS PERSONALES
    # ===========================================
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre(s) del paciente"
    )

    apellido_paterno = models.CharField(
        max_length=100,
        help_text="Apellido paterno del paciente"
    )

    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Apellido materno del paciente (opcional)"
    )

    fecha_nacimiento = models.DateField(
        help_text="Fecha de nacimiento del paciente"
    )

    genero = models.CharField(
        max_length=20,
        choices=GENEROS,
        help_text="Género del paciente"
    )

    estado_civil = models.CharField(
        max_length=20,
        choices=ESTADOS_CIVILES,
        blank=True,
        null=True,
        help_text="Estado civil del paciente"
    )

    # ===========================================
    # DATOS CLÍNICOS ADICIONALES
    # ===========================================
    grupo_sanguineo = models.CharField(
        max_length=5,
        choices=GRUPOS_SANGUINEOS,
        blank=True,
        null=True,
        help_text="Grupo sanguíneo y factor RH"
    )

    # ===========================================
    # DATOS DE CONTACTO
    # ===========================================
    telefono_principal = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono principal de contacto"
    )

    telefono_alternativo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono alternativo de contacto"
    )

    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Correo electrónico del paciente"
    )

    direccion = models.TextField(
        blank=True,
        null=True,
        help_text="Dirección completa del paciente"
    )

    ciudad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Ciudad de residencia"
    )

    # ===========================================
    # CONTACTO DE EMERGENCIA
    # ===========================================
    contacto_emergencia_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre completo del contacto de emergencia"
    )

    contacto_emergencia_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono del contacto de emergencia"
    )

    contacto_emergencia_relacion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Relación con el contacto de emergencia (ej: esposo, madre)"
    )

    # ===========================================
    # CONTROL Y ESTADO
    # ===========================================
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el paciente está activo en el sistema"
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de registro del paciente"
    )

    fecha_ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones generales sobre el paciente"
    )

    # ===========================================
    # META Y MÉTODOS
    # ===========================================
    class Meta:
        db_table = 'pacientes'
        managed = False  # La tabla es administrada externamente
        ordering = ['-fecha_registro']
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

    def __str__(self):
        """Representación en string del paciente"""
        return f"{self.id_clinico} - {self.nombre_completo}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del paciente"""
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"

    @property
    def edad(self):
        """Calcula la edad actual del paciente en años"""
        if not self.fecha_nacimiento:
            return None
        hoy = date.today()
        edad = hoy.year - self.fecha_nacimiento.year
        # Ajustar si aún no ha cumplido años este año
        if hoy.month < self.fecha_nacimiento.month or \
           (hoy.month == self.fecha_nacimiento.month and hoy.day < self.fecha_nacimiento.day):
            edad -= 1
        return edad

    def soft_delete(self):
        """Desactivar paciente en lugar de eliminarlo (soft delete)"""
        self.activo = False
        self.save()

    def activar(self):
        """Reactivar un paciente desactivado"""
        self.activo = True
        self.save()