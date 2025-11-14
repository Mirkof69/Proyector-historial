from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente
from embarazos.models import Embarazo
from controles.models import ControlPrenatal
from usuarios.models import Usuario
from decimal import Decimal
import math
from datetime import datetime, timedelta


class TipoCalculadora(models.TextChoices):
    """Tipos de calculadoras disponibles"""
    
    # Obstétricas
    EDAD_GESTACIONAL = 'edad_gestacional', 'Edad Gestacional y FPP'
    IMC = 'imc', 'Índice de Masa Corporal'
    GANANCIA_PESO = 'ganancia_peso', 'Ganancia de Peso Gestacional'
    BISHOP = 'bishop', 'Puntaje de Bishop'
    PREECLAMPSIA = 'preeclampsia', 'Riesgo de Preeclampsia'
    DIABETES_GESTACIONAL = 'diabetes_gestacional', 'Tamizaje Diabetes Gestacional'
    ILA = 'ila', 'Índice de Líquido Amniótico'
    PESO_FETAL = 'peso_fetal', 'Estimación de Peso Fetal'
    APGAR = 'apgar', 'Puntaje Apgar'
    PERCENTIL_PESO = 'percentil_peso', 'Percentil de Peso Fetal'
    
    # Ginecológicas
    RMI_OVARIO = 'rmi_ovario', 'Riesgo de Cáncer de Ovario (RMI)'
    RIESGO_ENDOMETRIO = 'riesgo_endometrio', 'Riesgo de Cáncer de Endometrio'
    
    # Generales
    PAM = 'pam', 'Presión Arterial Media'
    SUPERFICIE_CORPORAL = 'superficie_corporal', 'Superficie Corporal'


