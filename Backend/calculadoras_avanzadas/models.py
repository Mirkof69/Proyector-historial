"""Models module."""
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from ecografias.models import Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class ScoreBishop(models.Model):
    """Score de Bishop para evaluación de maduración cervical"""

    # Relaciones
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, verbose_name="Paciente",
    )
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Embarazo",
    )
    medico = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Médico",
    )

    # Fecha del examen
    fecha_evaluacion = models.DateTimeField(verbose_name="Fecha de Evaluación")
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(20), MaxValueValidator(42)],
        verbose_name="Edad Gestacional (semanas)",
    )

    # Parámetros del Score de Bishop
    dilatacion_cervical = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Dilatación Cervical (cm)",
        help_text="0-10 cm",
    )

    borramiento_cervical = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Borramiento Cervical (%)",
        help_text="0-100%",
    )

    consistencia_cervical = models.CharField(
        max_length=20,
        choices=[
            ("dura", "Dura"),
            ("media", "Media"),
            ("blanda", "Blanda"),
        ],
        verbose_name="Consistencia del Cérvix",
    )

    posicion_cervical = models.CharField(
        max_length=20,
        choices=[
            ("posterior", "Posterior"),
            ("media", "Media"),
            ("anterior", "Anterior"),
        ],
        verbose_name="Posición del Cérvix",
    )

    estacion_fetal = models.CharField(
        max_length=10,
        choices=[
            ("-3", "-3"),
            ("-2", "-2"),
            ("-1", "-1"),
            ("0", "0"),
            ("+1", "+1"),
            ("+2", "+2"),
        ],
        verbose_name="Estación Fetal",
    )

    # Resultados calculados
    score_total = models.IntegerField(
        null=True, blank=True, verbose_name="Score Total de Bishop",
    )

    interpretacion = models.CharField(
        max_length=100, blank=True, verbose_name="Interpretación del Score",
    )

    probabilidad_parto_espontaneo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Probabilidad Parto Espontáneo (%)",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "score_bishop"
        ordering = ["-fecha_evaluacion"]
        verbose_name = "Score de Bishop"
        verbose_name_plural = "Scores de Bishop"

    def save(self, *args, **kwargs):
        """Save"""
        self.calcular_score()
        super().save(*args, **kwargs)

    def calcular_score(self):
        """Calcula el Score de Bishop automáticamente"""
        if not all(
            [
                self.dilatacion_cervical is not None,
                self.borramiento_cervical is not None,
                self.consistencia_cervical,
                self.posicion_cervical,
                self.estacion_fetal,
            ],
        ):
            return  # No calcular si faltan datos

        score = 0

        # Dilatación (0-3 puntos)
        if self.dilatacion_cervical == 0:
            score += 0
        elif self.dilatacion_cervical <= 2:
            score += 1
        elif self.dilatacion_cervical <= 4:
            score += 2
        else:  # >= 5
            score += 3

        # Borramiento (0-3 puntos)
        if self.borramiento_cervical <= 30:
            score += 0
        elif self.borramiento_cervical <= 50:
            score += 1
        elif self.borramiento_cervical <= 80:
            score += 2
        else:  # > 80
            score += 3

        # Consistencia (0-2 puntos)
        consistencia_puntos = {"dura": 0, "media": 1, "blanda": 2}
        score += consistencia_puntos.get(self.consistencia_cervical, 0)

        # Posición (0-2 puntos)
        posicion_puntos = {"posterior": 0, "media": 1, "anterior": 2}
        score += posicion_puntos.get(self.posicion_cervical, 0)

        # Estación (0-3 puntos)
        try:
            estacion_num = int(self.estacion_fetal)
            if estacion_num <= -3:
                score += 0
            elif estacion_num == -2:
                score += 1
            elif estacion_num == -1:
                score += 2
            else:  # >= 0
                score += 3
        except Exception:
            score += 0

        self.score_total = score

        # Interpretación
        if score <= 5:
            self.interpretacion = "Cérvix inmaduro - Inducción difícil"
            self.probabilidad_parto_espontaneo = Decimal("15.0")
        elif score <= 8:
            self.interpretacion = "Cérvix moderadamente maduro"
            self.probabilidad_parto_espontaneo = Decimal("50.0")
        else:  # >= 9
            self.interpretacion = "Cérvix maduro - Inducción favorable"
            self.probabilidad_parto_espontaneo = Decimal("85.0")

    def get_recomendacion_clinica(self):
        """Recomendación clínica basada en el score"""
        if self.score_total is None:
            return "Complete los datos para obtener recomendaciones"

        if self.score_total <= 5:
            return "Se recomienda maduración cervical antes de inducción"
        if self.score_total <= 8:
            return "Inducción con precaución y monitoreo estrecho"
        return "Condiciones favorables para inducción del parto"

    def __str__(self):
        """Str"""
        return f"Bishop Score {self.score_total or 'Pendiente'} - Paciente {self.paciente.nombre_completo} - {self.fecha_evaluacion.date()}"


