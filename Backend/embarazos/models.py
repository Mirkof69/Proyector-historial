"""Models module."""
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, ClassVar

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from pacientes.models import Paciente

if TYPE_CHECKING:
    from controles.models import ControlPrenatal


class Embarazo(models.Model):
    if TYPE_CHECKING:
        controles: ClassVar[QuerySet[ControlPrenatal]]
    """Embarazo"""
    TIPOS = (
        ("simple", "Simple"),
        ("gemelar", "Gemelar"),
        ("multiple", "Múltiple"),
    )

    RIESGOS = (
        ("bajo", "Bajo"),
        ("medio", "Medio"),
        ("alto", "Alto"),
    )

    ESTADOS = (
        ("activo", "Activo"),
        ("finalizado", "Finalizado"),
        ("perdida", "Pérdida"),
    )

    # Campos del modelo
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        db_column="paciente_id",
        related_name="embarazos",
    )
    numero_gesta = models.IntegerField()
    numero_para = models.IntegerField(default=0)
    numero_abortos = models.IntegerField(default=0)
    numero_cesareas = models.IntegerField(default=0)
    fecha_ultima_menstruacion = models.DateField()
    fecha_probable_parto = models.DateField(blank=True, null=True)
    tipo_embarazo = models.CharField(max_length=50, choices=TIPOS, default="simple")
    riesgo_embarazo = models.CharField(max_length=50, choices=RIESGOS, default="bajo")
    estado = models.CharField(max_length=50, choices=ESTADOS, default="activo")
    notas = models.TextField(blank=True, null=True)
    medico_responsable = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="embarazos_responsable",
        db_column="medico_responsable_id",
        limit_choices_to={"rol": "medico"},
    )

    # ✅ CAMPOS ANTROPOMÉTRICOS PREGESTACIONALES
    peso_pregestacional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Peso Pregestacional (kg)",
        help_text="Peso de la paciente antes del embarazo en kilogramos",
    )
    talla_materna = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Talla Materna (cm)",
        help_text="Altura de la paciente en centímetros",
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    # Trazabilidad
    created_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="embarazos_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="embarazos_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "embarazos"
        ordering = ["-fecha_registro"]
        # managed = False  ← ELIMINADO

    @property
    def fur(self):
        """Alias para fecha_ultima_menstruacion (FUR = Fecha Última Regla)"""
        return self.fecha_ultima_menstruacion

    @property
    def imc_pregestacional(self):
        """Calcula el Índice de Masa Corporal (IMC) pregestacional"""
        if self.peso_pregestacional and self.talla_materna:
            # IMC = peso (kg) / (altura (m))^2
            altura_m = float(self.talla_materna) / 100  # Convertir cm a metros
            imc_value = float(self.peso_pregestacional) / (altura_m**2)
            return round(imc_value, 2)
        return None

    def clean(self):
        """✅ VALIDACIONES CRÍTICAS DEL EMBARAZO"""
        from datetime import timedelta

        from django.core.exceptions import ValidationError

        errors = {}

        # ✅ 1. VALIDAR FUM - NO PUEDE ESTAR EN EL FUTURO
        if self.fecha_ultima_menstruacion:
            if self.fecha_ultima_menstruacion > timezone.localdate():
                errors["fecha_ultima_menstruacion"] = (
                    "La Fecha de Última Menstruación no puede estar en el futuro."
                )

            # Validar que la FUM no sea muy antigua (más de 1 año atrás)
            hace_un_anio = timezone.localdate() - timedelta(days=365)
            if self.fecha_ultima_menstruacion < hace_un_anio:
                errors["fecha_ultima_menstruacion"] = (
                    "La Fecha de Última Menstruación no puede ser mayor a 1 año atrás."
                )

        # ✅ 2. VALIDAR G/P - NÚMERO DE PARTOS NO PUEDE SER MAYOR QUE GESTAS
        if self.numero_para > self.numero_gesta:
            errors["numero_para"] = (
                f"El número de partos ({self.numero_para}) no puede ser mayor que el número de gestas ({self.numero_gesta})."
            )

        # ✅ 2b. VALIDAR CESÁREAS ≤ PARTOS - NO PUEDE HABER MÁS CESÁREAS QUE PARTOS
        if (
            self.numero_cesareas
            and self.numero_para is not None
            and self.numero_cesareas > self.numero_para
        ):
            errors["numero_cesareas"] = (
                "El número de cesáreas no puede ser mayor al número de partos"
            )

        # ✅ 3. VALIDAR QUE G = P + ABORTOS + EMBARAZO ACTUAL
        total_embarazos = (
            self.numero_para + self.numero_abortos + 1
        )  # +1 por el embarazo actual
        if self.numero_gesta != total_embarazos:
            errors["numero_gesta"] = (
                f"El número de gestas ({self.numero_gesta}) no coincide con P({self.numero_para}) + Abortos({self.numero_abortos}) + Actual(1) = {total_embarazos}."
            )
        # ✅ 4. VALIDAR NÚMERO MÍNIMO DE GESTA
        if self.numero_gesta is not None and self.numero_gesta < 1:
            errors["numero_gesta"] = "El número de gestas debe ser al menos 1."

        # ✅ 4. VALIDAR EDAD DE LA PACIENTE
        if self.paciente:
            edad = self.paciente.edad
            if edad < 10:
                errors["paciente"] = (
                    f"La paciente tiene {edad} años. La edad mínima para embarazo es 10 años."
                )
            elif edad > 60:
                errors["paciente"] = (
                    f"La paciente tiene {edad} años. Edad muy avanzada para embarazo (máximo 60 años)."
                )

        # ✅ 5. VALIDAR PESO Y TALLA MATERNA
        if self.peso_pregestacional:
            if self.peso_pregestacional < 30:
                errors["peso_pregestacional"] = (
                    f"Peso pregestacional ({self.peso_pregestacional} kg) parece muy bajo. Mínimo 30 kg."
                )
            elif self.peso_pregestacional > 200:
                errors["peso_pregestacional"] = (
                    f"Peso pregestacional ({self.peso_pregestacional} kg) parece muy alto. Máximo 200 kg."
                )

        if self.talla_materna:
            if self.talla_materna < 100:
                errors["talla_materna"] = (
                    f"Talla materna ({self.talla_materna} cm) parece muy baja. Mínimo 100 cm."
                )
            elif self.talla_materna > 230:
                errors["talla_materna"] = (
                    f"Talla materna ({self.talla_materna} cm) parece muy alta. Máximo 230 cm."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.fecha_ultima_menstruacion and not self.fecha_probable_parto:
            self.fecha_probable_parto = self.fecha_ultima_menstruacion + timedelta(days=280)
        super().save(*args, **kwargs)

    def __str__(self):
        """Str"""
        return f"Embarazo {self.numero_gesta} - {self.paciente.id_clinico}"
