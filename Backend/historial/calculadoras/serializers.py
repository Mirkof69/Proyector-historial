# =============================================================================
# SERIALIZERS DE CALCULADORAS OBSTÉTRICAS FMF
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: calculadoras
# Descripción: Serializers para validación de entradas y salidas de las
#              15 calculadoras FMF (Fetal Medicine Foundation).
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import serializers
from decimal import Decimal


# =============================================================================
# SERIALIZERS DE ENTRADA - PREDICCIÓN DE PREECLAMPSIA
# =============================================================================

class PreeclampsiaInputSerializer(serializers.Serializer):
    """
    Serializer para predicción de preeclampsia (FMF Algorithm).

    Parámetros requeridos:
    - Factores maternos
    - Presión arterial media (PAM)
    - Doppler de arterias uterinas (IP)
    - Biomarcadores opcionales (PLGF, PAPP-A)
    """
    # Factores maternos
    edad_materna = serializers.IntegerField(min_value=15, max_value=50,
                                            help_text="Edad de la madre (años)")
    peso = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=30, max_value=200,
                                    help_text="Peso materno (kg)")
    talla = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=130, max_value=220,
                                     help_text="Talla materna (cm)")
    etnia = serializers.ChoiceField(choices=['caucasica', 'afrocaribena', 'asiatica', 'otra'],
                                    help_text="Etnia materna")
    paridad = serializers.IntegerField(min_value=0, max_value=15,
                                       help_text="Número de partos previos")

    # Historia médica
    historia_preeclampsia = serializers.BooleanField(default=False)
    hipertension_cronica = serializers.BooleanField(default=False)
    diabetes = serializers.BooleanField(default=False)
    lupus = serializers.BooleanField(default=False)
    concepcion_asistida = serializers.BooleanField(default=False)

    # Biofísicos
    pam = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=60, max_value=150,
                                   help_text="Presión Arterial Media (mmHg)")
    ip_uterinas_promedio = serializers.DecimalField(max_digits=4, decimal_places=2, min_value=0, max_value=5,
                                                    help_text="IP promedio de arterias uterinas")
    eg_semanas = serializers.IntegerField(min_value=11, max_value=13,
                                          help_text="Edad gestacional en semanas")

    # Biomarcadores opcionales
    plgf = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True,
                                    help_text="PLGF en pg/mL")
    papp_a = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True,
                                      help_text="PAPP-A en MoM")


class PreeclampsiaOutputSerializer(serializers.Serializer):
    """Serializer para resultado de predicción de preeclampsia."""
    riesgo_preeclampsia_precoz = serializers.DecimalField(max_digits=5, decimal_places=2)
    clasificacion = serializers.CharField()
    recomendacion = serializers.CharField()
    requiere_aspirina = serializers.BooleanField()
    factores_riesgo = serializers.ListField(child=serializers.CharField())
    mom_pam = serializers.DecimalField(max_digits=4, decimal_places=2)
    mom_ip = serializers.DecimalField(max_digits=4, decimal_places=2)


# =============================================================================
# SERIALIZERS DE ENTRADA - SCREENING DE TRISOMÍAS
# =============================================================================

class ScreeningTrisomiasInputSerializer(serializers.Serializer):
    """
    Serializer para screening combinado de trisomías 21, 18 y 13.

    Screening de primer trimestre (11-13+6 semanas).
    """
    edad_materna = serializers.IntegerField(min_value=15, max_value=50)
    eg_semanas = serializers.IntegerField(min_value=11, max_value=14,
                                          help_text="Edad gestacional 11-13+6")
    nt_mm = serializers.DecimalField(max_digits=4, decimal_places=2, min_value=0.5, max_value=10,
                                     help_text="Translucencia nucal (mm)")
    papp_a_mom = serializers.DecimalField(max_digits=5, decimal_places=3, min_value=0.01, max_value=10,
                                          help_text="PAPP-A en MoM")
    beta_hcg_mom = serializers.DecimalField(max_digits=5, decimal_places=3, min_value=0.01, max_value=20,
                                            help_text="β-hCG libre en MoM")
    hueso_nasal_presente = serializers.BooleanField(default=True,
                                                    help_text="Presencia de hueso nasal")


class ScreeningTrisomiasOutputSerializer(serializers.Serializer):
    """Serializer para resultado de screening de trisomías."""
    trisomia_21 = serializers.DictField()
    trisomia_18 = serializers.DictField()
    trisomia_13 = serializers.DictField()
    percentil_nt = serializers.IntegerField()
    mom_nt = serializers.DecimalField(max_digits=4, decimal_places=2)


# =============================================================================
# SERIALIZERS DE ENTRADA - RESTRICCIÓN DE CRECIMIENTO (SGA)
# =============================================================================

