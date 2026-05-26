"""Models module."""
import os
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from pacientes.models import Paciente

# from controles.models import ControlPrenatal  # REMOVED to fix circular import
from usuarios.models import Usuario


class TipoExamen(models.Model):
    """Catálogo de tipos de exámenes de laboratorio"""

    CATEGORIA_CHOICES = [
        ("hematologia", "Hematología"),
        ("bioquimica", "Bioquímica"),
        ("inmunologia", "Inmunología"),
        ("microbiologia", "Microbiología"),
        ("urinalisis", "Urianálisis"),
        ("serologia", "Serología"),
        ("hormonal", "Hormonal"),
        ("genetica", "Genética"),
    ]

    nombre = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Nombre del Examen",
        help_text="Ej: Hemograma Completo, Glucosa en Ayunas",
    )

    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código",
        help_text="Código interno del examen",
    )

    categoria = models.CharField(
        max_length=50, choices=CATEGORIA_CHOICES, verbose_name="Categoría",
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del examen",
    )

    preparacion = models.TextField(
        blank=True,
        verbose_name="Preparación",
        help_text="Indicaciones de preparación para el paciente",
    )

    tiempo_resultado = models.IntegerField(
        default=24,
        validators=[MinValueValidator(1)],
        verbose_name="Tiempo de Resultado (horas)",
        help_text="Tiempo estimado para obtener resultados",
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Precio (Bs)",
        help_text="Precio del examen en bolivianos",
    )

    activo = models.BooleanField(
        default=True, verbose_name="Activo", help_text="Si el examen está disponible",
    )

    # Trazabilidad
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tipos_examenes_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tipos_examenes_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "tipos_examenes"
        verbose_name = "Tipo de Examen"
        verbose_name_plural = "Tipos de Exámenes"
        ordering = ["categoria", "nombre"]
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["categoria"]),
        ]

    def get_examenes_realizados_mes(self):
        """Obtiene la cantidad de exámenes realizados este mes"""
        ahora = timezone.now()
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.examenes.filter(
            fecha_solicitud__gte=inicio_mes, estado="completado",
        ).count()

    def get_tiempo_promedio_resultado(self):
        """Calcula el tiempo promedio de resultados en días"""
        examenes_completados = self.examenes.filter(
            estado="completado", fecha_resultado__isnull=False,
        )

        if not examenes_completados.exists():
            return None

        total_tiempo = 0
        count = 0

        for examen in examenes_completados:
            if examen.fecha_solicitud and examen.fecha_resultado:
                tiempo_dias = (examen.fecha_resultado - examen.fecha_solicitud).days
                total_tiempo += tiempo_dias
                count += 1

        return round(total_tiempo / count, 1) if count > 0 else None

    def get_porcentaje_urgentes(self):
        """Obtiene el porcentaje de exámenes urgentes"""
        total = self.examenes.count()
        if total == 0:
            return 0
        urgentes = self.examenes.filter(prioridad__in=["urgente", "stat"]).count()
        return round((urgentes / total) * 100, 1)

    def __str__(self):
        """Str"""
        return f"{self.codigo} - {self.nombre}"


