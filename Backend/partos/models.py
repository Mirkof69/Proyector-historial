"""Models module."""
import re
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

# ✅ IMPORTS NECESARIOS PARA FOREIGNKEY
from pacientes.models import Paciente

# from embarazos.models import Embarazo  # REMOVED to fix circular import


def validar_edad_gestacional(value):
    """Valida formato de edad gestacional (ej: 39+2)

    Formato válido:
        pass
    - Números: 0 a 45 semanas (incluye abortos muy tempranos y post-término)
    - Opcional: +0 a +6 días

    Ejemplos válidos: 0+2, 3, 12, 39, 39+2, 42+0
    Ejemplos inválidos: 46, 39+7, -5
    """
    # Validar formato básico (número opcional + número opcional)
    if not re.match(r"^\d{1,2}(\+\d)$", value):
        raise ValidationError(
            "Formato inválido. Use formato: 39 o 39+2 (semanas o semanas+días)",
        )

    # Separar semanas y días
    parts = value.split("+")
    try:
        semanas = int(parts[0])
        dias = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError) as exc:
        raise ValidationError("Formato inválido. Debe ser número o número+número") from exc

    # ✅ Validar rangos (ahora permite desde 0 semanas para abortos muy tempranos)
    if semanas < 0 or semanas > 45:
        raise ValidationError("Las semanas de gestación deben estar entre 0 y 45")

    if dias < 0 or dias > 6:
        raise ValidationError("Los días deben estar entre 0 y 6")