class SGAInputSerializer(serializers.Serializer):
    """
    Serializer para predicción de restricción de crecimiento intrauterino (SGA).

    SGA: Small for Gestational Age (peso fetal < percentil 10).
    """
    edad_materna = serializers.IntegerField(min_value=15, max_value=50)
    peso_pregestacional = serializers.DecimalField(max_digits=5, decimal_places=2,
                                                   min_value=30, max_value=200)
    talla = serializers.DecimalField(max_digits=5, decimal_places=2,
                                     min_value=130, max_value=220)
    paridad = serializers.IntegerField(min_value=0, max_value=15)
    fuma = serializers.BooleanField(default=False)
    cigarrillos_dia = serializers.IntegerField(min_value=0, max_value=100, required=False)
    diabetes_previa = serializers.BooleanField(default=False)
    hipertension_cronica = serializers.BooleanField(default=False)
    sga_previo = serializers.BooleanField(default=False)
    eg_semanas = serializers.IntegerField(min_value=11, max_value=14)
    papp_a_mom = serializers.DecimalField(max_digits=5, decimal_places=3,
                                          required=False, allow_null=True)


class SGAOutputSerializer(serializers.Serializer):
    """Serializer para resultado de predicción SGA."""
    riesgo_sga = serializers.DecimalField(max_digits=5, decimal_places=2)
    clasificacion = serializers.CharField()
    recomendacion = serializers.CharField()
    factores_riesgo = serializers.ListField(child=serializers.CharField())


# =============================================================================
# SERIALIZERS DE ENTRADA - DIABETES GESTACIONAL
# =============================================================================

class DiabetesGestacionalInputSerializer(serializers.Serializer):
    """
    Serializer para predicción de diabetes gestacional.
    """
    edad_materna = serializers.IntegerField(min_value=15, max_value=50)
    peso = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=30, max_value=200)
    talla = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=130, max_value=220)
    etnia = serializers.ChoiceField(choices=['caucasica', 'afrocaribena', 'asiatica', 'otra'])
    diabetes_familiar = serializers.BooleanField(default=False,
                                                 help_text="Diabetes en familiar de 1er grado")
    diabetes_gestacional_previa = serializers.BooleanField(default=False)
    sop = serializers.BooleanField(default=False,
                                   help_text="Síndrome de ovario poliquístico")
    macrosomia_previa = serializers.BooleanField(default=False,
                                                 help_text="Hijo previo > 4.5 kg")


class DiabetesGestacionalOutputSerializer(serializers.Serializer):
    """Serializer para resultado de predicción diabetes gestacional."""
    riesgo_diabetes_gestacional = serializers.DecimalField(max_digits=5, decimal_places=2)
    clasificacion = serializers.CharField()
    recomendacion = serializers.CharField()
    requiere_curva_glucosa_temprana = serializers.BooleanField()


# =============================================================================
# SERIALIZERS DE ENTRADA - PARTO PRETÉRMINO
# =============================================================================

class PartoPreterminoInputSerializer(serializers.Serializer):
    """
    Serializer para predicción de parto pretérmino.
    """
    edad_materna = serializers.IntegerField(min_value=15, max_value=50)
    paridad = serializers.IntegerField(min_value=0, max_value=15)
    parto_pretermino_previo = serializers.BooleanField(default=False)
    eg_parto_previo = serializers.IntegerField(min_value=20, max_value=37,
                                               required=False, allow_null=True,
                                               help_text="EG del parto pretérmino previo")
    embarazo_multiple = serializers.BooleanField(default=False)
    longitud_cervical = serializers.DecimalField(max_digits=4, decimal_places=1,
                                                 min_value=0, max_value=60,
                                                 help_text="Longitud cervical (mm)")
    eg_medicion = serializers.IntegerField(min_value=16, max_value=24,
                                          help_text="EG al medir cuello")


class PartoPreterminoOutputSerializer(serializers.Serializer):
    """Serializer para resultado de predicción parto pretérmino."""
    riesgo_parto_pretermino_34 = serializers.DecimalField(max_digits=5, decimal_places=2)
    riesgo_parto_pretermino_37 = serializers.DecimalField(max_digits=5, decimal_places=2)
    clasificacion = serializers.CharField()
    recomendacion = serializers.CharField()
    requiere_progesterona = serializers.BooleanField()


# =============================================================================
# SERIALIZERS DE ENTRADA - PESO FETAL ESTIMADO
# =============================================================================

class PesoFetalInputSerializer(serializers.Serializer):
    """
    Serializer para estimación de peso fetal (fórmulas Hadlock).
    """
    dbp = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=10, max_value=120,
                                   help_text="Diámetro biparietal (mm)")
    cc = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=50, max_value=500,
                                  help_text="Circunferencia cefálica (mm)")
    ca = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=50, max_value=500,
                                  help_text="Circunferencia abdominal (mm)")
    lf = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=10, max_value=100,
                                  required=False, allow_null=True,
                                  help_text="Longitud del fémur (mm)")
    formula = serializers.ChoiceField(choices=['hadlock_iv', 'hadlock_iii', 'shepard'],
                                     default='hadlock_iv')