class CalculoClinico(models.Model):
    """Registro de cálculos clínicos realizados"""
    
    tipo_calculo = models.CharField(
        max_length=50,
        choices=TipoCalculadora.choices,
        verbose_name='Tipo de Cálculo'
    )
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='calculos_clinicos',
        verbose_name='Paciente'
    )
    
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calculos',
        verbose_name='Embarazo Asociado'
    )
    
    control_prenatal = models.ForeignKey(
        ControlPrenatal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calculos',
        verbose_name='Control Prenatal Asociado'
    )
    
    # Datos de entrada (JSON)
    parametros_entrada = models.JSONField(
        verbose_name='Parámetros de Entrada',
        help_text='Datos utilizados para el cálculo'
    )
    
    # Resultados (JSON)
    resultados = models.JSONField(
        verbose_name='Resultados del Cálculo',
        help_text='Resultados obtenidos'
    )
    
    # Interpretación
    interpretacion = models.TextField(
        blank=True,
        verbose_name='Interpretación',
        help_text='Interpretación clínica de los resultados'
    )
    
    # Metadatos
    realizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calculos_realizados',
        verbose_name='Realizado Por'
    )
    
    fecha_calculo = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del Cálculo'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        db_table = 'calculos_clinicos'
        verbose_name = 'Cálculo Clínico'
        verbose_name_plural = 'Cálculos Clínicos'
        ordering = ['-fecha_calculo']
        indexes = [
            models.Index(fields=['paciente', '-fecha_calculo']),
            models.Index(fields=['tipo_calculo']),
            models.Index(fields=['embarazo']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_calculo_display()} - {self.paciente.nombre_completo} - {self.fecha_calculo.strftime('%d/%m/%Y')}"


class EdadGestacional(models.Model):
    """Modelo para cálculos de edad gestacional"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='edad_gestacional',
        verbose_name='Cálculo'
    )
    
    fum = models.DateField(
        verbose_name='Fecha de Última Menstruación'
    )
    
    fecha_calculo = models.DateField(
        verbose_name='Fecha del Cálculo'
    )
    
    # Resultados
    semanas = models.IntegerField(
        verbose_name='Semanas de Gestación'
    )
    
    dias = models.IntegerField(
        verbose_name='Días Adicionales'
    )
    
    fpp = models.DateField(
        verbose_name='Fecha Probable de Parto'
    )
    
    trimestre = models.IntegerField(
        verbose_name='Trimestre',
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )
    
    class Meta:
        db_table = 'calculos_edad_gestacional'
        verbose_name = 'Edad Gestacional'
        verbose_name_plural = 'Edades Gestacionales'
    
    def __str__(self):
        return f"{self.semanas}s {self.dias}d - FPP: {self.fpp.strftime('%d/%m/%Y')}"


class IndiceMasaCorporal(models.Model):
    """Modelo para cálculos de IMC"""
    
    CLASIFICACION_CHOICES = [
        ('bajo_peso', 'Bajo Peso'),
        ('normal', 'Normal'),
        ('sobrepeso', 'Sobrepeso'),
        ('obesidad_i', 'Obesidad Grado I'),
        ('obesidad_ii', 'Obesidad Grado II'),
        ('obesidad_iii', 'Obesidad Grado III'),
    ]
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='imc',
        verbose_name='Cálculo'
    )
    
    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Peso (kg)'
    )
    
    altura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Altura (cm)'
    )
    
    # Resultados
    imc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='IMC'
    )
    
    clasificacion = models.CharField(
    max_length=20,
    choices=CLASIFICACION_CHOICES,
    default='aeg',  # ✅ AGREGAR ESTA LÍNEA
    verbose_name='Clasificacion'
)
    
    ganancia_peso_recomendada_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Ganancia de Peso Mínima Recomendada (kg)'
    )
    
    ganancia_peso_recomendada_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Ganancia de Peso Máxima Recomendada (kg)'
    )
    
    class Meta:
        db_table = 'calculos_imc'
        verbose_name = 'Índice de Masa Corporal'
        verbose_name_plural = 'Índices de Masa Corporal'
    
    def __str__(self):
        return f"IMC: {self.imc} - {self.get_clasificacion_display()}"


class GananciaPeso(models.Model):
    """Modelo para seguimiento de ganancia de peso gestacional"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='ganancia_peso',
        verbose_name='Cálculo'
    )
    
    peso_pregestacional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Peso Pregestacional (kg)'
    )
    
    peso_actual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Peso Actual (kg)'
    )
    
    semanas_gestacion = models.IntegerField(
        verbose_name='Semanas de Gestación'
    )
    
    imc_pregestacional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='IMC Pregestacional'
    )
    
    # Resultados
    ganancia_peso_actual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Ganancia de Peso Actual (kg)'
    )
    
    ganancia_peso_esperada_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Ganancia Esperada Mínima (kg)'
    )
    
    ganancia_peso_esperada_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Ganancia Esperada Máxima (kg)'
    )
    
    adecuada = models.BooleanField(
        verbose_name='Ganancia Adecuada'
    )
    
    interpretacion = models.CharField(
        max_length=200,
        verbose_name='Interpretación'
    )
    
    class Meta:
        db_table = 'calculos_ganancia_peso'
        verbose_name = 'Ganancia de Peso'
        verbose_name_plural = 'Ganancias de Peso'
    
    def __str__(self):
        return f"Ganancia: {self.ganancia_peso_actual}kg - {self.interpretacion}"