class ExamenLaboratorio(models.Model):
    """Solicitud de examen de laboratorio"""

    ESTADO_CHOICES = [
        ("solicitado", "Solicitado"),
        ("en_proceso", "En Proceso"),
        ("completado", "Completado"),
        ("cancelado", "Cancelado"),
    ]

    PRIORIDAD_CHOICES = [
        ("normal", "Normal"),
        ("urgente", "Urgente"),
        ("stat", "STAT (Inmediato)"),
    ]

    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="examenes_laboratorio",
        verbose_name="Paciente",
    )

    control_prenatal = models.ForeignKey(
        "controles.ControlPrenatal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="examenes",
        verbose_name="Control Prenatal Asociado",
    )

    tipo_examen = models.ForeignKey(
        TipoExamen,
        on_delete=models.PROTECT,
        related_name="examenes",
        verbose_name="Tipo de Examen",
    )

    medico_solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="examenes_solicitados",
        limit_choices_to={"rol": "medico"},
        verbose_name="Médico Solicitante",
    )

    # Datos del examen
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Solicitud",
    )

    fecha_muestra = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Toma de Muestra",
    )

    fecha_resultado = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Resultado",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="solicitado",
        verbose_name="Estado",
    )

    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDAD_CHOICES,
        default="normal",
        verbose_name="Prioridad",
    )

    indicaciones = models.TextField(
        blank=True,
        verbose_name="Indicaciones Clínicas",
        help_text="Motivo de la solicitud e indicaciones",
    )

    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones",
        help_text="Observaciones generales del examen",
    )

    # Trazabilidad
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="examenes_laboratorio_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="examenes_laboratorio_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "examenes_laboratorio"
        verbose_name = "Examen de Laboratorio"
        verbose_name_plural = "Exámenes de Laboratorio"
        ordering = ["-fecha_solicitud"]
        indexes = [
            models.Index(fields=["paciente", "-fecha_solicitud"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["-fecha_solicitud"]),
        ]

    @property
    def dias_desde_solicitud(self):
        """Días transcurridos desde la solicitud"""
        if self.fecha_solicitud:
            ahora = timezone.now()
            diferencia = ahora - self.fecha_solicitud
            return diferencia.days
        return None

    @property
    def esta_pendiente(self):
        """Verifica si el examen está pendiente"""
        return self.estado in ["solicitado", "en_proceso"]

    @property
    def esta_vencido(self):
        """Verifica si el examen excedió el tiempo esperado"""
        if self.estado == "completado":
            return False

        dias = self.dias_desde_solicitud
        tiempo_esperado_dias = self.tipo_examen.tiempo_resultado / 24

        if dias and dias > tiempo_esperado_dias:
            return True
        return False

    def get_tiempo_total_proceso(self):
        """Obtiene el tiempo total del proceso en horas"""
        if self.fecha_resultado and self.fecha_solicitud:
            diferencia = self.fecha_resultado - self.fecha_solicitud
            return round(diferencia.total_seconds() / 3600, 1)
        return None

    def get_resultados_criticos_count(self):
        """Cuenta los resultados críticos del examen"""
        return self.resultados.filter(es_critico=True).count()

    def get_resultados_anormales_count(self):
        """Cuenta los resultados anormales del examen"""
        return self.resultados.filter(es_normal=False, es_critico=False).count()

    def tiene_resultados_criticos(self):
        """Verifica si tiene resultados críticos"""
        return self.get_resultados_criticos_count() > 0

    def get_alerta_prioridad(self):
        """Obtiene el nivel de alerta según prioridad"""
        alertas = {"normal": "success", "urgente": "warning", "stat": "danger"}
        return alertas.get(self.prioridad, "info")

    def get_costo_total_estimado(self):
        """Calcula el costo total estimado incluyendo procesamiento"""
        costo_base = self.tipo_examen.precio

        # Factores adicionales según prioridad
        if self.prioridad == "urgente":
            costo_base *= Decimal("1.5")  # 50% adicional
        elif self.prioridad == "stat":
            costo_base *= Decimal("2.0")  # 100% adicional

        return costo_base

    # Métodos para el admin
    def tiempo_total_proceso(self):
        """Obtiene el tiempo total del proceso en horas (método para admin)"""
        return self.get_tiempo_total_proceso()

    def costo_total_estimado(self):
        """Obtiene el costo total estimado (método para admin)"""
        return self.get_costo_total_estimado()

    def __str__(self):
        """Str"""
        return f"{self.tipo_examen.nombre} - {self.paciente.nombre_completo} ({self.get_estado_display()})"


class ValorReferencia(models.Model):
    """Valores de referencia para resultados de laboratorio"""

    UNIDAD_CHOICES = [
        ("mg/dL", "mg/dL"),
        ("g/dL", "g/dL"),
        ("mmol/L", "mmol/L"),
        ("mEq/L", "mEq/L"),
        ("pg/mL", "pg/mL"),
        ("ng/mL", "ng/mL"),
        ("UI/L", "UI/L"),
        ("U/L", "U/L"),
        ("%", "%"),
        ("células/mm³", "células/mm³"),
        ("10³/µL", "10³/µL"),
        ("10⁶/µL", "10⁶/µL"),
        ("segundos", "segundos"),
        ("ratio", "ratio"),
        ("cualitativo", "Cualitativo"),
    ]

    tipo_examen = models.ForeignKey(
        TipoExamen,
        on_delete=models.CASCADE,
        related_name="valores_referencia",
        verbose_name="Tipo de Examen",
    )

    parametro = models.CharField(
        max_length=200,
        verbose_name="Parámetro",
        help_text="Ej: Hemoglobina, Glucosa, Hematocrito",
    )

    valor_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Mínimo",
    )

    valor_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Máximo",
    )

    valor_normal = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Valor Normal",
        help_text="Para valores cualitativos (Ej: Negativo, Positivo)",
    )

    unidad = models.CharField(
        max_length=50, choices=UNIDAD_CHOICES, verbose_name="Unidad de Medida",
    )

    condicion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Condición",
        help_text="Ej: En ayunas, Embarazadas primer trimestre",
    )

    es_critico_bajo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Crítico Bajo",
        help_text="Valor por debajo del cual se considera crítico",
    )

    es_critico_alto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Crítico Alto",
        help_text="Valor por encima del cual se considera crítico",
    )

    # Trazabilidad
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="valores_referencia_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="valores_referencia_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "valores_referencia"
        verbose_name = "Valor de Referencia"
        verbose_name_plural = "Valores de Referencia"
        ordering = ["tipo_examen", "parametro"]
        unique_together = ["tipo_examen", "parametro", "condicion"]

    def get_rango_completo(self):
        """Obtiene el rango completo como string"""
        if self.valor_minimo and self.valor_maximo:
            return f"{self.valor_minimo} - {self.valor_maximo} {self.unidad}"
        if self.valor_normal:
            return f"{self.valor_normal}"
        return "Rango no definido"

    def evaluar_valor(self, valor_numerico):
        """Evalúa si un valor está normal, anormal o crítico"""
        if not valor_numerico:
            return {"estado": "sin_valor", "mensaje": "Sin valor para evaluar"}

        valor = float(valor_numerico)

        # Verificar valores críticos
        if self.es_critico_bajo and valor < float(self.es_critico_bajo):
            return {
                "estado": "critico_bajo",
                "es_critico": True,
                "es_normal": False,
                "mensaje": f"Valor crítico bajo: {valor} < {self.es_critico_bajo}",
            }

        if self.es_critico_alto and valor > float(self.es_critico_alto):
            return {
                "estado": "critico_alto",
                "es_critico": True,
                "es_normal": False,
                "mensaje": f"Valor crítico alto: {valor} > {self.es_critico_alto}",
            }

        # Verificar rangos normales
        if self.valor_minimo and self.valor_maximo:
            if float(self.valor_minimo) <= valor <= float(self.valor_maximo):
                return {
                    "estado": "normal",
                    "es_critico": False,
                    "es_normal": True,
                    "mensaje": f"Valor normal: {self.valor_minimo} ≤ {valor} ≤ {self.valor_maximo}",
                }
            return {
                "estado": "anormal",
                "es_critico": False,
                "es_normal": False,
                "mensaje": f"Valor fuera de rango: {valor} (normal: {self.valor_minimo}-{self.valor_maximo})",
            }

        # Si no hay rangos definidos, considerar normal
        return {
            "estado": "sin_rango",
            "es_critico": False,
            "es_normal": True,
            "mensaje": "No hay rangos de referencia definidos",
        }

    def __str__(self):
        """Str"""
        rango = (
            f"{self.valor_minimo}-{self.valor_maximo}"
            if self.valor_minimo and self.valor_maximo
            else self.valor_normal
        )
        return f"{self.tipo_examen.nombre} - {self.parametro}: {rango} {self.unidad}"


