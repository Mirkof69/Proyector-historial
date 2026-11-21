"""=============================================================================
MODELO - HISTORIAL DE CALCULADORAS SIMPLES
=============================================================================
Persistencia para las 8 calculadoras simples del frontend (Edad Gestacional,
Score de Bishop, IMC, Riesgo Preeclampsia, Diabetes Gestacional, Indice
Liquido Amniotico, Peso Fetal, Score de Apgar). Antes solo se guardaban en
localStorage del navegador y se perdian al cerrar sesion o cambiar de
dispositivo.

No confundir con CalculadoraRiesgo (modelo clinico FMF en models.py): ese es
un sistema distinto con campos especificos por patologia. Este modelo es
generico — guarda los inputs/resultado como JSON porque cada una de las 8
calculadoras tiene una forma de datos distinta.
=============================================================================
"""

from django.db import models

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class CalculoHistorial(models.Model):
    """Historial de resultados de las calculadoras simples (no clinicas FMF)"""

    TIPO_CALCULADORA = [
        ("edad_gestacional", "Edad Gestacional"),
        ("bishop", "Score de Bishop"),
        ("imc", "IMC"),
        ("riesgo_preeclampsia", "Riesgo de Preeclampsia"),
        ("diabetes_gestacional", "Diabetes Gestacional"),
        ("ila", "Indice de Liquido Amniotico"),
        ("peso_fetal", "Peso Fetal"),
        ("apgar", "Score de Apgar"),
        ("capurro", "Método de Capurro"),
        ("silverman", "Test de Silverman-Andersen"),
        ("ballard", "Ballard Score"),
        ("icc", "Indice Cardio-Cerebral"),
        ("pa_media", "Presión Arterial Media"),
        ("fc_maxima", "Frecuencia Cardíaca Máxima"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculos_historial",
        verbose_name="Paciente",
    )
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculos_historial",
        verbose_name="Embarazo",
    )
    tipo_calculadora = models.CharField(
        max_length=30, choices=TIPO_CALCULADORA, db_index=True,
        verbose_name="Tipo de Calculadora",
    )
    inputs_json = models.JSONField(
        default=dict, verbose_name="Datos de entrada",
        help_text="Valores ingresados en el formulario de la calculadora",
    )
    resultado_json = models.JSONField(
        default=dict, verbose_name="Resultado calculado",
    )
    resultado_resumen = models.CharField(
        max_length=255, blank=True, default="",
        verbose_name="Resumen del resultado",
        help_text="Texto corto para mostrar en listados sin abrir el detalle",
    )
    fecha_calculo = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Fecha de cálculo",
    )
    calculado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculos_historial_realizados",
        verbose_name="Calculado por",
    )

    class Meta:
        """Meta"""
        db_table = "calculadoras_historial"
        verbose_name = "Historial de Cálculo"
        verbose_name_plural = "Historial de Cálculos"
        ordering = ["-fecha_calculo"]
        indexes = [
            models.Index(fields=["tipo_calculadora", "-fecha_calculo"]),
            models.Index(fields=["paciente", "-fecha_calculo"]),
        ]

    def __str__(self):
        """Str"""
        return f"{self.get_tipo_calculadora_display()} - {self.fecha_calculo:%d/%m/%Y %H:%M}"