class PesoFetalOutputSerializer(serializers.Serializer):
    """Serializer para resultado de peso fetal estimado."""
    peso_estimado_g = serializers.IntegerField()
    formula_utilizada = serializers.CharField()
    percentil = serializers.IntegerField(required=False)
    clasificacion = serializers.CharField(required=False)


# =============================================================================
# SERIALIZERS DE ENTRADA - DOPPLER
# =============================================================================

class DopplerInputSerializer(serializers.Serializer):
    """
    Serializer para evaluación Doppler (arteria umbilical y cerebral media).
    """
    tipo = serializers.ChoiceField(choices=['umbilical', 'cerebral_media'],
                                   help_text="Tipo de Doppler")
    pico_sistolico = serializers.DecimalField(max_digits=5, decimal_places=2,
                                              min_value=0, max_value=300,
                                              help_text="Velocidad pico sistólica (cm/s)")
    velocidad_diastolica = serializers.DecimalField(max_digits=5, decimal_places=2,
                                                    min_value=0, max_value=200,
                                                    help_text="Velocidad telediastólica (cm/s)")
    eg_semanas = serializers.IntegerField(min_value=18, max_value=42)


class DopplerOutputSerializer(serializers.Serializer):
    """Serializer para resultado Doppler."""
    ip = serializers.DecimalField(max_digits=4, decimal_places=2)
    ir = serializers.DecimalField(max_digits=4, decimal_places=2)
    sd_ratio = serializers.DecimalField(max_digits=5, decimal_places=2)
    percentil = serializers.IntegerField(required=False)
    interpretacion = serializers.CharField()
    recomendacion = serializers.CharField()


# =============================================================================
# SERIALIZERS DE ENTRADA - TRANSLUCENCIA NUCAL
# =============================================================================

class TranslucenciaNucalInputSerializer(serializers.Serializer):
    """
    Serializer para evaluación de translucencia nucal.
    """
    nt_mm = serializers.DecimalField(max_digits=4, decimal_places=2,
                                     min_value=0.5, max_value=10,
                                     help_text="Translucencia nucal (mm)")
    eg_semanas = serializers.IntegerField(min_value=11, max_value=14)
    eg_dias = serializers.IntegerField(min_value=0, max_value=6, default=0)
    lcc_mm = serializers.DecimalField(max_digits=5, decimal_places=2,
                                      min_value=45, max_value=84,
                                      help_text="Longitud cráneo-caudal (mm)")


class TranslucenciaNucalOutputSerializer(serializers.Serializer):
    """Serializer para resultado translucencia nucal."""
    percentil = serializers.IntegerField()
    mom = serializers.DecimalField(max_digits=4, decimal_places=2)
    normal = serializers.BooleanField()
    interpretacion = serializers.CharField()
    requiere_estudio = serializers.BooleanField()


# =============================================================================
# SERIALIZERS DE ENTRADA - PAM E IP UTERINAS
# =============================================================================

class PAMInputSerializer(serializers.Serializer):
    """Serializer para cálculo de Presión Arterial Media."""
    pas = serializers.IntegerField(min_value=60, max_value=250,
                                   help_text="Presión arterial sistólica (mmHg)")
    pad = serializers.IntegerField(min_value=40, max_value=150,
                                   help_text="Presión arterial diastólica (mmHg)")
    eg_semanas = serializers.IntegerField(min_value=11, max_value=40)


class PAMOutputSerializer(serializers.Serializer):
    """Serializer para resultado PAM."""
    pam = serializers.DecimalField(max_digits=5, decimal_places=2)
    mom = serializers.DecimalField(max_digits=4, decimal_places=2)
    percentil = serializers.IntegerField()
    elevada = serializers.BooleanField()


class IPUterinasInputSerializer(serializers.Serializer):
    """Serializer para índice de pulsatilidad de arterias uterinas."""
    ip_derecha = serializers.DecimalField(max_digits=4, decimal_places=2,
                                          min_value=0, max_value=5)
    ip_izquierda = serializers.DecimalField(max_digits=4, decimal_places=2,
                                            min_value=0, max_value=5)
    eg_semanas = serializers.IntegerField(min_value=11, max_value=40)


class IPUterinasOutputSerializer(serializers.Serializer):
    """Serializer para resultado IP uterinas."""
    ip_promedio = serializers.DecimalField(max_digits=4, decimal_places=2)
    mom = serializers.DecimalField(max_digits=4, decimal_places=2)
    percentil = serializers.IntegerField()
    elevado = serializers.BooleanField()
    interpretacion = serializers.CharField()


