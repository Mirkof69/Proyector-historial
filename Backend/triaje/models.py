"""=============================================================================
MÓDULO: TRIAJE - MODELS
=============================================================================
Gestión de triaje de enfermería (signos vitales y evaluación inicial)
Implementa flujo de trabajo: Enfermera → Médico
=============================================================================
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TriajeEnfermeria(models.Model):
    """Triaje de enfermería - Evaluación inicial del paciente
    Registrado por enfermera antes de pasar al médico
    """

    # ============== RELACIONES ==============
    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="triajes",
        db_column="paciente_id",
    )

    cita = models.OneToOneField(
        "citas.Cita",
        on_delete=models.CASCADE,
        related_name="triaje",
        null=True,
        blank=True,
        db_column="cita_id",
        help_text="Cita a la que corresponde este triaje",
    )

    # ============== ANTROPOMETRÍA ==============
    peso_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("20.00")),
            MaxValueValidator(Decimal("300.00")),
        ],
        help_text="Peso en kilogramos (20-300 kg)",
    )

    talla_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("50.00")),
            MaxValueValidator(Decimal("250.00")),
        ],
        help_text="Talla en centímetros (50-250 cm)",
    )

    imc = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Índice de Masa Corporal (calculado automáticamente)",
    )

    perimetro_abdominal_cm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("40.0")),
            MaxValueValidator(Decimal("200.0")),
        ],
        help_text="Perímetro abdominal en cm",
    )

    # ============== SIGNOS VITALES ==============
    presion_sistolica = models.PositiveIntegerField(
        validators=[MinValueValidator(60), MaxValueValidator(250)],
        help_text="Presión arterial sistólica (60-250 mmHg)",
    )

    presion_diastolica = models.PositiveIntegerField(
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        help_text="Presión arterial diastólica (40-150 mmHg)",
    )

    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal("34.0")),
            MaxValueValidator(Decimal("42.0")),
        ],
        help_text="Temperatura en °C (34-42°C)",
    )

    frecuencia_cardiaca = models.PositiveIntegerField(
        validators=[MinValueValidator(40), MaxValueValidator(200)],
        help_text="Frecuencia cardíaca en latidos por minuto (40-200 lpm)",
    )

    frecuencia_respiratoria = models.PositiveIntegerField(
        validators=[MinValueValidator(8), MaxValueValidator(40)],
        help_text="Frecuencia respiratoria en respiraciones por minuto (8-40 rpm)",
    )

    saturacion_oxigeno = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(70), MaxValueValidator(100)],
        help_text="Saturación de oxígeno en porcentaje (70-100%)",
    )

    # ============== EVALUACIÓN INICIAL ==============
    motivo_visita = models.TextField(
        help_text="Motivo de la visita referido por el paciente",
    )

    dolor_escala = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Escala de dolor 0-10 (0=sin dolor, 10=dolor máximo)",
    )

    nivel_conciencia = models.CharField(
        max_length=20,
        choices=[
            ("alerta", "Alerta"),
            ("somnoliento", "Somnoliento"),
            ("estuporoso", "Estuporoso"),
            ("inconsciente", "Inconsciente"),
        ],
        default="alerta",
    )

    # ============== OBSERVACIONES ==============
    observaciones = models.TextField(
        null=True, blank=True, help_text="Observaciones adicionales de enfermería",
    )

    # ============== ALERTAS ==============
    alerta_presion_alta = models.BooleanField(
        default=False, help_text="Alerta automática: PA sistólica ≥140 o PAD ≥90",
    )

    alerta_fiebre = models.BooleanField(
        default=False, help_text="Alerta automática: Temperatura ≥38°C",
    )

    alerta_taquicardia = models.BooleanField(
        default=False, help_text="Alerta automática: FC >100 lpm",
    )

    # ============== METADATOS ==============
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    enfermera = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="triajes_realizados",
        db_column="enfermera_id",
        limit_choices_to={"rol": "enfermera"},
    )

    # Trazabilidad
    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triajes_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triajes_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        verbose_name = "Triaje de Enfermería"
        verbose_name_plural = "Triajes de Enfermería"
        db_table = "triaje_enfermeria"
        ordering = ["-fecha_registro"]
        indexes = [
            models.Index(fields=["paciente", "-fecha_registro"]),
            models.Index(fields=["cita"]),
            models.Index(fields=["-fecha_registro"]),
        ]

    def __str__(self):
        """Str"""
        return f"Triaje de {self.paciente} - {self.fecha_registro.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        """Calcular IMC y activar alertas automáticamente"""
        # Calcular IMC
        if self.peso_kg and self.talla_cm:
            talla_m = float(self.talla_cm) / 100
            self.imc = Decimal(str(round(float(self.peso_kg) / (talla_m**2), 2)))

        # Alertas automáticas
        self.alerta_presion_alta = (
            self.presion_sistolica >= 140 or self.presion_diastolica >= 90
        )
        self.alerta_fiebre = float(self.temperatura) >= 38.0
        self.alerta_taquicardia = self.frecuencia_cardiaca > 100

        super().save(*args, **kwargs)

    def get_clasificacion_imc(self):
        """Clasificación del IMC"""
        if not self.imc:
            return "No calculado"

        imc = float(self.imc)
        if imc < 18.5:
            return "Bajo peso"
        if imc < 25:
            return "Normal"
        if imc < 30:
            return "Sobrepeso"
        if imc < 35:
            return "Obesidad I"
        if imc < 40:
            return "Obesidad II"
        return "Obesidad III"

    def get_clasificacion_presion(self):
        """Clasificación de presión arterial según guías"""
        if self.presion_sistolica < 120 and self.presion_diastolica < 80:
            return "Normal"
        if self.presion_sistolica < 130 and self.presion_diastolica < 80:
            return "Elevada"
        if self.presion_sistolica < 140 or self.presion_diastolica < 90:
            return "Hipertensión Estadio 1"
        if self.presion_sistolica >= 140 or self.presion_diastolica >= 90:
            return "Hipertensión Estadio 2"
        return "Crisis Hipertensiva"

    def get_presion_arterial(self):
        """Formato de presión arterial"""
        return f"{self.presion_sistolica}/{self.presion_diastolica} mmHg"

    def tiene_alertas(self):
        """Verifica si tiene alguna alerta activa"""
        return any(
            [self.alerta_presion_alta, self.alerta_fiebre, self.alerta_taquicardia],
        )

    def get_resumen(self):
        """Resumen del triaje para mostrar al médico"""
        alertas = []
        if self.alerta_presion_alta:
            alertas.append("⚠️ Presión arterial elevada")
        if self.alerta_fiebre:
            alertas.append("⚠️ Fiebre")
        if self.alerta_taquicardia:
            alertas.append("⚠️ Taquicardia")

        return {
            "presion": self.get_presion_arterial(),
            "temperatura": f"{self.temperatura}°C",
            "frecuencia_cardiaca": f"{self.frecuencia_cardiaca} lpm",
            "imc": f"{self.imc} ({self.get_clasificacion_imc()})"
            if self.imc
            else "No calculado",
            "alertas": alertas or ["✅ Sin alertas"],
            "motivo": self.motivo_visita,
        }