class RiesgoPreeclampsia(models.Model):
    """Cálculo de riesgo de preeclampsia (algoritmo ASPRE)"""

    # Relaciones
    # Relaciones
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, verbose_name="Paciente",
    )
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Embarazo",
    )

    # Fecha de evaluación
    fecha_evaluacion = models.DateTimeField(verbose_name="Fecha de Evaluación")
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(11), MaxValueValidator(14)],
        verbose_name="Edad Gestacional (semanas)",
        help_text="Evaluación óptima: 11-14 semanas",
    )

    # Datos maternos
    edad_materna = models.IntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(50)],
        verbose_name="Edad Materna (años)",
    )

    peso_materno = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        verbose_name="Peso Materno (kg)",
    )

    talla_materna = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(140), MaxValueValidator(200)],
        verbose_name="Talla Materna (cm)",
    )

    # Antecedentes
    raza = models.CharField(
        max_length=20,
        choices=[
            ("caucasica", "Caucásica"),
            ("afroamericana", "Afroamericana"),
            ("asiatica", "Asiática"),
            ("hispana", "Hispana"),
            ("otra", "Otra"),
        ],
        verbose_name="Raza/Etnia",
    )

    paridad = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Paridad",
        help_text="Número de partos previos",
    )

    # Antecedentes médicos
    hipertension_cronica = models.BooleanField(
        default=False, verbose_name="Hipertensión Crónica",
    )

    diabetes_tipo1 = models.BooleanField(default=False, verbose_name="Diabetes Tipo 1")

    diabetes_tipo2 = models.BooleanField(default=False, verbose_name="Diabetes Tipo 2")

    lupus = models.BooleanField(
        default=False, verbose_name="Lupus Eritematoso Sistémico",
    )

    antecedente_preeclampsia = models.BooleanField(
        default=False, verbose_name="Antecedente de Preeclampsia",
    )

    # Embarazo actual
    embarazo_multiple = models.BooleanField(
        default=False, verbose_name="Embarazo Múltiple",
    )

    metodo_concepcion = models.CharField(
        max_length=30,
        choices=[
            ("natural", "Natural"),
            ("fertilizacion_in_vitro", "FIV"),
            ("inseminacion", "Inseminación"),
        ],
        default="natural",
        verbose_name="Método de Concepción",
    )

    # Biomarcadores
    presion_arterial_media = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Presión Arterial Media (mmHg)",
    )

    # Resultados
    riesgo_calculado = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Riesgo Calculado (1:X)",
    )

    riesgo_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Riesgo (%)",
    )

    clasificacion_riesgo = models.CharField(
        max_length=20, blank=True, verbose_name="Clasificación de Riesgo",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "riesgo_preeclampsia"
        ordering = ["-fecha_evaluacion"]
        verbose_name = "Riesgo de Preeclampsia"
        verbose_name_plural = "Riesgos de Preeclampsia"

    def save(self, *args, **kwargs):
        """Save"""
        self.calcular_riesgo()
        super().save(*args, **kwargs)

    def calcular_riesgo(self):
        """Calcula el riesgo de preeclampsia"""
        if not all([self.edad_materna, self.peso_materno, self.talla_materna]):
            return  # No calcular si faltan datos básicos

        # Algoritmo simplificado basado en factores de riesgo
        riesgo_base = 0.02  # 2% riesgo base

        # Factores maternos
        if self.edad_materna >= 35:
            riesgo_base *= 1.5

        if self.edad_materna >= 40:
            riesgo_base *= 2.0

        # IMC
        imc = float(self.peso_materno) / (float(self.talla_materna) / 100) ** 2
        if imc >= 30:
            riesgo_base *= 2.0
        elif imc >= 25:
            riesgo_base *= 1.3

        # Paridad
        if self.paridad == 0:  # Nulípara
            riesgo_base *= 1.8

        # Antecedentes médicos
        if self.hipertension_cronica:
            riesgo_base *= 3.0

        if self.diabetes_tipo1 or self.diabetes_tipo2:
            riesgo_base *= 2.5

        if self.lupus:
            riesgo_base *= 4.0

        if self.antecedente_preeclampsia:
            riesgo_base *= 5.0

        # Embarazo múltiple
        if self.embarazo_multiple:
            riesgo_base *= 3.0

        # FIV
        if self.metodo_concepcion == "fertilizacion_in_vitro":
            riesgo_base *= 1.5

        # Raza
        if self.raza == "afroamericana":
            riesgo_base *= 1.4

        # Limitar el riesgo máximo
        riesgo_base = min(riesgo_base, 0.5)

        self.riesgo_porcentaje = Decimal(str(round(riesgo_base * 100, 2)))
        self.riesgo_calculado = (
            Decimal(str(round(1 / riesgo_base, 0)))
            if riesgo_base > 0
            else Decimal(500)
        )

        # Clasificación
        if riesgo_base >= 0.1:  # >= 10%
            self.clasificacion_riesgo = "Alto Riesgo"
        elif riesgo_base >= 0.05:  # >= 5%
            self.clasificacion_riesgo = "Riesgo Intermedio"
        else:
            self.clasificacion_riesgo = "Bajo Riesgo"

    def get_recomendaciones(self):
        """Recomendaciones basadas en el riesgo"""
        if self.riesgo_porcentaje is None:
            return ["Complete los datos para obtener recomendaciones"]

        recomendaciones = []

        if float(self.riesgo_porcentaje) >= 10:
            recomendaciones.extend(
                [
                    "Aspirina 100mg diaria desde las 12 semanas",
                    "Control prenatal especializado",
                    "Monitoreo estrecho de presión arterial",
                    "Doppler uterino de seguimiento",
                ],
            )
        elif float(self.riesgo_porcentaje) >= 5:
            recomendaciones.extend(
                [
                    "Considerar aspirina 100mg diaria",
                    "Control prenatal con mayor frecuencia",
                    "Vigilancia de signos de preeclampsia",
                ],
            )
        else:
            recomendaciones.extend(
                ["Control prenatal rutinario", "Educación sobre signos de alarma"],
            )

        return recomendaciones

    def get_imc_calculado(self):
        """Calcula el IMC"""
        if self.peso_materno and self.talla_materna:
            imc = float(self.peso_materno) / (float(self.talla_materna) / 100) ** 2
            return f"{imc:.1f} kg/m²"
        return "Datos incompletos"

    def __str__(self):
        """Str"""
        return f"Riesgo Preeclampsia {self.riesgo_porcentaje or 'Pendiente'}% - Paciente {self.paciente.nombre_completo}"


class CrecimientoFetal(models.Model):
    """Curvas de crecimiento fetal y percentiles"""

    # Relaciones
    # Relaciones
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, verbose_name="Paciente",
    )
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Embarazo",
    )
    ecografia = models.ForeignKey(
        Ecografia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ecografía",
    )

    # Fecha de evaluación
    fecha_evaluacion = models.DateTimeField(verbose_name="Fecha de Evaluación")
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(16), MaxValueValidator(42)],
        verbose_name="Edad Gestacional (semanas)",
    )
    edad_gestacional_dias = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        default=0,
        verbose_name="Días adicionales",
    )

    # Biometría fetal
    diametro_biparietal = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="DBP (mm)",
    )

    circunferencia_cefalica = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, verbose_name="CC (mm)",
    )

    circunferencia_abdominal = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, verbose_name="CA (mm)",
    )

    longitud_femur = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="LF (mm)",
    )

    peso_fetal_estimado = models.IntegerField(
        null=True, blank=True, verbose_name="Peso Fetal Estimado (g)",
    )

    # Percentiles calculados
    percentil_dbp = models.IntegerField(
        null=True, blank=True, verbose_name="Percentil DBP",
    )
    percentil_cc = models.IntegerField(
        null=True, blank=True, verbose_name="Percentil CC",
    )
    percentil_ca = models.IntegerField(
        null=True, blank=True, verbose_name="Percentil CA",
    )
    percentil_lf = models.IntegerField(
        null=True, blank=True, verbose_name="Percentil LF",
    )
    percentil_peso = models.IntegerField(
        null=True, blank=True, verbose_name="Percentil Peso",
    )

    # Evaluación del crecimiento
    clasificacion_peso = models.CharField(
        max_length=30, blank=True, verbose_name="Clasificación del Peso",
    )

    restriccion_crecimiento = models.BooleanField(
        default=False, verbose_name="¿Restricción de Crecimiento",
    )

    macrosomia = models.BooleanField(default=False, verbose_name="¿Macrosomía")

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "crecimiento_fetal"
        ordering = ["-fecha_evaluacion"]
        verbose_name = "Evaluación de Crecimiento Fetal"
        verbose_name_plural = "Evaluaciones de Crecimiento Fetal"

    def save(self, *args, **kwargs):
        """Save"""
        self.calcular_percentiles()
        super().save(*args, **kwargs)

    def get_edad_gestacional_decimal(self):
        """Convierte la edad gestacional a decimal"""
        if self.edad_gestacional_semanas is None:
            return "Datos incompletos"
        if self.edad_gestacional_dias is None:
            return f"{self.edad_gestacional_semanas}.0 semanas"
        return f"{self.edad_gestacional_semanas + (self.edad_gestacional_dias / 7):.1f} semanas"

    def calcular_percentiles(self):
        """Calcula percentiles basados en curvas de crecimiento"""
        if not self.edad_gestacional_semanas:
            return  # No calcular si falta EG

        edad_decimal = self.edad_gestacional_semanas + (
            (self.edad_gestacional_dias or 0) / 7
        )

        # Percentiles aproximados (en un sistema real usarías tablas exactas)
        if self.peso_fetal_estimado:
            # Estimación simple de percentiles de peso
            if edad_decimal >= 20:
                peso_esperado = (
                    50 * (edad_decimal - 20) ** 2 + 300
                )  # Fórmula aproximada

                if self.peso_fetal_estimado < peso_esperado * 0.7:
                    self.percentil_peso = 5
                elif self.peso_fetal_estimado < peso_esperado * 0.85:
                    self.percentil_peso = 10
                elif self.peso_fetal_estimado < peso_esperado * 1.15:
                    self.percentil_peso = 50
                elif self.peso_fetal_estimado < peso_esperado * 1.3:
                    self.percentil_peso = 90
                else:
                    self.percentil_peso = 95

        # Clasificación
        if self.percentil_peso:
            if self.percentil_peso < 10:
                self.clasificacion_peso = "Pequeño para edad gestacional"
                self.restriccion_crecimiento = True
            elif self.percentil_peso > 90:
                self.clasificacion_peso = "Grande para edad gestacional"
                self.macrosomia = True
            else:
                self.clasificacion_peso = "Adecuado para edad gestacional"

    def get_recomendaciones(self):
        """Recomendaciones basadas en el crecimiento"""
        if not self.clasificacion_peso:
            return ["Complete los datos para obtener recomendaciones"]

        recomendaciones = []

        if self.restriccion_crecimiento:
            recomendaciones.extend(
                [
                    "Control de crecimiento en 2-3 semanas",
                    "Estudio Doppler materno-fetal",
                    "Evaluación de bienestar fetal",
                    "Considerar etiología de restricción",
                ],
            )
        elif self.macrosomia:
            recomendaciones.extend(
                [
                    "Evaluación de diabetes gestacional",
                    "Control de peso materno",
                    "Planificación de vía de parto",
                    "Vigilancia de complicaciones",
                ],
            )
        else:
            recomendaciones.append("Continuar controles rutinarios")

        return recomendaciones

    def __str__(self):
        """Str"""
        eg = f"{self.edad_gestacional_semanas}+{self.edad_gestacional_dias or 0}"
        return f"Crecimiento Fetal {eg} - P{self.percentil_peso or ''}"