class PuntajeBishop(models.Model):
    """Modelo para puntaje de Bishop (maduración cervical)"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='bishop',
        verbose_name='Cálculo'
    )
    
    # Parámetros
    dilatacion = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Dilatación Cervical (cm)'
    )
    
    borramiento = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Borramiento (%)'
    )
    
    ESTACION_CHOICES = [
        (-3, '-3'),
        (-2, '-2'),
        (-1, '-1'),
        (0, '0'),
        (1, '+1'),
        (2, '+2'),
    ]
    
    estacion = models.IntegerField(
        choices=ESTACION_CHOICES,
        verbose_name='Estación de la Presentación'
    )
    
    CONSISTENCIA_CHOICES = [
        (0, 'Firme'),
        (1, 'Media'),
        (2, 'Blanda'),
    ]
    
    consistencia = models.IntegerField(
        choices=CONSISTENCIA_CHOICES,
        verbose_name='Consistencia Cervical'
    )
    
    POSICION_CHOICES = [
        (0, 'Posterior'),
        (1, 'Media'),
        (2, 'Anterior'),
    ]
    
    posicion = models.IntegerField(
        choices=POSICION_CHOICES,
        verbose_name='Posición Cervical'
    )
    
    # Resultados
    puntaje_total = models.IntegerField(
        verbose_name='Puntaje Total de Bishop'
    )
    
    interpretacion = models.CharField(
        max_length=100,
        verbose_name='Interpretación'
    )
    
    class Meta:
        db_table = 'calculos_bishop'
        verbose_name = 'Puntaje de Bishop'
        verbose_name_plural = 'Puntajes de Bishop'
    
    def __str__(self):
        return f"Bishop: {self.puntaje_total} - {self.interpretacion}"


class RiesgoPreeclampsia(models.Model):
    """Modelo para cálculo de riesgo de preeclampsia"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='riesgo_preeclampsia',
        verbose_name='Cálculo'
    )
    
    # Factores de riesgo
    edad = models.IntegerField(
        verbose_name='Edad (años)'
    )
    
    primiparidad = models.BooleanField(
        default=False,
        verbose_name='Primiparidad'
    )
    
    antecedente_preeclampsia = models.BooleanField(
        default=False,
        verbose_name='Antecedente de Preeclampsia'
    )
    
    diabetes = models.BooleanField(
        default=False,
        verbose_name='Diabetes'
    )
    
    hipertension_cronica = models.BooleanField(
        default=False,
        verbose_name='Hipertensión Crónica'
    )
    
    obesidad = models.BooleanField(
        default=False,
        verbose_name='Obesidad (IMC ≥30)'
    )
    
    embarazo_multiple = models.BooleanField(
        default=False,
        verbose_name='Embarazo Múltiple'
    )
    
    enfermedad_renal = models.BooleanField(
        default=False,
        verbose_name='Enfermedad Renal Crónica'
    )
    
    enfermedad_autoinmune = models.BooleanField(
        default=False,
        verbose_name='Enfermedad Autoinmune'
    )
    
    # Resultados
    RIESGO_CHOICES = [
        ('bajo', 'Bajo Riesgo'),
        ('moderado', 'Riesgo Moderado'),
        ('alto', 'Alto Riesgo'),
    ]
    
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=RIESGO_CHOICES,
        verbose_name='Nivel de Riesgo'
    )
    
    recomienda_aspirina = models.BooleanField(
        default=False,
        verbose_name='Recomienda Aspirina Profiláctica'
    )
    
    factores_riesgo_count = models.IntegerField(
        default=0,
        verbose_name='Cantidad de Factores de Riesgo'
    )
    
    class Meta:
        db_table = 'calculos_riesgo_preeclampsia'
        verbose_name = 'Riesgo de Preeclampsia'
        verbose_name_plural = 'Riesgos de Preeclampsia'
    
    def __str__(self):
        return f"Riesgo: {self.get_nivel_riesgo_display()}"


class DiabetesGestacional(models.Model):
    """Modelo para tamizaje de diabetes gestacional"""
    
    TIPO_TEST_CHOICES = [
        ('ogtt_75g', 'OGTT 75g (2 horas)'),
        ('ogtt_100g', 'OGTT 100g (3 horas)'),
        ('glucosa_ayunas', 'Glucosa en Ayunas'),
    ]
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='diabetes_gestacional',
        verbose_name='Cálculo'
    )
    
    tipo_test = models.CharField(
        max_length=20,
        choices=TIPO_TEST_CHOICES,
        verbose_name='Tipo de Test'
    )
    
    semanas_gestacion = models.IntegerField(
        verbose_name='Semanas de Gestación'
    )
    
    # Valores de glucosa (mg/dL)
    glucosa_ayunas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Glucosa en Ayunas (mg/dL)'
    )
    
    glucosa_1h = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Glucosa 1 hora (mg/dL)'
    )
    
    glucosa_2h = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Glucosa 2 horas (mg/dL)'
    )
    
    glucosa_3h = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Glucosa 3 horas (mg/dL)'
    )
    
    # Resultados
    diagnostico = models.CharField(
        max_length=100,
        verbose_name='Diagnóstico'
    )
    
    valores_alterados = models.IntegerField(
        default=0,
        verbose_name='Valores Alterados'
    )
    
    requiere_seguimiento = models.BooleanField(
        default=False,
        verbose_name='Requiere Seguimiento'
    )
    
    class Meta:
        db_table = 'calculos_diabetes_gestacional'
        verbose_name = 'Diabetes Gestacional'
        verbose_name_plural = 'Diabetes Gestacionales'
    
    def __str__(self):
        return f"{self.diagnostico}"


