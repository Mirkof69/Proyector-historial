# =============================================================================
# MODELOS DE ECOGRAFÍAS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: ecografias
# Descripción: Modelos para gestión de ecografías/ultrasonidos obstétricos
# Versión: 1.0.0
# =============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from embarazos.models import Embarazo


class Ecografia(models.Model):
    """
    Modelo para registro de ecografías obstétricas.

    Almacena todos los datos de ecografías/ultrasonidos realizados durante
    el embarazo, incluyendo biometría fetal, evaluación placentaria,
    líquido amniótico y hallazgos anatómicos.
    """

    TIPOS_ECOGRAFIA = (
        ('primer_trimestre', 'Primer Trimestre (11-14 semanas)'),
        ('segundo_trimestre', 'Segundo Trimestre (18-22 semanas)'),
        ('tercer_trimestre', 'Tercer Trimestre (28-32 semanas)'),
        ('genetica', 'Ecografía Genética'),
        ('doppler', 'Doppler'),
        ('otra', 'Otra'),
    )

    LOCALIZACION_PLACENTA = (
        ('anterior', 'Anterior'),
        ('posterior', 'Posterior'),
        ('fundica', 'Fúndica'),
        ('lateral_derecha', 'Lateral Derecha'),
        ('lateral_izquierda', 'Lateral Izquierda'),
        ('previa', 'Previa'),
    )

    GRADO_PLACENTARIO = (
        ('0', 'Grado 0'),
        ('I', 'Grado I'),
        ('II', 'Grado II'),
        ('III', 'Grado III'),
    )

    EVALUACION_ANATOMIA = (
        ('normal', 'Normal'),
        ('alterada', 'Alterada'),
        ('no_evaluada', 'No Evaluada'),
    )

    # =========================================================================
    # CAMPOS BÁSICOS
    # =========================================================================

    id = models.AutoField(primary_key=True)

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identificador único universal"
    )

    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        db_column='embarazo_id',
        related_name='ecografias',
        help_text="Embarazo al que pertenece esta ecografía"
    )

    fecha_ecografia = models.DateField(
        help_text="Fecha en que se realizó la ecografía"
    )

    tipo_ecografia = models.CharField(
        max_length=50,
        choices=TIPOS_ECOGRAFIA,
        help_text="Tipo de ecografía realizada"
    )

    # =========================================================================
    # EDAD GESTACIONAL
    # =========================================================================

    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(42)],
        help_text="Semanas de gestación al momento de la ecografía"
    )

    edad_gestacional_dias = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="Días adicionales de gestación (0-6)"
    )

    # =========================================================================
    # BIOMETRÍA FETAL
    # =========================================================================

    longitud_cefalocaudal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='LCC',
        help_text="Longitud céfalo-caudal en mm (primer trimestre)"
    )

    diametro_biparietal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='DBP',
        help_text="Diámetro biparietal en mm"
    )

    circunferencia_cefalica = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='CC',
        help_text="Circunferencia cefálica en mm"
    )

    circunferencia_abdominal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='CA',
        help_text="Circunferencia abdominal en mm"
    )

    longitud_femur = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='LF',
        help_text="Longitud del fémur en mm"
    )

    peso_fetal_estimado = models.DecimalField(
        max_digits=6,
        decimal_places=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('50')), MaxValueValidator(Decimal('6000'))],
        help_text="Peso fetal estimado en gramos"
    )

    # =========================================================================
    # PLACENTA Y LÍQUIDO AMNIÓTICO
    # =========================================================================

    localizacion_placenta = models.CharField(
        max_length=50,
        choices=LOCALIZACION_PLACENTA,
        blank=True,
        null=True,
        help_text="Localización de la placenta"
    )

    grado_placentario = models.CharField(
        max_length=10,
        choices=GRADO_PLACENTARIO,
        blank=True,
        null=True,
        help_text="Grado de maduración placentaria (Grannum)"
    )

    liquido_amniotico = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('normal', 'Normal'),
            ('oligohidramnios', 'Oligohidramnios (disminuido)'),
            ('polihidramnios', 'Polihidramnios (aumentado)'),
        ],
        help_text="Estado del líquido amniótico"
    )

    indice_liquido_amniotico = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name='ILA',
        help_text="Índice de líquido amniótico en cm (normal: 5-25 cm)"
    )

    # =========================================================================
    # EVALUACIÓN FETAL
    # =========================================================================

    numero_fetos = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Número de fetos observados"
    )

    latido_cardiaco_presente = models.BooleanField(
        default=True,
        help_text="¿Se observa latido cardíaco fetal?"
    )

    frecuencia_cardiaca_fetal = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(100), MaxValueValidator(200)],
        help_text="Frecuencia cardíaca fetal en latidos por minuto"
    )

    movimientos_fetales = models.BooleanField(
        default=True,
        help_text="¿Se observan movimientos fetales?"
    )

    evaluacion_anatomia = models.CharField(
        max_length=50,
        choices=EVALUACION_ANATOMIA,
        default='normal',
        help_text="Evaluación de la anatomía fetal"
    )

    # =========================================================================
    # HALLAZGOS Y OBSERVACIONES
    # =========================================================================

    hallazgos = models.TextField(
        blank=True,
        null=True,
        help_text="Hallazgos relevantes de la ecografía"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones adicionales del ecografista"
    )

    imagen = models.ImageField(
        upload_to='ecografias/%Y/%m/',
        blank=True,
        null=True,
        help_text="Imagen de la ecografía"
    )

    # =========================================================================
    # AUDITORÍA
    # =========================================================================

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    activo = models.BooleanField(
        default=True,
        help_text="Registro activo o eliminado (soft delete)"
    )

    fecha_eliminacion = models.DateTimeField(blank=True, null=True)

    # =========================================================================
    # META
    # =========================================================================

    class Meta:
        db_table = 'ecografias'
        managed = False  # Tabla ya existe en la base de datos
        ordering = ['-fecha_ecografia']
        verbose_name = 'Ecografía'
        verbose_name_plural = 'Ecografías'
        indexes = [
            models.Index(fields=['embarazo', 'fecha_ecografia']),
            models.Index(fields=['tipo_ecografia']),
        ]

    def __str__(self):
        return f"Ecografía {self.tipo_ecografia} - {self.fecha_ecografia}"

    def save(self, *args, **kwargs):
        """Validaciones antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Soft delete"""
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.save()

    def hard_delete(self):
        """Eliminación permanente"""
        super().delete()