class ResultadoLaboratorio(models.Model):
    """Resultados de exámenes de laboratorio"""

    examen = models.ForeignKey(
        ExamenLaboratorio,
        on_delete=models.CASCADE,
        related_name="resultados",
        verbose_name="Examen",
    )

    valor_referencia = models.ForeignKey(
        ValorReferencia,
        on_delete=models.PROTECT,
        related_name="resultados",
        verbose_name="Parámetro",
    )

    valor_numerico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Numérico",
    )

    valor_texto = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Valor Texto",
        help_text="Para resultados cualitativos",
    )

    es_normal = models.BooleanField(default=True, verbose_name="¿Es Normal")

    es_critico = models.BooleanField(default=False, verbose_name="¿Es Crítico")

    observaciones = models.TextField(
        blank=True, verbose_name="Observaciones del Resultado",
    )

    # Trazabilidad
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resultados_laboratorio_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resultados_laboratorio_modificados",
        verbose_name="Modificado por",
    )

    class Meta:
        """Meta"""
        db_table = "resultados_laboratorio"
        verbose_name = "Resultado de Laboratorio"
        verbose_name_plural = "Resultados de Laboratorio"
        ordering = ["examen", "valor_referencia"]
        indexes = [
            models.Index(fields=["examen"]),
            models.Index(fields=["es_critico"]),
            models.Index(fields=["es_normal"]),
        ]

    def calcular_estado_automatico(self):
        """Calcula automáticamente si el resultado es normal, anormal o crítico"""
        if not self.valor_numerico or not self.valor_referencia:
            return False

        evaluacion = self.valor_referencia.evaluar_valor(self.valor_numerico)
        self.es_critico = evaluacion["es_critico"]
        self.es_normal = evaluacion["es_normal"]
        return True

    def get_interpretacion_medica(self):
        """Devuelve la interpretación médica del resultado"""
        if not self.valor_numerico:
            return "Sin valor numérico para interpretar"

        valor = float(self.valor_numerico)
        parametro = self.valor_referencia.parametro.lower()

        # Interpretaciones específicas por parámetro
        interpretaciones = {
            "glucosa": self._interpretar_glucosa(valor),
            "hemoglobina": self._interpretar_hemoglobina(valor),
            "hematocrito": self._interpretar_hematocrito(valor),
            "leucocitos": self._interpretar_leucocitos(valor),
            "plaquetas": self._interpretar_plaquetas(valor),
            "creatinina": self._interpretar_creatinina(valor),
            "urea": self._interpretar_urea(valor),
            "colesterol": self._interpretar_colesterol(valor),
            "trigliceridos": self._interpretar_trigliceridos(valor),
        }

        for key, interpretation in interpretaciones.items():
            if key in parametro:
                return interpretation

        # Interpretación genérica
        if self.es_critico:
            return "⚠️ VALOR CRÍTICO: Requiere atención médica inmediata"
        if not self.es_normal:
            return " VALOR ANORMAL: Requiere evaluación médica"
        return "✅ VALOR NORMAL: Dentro de rangos esperados"

    def _interpretar_glucosa(self, valor):
        """Interpretación específica para glucosa"""
        if valor < 70:
            return f" HIPOGLUCEMIA SEVERA ({valor} mg/dL): Administrar glucosa inmediatamente"
        if valor < 100:
            return f"✅ GLUCOSA NORMAL ({valor} mg/dL): Valor óptimo"
        if valor < 126:
            return f" GLUCOSA ELEVADA ({valor} mg/dL): Riesgo de prediabetes"
        if valor < 200:
            return f" DIABETES ({valor} mg/dL): Requiere tratamiento antidiabético"
        return f" CRISIS DIABÉTICA ({valor} mg/dL): HOSPITALIZACIÓN INMEDIATA"

    def _interpretar_hemoglobina(self, valor):
        """Interpretación específica para hemoglobina"""
        if valor < 10:
            return f" ANEMIA SEVERA ({valor} g/dL): Considerar transfusión"
        if valor < 12:
            return f" ANEMIA LEVE ({valor} g/dL): Suplementar hierro"
        if valor <= 16:
            return f"✅ HEMOGLOBINA NORMAL ({valor} g/dL)"
        return f" POLICITEMIA ({valor} g/dL): Investigar causas"

    def _interpretar_hematocrito(self, valor):
        """Interpretación específica para hematocrito"""
        if valor < 30:
            return f" HEMATOCRITO BAJO ({valor}%): Anemia significativa"
        if valor <= 44:
            return f"✅ HEMATOCRITO NORMAL ({valor}%)"
        return f" HEMATOCRITO ELEVADO ({valor}%): Posible deshidratación"

    def _interpretar_leucocitos(self, valor):
        """Interpretación específica para leucocitos"""
        if valor < 4000:
            return f" LEUCOPENIA ({valor}/μL): Riesgo de infección"
        if valor <= 11000:
            return f"✅ LEUCOCITOS NORMALES ({valor}/μL)"
        return f" LEUCOCITOSIS ({valor}/μL): Posible infección o inflamación"

    def _interpretar_plaquetas(self, valor):
        """Interpretación específica para plaquetas"""
        if valor < 150000:
            return f" TROMBOCITOPENIA ({valor}/μL): Riesgo de sangrado"
        if valor <= 400000:
            return f"✅ PLAQUETAS NORMALES ({valor}/μL)"
        return f" TROMBOCITOSIS ({valor}/μL): Riesgo de trombosis"

    def _interpretar_creatinina(self, valor):
        """Interpretación específica para creatinina"""
        if valor > 1.5:
            return f" CREATININA ELEVADA ({valor} mg/dL): Posible insuficiencia renal"
        if valor <= 1.2:
            return f"✅ CREATININA NORMAL ({valor} mg/dL)"
        return f" CREATININA BORDERLINE ({valor} mg/dL): Monitorear función renal"

    def _interpretar_urea(self, valor):
        """Interpretación específica para urea"""
        if valor > 50:
            return f" UREA ELEVADA ({valor} mg/dL): Evaluar función renal"
        if valor <= 40:
            return f"✅ UREA NORMAL ({valor} mg/dL)"
        return f" UREA BORDERLINE ({valor} mg/dL): Control en seguimiento"

    def _interpretar_colesterol(self, valor):
        """Interpretación específica para colesterol"""
        if valor < 200:
            return f"✅ COLESTEROL DESEABLE ({valor} mg/dL)"
        if valor < 240:
            return f" COLESTEROL BORDERLINE ({valor} mg/dL): Modificar dieta"
        return f" COLESTEROL ALTO ({valor} mg/dL): Riesgo cardiovascular"

    def _interpretar_trigliceridos(self, valor):
        """Interpretación específica para triglicéridos"""
        if valor < 150:
            return f"✅ TRIGLICÉRIDOS NORMALES ({valor} mg/dL)"
        if valor < 200:
            return f" TRIGLICÉRIDOS BORDERLINE ({valor} mg/dL)"
        return f" TRIGLICÉRIDOS ALTOS ({valor} mg/dL): Riesgo cardiovascular"

    def get_protocolo_sugerido(self):
        """Devuelve el protocolo médico sugerido"""
        if not self.valor_numerico:
            return "No se puede determinar protocolo sin valor numérico"

        parametro = self.valor_referencia.parametro.lower()

        if self.es_critico:
            if "glucosa" in parametro:
                return self._protocolo_glucosa_critica()
            if "hemoglobina" in parametro or "hematocrito" in parametro:
                return self._protocolo_anemia_severa()
            if "creatinina" in parametro or "urea" in parametro:
                return self._protocolo_funcion_renal()
            return "1. Notificar al médico inmediatamente\n2. Repetir examen para confirmar\n3. Iniciar monitoreo continuo\n4. Considerar hospitalización si es necesario"
        if not self.es_normal:
            return "1. Evaluación médica en 24-48 horas\n2. Repetir examen en 1 semana\n3. Investigar causas subyacentes\n4. Modificaciones en estilo de vida si aplica"
        return "1. Continuar con controles rutinarios\n2. Mantener hábitos saludables\n3. Próximo control según programación"

    def _protocolo_glucosa_critica(self):
        """Protocolo para glucosa crítica"""
        valor = float(self.valor_numerico)
        if valor < 70:
            return """HIPOGLUCEMIA SEVERA:
                pass
1. Administrar 15-20g de glucosa oral (si consciente)
2. Si inconsciente: Glucosa IV al 50% (50ml)
3. Monitorear cada 15 minutos
4. Repetir glucosa en 1 hora
5. Investigar causa de hipoglucemia
6. Ajustar medicación antidiabética"""
        return """HIPERGLUCEMIA SEVERA:
                pass
1. Hidratación endovenosa (SSN 0.9%)
2. Insulina rápida según protocolo
3. Gasometría arterial (descartar cetoacidosis)
4. Electrolitos séricos completos
5. Monitoreo horario de glucosa
6. Considerar hospitalización en UCI"""

    def _protocolo_anemia_severa(self):
        """Protocolo para anemia severa"""
        return """ANEMIA SEVERA:
            pass
1. Tipificación sanguínea urgente
2. Pruebas cruzadas inmediatas
3. Considerar transfusión si Hb < 7 g/dL
4. Investigar causa (hierro sérico, B12, folatos)
5. Monitoreo de signos vitales
6. Evaluar sangrado activo"""

    def _protocolo_funcion_renal(self):
        """Protocolo para alteración de función renal"""
        return """FUNCIÓN RENAL ALTERADA:
            pass
1. Creatinina sérica y clearance
2. Electrolitos completos (Na, K, Cl)
3. Gasometría venosa
4. Ecografía renal
5. Suspender nefrotóxicos
6. Interconsulta a nefrología"""

    def get_recomendaciones_paciente(self):
        """Recomendaciones específicas para el paciente"""
        parametro = self.valor_referencia.parametro.lower()

        if "glucosa" in parametro and not self.es_normal:
            return """RECOMENDACIONES PARA GLUCOSA ALTERADA:
                pass
- Dieta baja en carbohidratos simples
- Ejercicio regular (30 min diarios)
- Control de peso corporal
- Monitoreo domiciliario de glucosa
- Medicación según prescripción médica"""

        if "colesterol" in parametro and not self.es_normal:
            return """RECOMENDACIONES PARA COLESTEROL ALTO:
                pass
- Dieta baja en grasas saturadas
- Aumentar consumo de fibra
- Ejercicio cardiovascular regular
- Evitar tabaco y alcohol excesivo
- Medicación si es indicada"""

        if (
            "hemoglobina" in parametro or "hematocrito" in parametro
        ) and not self.es_normal:
            return """RECOMENDACIONES PARA ANEMIA:
                pass
- Dieta rica en hierro (carnes rojas, espinacas)
- Suplementos de hierro según prescripción
- Vitamina C para mejorar absorción
- Evitar té y café con comidas
- Control médico regular"""

        return "Seguir indicaciones médicas específicas según el resultado obtenido"

    def get_valores_seguimiento(self):
        """Obtiene valores históricos para seguimiento"""
        return ResultadoLaboratorio.objects.filter(
            examen__paciente=self.examen.paciente,
            valor_referencia=self.valor_referencia,
        ).order_by("-fecha_registro")[:5]

    def calcular_tendencia(self):
        """Calcula la tendencia del parámetro (mejorando/empeorando/estable)"""
        valores_anteriores = self.get_valores_seguimiento()

        if len(valores_anteriores) < 2:
            return "Sin suficientes datos para tendencia"

        valor_actual = float(self.valor_numerico) if self.valor_numerico else 0
        valor_anterior = (
            float(valores_anteriores[1].valor_numerico)
            if valores_anteriores[1].valor_numerico
            else 0
        )

        if valor_actual == valor_anterior:
            return " ESTABLE"

        # Determinar si el aumento es bueno o malo según el parámetro
        parametro = self.valor_referencia.parametro.lower()

        if valor_actual > valor_anterior:
            if any(
                param in parametro
                for param in ["glucosa", "creatinina", "urea", "colesterol"]
            ):
                return " EMPEORANDO (aumentando)"
            return " MEJORANDO (aumentando)"
        if any(
            param in parametro
            for param in ["hemoglobina", "hematocrito", "plaquetas"]
        ):
            return " EMPEORANDO (disminuyendo)"
        return " MEJORANDO (disminuyendo)"

    # Métodos para el admin
    def interpretacion_medica_completa(self):
        """Método para mostrar interpretación completa en admin"""
        return self.get_interpretacion_medica()

    def protocolo_medico(self):
        """Método para mostrar protocolo médico en admin"""
        return self.get_protocolo_sugerido()

    def recomendaciones_paciente(self):
        """Método para mostrar recomendaciones en admin"""
        return self.get_recomendaciones_paciente()

    def tendencia_historica(self):
        """Método para mostrar tendencia histórica en admin"""
        valores = self.get_valores_seguimiento()
        if len(valores) <= 1:
            return "Sin datos históricos suficientes"

        historial = []
        for i, valor in enumerate(valores[:5]):
            fecha = valor.fecha_registro.strftime("%d/%m/%Y")
            val = valor.valor_numerico or valor.valor_texto
            estado = (
                " CRÍTICO"
                if valor.es_critico
                else "⚠️ ANORMAL"
                if not valor.es_normal
                else "✅ NORMAL"
            )
            historial.append(
                f"{i + 1}. {fecha}: {val} {valor.valor_referencia.unidad} - {estado}",
            )

        return "\n".join(historial)

    def save(self, *args, **kwargs):
        """Calcula automáticamente el estado al guardar"""
        self.calcular_estado_automatico()
        super().save(*args, **kwargs)

    def __str__(self):
        """Str"""
        valor = self.valor_numerico or self.valor_texto
        return (
            f"{self.valor_referencia.parametro}: {valor} {self.valor_referencia.unidad}"
        )