class IndiceLiquidoAmniotico(models.Model):
    """Modelo para cálculo del Índice de Líquido Amniótico (ILA)"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='ila',
        verbose_name='Cálculo'
    )
    
    semanas_gestacion = models.IntegerField(
        verbose_name='Semanas de Gestación'
    )
    
    # Mediciones de los 4 cuadrantes (en mm)
    cuadrante_1 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Cuadrante Superior Derecho (mm)'
    )
    
    cuadrante_2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Cuadrante Superior Izquierdo (mm)'
    )
    
    cuadrante_3 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Cuadrante Inferior Derecho (mm)'
    )
    
    cuadrante_4 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Cuadrante Inferior Izquierdo (mm)'
    )
    
    # Resultados
    ila = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Índice de Líquido Amniótico (mm)'
    )
    
    INTERPRETACION_CHOICES = [
        ('oligohidramnios', 'Oligohidramnios'),
        ('normal', 'Normal'),
        ('polihidramnios', 'Polihidramnios'),
    ]
    
    interpretacion = models.CharField(
        max_length=20,
        choices=INTERPRETACION_CHOICES,
        verbose_name='Interpretación'
    )
    
    class Meta:
        db_table = 'calculos_ila'
        verbose_name = 'Índice de Líquido Amniótico'
        verbose_name_plural = 'Índices de Líquido Amniótico'
    
    def __str__(self):
        return f"ILA: {self.ila}mm - {self.interpretacion}"


class PesoFetal(models.Model):
    """Modelo para estimación de peso fetal (Fórmula de Hadlock)"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='peso_fetal',
        verbose_name='Cálculo'
    )
    
    semanas_gestacion = models.IntegerField(
        verbose_name='Semanas de Gestación'
    )
    
    # Biometrías fetales (en mm)
    dbp = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Diámetro Biparietal (mm)'
    )
    
    cc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Circunferencia Cefálica (mm)'
    )
    
    ca = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Circunferencia Abdominal (mm)'
    )
    
    lf = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Longitud del Fémur (mm)'
    )
    
    # Resultados
    peso_estimado = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Peso Fetal Estimado (gramos)'
    )
    
    percentil = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Percentil de Peso'
    )
    
    CLASIFICACION_CHOICES = [
        ('rciu', 'Restricción de Crecimiento Intrauterino'),
        ('peg', 'Pequeño para Edad Gestacional'),
        ('aeg', 'Adecuado para Edad Gestacional'),
        ('geg', 'Grande para Edad Gestacional'),
        ('macrosomia', 'Macrosomía'),
    ]
    
    clasificacion = models.CharField(
        max_length=20,
        choices=CLASIFICACION_CHOICES,
        verbose_name='Clasificación'
    )
    
    class Meta:
        db_table = 'calculos_peso_fetal'
        verbose_name = 'Peso Fetal'
        verbose_name_plural = 'Pesos Fetales'
    
    def __str__(self):
        return f"Peso Fetal: {self.peso_estimado}g - P{self.percentil}"