class Parto(models.Model):
    """Modelo principal del Parto - VERSIÓN CORREGIDA CON FOREIGNKEY"""

    TIPO_PARTO_CHOICES = [
        ("vaginal_espontaneo", "Vaginal Espontáneo"),
        ("vaginal_instrumentado", "Vaginal Instrumentado"),
        ("cesarea_electiva", "Cesárea Electiva"),
        ("cesarea_urgencia", "Cesárea de Urgencia"),
        ("cesarea_emergencia", "Cesárea de Emergencia"),
    ]

    PRESENTACION_CHOICES = [
        ("cefalica", "Cefálica"),
        ("podalica", "Podálica"),
        ("transversa", "Transversa"),
        ("oblicua", "Oblicua"),
    ]

    POSICION_CHOICES = [
        ("oia", "Occípito Ilíaca Anterior"),
        ("oip", "Occípito Ilíaca Posterior"),
        ("oit", "Occípito Ilíaca Transversa"),
        ("oda", "Occípito Derecha Anterior"),
        ("odp", "Occípito Derecha Posterior"),
        ("odt", "Occípito Derecha Transversa"),
    ]

    MEMBRANAS_CHOICES = [
        ("integras", "Membranas Íntegras"),
        ("rotas_espontaneas", "Rotura Espontánea"),
        ("rotas_artificiales", "Rotura Artificial"),
    ]

    # ═══════════════════════════════════════════════════════════════════════
    # ✅ CORRECCIÓN: FOREIGNKEY EN VEZ DE IntegerField
    # ═══════════════════════════════════════════════════════════════════════

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name="partos",
        verbose_name="Paciente",
        help_text="Paciente del parto",
        db_column="paciente_id",
        null=False,  # ← REQUERIDO: Paciente es obligatorio
        blank=False,  # ← REQUERIDO: No puede estar en blanco
    )
    embarazo = models.ForeignKey(
        "embarazos.Embarazo",
        on_delete=models.PROTECT,
        related_name="partos",
        null=True,
        blank=True,
        verbose_name="Embarazo",
        help_text="Embarazo asociado al parto",
        db_column="embarazo_id",  # ← Mantiene el nombre de columna en DB
    )

    medico_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partos_atendidos",
        verbose_name="Médico Responsable",
        help_text="Médico que atiende el parto",
        db_column="medico_responsable_id",  # ← Mantiene el nombre de columna en DB
    )

    # Identificación
    numero_parto = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Parto",
        help_text="Número único del parto",
    )

    # Fechas y tiempos
    fecha_ingreso = models.DateTimeField(
        null=True,  # ✅ OPCIONAL: Permitir nulo para compatibilidad con frontend
        blank=True,
        verbose_name="Fecha y Hora de Ingreso",
        help_text="Fecha y hora en que la paciente ingresa para el parto",
    )

    fecha_inicio_trabajo_parto = models.DateTimeField(
        null=True, blank=True, verbose_name="Inicio del Trabajo de Parto",
    )

    fecha_parto = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha y Hora del Parto",
    )

    # Datos del parto
    edad_gestacional_parto = models.CharField(
        max_length=10,
        validators=[validar_edad_gestacional],
        verbose_name="Edad Gestacional al Parto",
        help_text="Ej: 39+2",
    )

    tipo_parto = models.CharField(
        max_length=30,
        choices=TIPO_PARTO_CHOICES,
        blank=True,  # ✅ Opcional para abortos
        null=True,  # ✅ Puede ser NULL
        verbose_name="Tipo de Parto",
        help_text="Solo requerido para partos (≥ 20 semanas)",
    )

    presentacion_fetal = models.CharField(
        max_length=20,
        choices=PRESENTACION_CHOICES,
        default="cefalica",
        verbose_name="Presentación Fetal",
    )

    posicion_fetal = models.CharField(
        max_length=20,
        choices=POSICION_CHOICES,
        blank=True,
        verbose_name="Posición Fetal",
    )

    # Estado de membranas
    estado_membranas = models.CharField(
        max_length=30,
        choices=MEMBRANAS_CHOICES,
        default="integras",
        verbose_name="Estado de Membranas",
    )

    hora_rotura_membranas = models.DateTimeField(
        null=True, blank=True, verbose_name="Hora de Rotura de Membranas",
    )

    caracteristicas_liquido = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Características del Líquido Amniótico",
        help_text="Claro, meconial, sanguinolento",
    )

    # Duración del trabajo de parto (simplificado)
    duracion_trabajo_parto_horas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Duración Total del Trabajo de Parto (horas)",
    )

    duracion_periodo_expulsivo_minutos = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(600)],
        verbose_name="Duración del Período Expulsivo (minutos)",
    )

    # Analgesia y anestesia
    analgesia_utilizada = models.BooleanField(
        default=False, verbose_name="¿Se utilizó analgesia",
    )

    tipo_analgesia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tipo de Analgesia",
        help_text="Epidural, raquídea, general, local",
    )

    # Episiotomía y desgarros
    episiotomia = models.BooleanField(
        default=False, verbose_name="¿Se realizó episiotomía",
    )

    tipo_episiotomia = models.CharField(
        max_length=50, blank=True, verbose_name="Tipo de Episiotomía",
    )

    desgarros = models.BooleanField(default=False, verbose_name="¿Hubo desgarros")

    grado_desgarros = models.CharField(
        max_length=100, blank=True, verbose_name="Grado y Localización de Desgarros",
    )

    # Alumbramiento
    tipo_alumbramiento = models.CharField(
        max_length=50,
        choices=[
            ("espontaneo", "Espontáneo"),
            ("dirigido", "Dirigido"),
            ("manual", "Manual"),
        ],
        default="espontaneo",
        verbose_name="Tipo de Alumbramiento",
    )

    placenta_completa = models.BooleanField(
        default=True, verbose_name="¿Placenta completa",
    )

    peso_placenta = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(100), MaxValueValidator(1000)],
        verbose_name="Peso de la Placenta (g)",
    )

    # Pérdida sanguínea
    perdida_sanguinea_estimada = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5000)],
        verbose_name="Pérdida Sanguínea Estimada (ml)",
    )

    hemorragia_postparto = models.BooleanField(
        default=False, verbose_name="¿Hemorragia postparto",
    )

    # Complicaciones
    complicaciones_maternas = models.TextField(
        blank=True,
        verbose_name="Complicaciones Maternas",
        help_text="Describir cualquier complicación durante el parto",
    )

    # Medicamentos utilizados
    oxitocina_utilizada = models.BooleanField(
        default=False, verbose_name="¿Se utilizó oxitocina",
    )

    dosis_oxitocina = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Dosis de Oxitocina",
        help_text="UI totales utilizadas",
    )

    otros_medicamentos = models.TextField(
        blank=True, verbose_name="Otros Medicamentos Utilizados",
    )

    # Observaciones y notas
    observaciones_parto = models.TextField(
        blank=True, verbose_name="Observaciones del Parto",
    )

    indicaciones_cesarea = models.TextField(
        blank=True,
        verbose_name="Indicaciones de Cesárea",
        help_text="Solo completar si es cesárea",
    )

    # Estado final
    parto_finalizado = models.BooleanField(
        default=False, verbose_name="¿Parto finalizado",
    )

    # Información adicional del trabajo de parto
    trabajo_parto_espontaneo = models.BooleanField(
        default=True, verbose_name="¿Trabajo de parto espontáneo",
    )

    induccion_parto = models.BooleanField(
        default=False, verbose_name="¿Se indujo el parto",
    )

    metodo_induccion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Método de Inducción",
        help_text="Prostaglandinas, oxitocina, amniotomía",
    )

    # Monitoreo fetal
    monitoreo_fetal_continuo = models.BooleanField(
        default=False, verbose_name="¿Monitoreo fetal continuo",
    )

    # ═══════════════════════════════════════════════════════════════════════
    # ✅ CAMPOS ESPECÍFICOS PARA PROTOCOLO DE ABORTO (< 20 semanas)
    # ═══════════════════════════════════════════════════════════════════════

    tipo_aborto = models.CharField(
        max_length=30,
        choices=[
            ("espontaneo", "Espontáneo"),
            ("inducido", "Inducido Terapéutico"),
            ("incompleto", "Incompleto"),
            ("completo", "Completo"),
            ("diferido", "Diferido/Retenido"),
            ("inevitable", "Inevitable"),
        ],
        blank=True,
        null=True,
        verbose_name="Tipo de Aborto",
        help_text="Solo completar si edad gestacional < 20 semanas",
    )

    metodo_evacuacion = models.CharField(
        max_length=50,
        choices=[
            ("aspiracion", "Aspiración por Vacío (AMEU)"),
            ("legrado", "Legrado Uterino"),
            ("medico", "Método Médico (Misoprostol)"),
            ("expectante", "Manejo Expectante"),
        ],
        blank=True,
        null=True,
        verbose_name="Método de Evacuación",
        help_text="Método utilizado para evacuación uterina en caso de aborto",
    )

    apoyo_psicologico_realizado = models.BooleanField(
        default=False, verbose_name="¿Se proporcionó apoyo psicológico",
    )

    protocolo_duelo_aplicado = models.BooleanField(
        default=False, verbose_name="¿Se aplicó protocolo de duelo",
    )

    observaciones_aborto = models.TextField(
        blank=True,
        verbose_name="Observaciones del Aborto",
        help_text="Detalles adicionales del manejo del aborto",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    # Auditoría
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partos_creados",
        verbose_name="Creado por",
    )

    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partos_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "partos"
        ordering = ["-fecha_parto"]
        verbose_name = "Parto"
        verbose_name_plural = "Partos"
        indexes = [
            models.Index(fields=["paciente", "-fecha_parto"]),
            models.Index(fields=["embarazo"]),
            models.Index(fields=["fecha_parto"]),
            models.Index(fields=["tipo_parto"]),
            models.Index(fields=["numero_parto"]),
        ]

    def save(self, *args, **kwargs):
        """Save"""
        # ✅ AUTO-ASIGNAR PACIENTE DESDE EMBARAZO SI FALTA
        # Esto previene que se creen partos sin paciente
        if not self.paciente_id and self.embarazo_id:
            # Si el parto no tiene paciente pero sí tiene embarazo,
            # asignar automáticamente el paciente del embarazo
            self.paciente = self.embarazo.paciente

        # Generar número de parto automáticamente con transacción atómica
        if not self.numero_parto:
            with transaction.atomic():
                year = timezone.now().year
                # Usar select_for_update() para evitar race conditions
                last_parto = (
                    Parto.objects.select_for_update()
                    .filter(fecha_registro__year=year)
                    .order_by("-numero_parto")
                    .first()
                )

                if last_parto and last_parto.numero_parto:
                    try:
                        last_number = int(last_parto.numero_parto.split("-", 1)[-1])
                        new_number = last_number + 1
                    except (ValueError, IndexError):
                        new_number = 1
                else:
                    new_number = 1

                self.numero_parto = f"PARTO-{year}-{new_number:04d}"

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """URL para ver el detalle del parto"""
        return reverse("parto-detail", kwargs={"pk": self.pk})

    def get_duracion_trabajo_parto_horas(self):
        """Devuelve la duración del trabajo de parto en horas"""
        if self.duracion_trabajo_parto_horas:
            return float(self.duracion_trabajo_parto_horas)
        return None

    def get_evaluacion_perdida_sanguinea(self):
        """Evalúa la pérdida sanguínea"""
        if not self.perdida_sanguinea_estimada:
            return "No registrada"

        perdida = self.perdida_sanguinea_estimada

        if perdida < 500:
            return "✅ Normal (< 500ml)"
        if perdida < 1000:
            return " Moderada (500-1000ml)"
        if perdida < 1500:
            return " Severa (1000-1500ml)"
        return " Muy severa (> 1500ml)"

    def get_estado_parto(self):
        """Devuelve el estado actual del parto"""
        if self.parto_finalizado:
            return "✅ Finalizado"
        if self.fecha_inicio_trabajo_parto:
            return " En trabajo de parto"
        return "⏳ Pendiente"

    def get_resumen_parto(self):
        """Resumen completo del parto"""
        resumen = []
        resumen.append(f"Parto {self.numero_parto}")
        resumen.append(f"Tipo: {self.get_tipo_parto_display()}")
        resumen.append(f"Edad gestacional: {self.edad_gestacional_parto}")
        resumen.append(f"Presentación: {self.get_presentacion_fetal_display()}")

        if self.perdida_sanguinea_estimada:
            resumen.append(f"Pérdida sanguínea: {self.perdida_sanguinea_estimada}ml")

        if self.duracion_trabajo_parto_horas:
            resumen.append(f"Duración: {self.duracion_trabajo_parto_horas}h")

        return " | ".join(resumen)

    def get_complicaciones_totales(self):
        """Lista todas las complicaciones"""
        complicaciones = []

        if self.hemorragia_postparto:
            complicaciones.append("Hemorragia postparto")

        if self.desgarros:
            complicaciones.append(f"Desgarros: {self.grado_desgarros}")

        if self.complicaciones_maternas:
            complicaciones.append(self.complicaciones_maternas)

        return complicaciones or ["Sin complicaciones registradas"]

    # ═══════════════════════════════════════════════════════════════════════════
    # ✅ SISTEMA DE ALERTAS MÉDICAS DEL PARTO
    # ═══════════════════════════════════════════════════════════════════════════

    def obtener_semanas_dias_gestacion(self):
        """Extrae semanas y días de la edad gestacional"""
        if not self.edad_gestacional_parto:
            return None, None

        parts = self.edad_gestacional_parto.split("+")
        semanas = int(parts[0])
        dias = int(parts[1]) if len(parts) > 1 else 0

        return semanas, dias

    def get_tipo_parto_segun_edad(self):
        """Clasifica el parto según edad gestacional"""
        semanas, _dias = self.obtener_semanas_dias_gestacion()

        if semanas is None:
            return "desconocido", "Edad gestacional no registrada"

        if semanas < 20:
            return "aborto", "Aborto (< 20 semanas)"
        if semanas < 28:
            return "prematuro_extremo", "Prematuro extremo (20-27 semanas)"
        if semanas < 32:
            return "muy_prematuro", "Muy prematuro (28-31 semanas)"
        if semanas < 37:
            return "prematuro", "Prematuro (32-36 semanas)"
        if semanas <= 41:
            return "termino", "A término (37-41 semanas)"
        return "post_termino", "Post-término (≥ 42 semanas)"

    @property
    def alertas_parto(self):
        """Devuelve lista de alertas médicas del parto"""
        alertas = []

        semanas, dias = self.obtener_semanas_dias_gestacion()

        if semanas is None:
            return alertas

        # ═══ ALERTAS CRÍTICAS ═══

        # 1. Aborto
        if semanas < 20:
            alertas.append(
                {
                    "tipo": "critica",
                    "nivel": "error",
                    "categoria": "edad_gestacional",
                    "mensaje": f"⚠️ ABORTO: Edad gestacional muy temprana ({semanas}+{dias} semanas)",
                    "recomendacion": "Protocolo de aborto. Manejo de duelo. Apoyo psicológico.",
                },
            )

        # 2. Prematurez extrema
        elif semanas < 28:
            alertas.append(
                {
                    "tipo": "critica",
                    "nivel": "error",
                    "categoria": "edad_gestacional",
                    "mensaje": f" PREMATURO EXTREMO: {semanas}+{dias} semanas",
                    "recomendacion": "Requiere UCIN nivel III. Surfactante. Soporte ventilatorio. Corticoides prenatales.",
                },
            )

        # 3. Muy prematuro
        elif semanas < 32:
            alertas.append(
                {
                    "tipo": "critica",
                    "nivel": "warning",
                    "categoria": "edad_gestacional",
                    "mensaje": f"⚠️ MUY PREMATURO: {semanas}+{dias} semanas",
                    "recomendacion": "UCIN. Monitoreo continuo. Termorregulación. Nutrición parenteral.",
                },
            )

        # 4. Prematuro
        elif semanas < 37:
            alertas.append(
                {
                    "tipo": "moderada",
                    "nivel": "warning",
                    "categoria": "edad_gestacional",
                    "mensaje": f"⚠️ PREMATURO: {semanas}+{dias} semanas",
                    "recomendacion": "Observación estrecha. Valorar madurez pulmonar. Apoyo térmico y nutricional.",
                },
            )

        # 5. Post-término
        elif semanas >= 42:
            alertas.append(
                {
                    "tipo": "moderada",
                    "nivel": "warning",
                    "categoria": "edad_gestacional",
                    "mensaje": f"⚠️ POST-TÉRMINO: {semanas}+{dias} semanas",
                    "recomendacion": "Vigilancia fetal estrecha. Riesgo de oligohidramnios y aspiración meconial.",
                },
            )

        # ═══ ALERTAS DE TIPO DE PARTO ═══

        # 6. Cesárea de emergencia
        if self.tipo_parto == "cesarea_emergencia":
            alertas.append(
                {
                    "tipo": "critica",
                    "nivel": "error",
                    "categoria": "tipo_parto",
                    "mensaje": " CESÁREA DE EMERGENCIA",
                    "recomendacion": "Protocolo de emergencia obstétrica. Preparación quirúrgica inmediata.",
                },
            )

        # 7. Cesárea de urgencia
        elif self.tipo_parto == "cesarea_urgencia":
            alertas.append(
                {
                    "tipo": "moderada",
                    "nivel": "warning",
                    "categoria": "tipo_parto",
                    "mensaje": "⚠️ CESÁREA DE URGENCIA",
                    "recomendacion": "Preparación quirúrgica prioritaria. Evaluación fetal continua.",
                },
            )

        # ═══ ALERTAS DE PRESENTACIÓN ═══

        # 8. Presentación anormal
        if self.presentacion_fetal in ["podalica", "transversa", "oblicua"]:
            alertas.append(
                {
                    "tipo": "moderada",
                    "nivel": "warning",
                    "categoria": "presentacion",
                    "mensaje": f"⚠️ PRESENTACIÓN ANORMAL: {self.get_presentacion_fetal_display()}",
                    "recomendacion": "Valorar cesárea. Maniobras de versión externa si es factible.",
                },
            )

        # ═══ ALERTAS DE LÍQUIDO AMNIÓTICO ═══

        # 9. Líquido meconial
        if (
            self.caracteristicas_liquido
            and "mecon" in self.caracteristicas_liquido.lower()
        ):
            alertas.append(
                {
                    "tipo": "moderada",
                    "nivel": "warning",
                    "categoria": "liquido_amniotico",
                    "mensaje": "⚠️ LÍQUIDO AMNIÓTICO MECONIAL",
                    "recomendacion": "Monitoreo fetal continuo. Preparación para aspiración. Equipo de reanimación.",
                },
            )

        # 10. Líquido sanguinolento
        if (
            self.caracteristicas_liquido
            and "sangu" in self.caracteristicas_liquido.lower()
        ):
            alertas.append(
                {
                    "tipo": "critica",
                    "nivel": "error",
                    "categoria": "liquido_amniotico",
                    "mensaje": " LÍQUIDO AMNIÓTICO SANGUINOLENTO",
                    "recomendacion": "Descartar desprendimiento placentario. Monitoreo continuo. Preparar para emergencia.",
                },
            )

        # ═══ ALERTAS DE HEMORRAGIA ═══

        # 11. Hemorragia postparto
        if self.hemorragia_postparto:
            if self.perdida_sanguinea_estimada:
                if self.perdida_sanguinea_estimada >= 1500:
                    alertas.append(
                        {
                            "tipo": "critica",
                            "nivel": "error",
                            "categoria": "hemorragia",
                            "mensaje": f" HEMORRAGIA SEVERA: {self.perdida_sanguinea_estimada}ml",
                            "recomendacion": "Protocolo de hemorragia masiva. Transfusión. Considerar histerectomía.",
                        },
                    )
                elif self.perdida_sanguinea_estimada >= 1000:
                    alertas.append(
                        {
                            "tipo": "critica",
                            "nivel": "warning",
                            "categoria": "hemorragia",
                            "mensaje": f"⚠️ HEMORRAGIA MODERADA-SEVERA: {self.perdida_sanguinea_estimada}ml",
                            "recomendacion": "Uterotónicos. Cristaloides. Hemoderivados según evolución.",
                        },
                    )
                else:
                    alertas.append(
                        {
                            "tipo": "moderada",
                            "nivel": "warning",
                            "categoria": "hemorragia",
                            "mensaje": f"⚠️ Hemorragia postparto: {self.perdida_sanguinea_estimada}ml",
                            "recomendacion": "Vigilancia estrecha. Uterotónicos. Control de signos vitales.",
                        },
                    )

        # ═══ ALERTAS DE TRABAJO DE PARTO ═══

        # 12. Trabajo de parto prolongado
        if self.duracion_trabajo_parto_horas and self.duracion_trabajo_parto_horas > 20:
            alertas.append(
                {
                    "tipo": "moderada",
                    "nivel": "warning",
                    "categoria": "trabajo_parto",
                    "mensaje": f"⚠️ TRABAJO DE PARTO PROLONGADO: {self.duracion_trabajo_parto_horas}h",
                    "recomendacion": "Valorar distocia. Considerar cesárea si no hay progreso.",
                },
            )

        # 13. Período expulsivo prolongado
        if (
            self.duracion_periodo_expulsivo_minutos
            and self.duracion_periodo_expulsivo_minutos > 120
        ):
            alertas.append(
                {
                    "tipo": "moderada",
                    "nivel": "warning",
                    "categoria": "trabajo_parto",
                    "mensaje": f"⚠️ PERÍODO EXPULSIVO PROLONGADO: {self.duracion_periodo_expulsivo_minutos} min",
                    "recomendacion": "Considerar parto instrumentado o cesárea. Monitoreo fetal continuo.",
                },
            )

        # ═══ ALERTAS DE DESGARROS ═══

        # 14. Desgarros grado III o IV
        if self.desgarros and self.grado_desgarros:
            grado_str = str(self.grado_desgarros)
            if (
                "III" in grado_str
                or "IV" in grado_str
                or "3" in grado_str
                or "4" in grado_str
            ):
                alertas.append(
                    {
                        "tipo": "moderada",
                        "nivel": "warning",
                        "categoria": "trauma_obstetrico",
                        "mensaje": f"⚠️ DESGARRO SEVERO: Grado {self.grado_desgarros}",
                        "recomendacion": "Reparación quirúrgica por especialista. Antibióticos profilácticos.",
                    },
                )

        return alertas

    @property
    def tiene_alertas(self):
        """Indica si el parto tiene alguna alerta"""
        return len(self.alertas_parto) > 0

    @property
    def tiene_alertas_criticas(self):
        """Indica si el parto tiene alertas críticas"""
        return any(alerta["tipo"] == "critica" for alerta in self.alertas_parto)

    @property
    def alertas_criticas(self):
        """Devuelve solo las alertas críticas"""
        return [alerta for alerta in self.alertas_parto if alerta["tipo"] == "critica"]

    @property
    def alertas_moderadas(self):
        """Devuelve solo las alertas moderadas"""
        return [alerta for alerta in self.alertas_parto if alerta["tipo"] == "moderada"]

    @property
    def recomendaciones_por_edad(self):
        """Devuelve recomendaciones según edad gestacional"""
        semanas, _dias = self.obtener_semanas_dias_gestacion()

        if semanas is None:
            return []

        recomendaciones = []

        # ═══ RECOMENDACIONES POR TRIMESTRE Y SEMANA ═══

        # PRIMER TRIMESTRE (0-13 semanas)
        if semanas < 14:
            recomendaciones.append(
                {
                    "tipo": "informacion",
                    "periodo": "Primer Trimestre",
                    "titulo": "Cuidados del Primer Trimestre",
                    "recomendaciones": [
                        "Iniciar ácido fólico (400-800 mcg/día)",
                        "Evitar alcohol, tabaco y drogas",
                        "Ultrasonido de primer trimestre (11-13 semanas)",
                        "Pruebas de laboratorio: grupo sanguíneo, hemograma, glucosa",
                        "Evitar medicamentos sin prescripción médica",
                        "No levantar objetos pesados",
                    ],
                },
            )

        # SEGUNDO TRIMESTRE (14-27 semanas)
        elif semanas < 28:
            recomendaciones.append(
                {
                    "tipo": "informacion",
                    "periodo": "Segundo Trimestre",
                    "titulo": "Cuidados del Segundo Trimestre",
                    "recomendaciones": [
                        "Ultrasonido morfológico (18-22 semanas)",
                        "Prueba de glucosa (24-28 semanas)",
                        "Control de peso y presión arterial",
                        "Ejercicio moderado regular",
                        "Suplemento de hierro si hay anemia",
                        "Vigilar signos de parto prematuro",
                    ],
                },
            )

        # TERCER TRIMESTRE (28-40 semanas)
        else:
            recomendaciones.append(
                {
                    "tipo": "informacion",
                    "periodo": "Tercer Trimestre",
                    "titulo": "Cuidados del Tercer Trimestre",
                    "recomendaciones": [
                        "Monitoreo fetal frecuente",
                        "Controles prenatales cada 2 semanas (hasta semana 36)",
                        "Controles semanales después de semana 36",
                        "Preparación para el parto",
                        "Vigilar movimientos fetales",
                        "Acudir de inmediato si: sangrado, dolor intenso, ruptura de membranas",
                    ],
                },
            )

        # RECOMENDACIONES ESPECÍFICAS POR SEMANA

        if semanas == 12:
            recomendaciones.append(
                {
                    "tipo": "importante",
                    "periodo": f"Semana {semanas}",
                    "titulo": "Ultrasonido de Translucencia Nucal",
                    "recomendaciones": [
                        "Realizar ultrasonido entre semanas 11-13",
                        "Evaluación de riesgo de anomalías cromosómicas",
                        "Medición de translucencia nucal",
                    ],
                },
            )

        if semanas == 20:
            recomendaciones.append(
                {
                    "tipo": "importante",
                    "periodo": f"Semana {semanas}",
                    "titulo": "Ultrasonido Morfológico",
                    "recomendaciones": [
                        "Ultrasonido detallado de anatomía fetal",
                        "Evaluación de órganos y estructuras",
                        "Medición de líquido amniótico",
                        "Evaluación de placenta",
                    ],
                },
            )

        if semanas == 24:
            recomendaciones.append(
                {
                    "tipo": "importante",
                    "periodo": f"Semana {semanas}",
                    "titulo": "Curva de Glucosa",
                    "recomendaciones": [
                        "Test de O'Sullivan (50g glucosa)",
                        "Screening de diabetes gestacional",
                        "Si positivo: curva completa de 100g",
                    ],
                },
            )

        if semanas == 28:
            recomendaciones.append(
                {
                    "tipo": "importante",
                    "periodo": f"Semana {semanas}",
                    "titulo": "Vacunas y Profilaxis",
                    "recomendaciones": [
                        "Vacuna Tdap (difteria, tétanos, tos ferina)",
                        "Inmunoglobulina anti-D si es Rh negativo",
                        "Hemograma de control",
                        "Prueba de anticuerpos",
                    ],
                },
            )

        if semanas >= 35:
            recomendaciones.append(
                {
                    "tipo": "importante",
                    "periodo": f"Semana {semanas}",
                    "titulo": "Preparación para el Parto",
                    "recomendaciones": [
                        "Cultivo vaginal y rectal (Streptococcus B)",
                        "Monitoreo fetal semanal",
                        "Evaluación de pelvis y canal de parto",
                        "Plan de parto discutido",
                        "Bolsa del hospital preparada",
                    ],
                },
            )

        if semanas >= 37:
            recomendaciones.append(
                {
                    "tipo": "atencion",
                    "periodo": "A Término",
                    "titulo": "Embarazo a Término - Preparación Inmediata",
                    "recomendaciones": [
                        "SIGNOS DE ALARMA - Acudir inmediatamente si:",
                        "  Contracciones regulares (cada 5-10 min)",
                        "  Ruptura de membranas (pérdida de líquido)",
                        "  Sangrado vaginal",
                        "  Disminución de movimientos fetales",
                        "  Dolor abdominal intenso",
                        "Tener número de emergencia a mano",
                        "Conocer ruta al hospital",
                    ],
                },
            )

        if semanas >= 41:
            recomendaciones.append(
                {
                    "tipo": "urgente",
                    "periodo": "Post-término",
                    "titulo": "EMBARAZO PROLONGADO - Evaluación Urgente",
                    "recomendaciones": [
                        "Evaluación obstétrica inmediata",
                        "Monitoreo fetal diario",
                        "Evaluación de líquido amniótico",
                        "Considerar inducción del parto",
                        "Riesgo aumentado de complicaciones",
                    ],
                },
            )

        return recomendaciones

    def __str__(self):
        """Str"""
        paciente_nombre = (
            f"{self.paciente.nombre} {self.paciente.apellido_paterno}"
            if self.paciente
            else "Sin paciente"
        )
        return f"Parto {self.numero_parto} - {paciente_nombre} - {self.get_tipo_parto_display()}"


