# =============================================================================
# MODELOS DE PARTOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: partos
# Descripción: Modelos para gestión de registros de partos y nacimientos
# Versión: 1.0.0
# =============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class Parto(models.Model):
    """
    Modelo para registro de partos y nacimientos.

    Almacena información completa del parto:
    - Datos del parto (fecha, hora, tipo, duración)
    - Datos del recién nacido (APGAR, peso, talla, perímetros)
    - Complicaciones maternas y neonatales
    - Datos de la placenta
    - Procedimientos realizados
    """

    TIPOS_PARTO = (
        ('vaginal', 'Parto Vaginal'),
        ('cesarea', 'Cesárea'),
        ('forceps', 'Fórceps'),
        ('ventosa', 'Ventosa'),
    )

    PRESENTACIONES = (
        ('cefalica', 'Cefálica'),
        ('podalica', 'Podálica'),
        ('transversa', 'Transversa'),
    )

    TIPOS_ANESTESIA = (
        ('ninguna', 'Ninguna'),
        ('local', 'Local'),
        ('epidural', 'Epidural'),
        ('raquidea', 'Raquídea'),
        ('general', 'General'),
    )

    TIPOS_ALUMBRAMIENTO = (
        ('espontaneo', 'Espontáneo'),
        ('manual', 'Manual'),
        ('instrumental', 'Instrumental'),
    )

    SEXOS = (
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
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

    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        db_column='embarazo_id',
        related_name='partos',
        help_text="Embarazo que finalizó con este parto"
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        db_column='paciente_id',
        related_name='partos',
        help_text="Paciente que tuvo el parto"
    )

    # =========================================================================
    # DATOS DEL PARTO
    # =========================================================================

    fecha_hora_parto = models.DateTimeField(
        help_text="Fecha y hora exacta del parto"
    )

    tipo_parto = models.CharField(
        max_length=50,
        choices=TIPOS_PARTO,
        help_text="Tipo de parto realizado"
    )

    presentacion = models.CharField(
        max_length=50,
        choices=PRESENTACIONES,
        blank=True,
        null=True,
        help_text="Presentación fetal"
    )

    duracion_trabajo_parto_horas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('72.0'))],
        help_text="Duración del trabajo de parto en horas"
    )

    edad_gestacional_parto_semanas = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(20), MaxValueValidator(45)],
        help_text="Edad gestacional al momento del parto en semanas"
    )

    # =========================================================================
    # DATOS DEL RECIÉN NACIDO
    # =========================================================================

    # Scores APGAR
    apgar_1_min = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score APGAR al minuto (0-10)"
    )

    apgar_5_min = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score APGAR a los 5 minutos (0-10)"
    )

    # Antropometría del RN
    peso_rn_gramos = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(500), MaxValueValidator(6000)],
        help_text="Peso del recién nacido en gramos"
    )

    talla_rn_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('30.0')), MaxValueValidator(Decimal('70.0'))],
        help_text="Talla del recién nacido en centímetros"
    )

    perimetro_cefalico_rn_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('20.0')), MaxValueValidator(Decimal('50.0'))],
        help_text="Perímetro cefálico del RN en cm"
    )

    perimetro_toracico_rn_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('20.0')), MaxValueValidator(Decimal('50.0'))],
        help_text="Perímetro torácico del RN en cm"
    )

    sexo_rn = models.CharField(
        max_length=20,
        choices=SEXOS,
        blank=True,
        null=True,
        help_text="Sexo del recién nacido"
    )

    reanimacion_neonatal = models.BooleanField(
        default=False,
        help_text="¿Requirió reanimación neonatal?"
    )

    # =========================================================================
    # PROCEDIMIENTOS Y ANESTESIA
    # =========================================================================

    anestesia = models.CharField(
        max_length=50,
        choices=TIPOS_ANESTESIA,
        blank=True,
        null=True,
        help_text="Tipo de anestesia utilizada"
    )

    episiotomia = models.BooleanField(
        default=False,
        help_text="¿Se realizó episiotomía?"
    )

    desgarros = models.BooleanField(
        default=False,
        help_text="¿Hubo desgarros perineales?"
    )

    grado_desgarro = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('I', 'Grado I'),
            ('II', 'Grado II'),
            ('III', 'Grado III'),
            ('IV', 'Grado IV'),
        ],
        help_text="Grado del desgarro si lo hubo"
    )

    # =========================================================================
    # ALUMBRAMIENTO Y PLACENTA
    # =========================================================================

    alumbramiento = models.CharField(
        max_length=50,
        choices=TIPOS_ALUMBRAMIENTO,
        blank=True,
        null=True,
        help_text="Tipo de alumbramiento"
    )

    peso_placenta_gramos = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(100), MaxValueValidator(1500)],
        help_text="Peso de la placenta en gramos"
    )

    anomalias_placenta = models.TextField(
        blank=True,
        null=True,
        help_text="Anomalías de la placenta si las hubo"
    )

    # =========================================================================
    # COMPLICACIONES
    # =========================================================================

    complicaciones_maternas = models.TextField(
        blank=True,
        null=True,
        help_text="Complicaciones maternas durante o después del parto"
    )

    complicaciones_neonatales = models.TextField(
        blank=True,
        null=True,
        help_text="Complicaciones del recién nacido"
    )

    hemorragia_postparto = models.BooleanField(
        default=False,
        help_text="¿Hubo hemorragia postparto?"
    )

    sangrado_ml = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5000)],
        help_text="Cantidad de sangrado estimado en ml"
    )

    # =========================================================================
    # OBSERVACIONES Y PERSONAL
    # =========================================================================

    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones adicionales del parto"
    )

    medico_atencion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre del médico que atendió el parto"
    )

    medico = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='medico_id',
        related_name='partos_atendidos',
        null=True,
        blank=True,
        limit_choices_to={'rol': 'medico'}
    )

    lugar_parto = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Lugar donde se realizó el parto (hospital, clínica, etc.)"
    )

    # =========================================================================
    # CESÁREA (si aplica)
    # =========================================================================

    indicacion_cesarea = models.TextField(
        blank=True,
        null=True,
        help_text="Indicación médica de la cesárea"
    )

    tipo_incision = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        choices=[
            ('pfannenstiel', 'Pfannenstiel (transversa baja)'),
            ('vertical', 'Vertical'),
            ('joel_cohen', 'Joel-Cohen'),
        ],
        help_text="Tipo de incisión en cesárea"
    )

    # =========================================================================
    # AUDITORÍA
    # =========================================================================

    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='creado_por_id',
        related_name='partos_registrados',
        null=True,
        blank=True
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    modificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='modificado_por_id',
        related_name='partos_modificados',
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
        db_table = 'partos'
        managed = False
        ordering = ['-fecha_hora_parto']
        verbose_name = 'Parto'
        verbose_name_plural = 'Partos'
        indexes = [
            models.Index(fields=['embarazo']),
            models.Index(fields=['paciente']),
            models.Index(fields=['fecha_hora_parto']),
            models.Index(fields=['tipo_parto']),
        ]

    def __str__(self):
        return f"Parto {self.tipo_parto} - {self.paciente.get_nombre_completo()} - {self.fecha_hora_parto.date()}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

    # =========================================================================
    # MÉTODOS DE UTILIDAD
    # =========================================================================

    def clasificar_peso_rn(self):
        """Clasifica el peso del recién nacido"""
        if not self.peso_rn_gramos:
            return None

        if self.peso_rn_gramos < 2500:
            return "Bajo peso al nacer"
        elif self.peso_rn_gramos > 4000:
            return "Macrosomía"
        else:
            return "Peso normal"

    def evaluar_apgar(self):
        """Evalúa los scores APGAR"""
        resultados = {}

        if self.apgar_1_min is not None:
            if self.apgar_1_min >= 7:
                resultados['apgar_1'] = "Normal"
            elif self.apgar_1_min >= 4:
                resultados['apgar_1'] = "Depresión moderada"
            else:
                resultados['apgar_1'] = "Depresión severa"

        if self.apgar_5_min is not None:
            if self.apgar_5_min >= 7:
                resultados['apgar_5'] = "Normal"
            elif self.apgar_5_min >= 4:
                resultados['apgar_5'] = "Depresión moderada"
            else:
                resultados['apgar_5'] = "Depresión severa"

        return resultados

    def get_edad_gestacional_clasificacion(self):
        """Clasifica la edad gestacional al parto"""
        if not self.edad_gestacional_parto_semanas:
            return None

        if self.edad_gestacional_parto_semanas < 37:
            return "Prematuro"
        elif self.edad_gestacional_parto_semanas <= 42:
            return "A término"
        else:
            return "Postérmino"