class RiesgoCromosomico(models.Model):
    """Screening combinado del primer trimestre para riesgo cromosómico"""

    # Relaciones
    # Relaciones
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, verbose_name="Paciente",
    )
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Embarazo",
    )
    ecografia = models.ForeignKey(
        Ecografia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ecografía",
    )

    # Fecha de evaluación
    fecha_evaluacion = models.DateTimeField(verbose_name="Fecha de Evaluación")
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(11), MaxValueValidator(14)],
        verbose_name="Edad Gestacional (semanas)",
        help_text="Screening del primer trimestre: 11-14 semanas",
    )
    edad_gestacional_dias = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        default=0,
        verbose_name="Días adicionales",
    )

    # Datos maternos
    edad_materna = models.IntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(50)],
        verbose_name="Edad Materna (años)",
    )

    peso_materno = models.DecimalField(
        max_digits=5, decimal_places=1, verbose_name="Peso Materno (kg)",
    )

    # Medidas ecográficas
    translucencia_nucal = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        verbose_name="Translucencia Nucal (mm)",
        help_text="Medida en mm",
    )

    hueso_nasal_presente = models.BooleanField(
        default=True, verbose_name="¿Hueso nasal presente",
    )

    crl_mm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="CRL (mm)",
        help_text="Longitud cráneo-rabadilla",
    )

    # Marcadores bioquímicos
    papp_a = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="PAPP-A (mUI/L)",
        help_text="Proteína plasmática A asociada al embarazo",
    )

    beta_hcg_libre = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="β-HCG libre (ng/mL)",
        help_text="Fracción libre de gonadotropina coriónica",
    )

    # MoMs calculados
    papp_a_mom = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="PAPP-A MoM",
    )

    beta_hcg_mom = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="β-HCG MoM",
    )

    tn_mom = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="TN MoM",
    )

    # Riesgos calculados
    riesgo_down_basal = models.CharField(
        max_length=20, blank=True, verbose_name="Riesgo Basal Down", help_text="1:X",
    )

    riesgo_down_ajustado = models.CharField(
        max_length=20, blank=True, verbose_name="Riesgo Ajustado Down", help_text="1:X",
    )

    riesgo_edwards = models.CharField(
        max_length=20, blank=True, verbose_name="Riesgo Edwards (T18)", help_text="1:X",
    )

    riesgo_patau = models.CharField(
        max_length=20, blank=True, verbose_name="Riesgo Patau (T13)", help_text="1:X",
    )

    # Clasificación de riesgo
    clasificacion_down = models.CharField(
        max_length=20,
        choices=[
            ("bajo", "Bajo Riesgo"),
            ("intermedio", "Riesgo Intermedio"),
            ("alto", "Alto Riesgo"),
        ],
        blank=True,
        verbose_name="Clasificación Down",
    )

    recomendacion = models.TextField(blank=True, verbose_name="Recomendación Clínica")

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "riesgo_cromosomico"
        ordering = ["-fecha_evaluacion"]
        verbose_name = "Riesgo Cromosómico"
        verbose_name_plural = "Riesgos Cromosómicos"

    def save(self, *args, **kwargs):
        """Save"""
        self.calcular_riesgo_cromosomico()
        super().save(*args, **kwargs)

    def calcular_riesgo_cromosomico(self):
        """Calcula el riesgo cromosómico"""
        if not all([self.edad_materna, self.translucencia_nucal]):
            return  # No calcular si faltan datos básicos

        # Riesgo basal por edad materna
        riesgo_edad = self.calcular_riesgo_por_edad()

        # Factor de ajuste por translucencia nucal
        factor_tn = self.calcular_factor_tn()

        # Factor de ajuste por marcadores bioquímicos
        factor_bioquimico = self.calcular_factor_bioquimico()

        # Riesgo ajustado
        riesgo_final = riesgo_edad * factor_tn * factor_bioquimico

        # Convertir a formato 1:X
        if riesgo_final > 0:
            self.riesgo_down_ajustado = f"1:{int(1 / riesgo_final)}"

        # Clasificación
        if riesgo_final >= 1 / 250:  # Mayor o igual a 1:250
            self.clasificacion_down = "alto"
            self.recomendacion = "Se recomienda diagnóstico invasivo (amniocentesis o biopsia de vellosidades coriales)"
        elif riesgo_final >= 1 / 1000:  # Entre 1:250 y 1:1000
            self.clasificacion_down = "intermedio"
            self.recomendacion = "Considerar screening adicional o diagnóstico invasivo según preferencia materna"
        else:
            self.clasificacion_down = "bajo"
            self.recomendacion = "Continuar controles rutinarios. Screening normal"

    def calcular_riesgo_por_edad(self):
        """Calcula riesgo basal por edad materna"""
        # Tabla simplificada de riesgo por edad
        riesgos_edad = {
            15: 1 / 1667,
            16: 1 / 1667,
            17: 1 / 1667,
            18: 1 / 1667,
            19: 1 / 1667,
            20: 1 / 1667,
            21: 1 / 1667,
            22: 1 / 1667,
            23: 1 / 1667,
            24: 1 / 1538,
            25: 1 / 1351,
            26: 1 / 1176,
            27: 1 / 1053,
            28: 1 / 952,
            29: 1 / 870,
            30: 1 / 800,
            31: 1 / 741,
            32: 1 / 690,
            33: 1 / 645,
            34: 1 / 606,
            35: 1 / 571,
            36: 1 / 541,
            37: 1 / 515,
            38: 1 / 490,
            39: 1 / 469,
            40: 1 / 449,
            41: 1 / 431,
            42: 1 / 414,
            43: 1 / 398,
            44: 1 / 383,
            45: 1 / 369,
            46: 1 / 356,
            47: 1 / 343,
            48: 1 / 331,
            49: 1 / 320,
            50: 1 / 309,
        }

        riesgo = riesgos_edad.get(self.edad_materna, 1 / 300)
        self.riesgo_down_basal = f"1:{int(1 / riesgo)}"
        return riesgo

    def calcular_factor_tn(self):
        """Calcula factor de ajuste por translucencia nucal"""
        if not self.translucencia_nucal:
            return 1.0

        # Cálculo simplificado del factor TN
        tn_mm = float(self.translucencia_nucal)

        if tn_mm <= 2.5:
            return 0.5  # Reduce el riesgo
        if tn_mm <= 3.5:
            return 2.0  # Duplica el riesgo
        return 10.0  # Aumenta significativamente el riesgo

    def calcular_factor_bioquimico(self):
        """Calcula factor de ajuste por marcadores bioquímicos"""
        factor = 1.0

        # PAPP-A (valores bajos aumentan riesgo)
        if self.papp_a_mom:
            if float(self.papp_a_mom) < 0.5:
                factor *= 2.0
            elif float(self.papp_a_mom) < 0.25:
                factor *= 4.0

        # β-HCG (valores muy altos o bajos aumentan riesgo)
        if self.beta_hcg_mom:
            hcg_mom = float(self.beta_hcg_mom)
            if hcg_mom > 2.0 or hcg_mom < 0.5:
                factor *= 1.5

        return factor

    def get_interpretacion_completa(self):
        """Interpretación completa del screening"""
        return {
            "riesgo_basal": self.riesgo_down_basal or "No calculado",
            "riesgo_ajustado": self.riesgo_down_ajustado or "No calculado",
            "clasificacion": self.get_clasificacion_down_display()
            if self.clasificacion_down
            else "No clasificado",
            "translucencia_nucal": f"{self.translucencia_nucal} mm"
            if self.translucencia_nucal
            else "No medida",
            "marcadores_bioquimicos": {
                "papp_a": f"{self.papp_a_mom} MoM"
                if self.papp_a_mom
                else "No disponible",
                "beta_hcg": f"{self.beta_hcg_mom} MoM"
                if self.beta_hcg_mom
                else "No disponible",
            },
            "recomendacion": self.recomendacion
            or "Complete los datos para obtener recomendaciones",
        }

    def __str__(self):
        """Str"""
        return f"Screening Cromosómico - Paciente {self.paciente.nombre_completo} - Riesgo: {self.riesgo_down_ajustado or 'Pendiente'}"


