"""=============================================================================
MÓDULO: ANTECEDENTES - MODELS
=============================================================================
Gestión completa de antecedentes gineco-obstétricos y patológicos
Crítico para evaluación de riesgos y seguridad del paciente
=============================================================================
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AntecedenteGinecoObstetrico(models.Model):
    """Antecedentes gineco-obstétricos del paciente
    Una sola instancia por paciente (OneToOne)
    """

    # Relación con Paciente
    paciente = models.OneToOneField(
        "pacientes.Paciente",
        on_delete=models.CASCADE,
        related_name="antecedente_gineco",
        db_column="paciente_id",
    )

    # ============== ANTECEDENTES MENSTRUALES ==============
    menarquia_edad = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(8), MaxValueValidator(25)],
        help_text="Edad de primera menstruación (8-25 años)",
    )

    ciclos_menstruales = models.CharField(
        max_length=20,
        choices=[
            ("regular", "Regular"),
            ("irregular", "Irregular"),
            ("amenorrea", "Amenorrea"),
        ],
        null=True,
        blank=True,
    )

    duracion_ciclo_dias = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(21), MaxValueValidator(45)],
        help_text="Duración del ciclo en días (21-45)",
    )

    duracion_menstruacion_dias = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(2), MaxValueValidator(9)],
        help_text="Duración del sangrado en días (2-9)",
    )

    fecha_ultima_menstruacion = models.DateField(
        null=True, blank=True, verbose_name="Fecha de Última Menstruación (FUM)",
    )

    # ============== FÓRMULA OBSTÉTRICA G-P-A-C ==============
    gestas = models.PositiveIntegerField(
        default=0, help_text="Número total de embarazos (incluyendo actual)",
    )

    partos = models.PositiveIntegerField(
        default=0, help_text="Número de partos (> 20 semanas)",
    )

    abortos = models.PositiveIntegerField(
        default=0, help_text="Número de abortos (< 20 semanas)",
    )

    cesareas = models.PositiveIntegerField(default=0, help_text="Número de cesáreas")

    hijos_vivos = models.PositiveIntegerField(
        default=0, help_text="Número de hijos vivos actualmente",
    )

    # ============== ANTICONCEPCIÓN ==============
    metodo_anticonceptivo_actual = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Método anticonceptivo en uso (si aplica)",
    )

    tiempo_uso_anticonceptivo_meses = models.PositiveIntegerField(
        null=True, blank=True, help_text="Tiempo de uso del método en meses",
    )

    fecha_suspension_anticonceptivo = models.DateField(
        null=True, blank=True, help_text="Fecha de suspensión (si aplica)",
    )

    # ============== VIDA SEXUAL ==============
    inicio_vida_sexual_edad = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        help_text="Edad de inicio de vida sexual",
    )

    numero_parejas_sexuales = models.PositiveIntegerField(
        null=True, blank=True, help_text="Número de parejas sexuales",
    )

    # ============== METADATOS ==============
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="antecedentes_gineco_modificados",
    )

    class Meta:
        """Meta"""
        verbose_name = "Antecedente Gineco-Obstétrico"
        verbose_name_plural = "Antecedentes Gineco-Obstétricos"
        db_table = "antecedentes_gineco_obstetricos"

    def __str__(self):
        """Str"""
        return f"Antecedente Gineco de {self.paciente} - G{self.gestas}P{self.partos}A{self.abortos}C{self.cesareas}"

    def get_formula_obstetrica(self):
        """Retorna la fórmula obstétrica GPAC"""
        return f"G{self.gestas}P{self.partos}A{self.abortos}C{self.cesareas}"


class AntecedentePatologico(models.Model):
    """Antecedentes patológicos personales y heredofamiliares
    Múltiples registros por paciente (ForeignKey)
    """

    # Relación con Paciente
    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.CASCADE,
        related_name="antecedentes_patologicos",
        db_column="paciente_id",
    )

    # Tipo de Antecedente
    tipo = models.CharField(
        max_length=20,
        choices=[("personal", "Personal"), ("heredofamiliar", "Heredofamiliar")],
        help_text="Personal: del paciente | Heredofamiliar: de familiares",
    )

    # ============== ALERGIAS (CRÍTICO) ==============
    tiene_alergias = models.BooleanField(default=False)
    alergias_medicamentos = models.TextField(
        null=True, blank=True, help_text="Detallar medicamentos y reacciones",
    )
    alergias_alimentos = models.TextField(
        null=True, blank=True, help_text="Detallar alimentos y reacciones",
    )
    alergias_otras = models.TextField(
        null=True, blank=True, help_text="Otras alergias (látex, yodo, etc.)",
    )

    # ============== ENFERMEDADES CRÓNICAS ==============
    # Endocrinas
    diabetes = models.BooleanField(default=False)
    diabetes_tipo = models.CharField(
        max_length=20,
        choices=[
            ("tipo1", "Tipo 1"),
            ("tipo2", "Tipo 2"),
            ("gestacional", "Gestacional"),
        ],
        null=True,
        blank=True,
    )

    # Cardiovasculares
    hipertension = models.BooleanField(default=False)
    cardiopatias = models.BooleanField(default=False)
    cardiopatia_detalle = models.TextField(null=True, blank=True)

    # Renales
    nefropatias = models.BooleanField(default=False)
    nefropatia_detalle = models.TextField(null=True, blank=True)

    # Hematológicas
    trastornos_coagulacion = models.BooleanField(default=False)
    anemia = models.BooleanField(default=False)

    # Autoinmunes
    lupus = models.BooleanField(default=False)
    artritis_reumatoide = models.BooleanField(default=False)

    # Respiratorias
    asma = models.BooleanField(default=False)

    # ============== ANTECEDENTES OBSTÉTRICOS ESPECÍFICOS ==============
    preeclampsia_previa = models.BooleanField(default=False)
    eclampsia_previa = models.BooleanField(default=False)
    diabetes_gestacional_previa = models.BooleanField(default=False)
    hemorragia_postparto_previa = models.BooleanField(default=False)

    # ============== OTROS ==============
    otras_enfermedades = models.TextField(
        null=True, blank=True, help_text="Otras enfermedades no listadas",
    )

    cirugiasanteriores = models.TextField(
        null=True, blank=True, help_text="Cirugías previas y fechas",
    )

    # ============== METADATOS ==============
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="antecedentes_patologicos_registrados",
    )

    class Meta:
        """Meta"""
        verbose_name = "Antecedente Patológico"
        verbose_name_plural = "Antecedentes Patológicos"
        db_table = "antecedentes_patologicos"
        ordering = ["-fecha_registro"]

    def __str__(self):
        """Str"""
        return f"Antecedente {self.tipo} de {self.paciente}"

    def tiene_factores_riesgo(self):
        """Verifica si tiene algún factor de riesgo importante"""
        return any(
            [
                self.diabetes,
                self.hipertension,
                self.cardiopatias,
                self.preeclampsia_previa,
                self.eclampsia_previa,
            ],
        )
