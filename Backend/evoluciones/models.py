"""EVOLUCIÓN EMBARAZO - Model Definition
"""

from django.db import models


# MODEL
class EvolucionEmbarazo(models.Model):
    """Agrupa citas y controles por embarazo específico"""

    embarazo = models.ForeignKey(
        "embarazos.Embarazo", on_delete=models.CASCADE, related_name="evoluciones",
    )
    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="evoluciones_embarazo",
    )
    fecha_evento = models.DateField()
    tipo_evento = models.CharField(
        max_length=30,
        choices=[
            ("cita", "Cita"),
            ("control", "Control Prenatal"),
            ("ecografia", "Ecografía"),
            ("laboratorio", "Laboratorio"),
            ("urgencia", "Urgencia"),
            ("otro", "Otro"),
        ],
    )
    descripcion = models.TextField()
    medico = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.SET_NULL, null=True, blank=True,
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta"""
        db_table = "evolucion_embarazo"
        ordering = ["-fecha_evento"]
        verbose_name = "Evolución de Embarazo"
        verbose_name_plural = "Evoluciones de Embarazo"

    def __str__(self):
        """Str"""
        return (
            f"{getattr(self, 'get_tipo_evento_display')()} - {self.paciente} - {self.fecha_evento}"
        )