class PuntajeApgar(models.Model):
    """Modelo para puntaje de Apgar"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='apgar',
        verbose_name='Cálculo'
    )
    
    minuto = models.IntegerField(
        choices=[(1, '1 minuto'), (5, '5 minutos'), (10, '10 minutos')],
        verbose_name='Momento de Evaluación'
    )
    
    # Componentes (0-2 cada uno)
    frecuencia_cardiaca = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        verbose_name='Frecuencia Cardíaca'
    )
    
    esfuerzo_respiratorio = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        verbose_name='Esfuerzo Respiratorio'
    )
    
    tono_muscular = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        verbose_name='Tono Muscular'
    )
    
    irritabilidad_refleja = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        verbose_name='Irritabilidad Refleja'
    )
    
    coloracion = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        verbose_name='Coloración'
    )
    
    # Resultado
    puntaje_total = models.IntegerField(
        verbose_name='Puntaje Total'
    )
    
    INTERPRETACION_CHOICES = [
        ('critico', 'Crítico (0-3)'),
        ('depresion_moderada', 'Depresión Moderada (4-6)'),
        ('normal', 'Normal (7-10)'),
    ]
    
    interpretacion = models.CharField(
        max_length=30,
        choices=INTERPRETACION_CHOICES,
        verbose_name='Interpretación'
    )
    
    class Meta:
        db_table = 'calculos_apgar'
        verbose_name = 'Puntaje Apgar'
        verbose_name_plural = 'Puntajes Apgar'
    
    def __str__(self):
        return f"Apgar {self.minuto}': {self.puntaje_total} - {self.interpretacion}"


class RMIOvario(models.Model):
    """Modelo para cálculo de Riesgo de Malignidad de Ovario (RMI)"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='rmi_ovario',
        verbose_name='Cálculo'
    )
    
    # Estado menopáusico
    ESTADO_MENOPAUSIA_CHOICES = [
        ('premenopausia', 'Premenopausia'),
        ('postmenopausia', 'Postmenopausia'),
    ]
    
    estado_menopausia = models.CharField(
        max_length=20,
        choices=ESTADO_MENOPAUSIA_CHOICES,
        verbose_name='Estado Menopáusico'
    )
    
    # Hallazgos ecográficos (U)
    masa_multilocular = models.BooleanField(
        default=False,
        verbose_name='Masa Multilocular'
    )
    
    masa_solida = models.BooleanField(
        default=False,
        verbose_name='Áreas Sólidas'
    )
    
    masa_bilateral = models.BooleanField(
        default=False,
        verbose_name='Lesiones Bilaterales'
    )
    
    ascitis = models.BooleanField(
        default=False,
        verbose_name='Ascitis'
    )
    
    metastasis = models.BooleanField(
        default=False,
        verbose_name='Evidencia de Metástasis'
    )
    
    # CA-125 (U/ml)
    ca125 = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name='CA-125 (U/ml)'
    )
    
    # Resultados
    puntuacion_u = models.IntegerField(
        verbose_name='Puntuación Ecográfica (U)'
    )
    
    factor_m = models.IntegerField(
        verbose_name='Factor Menopáusico (M)'
    )
    
    rmi = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='RMI (U x M x CA-125)'
    )
    
    RIESGO_CHOICES = [
        ('bajo', 'Bajo Riesgo (<25)'),
        ('intermedio', 'Riesgo Intermedio (25-250)'),
        ('alto', 'Alto Riesgo (>250)'),
    ]
    
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=RIESGO_CHOICES,
        verbose_name='Nivel de Riesgo'
    )
    
    class Meta:
        db_table = 'calculos_rmi_ovario'
        verbose_name = 'RMI de Ovario'
        verbose_name_plural = 'RMI de Ovarios'
    
    def __str__(self):
        return f"RMI: {self.rmi} - {self.nivel_riesgo}"


