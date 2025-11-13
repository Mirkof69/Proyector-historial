from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from pacientes.models import Paciente
from usuarios.models import Usuario
from datetime import datetime, time, timedelta
from django.utils import timezone


class Disponibilidad(models.Model):
    """Horarios de disponibilidad de los médicos"""
    
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    medico = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='disponibilidades',
        limit_choices_to={'rol': 'medico'},
        verbose_name='Médico'
    )
    
    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA,
        verbose_name='Día de la Semana'
    )
    
    hora_inicio = models.TimeField(
        verbose_name='Hora de Inicio',
        help_text='Hora de inicio de atención'
    )
    
    hora_fin = models.TimeField(
        verbose_name='Hora de Fin',
        help_text='Hora de fin de atención'
    )
    
    duracion_cita = models.IntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(120)],
        verbose_name='Duración de Cita (minutos)',
        help_text='Duración de cada cita en minutos'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si esta disponibilidad está activa'
    )
    
    fecha_inicio_vigencia = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Inicio Vigencia',
        help_text='Fecha desde la cual aplica esta disponibilidad'
    )
    
    fecha_fin_vigencia = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Fin Vigencia',
        help_text='Fecha hasta la cual aplica esta disponibilidad'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'disponibilidades'
        verbose_name = 'Disponibilidad'
        verbose_name_plural = 'Disponibilidades'
        ordering = ['dia_semana', 'hora_inicio']
        indexes = [
            models.Index(fields=['medico', 'dia_semana']),
            models.Index(fields=['activo']),
        ]
        unique_together = ['medico', 'dia_semana', 'hora_inicio', 'hora_fin']
    
    def __str__(self):
        hora_inicio_str = self.hora_inicio.strftime('%H:%M') if self.hora_inicio else 'N/A'
        hora_fin_str = self.hora_fin.strftime('%H:%M') if self.hora_fin else 'N/A'
        return f"{self.medico.nombre} - {self.get_dia_semana_display()} {hora_inicio_str}-{hora_fin_str}"
    
    def clean(self):
        """Validaciones del modelo"""
        # Validar que hora_fin sea mayor que hora_inicio
        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError({
                    'hora_fin': 'La hora de fin debe ser mayor que la hora de inicio'
                })
        
        # Validar fechas de vigencia
        if self.fecha_inicio_vigencia and self.fecha_fin_vigencia:
            if self.fecha_inicio_vigencia > self.fecha_fin_vigencia:
                raise ValidationError({
                    'fecha_fin_vigencia': 'La fecha fin debe ser mayor que la fecha inicio'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def horas_disponibles(self):
        """Retorna lista de horarios disponibles en este día"""
        if not self.hora_inicio or not self.hora_fin:
            return []
        
        horarios = []
        hora_actual = datetime.combine(datetime.today(), self.hora_inicio)
        hora_limite = datetime.combine(datetime.today(), self.hora_fin)
        
        while hora_actual < hora_limite:
            horarios.append(hora_actual.time())
            hora_actual += timedelta(minutes=self.duracion_cita)
        
        return horarios
    
    @property
    def total_slots(self):
        """Calcula el total de slots disponibles"""
        return len(self.horas_disponibles)


class Cita(models.Model):
    """Citas médicas agendadas"""
    
    ESTADO_CHOICES = [
        ('agendada', 'Agendada'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No Asistió'),
    ]
    
    TIPO_CITA_CHOICES = [
        ('primera_vez', 'Primera Vez'),
        ('control', 'Control'),
        ('urgencia', 'Urgencia'),
        ('seguimiento', 'Seguimiento'),
    ]
    
    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name='Paciente'
    )
    
    medico = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='citas_medico',
        limit_choices_to={'rol': 'medico'},
        verbose_name='Médico'
    )
    
    # Datos de la cita
    fecha_cita = models.DateField(
        verbose_name='Fecha de la Cita'
    )
    
    hora_cita = models.TimeField(
        verbose_name='Hora de la Cita'
    )
    
    duracion = models.IntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(120)],
        verbose_name='Duración (minutos)'
    )
    
    tipo_cita = models.CharField(
        max_length=20,
        choices=TIPO_CITA_CHOICES,
        default='control',
        verbose_name='Tipo de Cita'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='agendada',
        verbose_name='Estado'
    )
    
    motivo = models.TextField(
        verbose_name='Motivo de Consulta',
        help_text='Motivo por el cual solicita la cita'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales de la cita'
    )
    
    # Seguimiento
    confirmada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas_confirmadas',
        verbose_name='Confirmada Por'
    )
    
    fecha_confirmacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Confirmación'
    )
    
    recordatorio_enviado = models.BooleanField(
        default=False,
        verbose_name='Recordatorio Enviado'
    )
    
    fecha_recordatorio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Recordatorio'
    )
    
    # Metadata
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas_creadas',
        verbose_name='Creado Por'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'citas'
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha_cita', 'hora_cita']
        indexes = [
            models.Index(fields=['paciente', '-fecha_cita']),
            models.Index(fields=['medico', 'fecha_cita']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_cita', 'hora_cita']),
        ]
    
    def __str__(self):
        fecha_str = self.fecha_cita.strftime('%d/%m/%Y') if self.fecha_cita else 'N/A'
        hora_str = self.hora_cita.strftime('%H:%M') if self.hora_cita else 'N/A'
        return f"{self.paciente.nombre_completo} - {self.medico.nombre} {self.medico.apellido_paterno} - {fecha_str} {hora_str}"
    
    def clean(self):
        """Validaciones del modelo"""
        # No permitir citas en el pasado
        if self.fecha_cita and self.hora_cita:
            fecha_hora_cita = timezone.make_aware(
                datetime.combine(self.fecha_cita, self.hora_cita)
            )
            if fecha_hora_cita < timezone.now():
                raise ValidationError({
                    'fecha_cita': 'No se pueden agendar citas en el pasado'
                })
        
        # Validar que no exista otra cita en el mismo horario para el médico
        if self.fecha_cita and self.hora_cita and self.medico:
            citas_existentes = Cita.objects.filter(
                medico=self.medico,
                fecha_cita=self.fecha_cita,
                hora_cita=self.hora_cita,
                estado__in=['agendada', 'confirmada']
            ).exclude(pk=self.pk)
            
            if citas_existentes.exists():
                raise ValidationError({
                    'hora_cita': 'El médico ya tiene una cita agendada en este horario'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def fecha_hora_cita(self):
        """Retorna datetime completo de la cita"""
        if not self.fecha_cita or not self.hora_cita:
            return None
        return datetime.combine(self.fecha_cita, self.hora_cita)
    
    @property
    def esta_pendiente(self):
        """Verifica si la cita está pendiente"""
        return self.estado in ['agendada', 'confirmada']
    
    @property
    def dias_hasta_cita(self):
        """Calcula días hasta la cita"""
        if self.fecha_cita:
            hoy = datetime.now().date()
            diferencia = self.fecha_cita - hoy
            return diferencia.days
        return None
    
    @property
    def requiere_recordatorio(self):
        """Verifica si requiere enviar recordatorio"""
        if self.esta_pendiente and not self.recordatorio_enviado:
            dias = self.dias_hasta_cita
            if dias is not None and 0 < dias <= 3:
                return True
        return False
    
    def confirmar(self, usuario=None):
        """Confirma la cita"""
        self.estado = 'confirmada'
        self.fecha_confirmacion = timezone.now()
        if usuario:
            self.confirmada_por = usuario
        self.save()
    
    def cancelar(self):
        """Cancela la cita"""
        self.estado = 'cancelada'
        self.save()
    
    def completar(self):
        """Marca la cita como completada"""
        self.estado = 'completada'
        self.save()
    
    def marcar_no_asistio(self):
        """Marca que el paciente no asistió"""
        self.estado = 'no_asistio'
        self.save()


class HistorialCita(models.Model):
    """Historial de cambios de estado de citas"""
    
    cita = models.ForeignKey(
        Cita,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Cita'
    )
    
    estado_anterior = models.CharField(
        max_length=20,
        choices=Cita.ESTADO_CHOICES,
        verbose_name='Estado Anterior'
    )
    
    estado_nuevo = models.CharField(
        max_length=20,
        choices=Cita.ESTADO_CHOICES,
        verbose_name='Estado Nuevo'
    )
    
    motivo_cambio = models.TextField(
        blank=True,
        verbose_name='Motivo del Cambio'
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario que Realizó el Cambio'
    )
    
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'historial_citas'
        verbose_name = 'Historial de Cita'
        verbose_name_plural = 'Historiales de Citas'
        ordering = ['-fecha_cambio']
    
    def __str__(self):
        return f"Cita {self.cita.id}: {self.estado_anterior} → {self.estado_nuevo}"