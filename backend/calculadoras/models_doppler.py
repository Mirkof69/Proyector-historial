"""DOPPLER MATERNO - Modelos para Doppler de Arterias Uterinas
Protocolo FMF para predicción de preeclampsia
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from embarazos.models import Embarazo
from pacientes.models import Paciente


class DopplerMaterno(models.Model):
    """Doppler de arterias uterinas maternas
    Usado para calcular IP promedio y riesgo de preeclampsia
    """

    PACIENTE_LADO_CHOICES = [
        ("izquierda", "Arteria Uterina Izquierda"),
        ("derecha", "Arteria Uterina Derecha"),
        ("promedio", "Promedio Bilateral"),
    ]

    paciente = models.ForeignKey(
        Paciente, on_delete=models.PROTECT, related_name="dopplers_maternos",
    )
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dopplers_maternos",
    )
    fecha_examen = models.DateField(default=timezone.now)
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(7), MaxValueValidator(42)],
    )
    edad_gestacional_dias = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(6)],
    )

    # Lado medido
    lado = models.CharField(
        max_length=20, choices=PACIENTE_LADO_CHOICES, default="promedio",
    )

    # Medidas Doppler
    ps_cm_s = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Velocidad sistólica pico (cm/s)",
    )
    ed_cm_s = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Velocidad diastólica final (cm/s)",
    )
    ri = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Índice de resistencia",
    )
    ip = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Índice de pulsatilidad",
    )
    s_d_ratio = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Relación S/D",
    )

    # Clasificación clínica
    escotadura_diastolica = models.BooleanField(
        default=False, help_text="Presencia de escotadura diastólica",
    )
    clasificacion = models.CharField(
        max_length=30,
        default="normal",
        choices=[
            ("normal", "Normal"),
            ("resistencia_aumentada", "Resistencia Aumentada"),
            ("escotadura_bilateral", "Escotadura Bilateral"),
            ("alto_riesgo", "Alto Riesgo"),
        ],
    )

    # Auditoría
    realizado_por = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.SET_NULL, null=True,
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True)

    class Meta:
        """Meta"""
        db_table = "doppler_materno"
        ordering = ["-fecha_examen"]
        verbose_name = "Doppler Materno"
        verbose_name_plural = "Dopplers Maternos"

    def __str__(self):
        """Str"""
        return f"Doppler {self.paciente} - Sem {self.edad_gestacional_semanas}"

    def calcular_ri(self):
        """Calcula Índice de Resistencia: (PS - ED) / PS"""
        if self.ps_cm_s and self.ed_cm_s and self.ps_cm_s > 0:
            return round((self.ps_cm_s - self.ed_cm_s) / self.ps_cm_s, 3)
        return None

    def calcular_sd_ratio(self):
        """Calcula relación S/D: PS / ED"""
        if self.ps_cm_s is not None and self.ed_cm_s and self.ed_cm_s > 0:
            return round(self.ps_cm_s / self.ed_cm_s, 2)
        return None

    @property
    def es_alto_riesgo(self) -> bool:
        """Evalúa si el Doppler indica alto riesgo de preeclampsia"""
        if (
            self.ip
            and self.edad_gestacional_semanas >= 11
            and self.edad_gestacional_semanas <= 13
        ):
            return self.ip > 2.35
        if self.ip and self.edad_gestacional_semanas > 13:
            return self.ip > 1.45
        return bool(self.escotadura_diastolica)
