"""=============================================================================
MODELOS COMPLETOS DE LABORATORIO GINECO-OBSTÉTRICO
=============================================================================
Protocolo integral adaptado a La Paz, Bolivia (alta altitud)
Incluye todos los parámetros, valores de referencia, MoM y alertas
=============================================================================
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

# =============================================================================
# 1. HEMATOLOGÍA COMPLETA
# =============================================================================


class Hemograma(models.Model):
    """Hemograma completo con valores adaptados a altura"""

    CLASIFICACION_CHOICES = [
        ("NORMAL", "Normal"),
        ("ANEMIA_LEVE", "Anemia Leve"),
        ("ANEMIA_MODERADA", "Anemia Moderada"),
        ("ANEMIA_SEVERA", "Anemia Severa"),
        ("LEUCOCITOSIS", "Leucocitosis"),
        ("LEUCOPENIA", "Leucopenia"),
        ("TROMBOCITOPENIA", "Trombocitopenia"),
        ("TROMBOCITOSIS", "Trombocitosis"),
    ]

    # Relaciones
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="hemogramas",
    )
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hemogramas",
    )
    medico_solicitante = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="hemogramas_solicitados",
    )

    # Fechas
    fecha_toma = models.DateTimeField()
    fecha_resultado = models.DateTimeField(auto_now_add=True)
    semanas_gestacion = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(42)], null=True, blank=True,
    )

    # Eritrograma
    hemoglobina = models.DecimalField(max_digits=4, decimal_places=1, help_text="g/dL")
    hematocrito = models.DecimalField(max_digits=4, decimal_places=1, help_text="%")
    eritrocitos = models.DecimalField(
        max_digits=4, decimal_places=2, help_text="mill/µL",
    )
    vcm = models.DecimalField(
        max_digits=5, decimal_places=1, help_text="fL", null=True, blank=True,
    )
    hcm = models.DecimalField(
        max_digits=4, decimal_places=1, help_text="pg", null=True, blank=True,
    )
    chcm = models.DecimalField(
        max_digits=4, decimal_places=1, help_text="g/dL", null=True, blank=True,
    )
    rdw = models.DecimalField(
        max_digits=4, decimal_places=1, help_text="%", null=True, blank=True,
    )

    # Leucograma
    leucocitos = models.IntegerField(help_text="/µL")
    neutrofilos = models.IntegerField(null=True, blank=True, help_text="/µL")
    linfocitos = models.IntegerField(null=True, blank=True, help_text="/µL")
    monocitos = models.IntegerField(null=True, blank=True, help_text="/µL")
    eosinofilos = models.IntegerField(null=True, blank=True, help_text="/µL")
    basofilos = models.IntegerField(null=True, blank=True, help_text="/µL")

    # Plaquetas
    plaquetas = models.IntegerField(help_text="/µL")
    vpm = models.DecimalField(
        max_digits=4, decimal_places=1, help_text="fL", null=True, blank=True,
    )

    # Clasificación automática
    clasificacion = models.CharField(max_length=30, choices=CLASIFICACION_CHOICES)
    es_critico = models.BooleanField(default=False)
    alertas = models.JSONField(default=list, blank=True)

    # Interpretación
    interpretacion_automatica = models.TextField(blank=True)
    observaciones_medicas = models.TextField(blank=True)

    # Auditoría
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "laboratorio_hemograma"
        ordering = ["-fecha_toma"]
        indexes = [
            models.Index(fields=["paciente", "-fecha_toma"]),
            models.Index(fields=["embarazo", "-fecha_toma"]),
        ]

    def clasificar_automaticamente(self):
        """Clasificación automática según valores y embarazo"""
        alertas = []
        es_embarazo = self.embarazo is not None

        # Hemoglobina
        if es_embarazo:
            if self.hemoglobina < 7:
                self.clasificacion = "ANEMIA_SEVERA"
                self.es_critico = True
                alertas.append(
                    "⚠️ CRÍTICO: Anemia severa (<7 g/dL) - Requiere transfusión",
                )
            elif self.hemoglobina < 10:
                self.clasificacion = "ANEMIA_MODERADA"
                alertas.append("Anemia moderada - Suplementación hierro urgente")
            elif self.hemoglobina < 10.5:
                self.clasificacion = "ANEMIA_LEVE"
                alertas.append("Anemia leve - Iniciar hierro oral")
        else:
            # Ajuste por altura (La Paz)
            limite_inferior = 12.0
            if self.hemoglobina < 7:
                self.clasificacion = "ANEMIA_SEVERA"
                self.es_critico = True
                alertas.append("⚠️ CRÍTICO: Anemia severa")
            elif self.hemoglobina < 10:
                self.clasificacion = "ANEMIA_MODERADA"
            elif self.hemoglobina < limite_inferior:
                self.clasificacion = "ANEMIA_LEVE"

        # Leucocitos
        if self.leucocitos > 30000:
            self.es_critico = True
            alertas.append("⚠️ CRÍTICO: Leucocitosis severa (>30,000) - Sepsis")
        elif self.leucocitos > 15000 and not es_embarazo:
            self.clasificacion = "LEUCOCITOSIS"
            alertas.append("Leucocitosis - Descartar infección")
        elif self.leucocitos < 4000:
            self.clasificacion = "LEUCOPENIA"
            alertas.append("Leucopenia - Descartar inmunosupresión")

        # Plaquetas
        if self.plaquetas < 50000:
            self.es_critico = True
            self.clasificacion = "TROMBOCITOPENIA"
            alertas.append("⚠️ CRÍTICO: Trombocitopenia severa (<50,000)")
        elif self.plaquetas < 100000:
            self.clasificacion = "TROMBOCITOPENIA"
            alertas.append("Trombocitopenia - Descartar HELLP/preeclampsia")
        elif self.plaquetas < 150000:
            alertas.append("Plaquetas bajas - Vigilancia")

        if not self.clasificacion or self.clasificacion == "":
            self.clasificacion = "NORMAL"

        self.alertas = alertas
        return alertas

    def generar_interpretacion(self):
        """Generación automática de interpretación médica"""
        interpretacion = []

        # Contexto
        if self.embarazo:
            interpretacion.append(
                f"Hemograma en embarazo de {self.semanas_gestacion} semanas.",
            )
        else:
            interpretacion.append("Hemograma en mujer no embarazada.")

        # Hallazgos
        if self.clasificacion != "NORMAL":
            interpretacion.append(f"Hallazgo: {self.get_clasificacion_display()}.")

        # Eritrograma
        if self.hemoglobina < 10.5 and self.embarazo:
            tipo_anemia = (
                "normocítica"
                if 80 <= float(self.vcm or 0) <= 100
                else "microcítica"
                if float(self.vcm or 0) < 80
                else "macrocítica"
            )
            interpretacion.append(
                f"Anemia {tipo_anemia} (Hb {self.hemoglobina} g/dL, VCM {self.vcm} fL).",
            )

        # Recomendaciones
        if self.es_critico:
            interpretacion.append("⚠️ ATENCIÓN INMEDIATA REQUERIDA.")

        self.interpretacion_automatica = " ".join(interpretacion)
        return self.interpretacion_automatica

    def save(self, *args, **kwargs):
        """Save"""
        self.clasificar_automaticamente()
        self.generar_interpretacion()
        super().save(*args, **kwargs)

    def __str__(self):
        """Str"""
        return f"Hemograma {self.paciente.nombre_completo} - {self.fecha_toma.strftime('%d/%m/%Y')}"


# =============================================================================
# 2. BIOQUÍMICA SÉRICA
# =============================================================================


class Bioquimica(models.Model):
    """Perfil bioquímico completo"""

    # Relaciones
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="bioquimicas",
    )
    embarazo = models.ForeignKey(
        Embarazo, on_delete=models.CASCADE, null=True, blank=True,
    )
    medico_solicitante = models.ForeignKey(Usuario, on_delete=models.PROTECT)

    # Fechas
    fecha_toma = models.DateTimeField()
    fecha_resultado = models.DateTimeField(auto_now_add=True)
    semanas_gestacion = models.IntegerField(null=True, blank=True)

    # Metabolismo glucosa
    glucosa_ayunas = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, help_text="mg/dL",
    )
    glucosa_postprandial = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, help_text="mg/dL",
    )
    hba1c = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, help_text="%",
    )

    # Función renal
    creatinina = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, help_text="mg/dL",
    )
    urea = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, help_text="mg/dL",
    )
    acido_urico = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, help_text="mg/dL",
    )

    # Función hepática
    got_ast = models.IntegerField(null=True, blank=True, help_text="U/L")
    gpt_alt = models.IntegerField(null=True, blank=True, help_text="U/L")
    bilirrubina_total = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, help_text="mg/dL",
    )
    bilirrubina_directa = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, help_text="mg/dL",
    )
    fosfatasa_alcalina = models.IntegerField(null=True, blank=True, help_text="U/L")
    albumina = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True, help_text="g/dL",
    )

    # Electrolitos
    sodio = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, help_text="mEq/L",
    )
    potasio = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True, help_text="mEq/L",
    )
    cloro = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, help_text="mEq/L",
    )
    calcio = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, help_text="mg/dL",
    )
    magnesio = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True, help_text="mg/dL",
    )

    # Lípidos
    colesterol_total = models.IntegerField(null=True, blank=True, help_text="mg/dL")
    ldl = models.IntegerField(null=True, blank=True, help_text="mg/dL")
    hdl = models.IntegerField(null=True, blank=True, help_text="mg/dL")
    trigliceridos = models.IntegerField(null=True, blank=True, help_text="mg/dL")

    # Otros
    proteinas_totales = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True, help_text="g/dL",
    )
    ldh = models.IntegerField(null=True, blank=True, help_text="U/L")

    # Clasificación
    clasificacion = models.CharField(max_length=50, blank=True)
    alertas = models.JSONField(default=list, blank=True)
    es_critico = models.BooleanField(default=False)
    interpretacion_automatica = models.TextField(blank=True)
    observaciones_medicas = models.TextField(blank=True)

    # Auditoría
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "laboratorio_bioquimica"
        ordering = ["-fecha_toma"]

    def clasificar_automaticamente(self):
        """Clasificación y alertas automáticas"""
        alertas = []

        # Glucosa
        if self.glucosa_ayunas:
            if self.glucosa_ayunas >= 126:
                alertas.append(" Diabetes Mellitus (glucosa ayunas ≥126 mg/dL)")
                self.es_critico = True
            elif self.glucosa_ayunas >= 100:
                alertas.append(" Prediabetes (glucosa 100-125 mg/dL)")
            elif self.embarazo and self.glucosa_ayunas >= 92:
                alertas.append(" Diabetes Gestacional (IADPSG: ayunas ≥92 mg/dL)")

        # Función renal
        if self.creatinina and self.creatinina > 1.2:
            alertas.append(
                f"⚠️ Creatinina elevada ({self.creatinina} mg/dL) - Evaluar función renal",
            )
            if self.creatinina > 2.0:
                self.es_critico = True

        # Función hepática (HELLP)
        if self.embarazo and self.got_ast and self.got_ast > 70:
            alertas.append("⚠️ Transaminasas elevadas - Descartar HELLP/preeclampsia")

        # Ácido úrico (preeclampsia)
        if self.embarazo and self.acido_urico and self.acido_urico > 6.0:
            alertas.append("Hiperuricemia - Compatible con preeclampsia")

        # Calcio
        if self.calcio:
            if self.calcio < 8.0:
                alertas.append("Hipocalcemia")
            elif self.calcio > 10.5:
                alertas.append("Hipercalcemia")

        self.alertas = alertas
        return alertas

    def save(self, *args, **kwargs):
        """Save"""
        self.clasificar_automaticamente()
        super().save(*args, **kwargs)

    def __str__(self):
        """Str"""
        return f"Bioquímica {self.paciente.nombre_completo} - {self.fecha_toma.strftime('%d/%m/%Y')}"


# =============================================================================
# 3. HORMONAS Y MARCADORES DE EMBARAZO
# =============================================================================


class MarcadorEmbarazo(models.Model):
    """β-hCG, PAPP-A, PlGF, sFlt-1 con cálculo MoM"""

    # Relaciones
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    embarazo = models.ForeignKey(Embarazo, on_delete=models.CASCADE)
    medico_solicitante = models.ForeignKey(Usuario, on_delete=models.PROTECT)

    # Fechas y contexto
    fecha_toma = models.DateTimeField()
    semanas_gestacion = models.IntegerField()
    dias_adicionales = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(6)],
    )

    # Marcadores
    beta_hcg = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="mIU/mL",
    )
    papp_a = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True, help_text="mIU/mL",
    )
    free_bhcg = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True, help_text="ng/mL",
    )
    plgf = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, help_text="pg/mL",
    )
    sflt1 = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, help_text="pg/mL",
    )

    # Valores MoM
    beta_hcg_mom = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True,
    )
    papp_a_mom = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True,
    )
    free_bhcg_mom = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True,
    )
    plgf_mom = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True,
    )
    sflt1_mom = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True,
    )

    # Ratio sFlt-1/PlGF
    ratio_sflt_plgf = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
    )

    # Clasificación
    clasificacion = models.CharField(max_length=50, blank=True)
    alertas = models.JSONField(default=list, blank=True)
    interpretacion_automatica = models.TextField(blank=True)

    # Auditoría
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta"""
        db_table = "laboratorio_marcador_embarazo"
        ordering = ["-fecha_toma"]

    def calcular_mom(self):
        """Cálculo MoM para todos los marcadores"""
        # Aquí iría la lógica completa de cálculo MoM
        # Por ahora placeholder - se implementa en el servicio

    def clasificar(self):
        """Clasificación según valores MoM"""
        alertas = []

        # PAPP-A bajo = riesgo PE/SGA
        if self.papp_a_mom and self.papp_a_mom < 0.5:
            alertas.append(" PAPP-A muy bajo (<0.5 MoM) - Alto riesgo PE/SGA")
        elif self.papp_a_mom and self.papp_a_mom < 0.8:
            alertas.append(" PAPP-A bajo (0.5-0.8 MoM) - Vigilancia")

        # PlGF bajo = riesgo PE
        if self.plgf_mom and self.plgf_mom < 0.5:
            alertas.append(" PlGF muy bajo - Riesgo preeclampsia")

        # Ratio sFlt-1/PlGF
        if self.ratio_sflt_plgf and self.ratio_sflt_plgf > 38:
            alertas.append(" Ratio sFlt-1/PlGF elevado (>38) - Preeclampsia probable")

        self.alertas = alertas
        return alertas

    def __str__(self):
        """Str"""
        return f"Marcadores {self.paciente.nombre_completo} - {self.semanas_gestacion}+{self.dias_adicionales} sem"


# Continúa en siguiente archivo...
