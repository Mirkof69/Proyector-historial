"""=============================================================================
MÓDULO: VACUNAS - MODELS
=============================================================================
Modelos para gestión de vacunas en sistema de atención prenatal
- TipoVacuna: Catálogo de vacunas disponibles
- RegistroVacuna: Registro de vacunas aplicadas a pacientes
=============================================================================
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from pacientes.models import Paciente

# from embarazos.models import Embarazo  # REMOVED to fix circular import
from usuarios.models import Usuario


class TipoVacuna(models.Model):
    """Catálogo de tipos de vacunas disponibles
    Define las características y requisitos de cada vacuna
    """

    # Información básica
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la Vacuna",
        help_text="Nombre oficial de la vacuna",
    )

    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción detallada de la vacuna y su propósito",
    )

    # Esquema de dosificación
    dosis_requeridas = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Dosis Requeridas",
        help_text="Número de dosis necesarias para completar el esquema",
    )

    intervalo_dosis_dias = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Intervalo entre Dosis (días)",
        help_text="Días mínimos entre cada dosis (si aplica)",
    )

    # Requisitos de edad
    edad_minima_aplicacion = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Edad Mínima de Aplicación",
        help_text="Edad mínima en días para aplicar la vacuna",
    )

    # Información médica
    contraindicaciones = models.TextField(
        blank=True,
        verbose_name="Contraindicaciones",
        help_text="Condiciones que impiden la aplicación de la vacuna",
    )

    efectos_secundarios = models.TextField(
        blank=True,
        verbose_name="Efectos Secundarios",
        help_text="Efectos secundarios comunes y raros de la vacuna",
    )

    # Clasificación
    obligatoria_embarazo = models.BooleanField(
        default=False,
        verbose_name="Obligatoria en Embarazo",
        help_text="Indica si es obligatoria durante el embarazo",
    )

    # Estado
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si la vacuna está activa en el catálogo",
    )

    # Metadatos
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación",
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Modificación",
    )

    # Trazabilidad
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tipos_vacunas_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tipos_vacunas_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "tipos_vacunas"
        verbose_name = "Tipo de Vacuna"
        verbose_name_plural = "Tipos de Vacunas"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["activo"]),
            models.Index(fields=["obligatoria_embarazo"]),
        ]

    def __str__(self):
        """Str"""
        return f"{self.nombre} ({self.dosis_requeridas} dosis)"

    @property
    def es_multidosis(self) -> bool:
        """Verifica si requiere múltiples dosis"""
        return self.dosis_requeridas > 1

    @property
    def tiene_contraindicaciones(self) -> bool:
        """Verifica si tiene contraindicaciones registradas"""
        return bool(self.contraindicaciones)

    def clean(self):
        """Validaciones personalizadas"""
        if self.dosis_requeridas > 1 and not self.intervalo_dosis_dias:
            raise ValidationError(
                {
                    "intervalo_dosis_dias": "Las vacunas multidosis deben especificar el intervalo entre dosis",
                },
            )

    def get_resumen(self):
        """Retorna un resumen de la vacuna"""
        resumen = f"{self.nombre}"
        if self.es_multidosis:
            resumen += f" - {self.dosis_requeridas} dosis"
        if self.obligatoria_embarazo:
            resumen += " (Obligatoria en embarazo)"
        return resumen


class RegistroVacuna(models.Model):
    """Registro de vacunas aplicadas a pacientes embarazadas
    Almacena información detallada de cada aplicación
    """

    VIAS_ADMINISTRACION = (
        ("intramuscular", "Intramuscular"),
        ("subcutanea", "Subcutánea"),
        ("oral", "Oral"),
        ("intradermica", "Intradérmica"),
    )

    # Relaciones principales
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="vacunas",
        verbose_name="Paciente",
        help_text="Paciente que recibió la vacuna",
    )

    embarazo = models.ForeignKey(
        "embarazos.Embarazo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacunas",
        verbose_name="Embarazo",
        help_text="Embarazo durante el cual se aplicó la vacuna",
    )

    tipo_vacuna = models.ForeignKey(
        TipoVacuna,
        on_delete=models.PROTECT,
        related_name="registros",
        verbose_name="Tipo de Vacuna",
        help_text="Tipo de vacuna aplicada",
    )

    # Información de aplicación
    fecha_aplicacion = models.DateTimeField(
        verbose_name="Fecha y Hora de Aplicación",
        help_text="Fecha y hora en que se aplicó la vacuna",
    )

    numero_dosis = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Número de Dosis",
        help_text="Número de dosis dentro del esquema (1, 2, 3, etc.)",
    )

    # Detalles del producto
    lote = models.CharField(
        max_length=50, verbose_name="Lote", help_text="Número de lote de la vacuna",
    )

    laboratorio = models.CharField(
        max_length=100,
        verbose_name="Laboratorio",
        help_text="Laboratorio fabricante de la vacuna",
    )

    # Detalles de administración
    via_administracion = models.CharField(
        max_length=20,
        choices=VIAS_ADMINISTRACION,
        verbose_name="Vía de Administración",
        help_text="Vía por la cual se administró la vacuna",
    )

    sitio_aplicacion = models.CharField(
        max_length=100,
        verbose_name="Sitio de Aplicación",
        help_text="Ubicación anatómica donde se aplicó (ej: Deltoides izquierdo)",
    )

    # Responsable
    aplicado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacunas_aplicadas",
        verbose_name="Aplicado Por",
        help_text="Profesional que aplicó la vacuna",
    )

    # Seguimiento
    proxima_dosis_fecha = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Próxima Dosis",
        help_text="Fecha programada para la siguiente dosis (si aplica)",
    )

    # Reacciones y observaciones
    reacciones_adversas = models.TextField(
        blank=True,
        verbose_name="Reacciones Adversas",
        help_text="Reacciones adversas reportadas después de la aplicación",
    )

    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre la aplicación",
    )

    # Estado
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el registro está activo",
    )

    # Metadatos
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro",
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Modificación",
    )

    # Trazabilidad
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_vacunas_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_vacunas_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "registros_vacunas"
        verbose_name = "Registro de Vacuna"
        verbose_name_plural = "Registros de Vacunas"
        ordering = ["-fecha_aplicacion"]
        indexes = [
            models.Index(fields=["paciente", "tipo_vacuna"]),
            models.Index(fields=["fecha_aplicacion"]),
            models.Index(fields=["embarazo"]),
            models.Index(fields=["tipo_vacuna", "numero_dosis"]),
            models.Index(fields=["proxima_dosis_fecha"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["paciente", "tipo_vacuna", "numero_dosis", "fecha_aplicacion"],
                name="unique_vacuna_aplicacion",
            ),
        ]

    def __str__(self):
        """Str"""
        paciente_nombre = (
            self.paciente.nombre_completo if self.paciente else "Sin paciente"
        )
        return (
            f"{self.tipo_vacuna.nombre} - Dosis {self.numero_dosis} - {paciente_nombre}"
        )

    def clean(self):
        """Validaciones personalizadas"""
        # Validar que el número de dosis no exceda las requeridas
        if self.tipo_vacuna and self.numero_dosis > self.tipo_vacuna.dosis_requeridas:
            raise ValidationError(
                {
                    "numero_dosis": f"El número de dosis no puede exceder {self.tipo_vacuna.dosis_requeridas} para esta vacuna",
                },
            )

        # Validar que la fecha de próxima dosis sea futura
        if self.proxima_dosis_fecha:

            if self.proxima_dosis_fecha <= timezone.localdate():
                raise ValidationError(
                    {"proxima_dosis_fecha": "La fecha de próxima dosis debe ser futura"},
                )

    @property
    def esquema_completo(self) -> bool:
        """Verifica si se completó el esquema de vacunación"""
        return self.numero_dosis >= self.tipo_vacuna.dosis_requeridas

    @property
    def tiene_reacciones_adversas(self) -> bool:
        """Verifica si se reportaron reacciones adversas"""
        return bool(self.reacciones_adversas)

    @property
    def requiere_siguiente_dosis(self) -> bool:
        """Verifica si requiere siguiente dosis"""
        return (
            not self.esquema_completo
            and self.tipo_vacuna.dosis_requeridas > self.numero_dosis
        )

    @property
    def paciente_info(self):
        """Información resumida del paciente"""
        if not self.paciente:
            return None
        return {
            "id": self.paciente.id,
            "nombre": self.paciente.nombre_completo,
            "id_clinico": self.paciente.id_clinico,
        }

    @property
    def embarazo_info(self):
        """Información resumida del embarazo"""
        if not self.embarazo:
            return None
        return {
            "id": self.embarazo.id,
            "numero_gesta": self.embarazo.numero_gesta,
        }

    @property
    def aplicador_info(self):
        """Información del profesional que aplicó la vacuna"""
        if not self.aplicado_por:
            return None
        return {
            "id": self.aplicado_por.id,
            "nombre": self.aplicado_por.nombre_completo,
            "rol": getattr(self.aplicado_por, 'get_rol_display', lambda: '')(),
        }

    def get_progreso_esquema(self):
        """Retorna el progreso del esquema de vacunación"""
        total = self.tipo_vacuna.dosis_requeridas
        actual = self.numero_dosis
        porcentaje = (actual / total) * 100
        return {
            "dosis_actual": actual,
            "dosis_total": total,
            "porcentaje": round(porcentaje, 2),
            "completado": self.esquema_completo,
        }

    def get_resumen(self):
        """Retorna un resumen del registro"""
        resumen = f"{self.tipo_vacuna.nombre} - Dosis {self.numero_dosis}/{self.tipo_vacuna.dosis_requeridas}"
        if self.esquema_completo:
            resumen += " (Completado)"
        elif self.proxima_dosis_fecha:
            resumen += f" (Próxima: {self.proxima_dosis_fecha.strftime('%d/%m/%Y')})"
        return resumen

    def calcular_proxima_dosis_fecha(self):
        """Calcula automáticamente la fecha de próxima dosis"""
        if self.requiere_siguiente_dosis and self.tipo_vacuna.intervalo_dosis_dias:
            from datetime import timedelta

            return self.fecha_aplicacion.date() + timedelta(
                days=self.tipo_vacuna.intervalo_dosis_dias,
            )
        return None

    def save(self, *args, **kwargs):
        """Guarda el registro y calcula la próxima dosis si no está especificada"""
        # Auto-calcular próxima dosis si no está definida
        if not self.proxima_dosis_fecha and self.requiere_siguiente_dosis:
            self.proxima_dosis_fecha = self.calcular_proxima_dosis_fecha()

        super().save(*args, **kwargs)