# ═══════════════════════════════════════════════════════════════════════════
# RESTO DE MODELOS SIN CAMBIOS
# ═══════════════════════════════════════════════════════════════════════════


class RecienNacido(models.Model):
    """Modelo para registrar datos del recién nacido"""

    SEXO_CHOICES = [
        ("masculino", "Masculino"),
        ("femenino", "Femenino"),
        ("indeterminado", "Indeterminado"),
    ]

    ESTADO_CHOICES = [
        ("vivo", "Vivo"),
        ("mortinato", "Mortinato"),
        ("muerte_neonatal", "Muerte Neonatal"),
    ]

    # Relaciones
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name="recien_nacidos",
        verbose_name="Parto",
    )

    # Datos básicos
    numero_gemelo = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Número de Gemelo",
        help_text="1 para único, 2,3,4,5 para múltiples",
    )

    fecha_nacimiento = models.DateTimeField(verbose_name="Fecha y Hora de Nacimiento")

    sexo = models.CharField(max_length=20, choices=SEXO_CHOICES, verbose_name="Sexo")

    estado_nacimiento = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="vivo",
        verbose_name="Estado al Nacimiento",
    )

    # Medidas antropométricas
    peso_nacimiento = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(6000)],
        verbose_name="Peso al Nacimiento (g)",
    )

    talla_nacimiento = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(Decimal(20)), MaxValueValidator(Decimal(60))],
        verbose_name="Talla al Nacimiento (cm)",
    )

    perimetro_cefalico = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal(20)), MaxValueValidator(Decimal(50))],
        verbose_name="Perímetro Cefálico (cm)",
    )

    # Score de Apgar
    apgar_1_minuto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Apgar 1 minuto",
    )

    apgar_5_minutos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Apgar 5 minutos",
    )

    apgar_10_minutos = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Apgar 10 minutos",
    )

    # Reanimación
    requirio_reanimacion = models.BooleanField(
        default=False, verbose_name="¿Requirió reanimación",
    )

    tipo_reanimacion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Tipo de Reanimación",
        help_text="Estimulación, O2, VPP, masaje cardíaco, intubación",
    )

    # Malformaciones y patología
    malformaciones_congenitas = models.BooleanField(
        default=False, verbose_name="¿Malformaciones congénitas",
    )

    descripcion_malformaciones = models.TextField(
        blank=True, verbose_name="Descripción de Malformaciones",
    )

    # Destino del recién nacido
    destino_rn = models.CharField(
        max_length=100,
        choices=[
            ("alojamiento_conjunto", "Alojamiento Conjunto"),
            ("neonatologia", "Neonatología"),
            ("uci_neonatal", "UCI Neonatal"),
            ("traslado", "Traslado a otro centro"),
            ("fallecido", "Fallecido"),
        ],
        default="alojamiento_conjunto",
        verbose_name="Destino del Recién Nacido",
    )

    # Datos adicionales
    llanto_inmediato = models.BooleanField(
        default=True, verbose_name="¿Llanto inmediato",
    )

    respiracion_espontanea = models.BooleanField(
        default=True, verbose_name="¿Respiración espontánea",
    )

    tono_muscular_normal = models.BooleanField(
        default=True, verbose_name="¿Tono muscular normal",
    )

    # Observaciones
    observaciones_rn = models.TextField(
        blank=True, verbose_name="Observaciones del Recién Nacido",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "recien_nacidos"
        ordering = ["parto", "numero_gemelo"]
        verbose_name = "Recién Nacido"
        verbose_name_plural = "Recién Nacidos"
        unique_together = ["parto", "numero_gemelo"]
        indexes = [
            models.Index(fields=["parto", "numero_gemelo"]),
            models.Index(fields=["fecha_nacimiento"]),
            models.Index(fields=["peso_nacimiento"]),
        ]

    def get_clasificacion_peso(self):
        """Clasifica el peso del recién nacido"""
        peso = self.peso_nacimiento

        if peso < 1000:
            return " Extremadamente bajo peso (< 1000g)"
        if peso < 1500:
            return " Muy bajo peso (< 1500g)"
        if peso < 2500:
            return " Bajo peso (< 2500g)"
        if peso <= 4000:
            return "✅ Peso normal (2500-4000g)"
        if peso <= 4500:
            return " Macrosomía leve (4000-4500g)"
        return " Macrosomía severa (> 4500g)"

    def get_evaluacion_apgar(self):
        """Evalúa el score de Apgar"""
        apgar_5 = self.apgar_5_minutos

        if apgar_5 >= 8:
            return "✅ Excelente (8-10)"
        if apgar_5 >= 6:
            return " Moderado (6-7)"
        if apgar_5 >= 4:
            return " Bajo (4-5)"
        return " Crítico (0-3)"

    def get_edad_gestacional_nacimiento(self):
        """Clasificación por edad gestacional"""
        return "Requiere cálculo desde embarazo"

    def get_resumen_completo(self):
        """Resumen completo del recién nacido"""
        resumen = []
        resumen.append(f"RN {self.get_sexo_display()}")
        resumen.append(f"Peso: {self.peso_nacimiento}g")
        resumen.append(f"Talla: {self.talla_nacimiento}cm")
        resumen.append(f"Apgar: {self.apgar_1_minuto}/{self.apgar_5_minutos}")
        resumen.append(f"Estado: {self.get_estado_nacimiento_display()}")

        if self.requirio_reanimacion:
            resumen.append("Requirió reanimación")

        return " | ".join(resumen)

    def get_evaluacion_estado_general(self):
        """Evaluación del estado general del RN"""
        problemas = []

        if not self.llanto_inmediato:
            problemas.append("Sin llanto inmediato")

        if not self.respiracion_espontanea:
            problemas.append("Sin respiración espontánea")

        if not self.tono_muscular_normal:
            problemas.append("Tono muscular alterado")

        if self.requirio_reanimacion:
            problemas.append("Requirió reanimación")

        if self.malformaciones_congenitas:
            problemas.append("Malformaciones congénitas")

        if problemas:
            return f" Problemas: {', '.join(problemas)}"
        return "✅ Estado general normal"

    def clean(self):
        """✅ VALIDACIONES CRÍTICAS DEL RECIÉN NACIDO"""
        errors = {}

        # ✅ 1. VALIDAR APGAR - MÁXIMO 10 EN CADA MEDICIÓN
        if self.apgar_1_minuto is not None:
            if self.apgar_1_minuto < 0:
                errors["apgar_1_minuto"] = "Apgar al minuto 1 no puede ser negativo."
            elif self.apgar_1_minuto > 10:
                errors["apgar_1_minuto"] = (
                    f"Apgar al minuto 1 de {self.apgar_1_minuto} es imposible. Máximo es 10."
                )

        if self.apgar_5_minutos is not None:
            if self.apgar_5_minutos < 0:
                errors["apgar_5_minutos"] = (
                    "Apgar a los 5 minutos no puede ser negativo."
                )
            elif self.apgar_5_minutos > 10:
                errors["apgar_5_minutos"] = (
                    f"Apgar a los 5 minutos de {self.apgar_5_minutos} es imposible. Máximo es 10."
                )

        if self.apgar_10_minutos is not None:
            if self.apgar_10_minutos < 0:
                errors["apgar_10_minutos"] = (
                    "Apgar a los 10 minutos no puede ser negativo."
                )
            elif self.apgar_10_minutos > 10:
                errors["apgar_10_minutos"] = (
                    f"Apgar a los 10 minutos de {self.apgar_10_minutos} es imposible. Máximo es 10."
                )

        # ✅ 2. VALIDAR PESO DEL RECIÉN NACIDO
        if self.peso_nacimiento:
            if self.peso_nacimiento > 7000:
                errors["peso_nacimiento"] = (
                    f"Peso de {self.peso_nacimiento}g ({self.peso_nacimiento / 1000:.2f} kg) es extremadamente alto. Máximo realista 7000g (7 kg). Verificar medición."
                )
            elif self.peso_nacimiento < 400:
                errors["peso_nacimiento"] = (
                    f"Peso de {self.peso_nacimiento}g es extremadamente bajo. Mínimo viable 400g. Verificar viabilidad."
                )

        # ✅ 3. VALIDAR TALLA
        if self.talla_nacimiento:
            if self.talla_nacimiento > 60:
                errors["talla_nacimiento"] = (
                    f"Talla de {self.talla_nacimiento} cm es anormalmente alta. Máximo 60 cm."
                )
            elif self.talla_nacimiento < 25:
                errors["talla_nacimiento"] = (
                    f"Talla de {self.talla_nacimiento} cm es anormalmente baja. Mínimo 25 cm."
                )

        # ✅ 4. VALIDAR PERÍMETRO CEFÁLICO
        if self.perimetro_cefalico:
            if self.perimetro_cefalico > 42:
                errors["perimetro_cefalico"] = (
                    f"Perímetro cefálico de {self.perimetro_cefalico} cm es anormalmente alto (macrocefalia severa). Máximo 42 cm."
                )
            elif self.perimetro_cefalico < 25:
                errors["perimetro_cefalico"] = (
                    f"Perímetro cefálico de {self.perimetro_cefalico} cm es anormalmente bajo (microcefalia severa). Mínimo 25 cm."
                )

        # ✅ 5. VALIDAR COHERENCIA APGAR
        if self.apgar_1_minuto is not None and self.apgar_5_minutos is not None:
            # Normalmente el Apgar a los 5 minutos debería ser mayor o igual al del minuto 1
            if self.apgar_5_minutos < self.apgar_1_minuto - 2:
                errors["apgar_5_minutos"] = (
                    f"Apgar a los 5 min ({self.apgar_5_minutos}) es mucho menor que al 1 min ({self.apgar_1_minuto}). Verificar valores."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Str"""
        gemelo_str = f" (Gemelo {self.numero_gemelo})" if self.numero_gemelo > 1 else ""
        return f"RN - {self.parto.numero_parto}{gemelo_str} - {self.peso_nacimiento}g - Apgar {self.apgar_5_minutos}"


class PartogramaRegistro(models.Model):
    """Registro de partograma - seguimiento hora a hora del trabajo de parto"""

    parto = models.ForeignKey(
        Parto, on_delete=models.CASCADE, related_name="partograma", verbose_name="Parto",
    )

    # Tiempo
    hora_registro = models.DateTimeField(verbose_name="Hora del Registro")

    horas_trabajo_parto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(48)],
        verbose_name="Horas en Trabajo de Parto",
    )

    # Dilatación cervical
    dilatacion_cervical = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Dilatación Cervical (cm)",
    )

    borramiento_cervical = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Borramiento Cervical (%)",
    )

    # Descenso fetal
    estacion_fetal = models.CharField(
        max_length=10,
        verbose_name="Estación Fetal",
        help_text="Ej: -3, -2, -1, 0, +1, +2, +3",
    )

    # Contracciones uterinas
    contracciones_10min = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Contracciones en 10 minutos",
    )

    duracion_contracciones = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(120)],
        verbose_name="Duración Contracciones (segundos)",
    )

    intensidad_contracciones = models.CharField(
        max_length=20,
        choices=[
            ("leves", "Leves"),
            ("moderadas", "Moderadas"),
            ("fuertes", "Fuertes"),
        ],
        blank=True,
        verbose_name="Intensidad de Contracciones",
    )

    # Frecuencia cardíaca fetal
    fcf_baseline = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(80), MaxValueValidator(200)],
        verbose_name="FCF Basal (lpm)",
    )

    variabilidad_fcf = models.CharField(
        max_length=20,
        choices=[
            ("ausente", "Ausente"),
            ("minima", "Mínima"),
            ("moderada", "Moderada"),
            ("marcada", "Marcada"),
        ],
        blank=True,
        verbose_name="Variabilidad FCF",
    )

    desaceleraciones = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Desaceleraciones",
        help_text="Tardías, variables, prolongadas",
    )

    # Signos vitales maternos
    presion_arterial_sistolica = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(70), MaxValueValidator(250)],
        verbose_name="Presión Arterial Sistólica (mmHg)",
    )

    presion_arterial_diastolica = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        verbose_name="Presión Arterial Diastólica (mmHg)",
    )

    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(35.0), MaxValueValidator(42.0)],
        verbose_name="Temperatura (°C)",
    )

    pulso_materno = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        verbose_name="Pulso Materno (lpm)",
    )

    # Medicamentos
    oxitocina_dosis = models.CharField(
        max_length=50, blank=True, verbose_name="Dosis de Oxitocina", help_text="mU/min",
    )

    # Observaciones
    observaciones = models.TextField(
        blank=True, verbose_name="Observaciones del Registro",
    )

    # Alertas automáticas
    alerta_progreso_lento = models.BooleanField(
        default=False, verbose_name="Alerta: Progreso lento",
    )

    alerta_fcf_anormal = models.BooleanField(
        default=False, verbose_name="Alerta: FCF anormal",
    )

    alerta_signos_vitales = models.BooleanField(
        default=False, verbose_name="Alerta: Signos vitales alterados",
    )

    # Metadata
    registrado_por_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID Usuario que registró",
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta"""
        db_table = "partograma_registros"
        ordering = ["parto", "hora_registro"]
        verbose_name = "Registro de Partograma"
        verbose_name_plural = "Registros de Partograma"
        unique_together = ["parto", "hora_registro"]
        indexes = [
            models.Index(fields=["parto", "hora_registro"]),
            models.Index(fields=["dilatacion_cervical"]),
            models.Index(fields=["fcf_baseline"]),
        ]

    def save(self, *args, **kwargs):
        """Save"""
        # Generar alertas automáticas
        self.generar_alertas()
        super().save(*args, **kwargs)

    def generar_alertas(self):
        """Genera alertas automáticas basadas en los valores"""
        # Alerta FCF anormal
        if self.fcf_baseline:
            if self.fcf_baseline < 110 or self.fcf_baseline > 160:
                self.alerta_fcf_anormal = True

        # Alerta signos vitales
        if self.presion_arterial_sistolica and self.presion_arterial_sistolica > 140:
            self.alerta_signos_vitales = True

        if self.temperatura and (self.temperatura > 38.0 or self.temperatura < 36.0):
            self.alerta_signos_vitales = True

        # Alerta progreso lento
        if self.horas_trabajo_parto > 12 and self.dilatacion_cervical < 6:
            self.alerta_progreso_lento = True

    def get_presion_arterial(self):
        """Devuelve la presión arterial formateada"""
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            return (
                f"{self.presion_arterial_sistolica}/{self.presion_arterial_diastolica}"
            )
        return "No registrada"

    def get_evaluacion_fcf(self):
        """Evalúa la FCF"""
        if not self.fcf_baseline:
            return "No registrada"

        fcf = self.fcf_baseline

        if fcf < 110:
            return " Bradicardia"
        if fcf > 160:
            return " Taquicardia"
        return "✅ Normal"

    def get_progreso_dilatacion(self):
        """Evalúa el progreso de la dilatación"""
        return f"{self.dilatacion_cervical} cm"

    def get_evaluacion_contracciones(self):
        """Evalúa las contracciones"""
        if not self.contracciones_10min:
            return "Sin contracciones"

        contracciones = self.contracciones_10min
        intensidad = self.intensidad_contracciones

        if contracciones >= 3 and intensidad == "fuertes":
            return "✅ Contracciones adecuadas"
        if contracciones >= 2:
            return " Contracciones moderadas"
        return " Contracciones insuficientes"

    def get_alertas_activas(self):
        """Devuelve las alertas activas"""
        alertas = []

        if self.alerta_fcf_anormal:
            alertas.append("FCF anormal")

        if self.alerta_progreso_lento:
            alertas.append("Progreso lento")

        if self.alerta_signos_vitales:
            alertas.append("Signos vitales alterados")

        return alertas or ["Sin alertas"]

    def get_resumen_registro(self):
        """Resumen del registro de partograma"""
        resumen = []
        resumen.append(f"Hora {self.horas_trabajo_parto}h")
        resumen.append(f"Dilatación: {self.dilatacion_cervical}cm")
        resumen.append(f"Estación: {self.estacion_fetal}")
        resumen.append(f"Contracciones: {self.contracciones_10min}/10min")

        if self.fcf_baseline:
            resumen.append(f"FCF: {self.fcf_baseline}lpm")

        return " | ".join(resumen)

    def __str__(self):
        """Str"""
        return f"Partograma - {self.parto.numero_parto} - {self.hora_registro.strftime('%H:%M')} - {self.dilatacion_cervical}cm"


# ═══════════════════════════════════════════════════════════════════════════
# NUEVOS MODELOS PARA EXTENDER FUNCIONALIDAD
# ═══════════════════════════════════════════════════════════════════════════


class ComplicacionParto(models.Model):
    """Registro detallado de complicaciones durante el parto"""

    TIPO_COMPLICACION_CHOICES = [
        ("hemorragia", "Hemorragia"),
        ("distocia", "Distocia"),
        ("sufrimiento_fetal", "Sufrimiento Fetal"),
        ("desgarro_severo", "Desgarro Severo"),
        ("rotura_uterina", "Rotura Uterina"),
        ("prolapso_cordon", "Prolapso de Cordón"),
        ("desprendimiento_placenta", "Desprendimiento de Placenta"),
        ("eclampsia", "Eclampsia"),
        ("embolia_liquido", "Embolia de Líquido Amniótico"),
        ("otra", "Otra Complicación"),
    ]

    SEVERIDAD_CHOICES = [
        ("leve", " Leve"),
        ("moderada", " Moderada"),
        ("severa", " Severa"),
        ("critica", " Crítica"),
    ]

    # Relación con Parto
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name="complicaciones",
        verbose_name="Parto",
    )

    # Tipo y severidad
    tipo_complicacion = models.CharField(
        max_length=50,
        choices=TIPO_COMPLICACION_CHOICES,
        verbose_name="Tipo de Complicación",
    )

    severidad = models.CharField(
        max_length=20,
        choices=SEVERIDAD_CHOICES,
        default="leve",
        verbose_name="Severidad",
    )

    # Detalles
    momento_deteccion = models.DateTimeField(
        verbose_name="Momento de Detección",
        help_text="Cuándo se detectó la complicación",
    )

    descripcion_detallada = models.TextField(
        verbose_name="Descripción Detallada",
        help_text="Descripción completa de la complicación",
    )

    # Manejo y tratamiento
    tratamiento_realizado = models.TextField(
        blank=True,
        verbose_name="Tratamiento Realizado",
        help_text="Intervenciones y tratamientos aplicados",
    )

    medicamentos_utilizados = models.TextField(
        blank=True,
        verbose_name="Medicamentos Utilizados",
        help_text="Lista de medicamentos con dosis",
    )

    # Resultado
    resolucion_complicacion = models.CharField(
        max_length=20,
        choices=[
            ("resuelto", "Resuelto"),
            ("en_tratamiento", "En Tratamiento"),
            ("requiere_seguimiento", "Requiere Seguimiento"),
        ],
        default="resuelto",
        verbose_name="Estado de Resolución",
    )

    requirio_cirugia = models.BooleanField(
        default=False, verbose_name="¿Requirió cirugía",
    )

    tipo_cirugia = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Tipo de Cirugía",
        help_text="Descripción de procedimiento quirúrgico",
    )

    # Personal médico
    medico_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complicaciones_atendidas",
        verbose_name="Médico que Atendió",
    )

    # Observaciones
    observaciones = models.TextField(
        blank=True, verbose_name="Observaciones Adicionales",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        db_table = "complicaciones_parto"
        ordering = ["-momento_deteccion"]
        verbose_name = "Complicación del Parto"
        verbose_name_plural = "Complicaciones del Parto"
        indexes = [
            models.Index(fields=["parto", "-momento_deteccion"]),
            models.Index(fields=["tipo_complicacion"]),
            models.Index(fields=["severidad"]),
        ]

    def get_icono_severidad(self):
        """Devuelve el ícono según severidad"""
        iconos = {
            "leve": "",
            "moderada": "",
            "severa": "",
            "critica": "",
        }
        return iconos.get(self.severidad, "⚪")

    def get_resumen(self):
        """Resumen de la complicación"""
        return f"{self.get_icono_severidad()} {self.get_tipo_complicacion_display()} - {self.get_severidad_display()}"

    def __str__(self):
        """Str"""
        return f"Complicación: {self.get_tipo_complicacion_display()} ({self.get_severidad_display()}) - {self.parto.numero_parto}"


class ApgarScoreDetallado(models.Model):
    """Registro detallado del Score de Apgar con desglose por componente
    Permite un seguimiento más preciso que el registro simplificado en RecienNacido
    """

    PUNTUACION_CHOICES = [(i, str(i)) for i in range(3)]  # 0, 1, 2

    # Relación con Recién Nacido
    recien_nacido = models.ForeignKey(
        RecienNacido,
        on_delete=models.CASCADE,
        related_name="apgar_scores_detallados",
        verbose_name="Recién Nacido",
    )

    # Tiempo de evaluación
    minuto_evaluacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name="Minuto de Evaluación",
        help_text="1, 5, 10, 15, 20 minutos...",
    )

    # Componentes del Apgar Score
    frecuencia_cardiaca = models.IntegerField(
        choices=PUNTUACION_CHOICES,
        verbose_name="Frecuencia Cardíaca",
        help_text="0=Ausente, 1=<100, 2=>100",
    )

    esfuerzo_respiratorio = models.IntegerField(
        choices=PUNTUACION_CHOICES,
        verbose_name="Esfuerzo Respiratorio",
        help_text="0=Ausente, 1=Débil/irregular, 2=Fuerte/llanto",
    )

    tono_muscular = models.IntegerField(
        choices=PUNTUACION_CHOICES,
        verbose_name="Tono Muscular",
        help_text="0=Flácido, 1=Flexión leve, 2=Movimiento activo",
    )

    irritabilidad_refleja = models.IntegerField(
        choices=PUNTUACION_CHOICES,
        verbose_name="Irritabilidad Refleja",
        help_text="0=Sin respuesta, 1=Mueca, 2=Llanto vigoroso",
    )

    coloracion = models.IntegerField(
        choices=PUNTUACION_CHOICES,
        verbose_name="Coloración",
        help_text="0=Azul/pálido, 1=Cuerpo rosado/extremidades azules, 2=Completamente rosado",
    )

    # Detalles adicionales
    observaciones_evaluador = models.TextField(
        blank=True,
        verbose_name="Observaciones del Evaluador",
        help_text="Detalles relevantes durante la evaluación",
    )

    evaluador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="apgar_evaluados",
        verbose_name="Evaluador",
    )

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta"""
        db_table = "apgar_scores_detallados"
        ordering = ["recien_nacido", "minuto_evaluacion"]
        verbose_name = "Apgar Score Detallado"
        verbose_name_plural = "Apgar Scores Detallados"
        unique_together = ["recien_nacido", "minuto_evaluacion"]
        indexes = [
            models.Index(fields=["recien_nacido", "minuto_evaluacion"]),
            models.Index(fields=["fecha_registro"]),
        ]

    @property
    def score_total(self):
        """Calcula el score total de Apgar (0-10)"""
        return (
            self.frecuencia_cardiaca
            + self.esfuerzo_respiratorio
            + self.tono_muscular
            + self.irritabilidad_refleja
            + self.coloracion
        )

    def get_clasificacion(self):
        """Clasifica el score de Apgar"""
        score = self.score_total
        if score >= 8:
            return "✅ Excelente (8-10)"
        if score >= 6:
            return " Moderado (6-7)"
        if score >= 4:
            return " Bajo (4-5)"
        return " Crítico (0-3)"

    def get_desglose_componentes(self):
        """Devuelve el desglose de puntuación por componente"""
        return {
            "frecuencia_cardiaca": self.frecuencia_cardiaca,
            "esfuerzo_respiratorio": self.esfuerzo_respiratorio,
            "tono_muscular": self.tono_muscular,
            "irritabilidad_refleja": self.irritabilidad_refleja,
            "coloracion": self.coloracion,
            "total": self.score_total,
        }

    def get_componentes_problematicos(self):
        """Identifica componentes con puntuación baja"""
        problemas = []

        componentes = {
            "Frecuencia Cardíaca": self.frecuencia_cardiaca,
            "Esfuerzo Respiratorio": self.esfuerzo_respiratorio,
            "Tono Muscular": self.tono_muscular,
            "Irritabilidad Refleja": self.irritabilidad_refleja,
            "Coloración": self.coloracion,
        }

        for nombre, valor in componentes.items():
            if valor == 0:
                problemas.append(f" {nombre}: Ausente")
            elif valor == 1:
                problemas.append(f" {nombre}: Débil")

        return problemas or ["✅ Todos los componentes normales"]

    def __str__(self):
        """Str"""
        return f"Apgar {self.minuto_evaluacion}min: {self.score_total}/10 - {self.recien_nacido}"