# =============================================================================
# SERIALIZERS DE ENTRADA - BIOMARCADORES
# =============================================================================

class BiomarcadoresInputSerializer(serializers.Serializer):
    """
    Serializer para ratio sFLT-1/PlGF (predicción preeclampsia).
    """
    sflt1 = serializers.DecimalField(max_digits=8, decimal_places=2,
                                     min_value=0, max_value=100000,
                                     help_text="sFLT-1 en pg/mL")
    plgf = serializers.DecimalField(max_digits=8, decimal_places=2,
                                    min_value=0, max_value=10000,
                                    help_text="PlGF en pg/mL")
    eg_semanas = serializers.IntegerField(min_value=20, max_value=40)


class BiomarcadoresOutputSerializer(serializers.Serializer):
    """Serializer para resultado biomarcadores."""
    ratio_sflt_plgf = serializers.DecimalField(max_digits=6, decimal_places=2)
    interpretacion = serializers.CharField()
    riesgo_preeclampsia_corto_plazo = serializers.CharField()
    recomendacion = serializers.CharField()


# =============================================================================
# SERIALIZERS DE ENTRADA - ÍNDICE DE SHOCK
# =============================================================================

class IndiceShockInputSerializer(serializers.Serializer):
    """
    Serializer para cálculo de índice de shock materno.

    Índice de Shock = FC / PAS
    Normal: < 0.9
    Shock: > 1.0
    """
    frecuencia_cardiaca = serializers.IntegerField(min_value=40, max_value=200,
                                                   help_text="Frecuencia cardíaca (lpm)")
    presion_sistolica = serializers.IntegerField(min_value=60, max_value=250,
                                                 help_text="Presión sistólica (mmHg)")


class IndiceShockOutputSerializer(serializers.Serializer):
    """Serializer para resultado índice de shock."""
    indice_shock = serializers.DecimalField(max_digits=4, decimal_places=2)
    interpretacion = serializers.CharField()
    severidad = serializers.CharField()
    accion_requerida = serializers.CharField()


# =============================================================================
# SERIALIZERS DE ENTRADA - TEST NO ESTRESANTE
# =============================================================================

class TestNoEstresanteInputSerializer(serializers.Serializer):
    """
    Serializer para evaluación de Test No Estresante (NST).

    Evalúa frecuencia cardíaca fetal basal, variabilidad y aceleraciones.
    """
    fcf_basal = serializers.IntegerField(min_value=90, max_value=180,
                                        help_text="FCF basal (lpm)")
    aceleraciones = serializers.IntegerField(min_value=0, max_value=20,
                                            help_text="Número de aceleraciones en 20 min")
    desaceleraciones = serializers.IntegerField(min_value=0, max_value=20,
                                               help_text="Número de desaceleraciones")
    variabilidad = serializers.ChoiceField(choices=[
        ('ausente', 'Ausente (< 5 lpm)'),
        ('minima', 'Mínima (5-10 lpm)'),
        ('moderada', 'Moderada (10-25 lpm)'),
        ('marcada', 'Marcada (> 25 lpm)')
    ])
    duracion_minutos = serializers.IntegerField(min_value=20, max_value=60, default=20)
    eg_semanas = serializers.IntegerField(min_value=28, max_value=42)


class TestNoEstresanteOutputSerializer(serializers.Serializer):
    """Serializer para resultado NST."""
    resultado = serializers.CharField()
    reactivo = serializers.BooleanField()
    interpretacion = serializers.CharField()
    recomendacion = serializers.CharField()
    requiere_extension = serializers.BooleanField()


# =============================================================================
# SERIALIZERS DE ENTRADA - CRECIMIENTO FETAL
# =============================================================================

class CrecimientoFetalInputSerializer(serializers.Serializer):
    """
    Serializer para evaluación de curva de crecimiento fetal.

    Compara peso estimado con percentiles esperados para edad gestacional.
    """
    peso_estimado_g = serializers.IntegerField(min_value=100, max_value=6000,
                                               help_text="Peso fetal estimado (gramos)")
    eg_semanas = serializers.IntegerField(min_value=20, max_value=42)
    sexo_fetal = serializers.ChoiceField(choices=['masculino', 'femenino', 'desconocido'],
                                        default='desconocido')


class CrecimientoFetalOutputSerializer(serializers.Serializer):
    """Serializer para resultado evaluación crecimiento fetal."""
    percentil = serializers.IntegerField()
    clasificacion = serializers.CharField()
    peso_esperado_p50 = serializers.IntegerField()
    desviacion_porcentaje = serializers.DecimalField(max_digits=6, decimal_places=2)
    interpretacion = serializers.CharField()
    recomendacion = serializers.CharField()
