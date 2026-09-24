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


#: 44 semanas: más allá, un embarazo en curso no es plausible.
MAX_DIAS_EMBARAZO_EN_CURSO = 44 * 7


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
        on_delete=models.PROTECT,
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
        constraints = [
            # «Un solo embarazo activo por paciente» se validaba solo en el
            # serializer: dos peticiones simultáneas (doble clic, dos
            # pestañas) podían crear dos. Ahora lo garantiza la base.
            models.UniqueConstraint(
                fields=["paciente"], condition=models.Q(estado="activo"),
                name="un_embarazo_activo_por_paciente",
            ),
        ]
        indexes = [
            models.Index(fields=["paciente", "estado"], name="embarazo_paciente_estado"),
        ]

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

        from django.core.exceptions import ValidationError

        errors = {}

        # ✅ 1. VALIDAR FUM - NO PUEDE ESTAR EN EL FUTURO
        if self.fecha_ultima_menstruacion:
            if self.fecha_ultima_menstruacion > timezone.localdate():
                errors["fecha_ultima_menstruacion"] = (
                    "La Fecha de Última Menstruación no puede estar en el futuro."
                )

            # Un embarazo EN CURSO no puede pasar de 44 semanas. Solo se
            # comprueba al registrar o cambiar la FUM de un embarazo activo:
            # antes se exigía siempre y un embarazo terminado hace más de un
            # año no se podía editar ni para corregir una nota.
            dias = (timezone.localdate() - self.fecha_ultima_menstruacion).days
            if self.estado == "activo" and dias > MAX_DIAS_EMBARAZO_EN_CURSO and self._fum_es_nueva():
                errors["fecha_ultima_menstruacion"] = (
                    f"Con esa FUM el embarazo tendría {dias // 7} semanas. Un embarazo en "
                    "curso no pasa de 44: revise la fecha o regístrelo como finalizado."
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

        # ✅ 4. VALIDAR EDAD DE LA PACIENTE (a la fecha del embarazo, no a hoy)
        if self.paciente and self.paciente.fecha_nacimiento and self.fecha_ultima_menstruacion:
            nacimiento, fum = self.paciente.fecha_nacimiento, self.fecha_ultima_menstruacion
            edad = fum.year - nacimiento.year - ((fum.month, fum.day) < (nacimiento.month, nacimiento.day))
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

    def _fum_es_nueva(self):
        """True si la FUM se registra ahora o es distinta de la guardada."""
        if not self.pk:
            return True
        guardada = (
            type(self).objects.filter(pk=self.pk)
            .values_list("fecha_ultima_menstruacion", flat=True).first()
        )
        return guardada != self.fecha_ultima_menstruacion

    def save(self, *args, **kwargs):
        if self.fecha_ultima_menstruacion and not self.fecha_probable_parto:
            self.fecha_probable_parto = self.fecha_ultima_menstruacion + timedelta(days=280)
        super().save(*args, **kwargs)

    def __str__(self):
        """Str"""
        return f"Embarazo {self.numero_gesta} - {self.paciente.id_clinico}"
