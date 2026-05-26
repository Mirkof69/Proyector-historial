"""=============================================================================
MÓDULO: CONSULTORIOS - MODELS
=============================================================================
Gestión de consultorios y espacios físicos
Para asignación de citas y control de ubicaciones
=============================================================================
"""

from django.db import models


class Consultorio(models.Model):
    """Consultorios y espacios físicos de la clínica
    """

    # ============== IDENTIFICACIÓN ==============
    nombre = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nombre identificador del consultorio (ej: 'Consultorio 1')",
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Código interno (ej: 'CONS-01')",
    )

    # ============== UBICACIÓN ==============
    ubicacion = models.CharField(
        max_length=100, help_text="Descripción de ubicación general",
    )

    piso = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Piso o nivel (ej: 'Planta Baja', 'Piso 1')",
    )

    edificio = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Edificio (para clínicas con múltiples edificios)",
    )

    # ============== CARACTERÍSTICAS ==============
    tipo_consultorio = models.CharField(
        max_length=30,
        choices=[
            ("general", "Consulta General"),
            ("ginecologia", "Ginecología"),
            ("ecografia", "Ecografía"),
            ("laboratorio", "Laboratorio"),
            ("procedimientos", "Procedimientos"),
            ("urgencias", "Urgencias"),
        ],
        default="general",
    )

    capacidad_personas = models.PositiveIntegerField(
        default=3,
        help_text="Capacidad máxima de personas (incluyendo paciente y médico)",
    )

    tiene_bano = models.BooleanField(default=False)
    tiene_camilla = models.BooleanField(default=True)
    tiene_ecografo = models.BooleanField(default=False)

    # ============== EQUIPAMIENTO ==============
    equipamiento = models.TextField(
        null=True, blank=True, help_text="Lista de equipamiento disponible",
    )

    # ============== ESTADO ==============
    activo = models.BooleanField(
        default=True, help_text="Consultorio disponible para asignación",
    )

    en_mantenimiento = models.BooleanField(
        default=False, help_text="Consultorio temporalmente fuera de servicio",
    )

    observaciones = models.TextField(
        null=True, blank=True, help_text="Observaciones adicionales",
    )

    # ============== METADATOS ==============
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    # Trazabilidad
    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultorios_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultorios_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        verbose_name = "Consultorio"
        verbose_name_plural = "Consultorios"
        db_table = "consultorios"
        ordering = ["nombre"]

    def __str__(self):
        """Str"""
        return f"{self.nombre} - {self.ubicacion}"

    def esta_disponible(self):
        """Verifica si el consultorio está disponible"""
        return self.activo and not self.en_mantenimiento

    def get_descripcion_completa(self):
        """Descripción completa del consultorio"""
        partes = [self.nombre]
        if self.piso:
            partes.append(f"Piso: {self.piso}")
        if self.edificio:
            partes.append(f"Edificio: {self.edificio}")
        partes.append(self.ubicacion)
        return " | ".join(partes)
