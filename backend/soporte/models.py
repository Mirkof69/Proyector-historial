"""Models module."""
from django.db import models


class TicketSoporte(models.Model):
    """Ticket de soporte tecnico creado por un usuario del sistema."""

    MODULO_CHOICES = [
        ("login", "Acceso / Login"),
        ("pacientes", "Pacientes"),
        ("controles", "Controles Prenatales"),
        ("reportes", "Reportes"),
        ("otro", "Otro"),
    ]

    PRIORIDAD_CHOICES = [
        ("baja", "Baja (Consulta)"),
        ("media", "Media (Funcionalidad parcial)"),
        ("alta", "Alta (Sistema detenido)"),
    ]

    ESTADO_CHOICES = [
        ("abierto", "Abierto"),
        ("en_proceso", "En Proceso"),
        ("resuelto", "Resuelto"),
        ("cerrado", "Cerrado"),
    ]

    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_soporte",
        verbose_name="Usuario solicitante",
    )

    asunto = models.CharField(max_length=200, verbose_name="Asunto")

    modulo = models.CharField(
        max_length=20, choices=MODULO_CHOICES, verbose_name="Módulo afectado",
    )

    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default="media",
        verbose_name="Prioridad",
    )

    descripcion = models.TextField(verbose_name="Descripción detallada")

    estado = models.CharField(
        max_length=15, choices=ESTADO_CHOICES, default="abierto", verbose_name="Estado",
    )

    respuesta_admin = models.TextField(blank=True, verbose_name="Respuesta del equipo de TI")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta"""
        db_table = "tickets_soporte"
        ordering = ["-fecha_creacion"]
        verbose_name = "Ticket de Soporte"
        verbose_name_plural = "Tickets de Soporte"

    def __str__(self):
        """Str"""
        return f"#{self.id} - {self.asunto}"
