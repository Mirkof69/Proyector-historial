"""=============================================================================
MODELOS - SISTEMA DE CALCULADORAS MÉDICAS
=============================================================================
Modelos para calculadoras de riesgo obstétrico basadas en FMF
Adaptado para población de altura (La Paz, Bolivia - 3600-4000m)

FASE 1: Preeclampsia, Trisomías, Diabetes Gestacional
=============================================================================
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

# =============================================================================
# MODELO PRINCIPAL - CALCULADORA DE RIESGO
# =============================================================================


class CalculadoraRiesgo(models.Model):
    """Registro de cálculo de riesgo obstétrico"""

    TIPO_CALCULADORA = [
        ("preeclampsia", "Preeclampsia"),
        ("trisomias", "Trisomías (21, 18, 13)"),
        ("diabetes_gestacional", "Diabetes Gestacional"),
        ("sga_rciu", "Restricción Crecimiento (SGA/RCIU)"),
        ("parto_pretermino", "Parto Pretérmino"),
        ("macrosomia", "Macrosomía Fetal"),
        ("aborto", "Aborto Espontáneo"),
        ("obito", "Óbito Fetal"),
        ("anemia_fetal", "Anemia Fetal"),
    ]

    CATEGORIA_RIESGO = [
        ("bajo", "Bajo Riesgo"),
        ("intermedio", "Riesgo Intermedio"),
        ("alto", "Alto Riesgo"),
        ("critico", "Riesgo Crítico"),
    ]

    ETNIA_CHOICES = [
        ("caucasica", "Caucásica"),
        ("afrocaribeña", "Afrocaribeña"),
        ("sudasiatica", "Sudasiática"),
        ("indigena", "Indígena"),
        ("mestiza", "Mestiza"),
        ("otra", "Otra"),
    ]

    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="calculadoras_riesgo",
        verbose_name="Paciente",
    )

    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calculadoras_riesgo",
        verbose_name="Embarazo Asociado",
    )

    # Tipo de calculadora
    tipo = models.CharField(
        max_length=50, choices=TIPO_CALCULADORA, verbose_name="Tipo de Calculadora",
    )

    # Edad gestacional al momento del cálculo
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(42)],
        verbose_name="Edad Gestacional (semanas)",
    )

    edad_gestacional_dias = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        default=0,
        verbose_name="Días adicionales",
    )

    # Datos maternos básicos
    edad_materna = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(60)],
        verbose_name="Edad Materna (años)",
    )

    peso_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("30.00")),
            MaxValueValidator(Decimal("200.00")),
        ],
        verbose_name="Peso (kg)",
    )

    talla_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("120.00")),
            MaxValueValidator(Decimal("220.00")),
        ],
        verbose_name="Talla (cm)",
    )

    imc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="IMC",
        help_text="Calculado automáticamente",
    )

    etnia = models.CharField(
        max_length=20, choices=ETNIA_CHOICES, default="mestiza", verbose_name="Etnia",
    )

    tabaquismo = models.BooleanField(default=False, verbose_name="Fumadora Activa")

    # Historia médica
    hta_cronica = models.BooleanField(
        default=False, verbose_name="Hipertensión Crónica",
    )

    diabetes_previa = models.BooleanField(
        default=False, verbose_name="Diabetes Pregestacional",
    )

    diabetes_tipo = models.CharField(
        max_length=10,
        choices=[("tipo1", "Tipo 1"), ("tipo2", "Tipo 2"), ("ninguna", "Ninguna")],
        default="ninguna",
        verbose_name="Tipo de Diabetes",
    )

    lupus = models.BooleanField(
        default=False, verbose_name="Lupus Eritematoso Sistémico",
    )

    sindrome_antifosfolipido = models.BooleanField(
        default=False, verbose_name="Síndrome Antifosfolípido",
    )

    # Historia obstétrica
    preeclampsia_previa = models.BooleanField(
        default=False, verbose_name="Preeclampsia Previa",
    )

    diabetes_gestacional_previa = models.BooleanField(
        default=False, verbose_name="Diabetes Gestacional Previa",
    )

    parto_pretermino_previo = models.BooleanField(
        default=False, verbose_name="Parto Pretérmino Previo",
    )

    macrosomia_previa = models.BooleanField(
        default=False, verbose_name="Macrosomía Previa (>4000g)",
    )

    historia_familiar_diabetes = models.BooleanField(
        default=False, verbose_name="Historia Familiar de Diabetes",
    )

    madre_con_preeclampsia = models.BooleanField(
        default=False, verbose_name="Madre con Preeclampsia",
    )

    paridad = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Paridad (gestas previas)",
    )

    intervalo_interembarazo_meses = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Intervalo Interembarazo (meses)",
    )

    metodo_concepcion = models.CharField(
        max_length=20,
        choices=[("espontaneo", "Espontáneo"), ("iv", "FIV"), ("otro", "Otro")],
        default="espontaneo",
        verbose_name="Método de Concepción",
    )

    # Resultado del cálculo
    riesgo_porcentaje = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True, verbose_name="Riesgo (%)",
    )

    riesgo_ratio = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Riesgo (ratio)",
        help_text="Ejemplo: 1:85",
    )

    categoria_riesgo = models.CharField(
        max_length=20,
        choices=CATEGORIA_RIESGO,
        null=True,
        blank=True,
        verbose_name="Categoría de Riesgo",
    )

    # Interpretación y recomendaciones
    interpretacion_clinica = models.TextField(
        null=True, blank=True, verbose_name="Interpretación Clínica",
    )

    recomendaciones = models.TextField(
        null=True, blank=True, verbose_name="Recomendaciones",
    )

    conducta_sugerida = models.TextField(
        null=True, blank=True, verbose_name="Conducta Sugerida",
    )

    # Metadata
    fecha_calculo = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Cálculo",
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Modificación",
    )

    calculado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="calculadoras_realizadas",
        verbose_name="Calculado Por",
    )

    # Trazabilidad
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculadoras_riesgo_creadas",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculadoras_riesgo_modificadas",
        verbose_name="Modificado por",
    )

    notas_adicionales = models.TextField(
        blank=True, verbose_name="Notas Adicionales del Profesional",
    )

    class Meta:
        """Meta"""
        db_table = "calculadoras_riesgo"
        verbose_name = "Calculadora de Riesgo"
        verbose_name_plural = "Calculadoras de Riesgo"
        ordering = ["-fecha_calculo"]
        indexes = [
            models.Index(fields=["paciente", "-fecha_calculo"]),
            models.Index(fields=["tipo", "-fecha_calculo"]),
            models.Index(fields=["categoria_riesgo"]),
        ]

    def save(self, *args, **kwargs):
        """Save"""
        # Calcular IMC automáticamente
        if self.peso_kg and self.talla_cm:
            talla_m = Decimal(str(self.talla_cm)) / Decimal("100")
            self.imc = round(self.peso_kg / (talla_m ** 2), 2)
        super().save(*args, **kwargs)

    @property
    def edad_gestacional_total_dias(self):
        """Edad gestacional en días totales"""
        return (self.edad_gestacional_semanas * 7) + self.edad_gestacional_dias

    @property
    def edad_gestacional_texto(self):
        """Formato legible de edad gestacional"""
        return f"{self.edad_gestacional_semanas}+{self.edad_gestacional_dias} semanas"

    def __str__(self):
        """Str"""
        return f"{getattr(self, 'get_tipo_display')()} - {self.paciente.nombre_completo} ({self.edad_gestacional_texto})"


# =============================================================================
# BIOMARCADORES - CONVERSIÓN MoM
# =============================================================================


class BiomarcadorMOM(models.Model):
    """Biomarcadores bioquímicos con conversión a MoM"""

    MARCADOR_CHOICES = [
        ("pappa", "PAPP-A"),
        ("bhcg", "β-hCG libre"),
        ("plg", "PLGF (Factor Crecimiento Placentario)"),
        ("sflt1", "sFlt-1 (Factor Antiangiogénico)"),
        ("pam", "PAM (Presión Arterial Media)"),
        ("utpi", "UtA-PI (Índice Pulsatilidad Arteria Uterina)"),
        ("afp", "AFP (Alfafetoproteína)"),
        ("bhcg_total", "β-hCG Total"),
        ("estriol", "Estriol Libre"),
        ("inhibina_a", "Inhibina A"),
    ]

    calculadora = models.ForeignKey(
        CalculadoraRiesgo,
        on_delete=models.CASCADE,
        related_name="biomarcadores",
        verbose_name="Calculadora",
    )

    marcador = models.CharField(
        max_length=20, choices=MARCADOR_CHOICES, verbose_name="Marcador",
    )

    # Valor crudo (del laboratorio)
    valor_crudo = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Valor Crudo",
    )

    unidad = models.CharField(
        max_length=50, verbose_name="Unidad", help_text="Ej: mIU/mL, ng/mL, mmHg",
    )

    # Conversión MoM
    mediana_esperada = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Mediana Esperada (ajustada)",
    )

    mediana_base = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Mediana Base (sin ajustes)",
    )

    mom_calculado = models.DecimalField(
        max_digits=6, decimal_places=3, verbose_name="MoM Calculado",
    )

    # Factores de corrección aplicados
    correccion_peso = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("1.000"),
        verbose_name="Factor Corrección Peso",
    )

    correccion_etnia = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("1.000"),
        verbose_name="Factor Corrección Etnia",
    )

    correccion_tabaco = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("1.000"),
        verbose_name="Factor Corrección Tabaco",
    )

    correccion_diabetes = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("1.000"),
        verbose_name="Factor Corrección Diabetes",
    )

    # Interpretación del MoM
    dentro_rango = models.BooleanField(
        default=True, verbose_name="Dentro del Rango Normal (0.8-1.2)",
    )

    interpretacion = models.CharField(
        max_length=100, blank=True, verbose_name="Interpretación",
    )

    fecha_medicion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Medición",
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Modificación",
    )

    # Trazabilidad
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="biomarcadores_mom_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="biomarcadores_mom_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "biomarcadores_mom"
        verbose_name = "Biomarcador MoM"
        verbose_name_plural = "Biomarcadores MoM"
        ordering = ["calculadora", "marcador"]
        unique_together = ["calculadora", "marcador"]

    def save(self, *args, **kwargs):
        """Save"""
        # Interpretar MoM
        if 0.8 <= float(self.mom_calculado) <= 1.2:
            self.dentro_rango = True
            self.interpretacion = "Normal"
        elif float(self.mom_calculado) < 0.5:
            self.dentro_rango = False
            self.interpretacion = "Muy bajo (<0.5 MoM) - Alto riesgo"
        elif float(self.mom_calculado) < 0.8:
            self.dentro_rango = False
            self.interpretacion = "Bajo (0.5-0.79 MoM) - Riesgo moderado"
        elif float(self.mom_calculado) > 1.5:
            self.dentro_rango = False
            self.interpretacion = "Muy alto (>1.5 MoM) - Alto riesgo"
        else:
            self.dentro_rango = False
            self.interpretacion = "Alto (1.21-1.5 MoM) - Riesgo moderado"

        super().save(*args, **kwargs)

    def __str__(self):
        """Str"""
        return f"{getattr(self, 'get_marcador_display')()}: {self.mom_calculado} MoM"


# =============================================================================
# MEDICIONES ECOGRÁFICAS
# =============================================================================


class MedicionEcografica(models.Model):
    """Mediciones ecográficas para cálculos de riesgo"""

    calculadora = models.ForeignKey(
        CalculadoraRiesgo,
        on_delete=models.CASCADE,
        related_name="mediciones_eco",
        verbose_name="Calculadora",
    )

    # Biometría fetal (1er trimestre)
    crl_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="CRL - Crown-Rump Length (mm)",
        help_text="Longitud céfalo-nalgas (9-14 semanas)",
    )

    nt_mm = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("10.00")),
        ],
        verbose_name="NT - Translucencia Nucal (mm)",
        help_text="Importante para trisomías (11-13+6 semanas)",
    )

    fcf_lpm = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(100), MaxValueValidator(220)],
        verbose_name="FCF - Frecuencia Cardíaca Fetal (lpm)",
    )

    # Biometría fetal (2º-3º trimestre)
    bpd_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="BPD - Diámetro Biparietal (mm)",
    )

    hc_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="HC - Circunferencia Cefálica (mm)",
    )

    ac_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="AC - Circunferencia Abdominal (mm)",
    )

    fl_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="FL - Longitud Fémur (mm)",
    )

    # Peso fetal estimado (calculado)
    efw_gramos = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="EFW - Peso Fetal Estimado (gramos)",
        help_text="Calculado por fórmula de Hadlock",
    )

    # Percentiles calculados
    nt_percentil = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        verbose_name="NT Percentil",
    )

    efw_percentil = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        verbose_name="EFW Percentil",
    )

    crl_percentil = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        verbose_name="CRL Percentil",
    )

    # Longitud cervical (para parto pretérmino)
    longitud_cervical_mm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Longitud Cervical (mm)",
        help_text="Medición transvaginal (20-26 semanas)",
    )

    fecha_medicion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Medición",
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Modificación",
    )

    # Trazabilidad
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mediciones_ecograficas_creadas",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mediciones_ecograficas_modificadas",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "mediciones_ecograficas"
        verbose_name = "Medición Ecográfica"
        verbose_name_plural = "Mediciones Ecográficas"
        ordering = ["-fecha_medicion"]

    def __str__(self):
        """Str"""
        return f"Ecografía - {self.calculadora.paciente.nombre_completo}"


# ── AlertaLaboratorio (5NF) ───────────────────────────────────────────────────

class AlertaLaboratorio(models.Model):
    """1 fila = 1 alerta atómica de laboratorio (5NF).

    Usa FK polimórfico (ContentType + object_id) para apuntar a cualquier
    modelo de laboratorio: Hemograma, Bioquimica, MarcadorEmbarazo.
    """

    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        verbose_name="Tipo de modelo",
        db_index=True,
    )
    object_id = models.PositiveBigIntegerField(
        verbose_name="ID del registro",
        db_index=True,
    )
    mensaje = models.TextField(verbose_name="Mensaje de alerta")
    severidad = models.CharField(
        max_length=10,
        choices=[
            ("CRITICO", "Crítico"),
            ("ALTO", "Alto"),
            ("MEDIO", "Medio"),
            ("BAJO", "Bajo"),
            ("INFO", "Informativo"),
        ],
        default="MEDIO",
        verbose_name="Severidad",
        db_index=True,
    )
    codigo = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Código de alerta",
        db_index=True,
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de generación",
        db_index=True,
    )
    procesada = models.BooleanField(
        default=False,
        verbose_name="Procesada",
        db_index=True,
    )
    procesada_por_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name="ID del usuario que procesó",
    )
    procesada_en = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de procesamiento",
    )

    def __str__(self):
        """Str representation"""
        return f"Alerta {self.pk}"

    class Meta:
        db_table = "calculadoras_alerta_laboratorio"
        verbose_name = "Alerta de Laboratorio"
        verbose_name_plural = "Alertas de Laboratorio"
        ordering = ["-fecha", "-severidad"]