class RiesgoEndometrio(models.Model):
    """Modelo para evaluación de riesgo de cáncer de endometrio"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='riesgo_endometrio',
        verbose_name='Cálculo'
    )
    
    edad = models.IntegerField(
        verbose_name='Edad (años)'
    )
    
    # Factores de riesgo
    obesidad = models.BooleanField(
        default=False,
        verbose_name='Obesidad (IMC ≥30)'
    )
    
    diabetes = models.BooleanField(
        default=False,
        verbose_name='Diabetes Mellitus'
    )
    
    hipertension = models.BooleanField(
        default=False,
        verbose_name='Hipertensión'
    )
    
    nuliparidad = models.BooleanField(
        default=False,
        verbose_name='Nuliparidad'
    )
    
    menarquia_temprana = models.BooleanField(
        default=False,
        verbose_name='Menarquia Temprana (<12 años)'
    )
    
    menopausia_tardia = models.BooleanField(
        default=False,
        verbose_name='Menopausia Tardía (>55 años)'
    )
    
    terapia_hormonal = models.BooleanField(
        default=False,
        verbose_name='Terapia con Estrógenos sin Oposición'
    )
    
    tamoxifeno = models.BooleanField(
        default=False,
        verbose_name='Uso de Tamoxifeno'
    )
    
    sindrome_ovario_poliquistico = models.BooleanField(
        default=False,
        verbose_name='Síndrome de Ovario Poliquístico'
    )
    
    antecedente_familiar = models.BooleanField(
        default=False,
        verbose_name='Antecedente Familiar de Cáncer Endometrial'
    )
    
    # Grosor endometrial (mm)
    grosor_endometrial = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Grosor Endometrial (mm)'
    )
    
    # Resultados
    factores_riesgo_count = models.IntegerField(
        default=0,
        verbose_name='Cantidad de Factores de Riesgo'
    )
    
    RIESGO_CHOICES = [
        ('bajo', 'Bajo Riesgo'),
        ('moderado', 'Riesgo Moderado'),
        ('alto', 'Alto Riesgo'),
    ]
    
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=RIESGO_CHOICES,
        verbose_name='Nivel de Riesgo'
    )
    
    requiere_biopsia = models.BooleanField(
        default=False,
        verbose_name='Requiere Biopsia Endometrial'
    )
    
    class Meta:
        db_table = 'calculos_riesgo_endometrio'
        verbose_name = 'Riesgo de Cáncer de Endometrio'
        verbose_name_plural = 'Riesgos de Cáncer de Endometrio'
    
    def __str__(self):
        return f"Riesgo: {self.get_nivel_riesgo_display()}"


class PresionArterialMedia(models.Model):
    """Modelo para cálculo de presión arterial media"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='pam',
        verbose_name='Cálculo'
    )
    
    presion_sistolica = models.IntegerField(
        verbose_name='Presión Sistólica (mmHg)'
    )
    
    presion_diastolica = models.IntegerField(
        verbose_name='Presión Diastólica (mmHg)'
    )
    
    # Resultado
    pam = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Presión Arterial Media (mmHg)'
    )
    
    INTERPRETACION_CHOICES = [
        ('hipotension', 'Hipotensión (<70 mmHg)'),
        ('normal', 'Normal (70-100 mmHg)'),
        ('elevada', 'Elevada (100-110 mmHg)'),
        ('hipertension', 'Hipertensión (>110 mmHg)'),
    ]
    
    interpretacion = models.CharField(
        max_length=20,
        choices=INTERPRETACION_CHOICES,
        verbose_name='Interpretación'
    )
    
    class Meta:
        db_table = 'calculos_pam'
        verbose_name = 'Presión Arterial Media'
        verbose_name_plural = 'Presiones Arteriales Medias'
    
    def __str__(self):
        return f"PAM: {self.pam} mmHg - {self.interpretacion}"


class SuperficieCorporal(models.Model):
    """Modelo para cálculo de superficie corporal (fórmula de Mosteller)"""
    
    calculo = models.OneToOneField(
        CalculoClinico,
        on_delete=models.CASCADE,
        related_name='superficie_corporal',
        verbose_name='Cálculo'
    )
    
    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Peso (kg)'
    )
    
    altura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Altura (cm)'
    )
    
    # Resultado
    superficie_corporal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Superficie Corporal (m²)'
    )
    
    class Meta:
        db_table = 'calculos_superficie_corporal'
        verbose_name = 'Superficie Corporal'
        verbose_name_plural = 'Superficies Corporales'
    
    def __str__(self):
        return f"SC: {self.superficie_corporal} m²"