# =============================================================================
# MODELOS DE LABORATORIO
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: laboratorio
# Descripción: Modelos para gestión de exámenes de laboratorio
# Versión: 1.0.0
# =============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from embarazos.models import Embarazo


class ExamenLaboratorio(models.Model):
    """
    Modelo para registro de exámenes de laboratorio durante el embarazo.

    Incluye:
    - Hematología (hemoglobina, hematocrito, leucocitos, plaquetas)
    - Química sanguínea (glucosa, urea, creatinina, enzimas hepáticas)
    - Serología (VDRL, VIH, Hepatitis, Toxoplasmosis, Rubéola)
    - Uroanálisis completo
    - Cultivos y antibiogramas
    """

    TIPOS_EXAMEN = (
        ('hematologia', 'Hematología'),
        ('quimica', 'Química Sanguínea'),
        ('serologia', 'Serología'),
        ('orina', 'Examen de Orina'),
        ('cultivo', 'Cultivo'),
        ('otro', 'Otro'),
    )

    ESTADO_EXAMEN = (
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
    )

    RESULTADO_SEROLOGIA = (
        ('no_reactivo', 'No Reactivo'),
        ('reactivo', 'Reactivo'),
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
        related_name='examenes_laboratorio',
        help_text="Embarazo al que pertenece este examen"
    )

    fecha_examen = models.DateField(
        help_text="Fecha en que se tomó la muestra"
    )

    fecha_resultado = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de entrega de resultados"
    )

    tipo_examen = models.CharField(
        max_length=50,
        choices=TIPOS_EXAMEN,
        help_text="Tipo de examen de laboratorio"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_EXAMEN,
        default='pendiente'
    )

    laboratorio = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre del laboratorio que procesó la muestra"
    )

    # =========================================================================
    # HEMOGRAMA COMPLETO
    # =========================================================================

    hemoglobina = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('25.0'))],
        help_text="Hemoglobina en g/dL (normal embarazo: 11-14 g/dL)"
    )

    hematocrito = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('70.0'))],
        help_text="Hematocrito en % (normal embarazo: 33-44%)"
    )

    leucocitos = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100000)],
        help_text="Leucocitos en /mm³ (normal: 4000-11000)"
    )

    plaquetas = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000000)],
        help_text="Plaquetas en /mm³ (normal: 150000-400000)"
    )

    # =========================================================================
    # QUÍMICA SANGUÍNEA
    # =========================================================================

    glucosa = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('600.0'))],
        help_text="Glucosa en mg/dL (normal ayunas: <95 mg/dL)"
    )

    urea = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('300.0'))],
        help_text="Urea en mg/dL (normal: 15-45 mg/dL)"
    )

    creatinina = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('15.00'))],
        help_text="Creatinina en mg/dL (normal: 0.6-1.2 mg/dL)"
    )

    acido_urico = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('20.0'))],
        help_text="Ácido úrico en mg/dL (normal: 2.5-5.6 mg/dL)"
    )

    proteinas_totales = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Proteínas totales en g/dL (normal: 6.0-8.0 g/dL)"
    )

    albumina = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Albúmina en g/dL (normal: 3.5-5.0 g/dL)"
    )

    globulina = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Globulina en g/dL"
    )

    bilirrubina_total = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Bilirrubina total en mg/dL (normal: <1.2 mg/dL)"
    )

    tgo = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(2000)],
        verbose_name='TGO (AST)',
        help_text="Transaminasa Glutámico Oxalacética en U/L (normal: <40 U/L)"
    )

    tgp = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(2000)],
        verbose_name='TGP (ALT)',
        help_text="Transaminasa Glutámico Pirúvica en U/L (normal: <40 U/L)"
    )

    fosfatasa_alcalina = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(2000)],
        help_text="Fosfatasa alcalina en U/L (normal embarazo: hasta 450 U/L)"
    )

    # =========================================================================
    # GRUPO SANGUÍNEO Y SEROLOGÍA
    # =========================================================================

    grupo_sanguineo = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('AB', 'AB'),
            ('O', 'O'),
        ],
        help_text="Grupo sanguíneo ABO"
    )

    factor_rh = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('positivo', 'Positivo'),
            ('negativo', 'Negativo'),
        ],
        help_text="Factor Rh"
    )

    vdrl = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=RESULTADO_SEROLOGIA,
        verbose_name='VDRL',
        help_text="Prueba de sífilis (VDRL)"
    )

    vih = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=RESULTADO_SEROLOGIA,
        verbose_name='VIH',
        help_text="Prueba de VIH"
    )

    hepatitis_b = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=RESULTADO_SEROLOGIA,
        verbose_name='HBsAg',
        help_text="Antígeno de superficie de Hepatitis B"
    )

    toxoplasmosis_igg = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=RESULTADO_SEROLOGIA,
        verbose_name='Toxoplasmosis IgG',
        help_text="Anticuerpos IgG contra Toxoplasma"
    )

    toxoplasmosis_igm = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=RESULTADO_SEROLOGIA,
        verbose_name='Toxoplasmosis IgM',
        help_text="Anticuerpos IgM contra Toxoplasma (infección reciente)"
    )

    rubeola_igg = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=RESULTADO_SEROLOGIA,
        verbose_name='Rubéola IgG',
        help_text="Anticuerpos IgG contra Rubéola"
    )

    # =========================================================================
    # EXAMEN DE ORINA
    # =========================================================================

    orina_color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Color de la orina (amarillo, ámbar, etc.)"
    )

    orina_aspecto = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Aspecto de la orina (transparente, turbio, etc.)"
    )

    orina_ph = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('4.0')), MaxValueValidator(Decimal('9.0'))],
        verbose_name='pH',
        help_text="pH de la orina (normal: 5.0-7.0)"
    )

    orina_densidad = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('1.000')), MaxValueValidator(Decimal('1.060'))],
        help_text="Densidad de la orina (normal: 1.010-1.030)"
    )

    orina_glucosa = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('negativo', 'Negativo'),
            ('positivo', 'Positivo'),
        ],
        help_text="Glucosa en orina"
    )

    orina_proteinas = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('negativo', 'Negativo'),
            ('trazas', 'Trazas'),
            ('positivo_1', '+ (Positivo 1)'),
            ('positivo_2', '++ (Positivo 2)'),
            ('positivo_3', '+++ (Positivo 3)'),
        ],
        help_text="Proteínas en orina (proteinuria)"
    )

    orina_leucocitos = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Leucocitos por campo en orina (normal: 0-5)"
    )

    orina_hematies = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Hematíes por campo en orina (normal: 0-3)"
    )

    orina_celulas_epiteliales = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Células epiteliales en orina"
    )

    orina_bacterias = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('ausente', 'Ausente'),
            ('escaso', 'Escaso'),
            ('moderado', 'Moderado'),
            ('abundante', 'Abundante'),
        ],
        help_text="Presencia de bacterias en orina"
    )

    # =========================================================================
    # CULTIVOS
    # =========================================================================

    urocultivo = models.TextField(
        blank=True,
        null=True,
        help_text="Resultado de urocultivo"
    )

    antibiograma = models.TextField(
        blank=True,
        null=True,
        help_text="Resultado de antibiograma (sensibilidad antibiótica)"
    )

    # =========================================================================
    # OBSERVACIONES Y ARCHIVO
    # =========================================================================

    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones adicionales del examen"
    )

    archivo_resultado = models.FileField(
        upload_to='laboratorio/%Y/%m/',
        blank=True,
        null=True,
        help_text="Archivo PDF del resultado del laboratorio"
    )

    # =========================================================================
    # AUDITORÍA
    # =========================================================================

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    activo = models.BooleanField(default=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'examenes_laboratorio'
        managed = False
        ordering = ['-fecha_examen']
        verbose_name = 'Examen de Laboratorio'
        verbose_name_plural = 'Exámenes de Laboratorio'
        indexes = [
            models.Index(fields=['embarazo', 'fecha_examen']),
            models.Index(fields=['tipo_examen']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.tipo_examen} - {self.fecha_examen}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()
