# =============================================================================
# MODELOS DE CITAS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: citas
# Descripción: Modelos para gestión de citas médicas
# Versión: 1.0.0
# =============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time
import uuid

from pacientes.models import Paciente
from usuarios.models import Usuario


class Cita(models.Model):
    """
    Modelo para gestión de citas médicas.

    Gestiona el sistema de agendamiento de citas para controles prenatales,
    ecografías, exámenes de laboratorio y otras consultas obstétricas.
    """

    TIPOS_CITA = (
        ('control_prenatal', 'Control Prenatal'),
        ('ecografia', 'Ecografía'),
        ('laboratorio', 'Laboratorio'),
        ('urgencia', 'Urgencia'),
        ('consulta', 'Consulta General'),
        ('otro', 'Otro'),
    )

    ESTADOS_CITA = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    )

    # =========================================================================
    # CAMPOS BÁSICOS
    # =========================================================================

    id = models.AutoField(primary_key=True)

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        db_column='paciente_id',
        related_name='citas',
        help_text="Paciente que solicita la cita"
    )

    fecha_cita = models.DateField(
        help_text="Fecha programada para la cita"
    )

    hora_cita = models.TimeField(
        help_text="Hora programada para la cita"
    )

    duracion_estimada = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(5), MaxValueValidator(240)],
        help_text="Duración estimada de la cita en minutos"
    )

    tipo_cita = models.CharField(
        max_length=50,
        choices=TIPOS_CITA,
        help_text="Tipo de cita médica"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CITA,
        default='pendiente',
        help_text="Estado actual de la cita"
    )

    # =========================================================================
    # INFORMACIÓN ADICIONAL
    # =========================================================================

    motivo = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo de la cita"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones adicionales"
    )

    # =========================================================================
    # MÉDICO Y SALA
    # =========================================================================

    medico = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='medico_id',
        related_name='citas_medico',
        null=True,
        blank=True,
        limit_choices_to={'rol': 'medico'},
        help_text="Médico asignado a la cita"
    )

    sala = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Sala o consultorio asignado"
    )

    # =========================================================================
    # RECORDATORIOS Y CONFIRMACIÓN
    # =========================================================================

    recordatorio_enviado = models.BooleanField(
        default=False,
        help_text="¿Se envió recordatorio al paciente?"
    )

    fecha_recordatorio = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha y hora en que se envió el recordatorio"
    )

    fecha_confirmacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha y hora de confirmación de la cita"
    )

    # =========================================================================
    # CANCELACIÓN
    # =========================================================================

    fecha_cancelacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha y hora de cancelación"
    )

    motivo_cancelacion = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo de la cancelación"
    )

    cancelado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='cancelado_por_id',
        related_name='citas_canceladas',
        null=True,
        blank=True,
        help_text="Usuario que canceló la cita"
    )

    # =========================================================================
    # AUDITORÍA
    # =========================================================================

    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='creado_por_id',
        related_name='citas_creadas',
        null=True,
        blank=True
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    modificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='modificado_por_id',
        related_name='citas_modificadas',
        null=True,
        blank=True
    )

    fecha_modificacion = models.DateTimeField(auto_now=True)

    activo = models.BooleanField(default=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)

    # =========================================================================
    # META
    # =========================================================================

    class Meta:
        db_table = 'citas'
        managed = False
        ordering = ['fecha_cita', 'hora_cita']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        indexes = [
            models.Index(fields=['paciente', 'fecha_cita']),
            models.Index(fields=['medico', 'fecha_cita']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo_cita']),
        ]

    def __str__(self):
        return f"Cita {self.tipo_cita} - {self.paciente.get_nombre_completo()} - {self.fecha_cita}"

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        errors = {}

        # Validar que la fecha de la cita no sea pasada
        if self.fecha_cita and self.fecha_cita < timezone.now().date():
            if not self.pk:  # Solo para citas nuevas
                errors['fecha_cita'] = "No se pueden crear citas con fechas pasadas"

        # Validar que si está confirmada, tenga médico asignado
        if self.estado == 'confirmada' and not self.medico:
            errors['medico'] = "Una cita confirmada debe tener un médico asignado"

        # Validar que si está cancelada, tenga motivo
        if self.estado == 'cancelada' and not self.motivo_cancelacion:
            errors['motivo_cancelacion'] = "Debe especificar el motivo de la cancelación"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Validaciones y lógica antes de guardar"""
        self.full_clean()

        # Si se confirma la cita, registrar fecha de confirmación
        if self.estado == 'confirmada' and not self.fecha_confirmacion:
            self.fecha_confirmacion = timezone.now()

        # Si se cancela la cita, registrar fecha de cancelación
        if self.estado == 'cancelada' and not self.fecha_cancelacion:
            self.fecha_cancelacion = timezone.now()

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Soft delete"""
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.save()

    def hard_delete(self):
        """Eliminación permanente"""
        super().delete()

    # =========================================================================
    # MÉTODOS DE UTILIDAD
    # =========================================================================

    def confirmar(self, usuario=None):
        """Confirmar la cita"""
        self.estado = 'confirmada'
        self.fecha_confirmacion = timezone.now()
        if usuario:
            self.modificado_por = usuario
        self.save()

    def cancelar(self, motivo, usuario=None):
        """Cancelar la cita"""
        self.estado = 'cancelada'
        self.motivo_cancelacion = motivo
        self.fecha_cancelacion = timezone.now()
        if usuario:
            self.cancelado_por = usuario
            self.modificado_por = usuario
        self.save()

    def completar(self, usuario=None):
        """Marcar cita como completada"""
        self.estado = 'completada'
        if usuario:
            self.modificado_por = usuario
        self.save()

    def es_pasada(self):
        """Verifica si la cita es una fecha pasada"""
        if self.fecha_cita < timezone.now().date():
            return True
        if self.fecha_cita == timezone.now().date():
            return self.hora_cita < timezone.now().time()
        return False

    def puede_modificarse(self):
        """Verifica si la cita puede ser modificada"""
        return self.estado in ['pendiente', 'confirmada'] and not self.es_pasada()

    def puede_cancelarse(self):
        """Verifica si la cita puede ser cancelada"""
        return self.estado in ['pendiente', 'confirmada'] and not self.es_pasada()