class ImagenLaboratorio(models.Model):
    """Imágenes y archivos de resultados de laboratorio"""

    TIPO_ARCHIVO_CHOICES = [
        ("hoja_resultados", "Hoja de Resultados"),
        ("hemograma", "Hemograma"),
        ("bioquimica", "Bioquímica Clínica"),
        ("urinalisis", "Urianálisis"),
        ("cultivo", "Cultivo"),
        ("antibiograma", "Antibiograma"),
        ("serologia", "Serología"),
        ("perfil_hormonal", "Perfil Hormonal"),
        ("perfil_tiroideo", "Perfil Tiroideo"),
        ("coagulacion", "Coagulación"),
        ("inmunologia", "Inmunología"),
        ("toxicologia", "Toxicología"),
        ("genetica", "Genética"),
        ("citologia", "Citología"),
        ("histopatologia", "Histopatología"),
        ("microbiologia", "Microbiología"),
        ("papanicolau", "Papanicolau"),
        ("biopsia", "Biopsia"),
        ("otros", "Otros Resultados"),
    ]

    FORMATO_CHOICES = [
        ("pd", "PDF"),
        ("jpg", "JPG/JPEG"),
        ("png", "PNG"),
        ("tif", "TIFF"),
        ("dicom", "DICOM"),
    ]

    examen = models.ForeignKey(
        ExamenLaboratorio,
        on_delete=models.CASCADE,
        related_name="imagenes",
        verbose_name="Examen de Laboratorio",
    )

    archivo = models.FileField(
        upload_to="laboratorio/%Y/%m/%d/",
        verbose_name="Archivo/Imagen",
        help_text="Resultado escaneado, foto o PDF del laboratorio",
    )

    tipo_archivo = models.CharField(
        max_length=50,
        choices=TIPO_ARCHIVO_CHOICES,
        default="hoja_resultados",
        verbose_name="Tipo de Archivo",
    )

    formato = models.CharField(
        max_length=10,
        choices=FORMATO_CHOICES,
        default="pd",
        verbose_name="Formato del Archivo",
    )

    titulo = models.CharField(
        max_length=200,
        verbose_name="Título del Documento",
        default="Resultado de Laboratorio",
        help_text="Ej: Hemograma completo 12/12/2024",
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Notas adicionales sobre el resultado",
    )

    numero_paginas = models.PositiveIntegerField(
        default=1,
        verbose_name="Número de Páginas",
        help_text="Para documentos multi-página",
    )

    calidad_digitalizacion = models.CharField(
        max_length=20,
        choices=[
            ("excelente", "Excelente"),
            ("buena", "Buena"),
            ("regular", "Regular"),
            ("baja", "Baja"),
        ],
        default="buena",
        verbose_name="Calidad de Digitalización",
    )

    es_documento_oficial = models.BooleanField(
        default=True,
        verbose_name="¿Es Documento Oficial",
        help_text="Documento sellado y firmado por laboratorio",
    )

    laboratorio_externo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Laboratorio Externo",
        help_text="Nombre del laboratorio que realizó el examen",
    )

    fecha_digitalizacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Digitalización",
    )

    digitalizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="digitalizaciones_laboratorio",
        verbose_name="Digitalizado Por",
    )

    # Trazabilidad adicional
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imagenes_laboratorio_creadas",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imagenes_laboratorio_modificadas",
        verbose_name="Modificado por",
    )

    orden = models.PositiveIntegerField(
        default=1, verbose_name="Orden", help_text="Orden de visualización",
    )

    es_archivo_principal = models.BooleanField(
        default=False,
        verbose_name="¿Es Archivo Principal",
        help_text="Documento principal del resultado",
    )

    # OCR y análisis automático
    texto_extraido_ocr = models.TextField(
        blank=True,
        verbose_name="Texto Extraído (OCR)",
        help_text="Texto extraído automáticamente del documento",
    )

    datos_extraidos_ia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos Extraídos por IA",
        help_text="Valores y parámetros detectados automáticamente",
    )

    validado_por_medico = models.BooleanField(
        default=False,
        verbose_name="¿Validado por Médico",
        help_text="El médico ha verificado que el archivo es correcto",
    )

    class Meta:
        """Meta"""
        db_table = "imagenes_laboratorio"
        verbose_name = "Imagen/Archivo de Laboratorio"
        verbose_name_plural = "Imágenes/Archivos de Laboratorio"
        ordering = ["examen", "orden"]
        indexes = [
            models.Index(fields=["examen", "tipo_archivo"]),
            models.Index(fields=["fecha_digitalizacion"]),
        ]

    def get_tamano_archivo(self):
        """Obtiene el tamaño del archivo en formato legible"""
        if self.archivo and hasattr(self.archivo, "size"):
            size = self.archivo.size
            if size < 1024:
                return f"{size} bytes"
            if size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            return f"{size / (1024 * 1024):.1f} MB"
        return "Tamaño desconocido"

    def get_extension(self):
        """Obtiene la extensión del archivo"""
        if self.archivo:
            return os.path.splitext(self.archivo.name)[1].lower()
        return ""

    def es_imagen(self):
        """Verifica si el archivo es una imagen"""
        extensiones_imagen = [".jpg", ".jpeg", ".png", ".tif", ".ti", ".bmp", ".gi"]
        return self.get_extension() in extensiones_imagen

    def es_pdf(self):
        """Verifica si el archivo es PDF"""
        return self.get_extension() == ".pd"

    def generar_thumbnail(self, size=(300, 300)):
        """Genera miniatura si es imagen"""
        if not self.es_imagen():
            return None

        try:
            from PIL import Image

            thumb_name = f"thumb_{os.path.basename(self.archivo.name)}"
            thumb_path = os.path.join(
                os.path.dirname(self.archivo.path), "thumbnails", thumb_name,
            )

            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)

            with Image.open(self.archivo.path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumb_path, "JPEG", quality=85)

            return thumb_path
        except Exception as e:
            print(f"Error generando thumbnail: {e}")
            return None

    def extraer_texto_ocr(self):
        """Placeholder para OCR futuro con Tesseract o servicio IA"""
        # Aquí se integraría Tesseract OCR o Google Vision API
        ocr_result = {
            "procesado": True,
            "fecha_ocr": str(timezone.now()),
            "confianza_promedio": 0.0,
            "texto_completo": "",
            "parametros_detectados": [],
            "valores_detectados": {},
        }

        self.texto_extraido_ocr = "Texto pendiente de extracción..."
        self.datos_extraidos_ia = ocr_result
        return ocr_result

    def validar_firma_digital(self):
        """Placeholder para validación de firma digital en PDFs"""
        if not self.es_pdf():
            return {"firmado": False, "mensaje": "No es archivo PDF"}

        # Aquí se integraría PyPDF2 o similar para verificar firmas
        return {
            "firmado": False,
            "valido": False,
            "firmante": None,
            "fecha_firma": None,
        }

    def save(self, *args, **kwargs):
        """Save"""
        # Detectar formato automáticamente
        extension = self.get_extension()
        formato_map = {
            ".pd": "pd",
            ".jpg": "jpg",
            ".jpeg": "jpg",
            ".png": "png",
            ".tif": "tif",
            ".ti": "tif",
        }
        if extension in formato_map:
            self.formato = formato_map[extension]

        # Si es principal, quitar flag de otros
        if self.es_archivo_principal:
            ImagenLaboratorio.objects.filter(
                examen=self.examen, es_archivo_principal=True,
            ).update(es_archivo_principal=False)

        super().save(*args, **kwargs)

        # Generar thumbnail si es imagen
        if self.es_imagen():
            self.generar_thumbnail()

    def __str__(self):
        """Str"""
        return f"{self.titulo} - {self.examen.paciente.nombre_completo}"
