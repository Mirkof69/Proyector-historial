"""=============================================================================
MODELOS - NOTAS DE EVOLUCIÓN
=============================================================================
Sistema completo de notas médicas de evolución del paciente
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from pacientes.models import Paciente

# from embarazos.models import Embarazo  # REMOVED to fix circular import
# from controles.models import ControlPrenatal  # REMOVED to fix circular import
from usuarios.models import Usuario


class NotaEvolucion(models.Model):
    """Nota de evolución médica - Registro detallado de cada consulta o control

    Incluye:
        pass
    - Motivo de consulta
    - Signos vitales
    - Examen físico
    - Impresión diagnóstica
    - Plan de tratamiento
    - Observaciones
    """

    TIPO_CONSULTA_CHOICES = [
        ("control_prenatal", "Control Prenatal"),
        ("urgencia", "Consulta de Urgencia"),
        ("seguimiento", "Seguimiento"),
        ("interconsulta", "Interconsulta"),
        ("puerperio", "Control Puerperio"),
        ("otro", "Otro"),
    ]

    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="notas_evolucion",
        verbose_name="Paciente",
    )

    embarazo = models.ForeignKey(
        "embarazos.Embarazo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_evolucion",
        verbose_name="Embarazo Asociado",
    )

    control_prenatal = models.ForeignKey(
        "controles.ControlPrenatal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_evolucion",
        verbose_name="Control Prenatal Asociado",
    )

    medico = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="notas_evolucion_creadas",
        verbose_name="Médico Responsable",
    )

    # Información de la consulta
    fecha_consulta = models.DateTimeField(verbose_name="Fecha y Hora de Consulta")

    tipo_consulta = models.CharField(
        max_length=30,
        choices=TIPO_CONSULTA_CHOICES,
        default="control_prenatal",
        verbose_name="Tipo de Consulta",
    )

    # Motivo de consulta
    motivo_consulta = models.TextField(
        verbose_name="Motivo de Consulta",
        help_text="Razón principal de la consulta según paciente",
    )

    # Signos vitales
    presion_arterial_sistolica = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(250)],
        verbose_name="Presión Arterial Sistólica (mmHg)",
    )

    presion_arterial_diastolica = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(150)],
        verbose_name="Presión Arterial Diastólica (mmHg)",
    )

    frecuencia_cardiaca = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(200)],
        verbose_name="Frecuencia Cardíaca (lpm)",
    )

    frecuencia_respiratoria = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(40)],
        verbose_name="Frecuencia Respiratoria (rpm)",
    )

    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(35.0), MaxValueValidator(42.0)],
        verbose_name="Temperatura (°C)",
    )

    saturacion_oxigeno = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(70), MaxValueValidator(100)],
        verbose_name="Saturación de Oxígeno (%)",
    )

    # Datos obstétricos (si aplica)
    edad_gestacional_semanas = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(4), MaxValueValidator(45)],
        verbose_name="Edad Gestacional (semanas)",
    )

    edad_gestacional_dias = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="Edad Gestacional (días adicionales)",
    )

    altura_uterina = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        verbose_name="Altura Uterina (cm)",
    )

    frecuencia_cardiaca_fetal = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(100), MaxValueValidator(180)],
        verbose_name="Frecuencia Cardíaca Fetal (lpm)",
    )

    presentacion_fetal = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Presentación Fetal",
        help_text="Ej: Cefálica, Pélvica, Transversa",
    )

    movimientos_fetales = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Movimientos Fetales",
        help_text="Presentes/Ausentes, Frecuencia",
    )

    # Examen físico
    examen_fisico = models.TextField(
        verbose_name="Examen Físico Completo",
        help_text="Hallazgos del examen físico general y por sistemas",
    )

    examen_obstetrico = models.TextField(
        blank=True,
        verbose_name="Examen Obstétrico",
        help_text="Maniobras de Leopold, especuloscopía, tacto vaginal",
    )

    # Diagnóstico y plan
    diagnosticos = models.TextField(
        verbose_name="Impresión Diagnóstica",
        help_text="Lista de diagnósticos actuales (CIE-10 si es posible)",
    )

    plan_tratamiento = models.TextField(
        verbose_name="Plan de Tratamiento",
        help_text="Medicamentos, indicaciones, estudios a solicitar",
    )

    indicaciones = models.TextField(
        blank=True,
        verbose_name="Indicaciones al Paciente",
        help_text="Signos de alarma, cuidados, próxima cita",
    )

    # Observaciones adicionales
    observaciones = models.TextField(
        blank=True, verbose_name="Observaciones Adicionales",
    )

    # Control de calidad
    revisado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_evolucion_revisadas",
        verbose_name="Revisado Por",
    )

    fecha_revision = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Revisión",
    )

    # Trazabilidad
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro",
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Última Modificación",
    )

    activo = models.BooleanField(
        default=True, verbose_name="Activo", help_text="Nota visible en el sistema",
    )

    # Trazabilidad adicional
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_evolucion_creadas_trazabilidad",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_evolucion_modificadas",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "notas_evolucion"
        verbose_name = "Nota de Evolución"
        verbose_name_plural = "Notas de Evolución"
        ordering = ["-fecha_consulta"]
        indexes = [
            models.Index(fields=["paciente", "-fecha_consulta"]),
            models.Index(fields=["embarazo", "-fecha_consulta"]),
            models.Index(fields=["medico", "-fecha_consulta"]),
        ]

    def __str__(self):
        """Str"""
        return f"Nota {self.id} - {self.paciente.nombre_completo} - {self.fecha_consulta.strftime('%d/%m/%Y')}"

    @property
    def presion_arterial(self):
        """Retorna PA en formato 120/80"""
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            return (
                f"{self.presion_arterial_sistolica}/{self.presion_arterial_diastolica}"
            )
        return None

    @property
    def edad_gestacional_completa(self):
        """Retorna EG en formato 32w 4d"""
        if self.edad_gestacional_semanas is not None:
            dias = self.edad_gestacional_dias or 0
            return f"{self.edad_gestacional_semanas}s {dias}d"
        return None