class DosisMedicamentos(models.Model):
    """Calculadora de dosis de medicamentos obstétricos"""

    MEDICAMENTO_CHOICES = [
        ("oxitocina", "Oxitocina"),
        ("sulfato_magnesio", "Sulfato de Magnesio"),
        ("betametasona", "Betametasona"),
        ("dexametasona", "Dexametasona"),
        ("nifedipino", "Nifedipino"),
        ("indometacina", "Indometacina"),
        ("metildopa", "Metildopa"),
        ("labetalol", "Labetalol"),
    ]

    INDICACION_CHOICES = [
        ("induccion_parto", "Inducción del Parto"),
        ("conduccion_parto", "Conducción del Parto"),
        ("hemorragia_postparto", "Hemorragia Postparto"),
        ("preeclampsia_severa", "Preeclampsia Severa"),
        ("eclampsia", "Eclampsia"),
        ("maduracin_pulmonar", "Maduración Pulmonar"),
        ("tocolis_aguda", "Tocolisis Aguda"),
        ("hipertension_gestacional", "Hipertensión Gestacional"),
    ]

    # Relaciones
    paciente_id = models.IntegerField(verbose_name="ID del Paciente")
    embarazo_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID del Embarazo",
    )
    parto_id = models.IntegerField(null=True, blank=True, verbose_name="ID del Parto")

    # Datos del cálculo
    fecha_calculo = models.DateTimeField(verbose_name="Fecha del Cálculo")
    medicamento = models.CharField(
        max_length=30, choices=MEDICAMENTO_CHOICES, verbose_name="Medicamento",
    )

    indicacion = models.CharField(
        max_length=30, choices=INDICACION_CHOICES, verbose_name="Indicación",
    )

    # Datos maternos
    peso_materno = models.DecimalField(
        max_digits=5, decimal_places=1, verbose_name="Peso Materno (kg)",
    )

    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(20), MaxValueValidator(42)],
        null=True,
        blank=True,
        verbose_name="Edad Gestacional (semanas)",
    )

    # Parámetros clínicos específicos
    presion_arterial_sistolica = models.IntegerField(
        null=True, blank=True, verbose_name="PAS (mmHg)",
    )

    presion_arterial_diastolica = models.IntegerField(
        null=True, blank=True, verbose_name="PAD (mmHg)",
    )

    creatinina_serica = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Creatinina (mg/dL)",
    )

    # Resultados calculados
    dosis_inicial = models.CharField(
        max_length=100, blank=True, verbose_name="Dosis Inicial",
    )

    dosis_mantenimiento = models.CharField(
        max_length=100, blank=True, verbose_name="Dosis de Mantenimiento",
    )

    dosis_maxima = models.CharField(
        max_length=100, blank=True, verbose_name="Dosis Máxima",
    )

    via_administracion = models.CharField(
        max_length=50, blank=True, verbose_name="Vía de Administración",
    )

    intervalo_dosis = models.CharField(
        max_length=50, blank=True, verbose_name="Intervalo entre Dosis",
    )

    duracion_tratamiento = models.CharField(
        max_length=100, blank=True, verbose_name="Duración del Tratamiento",
    )

    # Precauciones y contraindicaciones
    precauciones = models.TextField(blank=True, verbose_name="Precauciones Especiales")

    contraindicaciones = models.TextField(blank=True, verbose_name="Contraindicaciones")

    monitoreo_requerido = models.TextField(
        blank=True, verbose_name="Monitoreo Requerido",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "dosis_medicamentos"
        ordering = ["-fecha_calculo"]
        verbose_name = "Dosis de Medicamento"
        verbose_name_plural = "Dosis de Medicamentos"

    def save(self, *args, **kwargs):
        """Save"""
        self.calcular_dosis()
        super().save(*args, **kwargs)

    def calcular_dosis(self):
        """Calcula las dosis según el medicamento y la indicación"""
        if not all([self.medicamento, self.indicacion, self.peso_materno]):
            return  # No calcular si faltan datos básicos

        if self.medicamento == "oxitocina":
            self.calcular_dosis_oxitocina()
        elif self.medicamento == "sulfato_magnesio":
            self.calcular_dosis_sulfato_magnesio()
        elif self.medicamento == "betametasona":
            self.calcular_dosis_betametasona()
        elif self.medicamento == "nifedipino":
            self.calcular_dosis_nifedipino()
        elif self.medicamento == "labetalol":
            self.calcular_dosis_labetalol()

    def calcular_dosis_oxitocina(self):
        """Cálculo de dosis de oxitocina"""
        if self.indicacion == "induccion_parto":
            self.dosis_inicial = "1-2 mU/min"
            self.dosis_mantenimiento = "Incrementar 1-2 mU/min cada 15-30 min"
            self.dosis_maxima = "20-40 mU/min"
            self.via_administracion = "Intravenosa continua"
            self.intervalo_dosis = "Ajuste cada 15-30 minutos"
            self.monitoreo_requerido = (
                "Monitoreo fetal continuo, contracciones uterinas, presión arterial"
            )

        elif self.indicacion == "hemorragia_postparto":
            self.dosis_inicial = "10-40 UI en 500-1000 mL SSN"
            self.dosis_mantenimiento = "125-250 mL/hr"
            self.dosis_maxima = "80 UI en 24 horas"
            self.via_administracion = "Intravenosa"
            self.monitoreo_requerido = "Sangrado activo, signos vitales, tono uterino"

        self.precauciones = "Contracciones tetánicas, rotura uterina, sufrimiento fetal"
        self.contraindicaciones = (
            "Presentación anormal, placenta previa, cicatriz uterina previa"
        )

    def calcular_dosis_sulfato_magnesio(self):
        """Cálculo de dosis de sulfato de magnesio"""
        _peso = float(self.peso_materno)

        if self.indicacion in ["preeclampsia_severa", "eclampsia"]:
            # Dosis de carga
            dosis_carga = 4  # gramos IV
            self.dosis_inicial = f"{dosis_carga}g IV en 20 minutos"

            # Dosis de mantenimiento
            dosis_mant = 1  # g/hora
            self.dosis_mantenimiento = f"{dosis_mant}g/hora IV continua"

            self.via_administracion = "Intravenosa"
            self.duracion_tratamiento = (
                "24 horas postparto o hasta 24h sin convulsiones"
            )
            self.monitoreo_requerido = "Reflejos tendinosos, diuresis, frecuencia respiratoria, nivel de conciencia"
            self.precauciones = "Depresión respiratoria, oliguria, ausencia de reflejos"
            self.contraindicaciones = (
                "Miastenia gravis, bloqueo cardíaco, insuficiencia renal severa"
            )

    def calcular_dosis_betametasona(self):
        """Cálculo de dosis de betametasona para maduración pulmonar"""
        if self.indicacion == "maduracin_pulmonar":
            self.dosis_inicial = "12 mg IM"
            self.dosis_mantenimiento = "12 mg IM a las 24 horas"
            self.via_administracion = "Intramuscular"
            self.intervalo_dosis = "24 horas entre dosis"
            self.duracion_tratamiento = "2 dosis totales"
            self.monitoreo_requerido = "Glucemia materna, signos de infección"

            if self.edad_gestacional_semanas:
                if self.edad_gestacional_semanas < 24:
                    self.precauciones = "Eficacia limitada antes de 24 semanas"
                elif self.edad_gestacional_semanas > 34:
                    self.precauciones = "Beneficio limitado después de 34 semanas"

    def calcular_dosis_nifedipino(self):
        """Cálculo de dosis de nifedipino"""
        if self.indicacion == "tocolis_aguda":
            self.dosis_inicial = "10 mg sublingual"
            self.dosis_mantenimiento = "10-20 mg cada 4-6 horas VO"
            self.dosis_maxima = "120 mg/día"
            self.via_administracion = "Sublingual/Oral"
            self.monitoreo_requerido = (
                "Presión arterial, frecuencia cardíaca materna, actividad uterina"
            )

        elif self.indicacion == "hipertension_gestacional":
            if (
                self.presion_arterial_sistolica
                and self.presion_arterial_sistolica >= 160
            ):
                self.dosis_inicial = "10 mg sublingual STAT"
                self.dosis_mantenimiento = "10-20 mg cada 6 horas"
            else:
                self.dosis_inicial = "5-10 mg cada 8 horas"
                self.dosis_mantenimiento = "20-60 mg/día dividido"

            self.monitoreo_requerido = (
                "Presión arterial cada 15 min x 1 hora, luego cada hora"
            )

        self.precauciones = "Hipotensión materna, taquicardia, cefalea"
        self.contraindicaciones = (
            "Hipotensión, insuficiencia cardíaca, estenosis aórtica"
        )

    def calcular_dosis_labetalol(self):
        """Cálculo de dosis de labetalol"""
        if self.indicacion == "hipertension_gestacional":
            if (
                self.presion_arterial_sistolica
                and self.presion_arterial_sistolica >= 160
            ):
                # Crisis hipertensiva
                self.dosis_inicial = "20 mg IV bolo"
                self.dosis_mantenimiento = "20-80 mg IV cada 10 min (máx 300 mg)"
                self.via_administracion = "Intravenosa"
            else:
                # Hipertensión crónica
                self.dosis_inicial = "100 mg VO BID"
                self.dosis_mantenimiento = "200-400 mg BID"
                self.dosis_maxima = "1200 mg/día"
                self.via_administracion = "Oral"

            self.monitoreo_requerido = (
                "Presión arterial, frecuencia cardíaca, bienestar fetal"
            )
            self.precauciones = "Bradicardia materna, hipotensión, asma"
            self.contraindicaciones = (
                "Asma severa, bloqueo cardíaco, insuficiencia cardíaca descompensada"
            )

    def get_protocolo_administracion(self):
        """Protocolo completo de administración"""
        return {
            "medicamento": self.get_medicamento_display(),
            "indicacion": self.get_indicacion_display(),
            "dosis_inicial": self.dosis_inicial or "No calculada",
            "mantenimiento": self.dosis_mantenimiento or "No calculada",
            "via": self.via_administracion or "No especificada",
            "intervalo": self.intervalo_dosis or "No especificado",
            "duracion": self.duracion_tratamiento or "No especificada",
            "monitoreo": self.monitoreo_requerido or "Estándar",
            "precauciones": self.precauciones or "Generales",
            "contraindicaciones": self.contraindicaciones or "Consultar literatura",
        }

    def __str__(self):
        """Str"""
        return f"{self.get_medicamento_display()} - {self.get_indicacion_display()} - Paciente {self.paciente_id}"


class HemorragiaObstetrica(models.Model):
    """Calculadora y protocolo para hemorragia obstétrica"""

    TIPO_HEMORRAGIA_CHOICES = [
        ("anteparto", "Hemorragia Anteparto"),
        ("intraparto", "Hemorragia Intraparto"),
        ("postparto_inmediato", "Hemorragia Postparto Inmediato"),
        ("postparto_tardio", "Hemorragia Postparto Tardío"),
    ]

    CAUSA_CHOICES = [
        ("atonia_uterina", "Atonía Uterina"),
        ("retencion_placentaria", "Retención Placentaria"),
        ("desgarros_tractus", "Desgarros del Tractus Genital"),
        ("rotura_uterina", "Rotura Uterina"),
        ("placenta_previa", "Placenta Previa"),
        ("desprendimiento_placenta", "Desprendimiento de Placenta"),
        ("coagulopatia", "Coagulopatía"),
        ("inversion_uterina", "Inversión Uterina"),
    ]

    # Relaciones
    paciente_id = models.IntegerField(verbose_name="ID del Paciente")
    embarazo_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID del Embarazo",
    )
    parto_id = models.IntegerField(null=True, blank=True, verbose_name="ID del Parto")

    # Datos del evento
    fecha_evento = models.DateTimeField(verbose_name="Fecha y Hora del Evento")
    tipo_hemorragia = models.CharField(
        max_length=30,
        choices=TIPO_HEMORRAGIA_CHOICES,
        verbose_name="Tipo de Hemorragia",
    )

    causa_principal = models.CharField(
        max_length=30, choices=CAUSA_CHOICES, verbose_name="Causa Principal",
    )

    # Evaluación inicial
    perdida_sanguinea_estimada = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5000)],
        verbose_name="Pérdida Sanguínea Estimada (mL)",
    )

    # Signos vitales iniciales
    presion_arterial_sistolica = models.IntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(200)],
        verbose_name="PAS (mmHg)",
    )

    presion_arterial_diastolica = models.IntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(120)],
        verbose_name="PAD (mmHg)",
    )

    frecuencia_cardiaca = models.IntegerField(
        validators=[MinValueValidator(40), MaxValueValidator(180)],
        verbose_name="FC (lpm)",
    )

    # Laboratorio inicial
    hemoglobina_inicial = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Hemoglobina Inicial (g/dL)",
    )

    hematocrito_inicial = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Hematocrito Inicial (%)",
    )

    plaquetas = models.IntegerField(
        null=True, blank=True, verbose_name="Plaquetas (/mm³)",
    )

    # Cálculos automáticos
    severidad_hemorragia = models.CharField(
        max_length=20, blank=True, verbose_name="Severidad de la Hemorragia",
    )

    indice_shock = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Índice de Shock",
    )

    deficit_volumen_estimado = models.IntegerField(
        null=True, blank=True, verbose_name="Déficit de Volumen Estimado (mL)",
    )

    # Protocolo de manejo
    paso_protocolo_actual = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Paso Actual del Protocolo",
    )

    medidas_implementadas = models.TextField(
        blank=True, verbose_name="Medidas Implementadas",
    )

    # Transfusión
    requiere_transfusion = models.BooleanField(
        default=False, verbose_name="¿Requiere Transfusión",
    )

    unidades_globulos_rojos = models.IntegerField(
        default=0, verbose_name="Unidades de Glóbulos Rojos",
    )

    unidades_plasma_fresco = models.IntegerField(
        default=0, verbose_name="Unidades de Plasma Fresco",
    )

    unidades_plaquetas = models.IntegerField(
        default=0, verbose_name="Unidades de Plaquetas",
    )

    # Resultado
    hemorragia_controlada = models.BooleanField(
        default=False, verbose_name="¿Hemorragia Controlada",
    )

    requirio_cirugia = models.BooleanField(
        default=False, verbose_name="¿Requirió Cirugía",
    )

    tipo_cirugia = models.CharField(
        max_length=100, blank=True, verbose_name="Tipo de Cirugía",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "hemorragia_obstetrica"
        ordering = ["-fecha_evento"]
        verbose_name = "Hemorragia Obstétrica"
        verbose_name_plural = "Hemorragias Obstétricas"

    def save(self, *args, **kwargs):
        """Save"""
        self.calcular_indices()
        self.determinar_severidad()
        self.calcular_necesidades_transfusion()
        super().save(*args, **kwargs)

    def calcular_indices(self):
        """Calcula índices pronósticos"""
        # Índice de shock
        if (
            self.frecuencia_cardiaca
            and self.presion_arterial_sistolica
            and self.presion_arterial_sistolica > 0
        ):
            self.indice_shock = Decimal(
                str(self.frecuencia_cardiaca / self.presion_arterial_sistolica),
            )

        # Déficit de volumen estimado
        if self.perdida_sanguinea_estimada:
            self.deficit_volumen_estimado = self.perdida_sanguinea_estimada

    def determinar_severidad(self):
        """Determina la severidad de la hemorragia"""
        if not self.perdida_sanguinea_estimada:
            return

        perdida = self.perdida_sanguinea_estimada

        if perdida < 500:
            self.severidad_hemorragia = "Leve"
        elif perdida < 1000:
            self.severidad_hemorragia = "Moderada"
        elif perdida < 1500:
            self.severidad_hemorragia = "Severa"
        else:
            self.severidad_hemorragia = "Masiva"

        # Ajustar por signos vitales
        if self.indice_shock and float(self.indice_shock) > 1.0:
            if self.severidad_hemorragia in ["Leve", "Moderada"]:
                self.severidad_hemorragia = "Severa"

    def calcular_necesidades_transfusion(self):
        """Calcula necesidades de transfusión"""
        if self.severidad_hemorragia in ["Severa", "Masiva"]:
            self.requiere_transfusion = True

            # Estimación de unidades necesarias
            if (
                self.perdida_sanguinea_estimada
                and self.perdida_sanguinea_estimada >= 1500
            ):
                self.unidades_globulos_rojos = 4
                self.unidades_plasma_fresco = 4
                self.unidades_plaquetas = 1
            elif (
                self.perdida_sanguinea_estimada
                and self.perdida_sanguinea_estimada >= 1000
            ):
                self.unidades_globulos_rojos = 2
                self.unidades_plasma_fresco = 2

        # Ajustar por hemoglobina
        if self.hemoglobina_inicial and float(self.hemoglobina_inicial) < 7.0:
            self.requiere_transfusion = True
            self.unidades_globulos_rojos = max(self.unidades_globulos_rojos, 2)

    def get_protocolo_manejo(self):
        """Protocolo de manejo por pasos"""
        protocolos = {
            1: {
                "titulo": "PASO 1: Evaluación Inicial y Medidas Básicas",
                "acciones": [
                    "Comunicación con equipo de emergencia",
                    "Dos accesos venosos calibre 14-16G",
                    "Monitoreo signos vitales",
                    "Laboratorio: CBC, coagulación, tipificación",
                    "Catéter urinario",
                    "Oxígeno suplementario",
                ],
            },
            2: {
                "titulo": "PASO 2: Identificación y Tratamiento de Causa",
                "acciones": [
                    "Masaje uterino bimanual",
                    "Oxitocina 20-40 UI en 1000mL SSN",
                    "Revisión manual de útero",
                    "Reparación de desgarros",
                    "Compresión aórtica si es necesario",
                ],
            },
            3: {
                "titulo": "PASO 3: Uterotonicos Adicionales",
                "acciones": [
                    "Metilergonovina 0.2mg IM (contraindicada si HTA)",
                    "Misoprostol 800-1000mcg rectal",
                    "Ácido tranexámico 1g IV en 10 min",
                    "Reposición de volumen con cristaloides",
                ],
            },
            4: {
                "titulo": "PASO 4: Intervenciones Avanzadas",
                "acciones": [
                    "Transfusión sanguínea según protocolo",
                    "Taponamiento uterino con balón",
                    "Suturas compresivas (B-Lynch)",
                    "Ligadura de arterias uterinas",
                    "Embolización arterial si disponible",
                ],
            },
            5: {
                "titulo": "PASO 5: Histerectomía de Emergencia",
                "acciones": [
                    "Decisión quirúrgica inmediata",
                    "Histerectomía total o subtotal",
                    "Manejo en UCI postoperatorio",
                    "Soporte hemodinámico avanzado",
                ],
            },
        }

        return protocolos.get(self.paso_protocolo_actual, protocolos[1])

    def get_recomendaciones_laboratorio(self):
        """Recomendaciones de laboratorio según severidad"""
        recomendaciones = [
            "Hemograma completo con plaquetas",
            "Tiempo de protrombina y TTPA",
            "Fibrinógeno",
            "Tipificación y pruebas cruzadas",
        ]

        if self.severidad_hemorragia in ["Severa", "Masiva"]:
            recomendaciones.extend(
                [
                    "Productos de degradación de fibrina",
                    "Lactato sérico",
                    "Gases arteriales",
                    "Electrolitos y función renal",
                ],
            )

        return recomendaciones

    def __str__(self):
        """Str"""
        return f"Hemorragia {self.severidad_hemorragia or 'Evaluando'} - Paciente {self.paciente_id} - {self.perdida_sanguinea_estimada}mL"


class SufrimientoFetal(models.Model):
    """Evaluación de sufrimiento fetal y bienestar fetal"""

    TIPO_EVALUACION_CHOICES = [
        ("anteparto", "Evaluación Anteparto"),
        ("intraparto", "Evaluación Intraparto"),
        ("postparto", "Evaluación Postparto"),
    ]

    TIPO_MONITOREO_CHOICES = [
        ("ctg_externo", "CTG Externo"),
        ("ctg_interno", "CTG Interno"),
        ("perfil_biofsico", "Perfil Biofísico"),
        ("doppler_fetal", "Doppler Fetal"),
    ]

    # Relaciones
    paciente_id = models.IntegerField(verbose_name="ID del Paciente")
    embarazo_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID del Embarazo",
    )
    parto_id = models.IntegerField(null=True, blank=True, verbose_name="ID del Parto")

    # Datos de la evaluación
    fecha_evaluacion = models.DateTimeField(verbose_name="Fecha y Hora de Evaluación")
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(20), MaxValueValidator(42)],
        verbose_name="Edad Gestacional (semanas)",
    )

    tipo_evaluacion = models.CharField(
        max_length=20,
        choices=TIPO_EVALUACION_CHOICES,
        verbose_name="Tipo de Evaluación",
    )

    tipo_monitoreo = models.CharField(
        max_length=20, choices=TIPO_MONITOREO_CHOICES, verbose_name="Tipo de Monitoreo",
    )

    # Parámetros del CTG
    fcf_basal = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(80), MaxValueValidator(200)],
        verbose_name="FCF Basal (lpm)",
    )

    variabilidad_fcf = models.CharField(
        max_length=20,
        choices=[
            ("ausente", "Ausente (< 5 lpm)"),
            ("minima", "Mínima (5-10 lpm)"),
            ("moderada", "Moderada (11-25 lpm)"),
            ("marcada", "Marcada (> 25 lpm)"),
        ],
        blank=True,
        verbose_name="Variabilidad FCF",
    )

    aceleraciones_presentes = models.BooleanField(
        default=True, verbose_name="¿Aceleraciones presentes",
    )

    # Desaceleraciones
    desaceleraciones_tardias = models.BooleanField(
        default=False, verbose_name="Desaceleraciones Tardías",
    )

    desaceleraciones_variables = models.BooleanField(
        default=False, verbose_name="Desaceleraciones Variables",
    )

    desaceleraciones_prolongadas = models.BooleanField(
        default=False, verbose_name="Desaceleraciones Prolongadas",
    )

    # Perfil biofísico (si aplica)
    movimientos_fetales = models.CharField(
        max_length=20,
        choices=[
            ("presentes", "Presentes"),
            ("disminuidos", "Disminuidos"),
            ("ausentes", "Ausentes"),
        ],
        blank=True,
        verbose_name="Movimientos Fetales",
    )

    tono_fetal = models.CharField(
        max_length=20,
        choices=[
            ("normal", "Normal"),
            ("disminuido", "Disminuido"),
        ],
        blank=True,
        verbose_name="Tono Fetal",
    )

    liquido_amniotico = models.CharField(
        max_length=20,
        choices=[
            ("normal", "Normal"),
            ("oligohidramnios", "Oligohidramnios"),
            ("polihidramnios", "Polihidramnios"),
        ],
        blank=True,
        verbose_name="Líquido Amniótico",
    )

    # Doppler fetal
    indice_pulsatilidad_umbilical = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="IP Arteria Umbilical",
    )

    indice_pulsatilidad_cerebral = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="IP Arteria Cerebral Media",
    )

    # Scores calculados
    score_fisher = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Score de Fisher",
    )

    perfil_biofsico_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Score Perfil Biofísico",
    )

    # Interpretación
    clasificacion_ctg = models.CharField(
        max_length=20,
        choices=[
            ("categoria_1", "Categoría I (Normal)"),
            ("categoria_2", "Categoría II (Indeterminado)"),
            ("categoria_3", "Categoría III (Anormal)"),
        ],
        blank=True,
        verbose_name="Clasificación CTG",
    )

    riesgo_sufrimiento_fetal = models.CharField(
        max_length=20,
        choices=[
            ("bajo", "Bajo Riesgo"),
            ("intermedio", "Riesgo Intermedio"),
            ("alto", "Alto Riesgo"),
        ],
        blank=True,
        verbose_name="Riesgo de Sufrimiento Fetal",
    )

    # Recomendaciones
    conducta_recomendada = models.TextField(
        blank=True, verbose_name="Conducta Recomendada",
    )

    requiere_intervencion_inmediata = models.BooleanField(
        default=False, verbose_name="¿Requiere Intervención Inmediata",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "sufrimiento_fetal"
        ordering = ["-fecha_evaluacion"]
        verbose_name = "Evaluación de Sufrimiento Fetal"
        verbose_name_plural = "Evaluaciones de Sufrimiento Fetal"

    def save(self, *args, **kwargs):
        """Save"""
        self.calcular_scores()
        self.determinar_clasificacion()
        self.generar_recomendaciones()
        super().save(*args, **kwargs)

    def calcular_scores(self):
        """Calcula scores de bienestar fetal"""
        # Score de Fisher (modificado)
        if self.tipo_monitoreo in ["ctg_externo", "ctg_interno"]:
            score = 0

            # FCF basal
            if self.fcf_basal:
                if 110 <= self.fcf_basal <= 160:
                    score += 2
                elif 100 <= self.fcf_basal < 110 or 160 < self.fcf_basal <= 180:
                    score += 1
                else:
                    score += 0

            # Variabilidad
            if self.variabilidad_fcf == "moderada":
                score += 2
            elif self.variabilidad_fcf == "minima":
                score += 1
            else:
                score += 0

            # Aceleraciones
            if self.aceleraciones_presentes:
                score += 2
            else:
                score += 0

            # Desaceleraciones
            if not any(
                [
                    self.desaceleraciones_tardias,
                    self.desaceleraciones_variables,
                    self.desaceleraciones_prolongadas,
                ],
            ):
                score += 2
            elif self.desaceleraciones_variables and not self.desaceleraciones_tardias:
                score += 1
            else:
                score += 0

            self.score_fisher = score

        # Perfil biofísico
        if self.tipo_monitoreo == "perfil_biofsico":
            pbf_score = 0

            # CTG reactivo
            if self.aceleraciones_presentes and self.variabilidad_fcf == "moderada":
                pbf_score += 2

            # Movimientos fetales
            if self.movimientos_fetales == "presentes":
                pbf_score += 2

            # Tono fetal
            if self.tono_fetal == "normal":
                pbf_score += 2

            # Respiración fetal (asumimos normal si no hay datos)
            pbf_score += 2

            # Líquido amniótico
            if self.liquido_amniotico == "normal":
                pbf_score += 2

            self.perfil_biofsico_score = pbf_score

    def determinar_clasificacion(self):
        """Determina la clasificación del CTG y riesgo"""
        if self.tipo_monitoreo in ["ctg_externo", "ctg_interno"]:
            # Clasificación NICHD
            if (
                self.fcf_basal
                and 110 <= self.fcf_basal <= 160
                and self.variabilidad_fcf == "moderada"
                and self.aceleraciones_presentes
                and not any(
                    [
                        self.desaceleraciones_tardias,
                        self.desaceleraciones_variables,
                        self.desaceleraciones_prolongadas,
                    ],
                )
            ):
                self.clasificacion_ctg = "categoria_1"
                self.riesgo_sufrimiento_fetal = "bajo"

            elif (
                self.desaceleraciones_tardias
                or self.desaceleraciones_prolongadas
                or self.variabilidad_fcf == "ausente"
                or (self.fcf_basal and (self.fcf_basal < 110 or self.fcf_basal > 180))
            ):
                self.clasificacion_ctg = "categoria_3"
                self.riesgo_sufrimiento_fetal = "alto"
                self.requiere_intervencion_inmediata = True

            else:
                self.clasificacion_ctg = "categoria_2"
                self.riesgo_sufrimiento_fetal = "intermedio"

        # Perfil biofísico
        if self.perfil_biofsico_score is not None:
            if self.perfil_biofsico_score >= 8:
                self.riesgo_sufrimiento_fetal = "bajo"
            elif self.perfil_biofsico_score >= 6:
                self.riesgo_sufrimiento_fetal = "intermedio"
            else:
                self.riesgo_sufrimiento_fetal = "alto"
                self.requiere_intervencion_inmediata = True

    def generar_recomendaciones(self):
        """Genera recomendaciones basadas en la evaluación"""
        recomendaciones = []

        if self.clasificacion_ctg == "categoria_1":
            recomendaciones.append("Continuar monitoreo rutinario")
            recomendaciones.append(
                "Evaluación cada 30 minutos en trabajo de parto activo",
            )

        elif self.clasificacion_ctg == "categoria_2":
            recomendaciones.append("Aumentar frecuencia de monitoreo")
            recomendaciones.append("Corregir factores maternos (hipotensión, hipoxia)")
            recomendaciones.append(
                "Considerar estimulación fetal o cambios de posición",
            )
            recomendaciones.append("Reevaluar en 30 minutos")

            if self.tipo_evaluacion == "intraparto":
                recomendaciones.append("Considerar electrodo fetal interno si persiste")

        elif self.clasificacion_ctg == "categoria_3":
            recomendaciones.append(" INTERVENCIÓN INMEDIATA REQUERIDA")
            recomendaciones.append("Finalización inmediata del embarazo")
            recomendaciones.append("Cesárea de emergencia si intraparto")
            recomendaciones.append("Reanimación intrauterina mientras se prepara")
            recomendaciones.append("Notificar a neonatología")

        # Recomendaciones por perfil biofísico
        if self.perfil_biofsico_score is not None:
            if self.perfil_biofsico_score <= 4:
                recomendaciones.append("Finalización inmediata si > 32 semanas")
                recomendaciones.append("Maduración pulmonar si < 32 semanas")
            elif self.perfil_biofsico_score <= 6:
                recomendaciones.append("Repetir evaluación en 24 horas")
                recomendaciones.append("Considerar finalización según edad gestacional")

        # Recomendaciones por Doppler
        if (
            self.indice_pulsatilidad_umbilical
            and float(self.indice_pulsatilidad_umbilical) > 1.45
        ):
            recomendaciones.append("Doppler anormal - Vigilancia estrecha")
            recomendaciones.append("Control de crecimiento cada 2 semanas")

        if not recomendaciones:
            recomendaciones.append(
                "Complete los datos para obtener recomendaciones específicas",
            )

        self.conducta_recomendada = "\n".join([f"• {rec}" for rec in recomendaciones])

    def get_interpretacion_completa(self):
        """Interpretación completa del estudio"""
        return {
            "tipo_evaluacion": self.get_tipo_evaluacion_display(),
            "monitoreo": self.get_tipo_monitoreo_display(),
            "fcf_basal": f"{self.fcf_basal} lpm" if self.fcf_basal else "No registrada",
            "variabilidad": self.get_variabilidad_fcf_display()
            if self.variabilidad_fcf
            else "No evaluada",
            "clasificacion_ctg": self.get_clasificacion_ctg_display()
            if self.clasificacion_ctg
            else "No clasificado",
            "riesgo": self.get_riesgo_sufrimiento_fetal_display()
            if self.riesgo_sufrimiento_fetal
            else "No evaluado",
            "score_fisher": self.score_fisher
            if self.score_fisher is not None
            else "No calculado",
            "pbf_score": self.perfil_biofsico_score
            if self.perfil_biofsico_score is not None
            else "No calculado",
            "intervencion_inmediata": self.requiere_intervencion_inmediata,
            "recomendaciones": self.conducta_recomendada
            or "Complete los datos para obtener recomendaciones",
        }

    def __str__(self):
        """Str"""
        return f"Bienestar Fetal - Paciente {self.paciente_id} - {self.get_riesgo_sufrimiento_fetal_display() if self.riesgo_sufrimiento_fetal else 'Evaluando'}"
