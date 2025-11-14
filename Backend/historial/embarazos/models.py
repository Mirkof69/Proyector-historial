# =============================================================================
# MODELOS DE EMBARAZOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: embarazos
# Descripción: Modelos completos para gestión de embarazos, complicaciones,
#              seguimiento, eventos y resultados perinatales.
# Versión: 3.0.0
# Última actualización: 2025-11-14
# =============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import uuid

from pacientes.models import Paciente


# =============================================================================
# MODELO PRINCIPAL: EMBARAZO
# =============================================================================

class Embarazo(models.Model):
    """
    Modelo completo de embarazo con seguimiento detallado.

    Almacena:
    - Información básica del embarazo (FUR, FPP, número de gesta)
    - Tipo de embarazo (único, gemelar, múltiple)
    - Datos pre-gestacionales (peso, IMC, talla)
    - Factores de riesgo y complicaciones
    - Resultado del embarazo
    - Hospitalizaciones
    - Auditoría completa

    Funcionalidades:
    - Cálculo automático de edad gestacional
    - Cálculo de FPP (Fecha Probable de Parto)
    - Clasificación de IMC pre-gestacional
    - Determinación de trimestre actual
    - Evaluación de riesgo
    - Soft delete
    """

    # =========================================================================
    # OPCIONES Y CHOICES
    # =========================================================================

    TIPOS_EMBARAZO = (
        ('unico', 'Único'),
        ('gemelar', 'Gemelar'),
        ('triple', 'Triple'),
        ('cuadruple', 'Cuádruple'),
        ('multiple_otro', 'Múltiple (Otro)'),
    )

    CORIONICIDAD_CHOICES = (
        ('monocorial_monoamniotico', 'Monocorial Monoamniótico'),
        ('monocorial_biamniotico', 'Monocorial Biamniótico'),
        ('bicorial_biamniotico', 'Bicorial Biamniótico'),
        ('tricorial', 'Tricorial'),
        ('no_determinada', 'No Determinada'),
    )

    NIVEL_RIESGO_CHOICES = (
        ('bajo', 'Bajo Riesgo'),
        ('medio', 'Riesgo Medio'),
        ('alto', 'Alto Riesgo'),
        ('muy_alto', 'Muy Alto Riesgo'),
    )

    ESTADO_EMBARAZO_CHOICES = (
        ('en_curso', 'En Curso'),
        ('finalizado_parto', 'Finalizado - Parto Vaginal'),
        ('finalizado_cesarea', 'Finalizado - Cesárea'),
        ('finalizado_aborto', 'Finalizado - Aborto'),
        ('finalizado_muerte_fetal', 'Finalizado - Muerte Fetal'),
        ('finalizado_otro', 'Finalizado - Otro'),
    )

    METODO_CONCEPCION_CHOICES = (
        ('natural', 'Natural'),
        ('fertilizacion_in_vitro', 'Fertilización In Vitro (FIV)'),
        ('inseminacion_artificial', 'Inseminación Artificial'),
        ('icsi', 'ICSI'),
        ('transferencia_embriones', 'Transferencia de Embriones'),
        ('otro', 'Otro'),
    )

    # =========================================================================
    # CAMPOS BÁSICOS
    # =========================================================================

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identificador único universal del embarazo"
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        db_column='paciente_id',
        related_name='embarazos',
        help_text="Paciente gestante"
    )

    numero_gesta = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Número de gesta (embarazo actual incluido)"
    )

    # =========================================================================
    # FECHAS CLAVE
    # =========================================================================

    fecha_ultima_menstruacion = models.DateField(
        verbose_name='FUR',
        help_text="Fecha de Última Regla (FUR)"
    )

    fecha_probable_parto = models.DateField(
        blank=True,
        null=True,
        verbose_name='FPP',
        help_text="Fecha Probable de Parto (FPP) - Se calcula automáticamente"
    )

    fur_confiable = models.BooleanField(
        default=True,
        help_text="¿La FUR es confiable?"
    )

    fecha_primera_ecografia = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de la primera ecografía obstétrica"
    )

    edad_gestacional_primera_eco = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Edad gestacional en semanas según primera ecografía"
    )

    fpp_corregida_eco = models.DateField(
        blank=True,
        null=True,
        help_text="FPP corregida según ecografía si difiere >7 días de FUR"
    )

    # =========================================================================
    # TIPO DE EMBARAZO Y CONCEPCIÓN
    # =========================================================================

    tipo_embarazo = models.CharField(
        max_length=50,
        choices=TIPOS_EMBARAZO,
        default='unico'
    )

    numero_fetos = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Número de fetos"
    )

    corionicidad = models.CharField(
        max_length=50,
        choices=CORIONICIDAD_CHOICES,
        blank=True,
        null=True,
        help_text="Corionicidad en embarazos múltiples"
    )

    es_planeado = models.BooleanField(
        default=False,
        help_text="¿El embarazo fue planeado?"
    )

    metodo_concepcion = models.CharField(
        max_length=50,
        choices=METODO_CONCEPCION_CHOICES,
        default='natural'
    )

    metodo_anticonceptivo_fallo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Método anticonceptivo que falló (si aplica)"
    )

    # =========================================================================
    # DATOS PRE-GESTACIONALES
    # =========================================================================

    peso_pregestacional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('30.00')), MaxValueValidator(Decimal('200.00'))],
        help_text="Peso pre-gestacional en kg"
    )

    talla_madre = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('120.00')), MaxValueValidator(Decimal('220.00'))],
        help_text="Talla de la madre en cm"
    )

    imc_pregestacional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="IMC pre-gestacional (calculado automáticamente)"
    )

    clasificacion_imc = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Clasificación del IMC (bajo peso, normal, sobrepeso, obesidad)"
    )

    semanas_al_diagnostico = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(42)],
        help_text="Semanas de gestación al momento del diagnóstico"
    )

    # =========================================================================
    # NIVEL DE RIESGO
    # =========================================================================

    embarazo_alto_riesgo = models.BooleanField(
        default=False,
        help_text="¿Es un embarazo de alto riesgo?"
    )

    nivel_riesgo = models.CharField(
        max_length=20,
        choices=NIVEL_RIESGO_CHOICES,
        default='bajo'
    )

    factores_riesgo = models.TextField(
        blank=True,
        null=True,
        help_text="Lista detallada de factores de riesgo identificados"
    )

    # =========================================================================
    # COMPLICACIONES DEL EMBARAZO ACTUAL
    # =========================================================================

    tiene_complicaciones = models.BooleanField(
        default=False,
        help_text="¿Ha presentado complicaciones?"
    )

    # Complicaciones metabólicas
    diabetes_gestacional = models.BooleanField(default=False)
    diabetes_gestacional_fecha = models.DateField(blank=True, null=True)

    # Complicaciones hipertensivas
    hipertension_gestacional = models.BooleanField(default=False)
    hipertension_gestacional_fecha = models.DateField(blank=True, null=True)

    preeclampsia = models.BooleanField(default=False)
    preeclampsia_fecha = models.DateField(blank=True, null=True)
    preeclampsia_severidad = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[('leve', 'Leve'), ('grave', 'Grave')]
    )

    eclampsia = models.BooleanField(default=False)
    eclampsia_fecha = models.DateField(blank=True, null=True)

    sindrome_hellp = models.BooleanField(
        default=False,
        help_text="Síndrome HELLP"
    )
    sindrome_hellp_fecha = models.DateField(blank=True, null=True)

    # Amenaza de parto prematuro y membranas
    amenaza_parto_prematuro = models.BooleanField(default=False)
    amenaza_parto_prematuro_fecha = models.DateField(blank=True, null=True)

    ruptura_prematura_membranas = models.BooleanField(
        default=False,
        verbose_name='RPM'
    )
    ruptura_prematura_membranas_fecha = models.DateField(blank=True, null=True)
    ruptura_prematura_membranas_semanas = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True
    )

    # Complicaciones placentarias
    placenta_previa = models.BooleanField(default=False)
    placenta_previa_tipo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('marginal', 'Marginal'),
            ('parcial', 'Parcial'),
            ('total', 'Total'),
            ('oclusiva', 'Oclusiva')
        ]
    )

    desprendimiento_placenta = models.BooleanField(
        default=False,
        verbose_name='DPPNI'
    )
    desprendimiento_placenta_fecha = models.DateField(blank=True, null=True)

    placenta_accreta = models.BooleanField(default=False)

    # Restricción del crecimiento fetal
    restriccion_crecimiento = models.BooleanField(
        default=False,
        verbose_name='RCIU'
    )
    restriccion_crecimiento_fecha = models.DateField(blank=True, null=True)
    restriccion_crecimiento_tipo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[('simetrico', 'Simétrico'), ('asimetrico', 'Asimétrico')]
    )

    # Problemas del líquido amniótico
    polihidramnios = models.BooleanField(default=False)
    polihidramnios_fecha = models.DateField(blank=True, null=True)

    oligohidramnios = models.BooleanField(default=False)
    oligohidramnios_fecha = models.DateField(blank=True, null=True)

    # Otras complicaciones
    colestasis_intrahepatica = models.BooleanField(default=False)
    colestasis_intrahepatica_fecha = models.DateField(blank=True, null=True)

    anemia_gestacional = models.BooleanField(default=False)
    hemoglobina_minima = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Hemoglobina mínima durante el embarazo (g/dL)"
    )

    infeccion_urinaria_recurrente = models.BooleanField(default=False)
    numero_itus = models.IntegerField(
        default=0,
        help_text="Número de ITUs durante el embarazo"
    )

    amenaza_aborto = models.BooleanField(default=False)
    amenaza_aborto_semanas = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True
    )

    incompetencia_cervical_actual = models.BooleanField(default=False)
    cerclaje_realizado = models.BooleanField(default=False)
    cerclaje_fecha = models.DateField(blank=True, null=True)

    # =========================================================================
    # HOSPITALIZACIÓN
    # =========================================================================

    requirio_hospitalizacion = models.BooleanField(
        default=False,
        help_text="¿Requirió hospitalización durante el embarazo?"
    )

    numero_hospitalizaciones = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    dias_hospitalizacion_total = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total de días hospitalizados durante el embarazo"
    )

    hospitalizacion_uci = models.BooleanField(
        default=False,
        help_text="¿Requirió UCI?"
    )

    # =========================================================================
    # RESULTADO DEL EMBARAZO
    # =========================================================================

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_EMBARAZO_CHOICES,
        default='en_curso'
    )

    fecha_finalizacion = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha en que finalizó el embarazo"
    )

    edad_gestacional_finalizacion = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Edad gestacional al momento de finalizar (semanas)"
    )

    via_finalizacion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('parto_vaginal', 'Parto Vaginal'),
            ('cesarea', 'Cesárea'),
            ('aborto_espontaneo', 'Aborto Espontáneo'),
            ('aborto_inducido', 'Aborto Inducido'),
            ('legrado', 'Legrado'),
            ('muerte_fetal', 'Muerte Fetal')
        ]
    )

    indicacion_cesarea = models.TextField(
        blank=True,
        null=True,
        help_text="Indicación médica de la cesárea (si aplica)"
    )

    resultado_embarazo = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción detallada del resultado del embarazo"
    )

    # =========================================================================
    # INFORMACIÓN ADICIONAL
    # =========================================================================

    medico_responsable = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_column='medico_responsable',
        help_text="Nombre del médico responsable del seguimiento"
    )

    medico_responsable_fk = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='embarazos_responsable',
        limit_choices_to={'rol': 'medico'},
        help_text="Médico responsable (relación a Usuario)"
    )

    notas = models.TextField(
        blank=True,
        null=True,
        help_text="Notas generales del embarazo"
    )

    plan_parto = models.TextField(
        blank=True,
        null=True,
        help_text="Plan de parto acordado con la paciente"
    )

    # =========================================================================
    # SOFT DELETE Y AUDITORÍA
    # =========================================================================

    activo = models.BooleanField(
        default=True,
        help_text="Registro activo o eliminado (soft delete)"
    )

    eliminado = models.BooleanField(default=False)

    fecha_eliminacion = models.DateTimeField(
        blank=True,
        null=True
    )

    eliminado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='embarazos_eliminados'
    )

    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='embarazos_creados'
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    modificado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='embarazos_modificados'
    )

    fecha_modificacion = models.DateTimeField(auto_now=True)

    # =========================================================================
    # MÉTODOS DEL MODELO
    # =========================================================================

    class Meta:
        db_table = 'embarazos'
        managed = False
        ordering = ['-fecha_registro']
        verbose_name = "Embarazo"
        verbose_name_plural = "Embarazos"
        indexes = [
            models.Index(fields=['paciente', 'estado']),
            models.Index(fields=['fecha_ultima_menstruacion']),
            models.Index(fields=['nivel_riesgo']),
        ]

    def __str__(self):
        return f"Embarazo {self.numero_gesta} - {self.paciente.nombres} {self.paciente.apellidos}"

    def save(self, *args, **kwargs):
        """
        Sobrescribe save para cálculos automáticos.
        """
        # Calcular FPP si no existe
        if not self.fecha_probable_parto and self.fecha_ultima_menstruacion:
            self.fecha_probable_parto = self.calcular_fpp()

        # Calcular IMC pre-gestacional
        if self.peso_pregestacional and self.talla_madre and not self.imc_pregestacional:
            self.imc_pregestacional = self.calcular_imc_pregestacional()
            self.clasificacion_imc = self.clasificar_imc()

        # Actualizar flag de complicaciones
        self.tiene_complicaciones = self.verificar_complicaciones()

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete: marca como eliminado sin borrar de la base de datos.
        """
        self.activo = False
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def hard_delete(self):
        """
        Eliminación permanente de la base de datos.
        """
        super().delete()

    # -------------------------------------------------------------------------
    # CÁLCULOS DE EDAD GESTACIONAL
    # -------------------------------------------------------------------------

    def calcular_fpp(self):
        """
        Calcula la Fecha Probable de Parto usando la Regla de Naegele.
        FPP = FUR + 7 días - 3 meses + 1 año
        """
        if not self.fecha_ultima_menstruacion:
            return None

        fpp = self.fecha_ultima_menstruacion + timedelta(days=280)  # 40 semanas = 280 días
        return fpp

    def get_edad_gestacional_actual(self):
        """
        Calcula la edad gestacional actual en semanas.
        Usa la FUR si es confiable, o la FPP corregida por ecografía.
        """
        if self.estado != 'en_curso':
            return self.edad_gestacional_finalizacion

        hoy = timezone.now().date()

        # Usar FPP corregida si existe
        if self.fpp_corregida_eco and not self.fur_confiable:
            dias_hasta_fpp = (self.fpp_corregida_eco - hoy).days
            semanas = 40 - (dias_hasta_fpp / 7)
        else:
            # Usar FUR
            dias_desde_fur = (hoy - self.fecha_ultima_menstruacion).days
            semanas = dias_desde_fur / 7

        return round(semanas, 1) if semanas >= 0 else 0

    def get_dias_gestacionales(self):
        """
        Retorna edad gestacional en días.
        """
        if self.estado != 'en_curso':
            return None

        hoy = timezone.now().date()
        dias = (hoy - self.fecha_ultima_menstruacion).days
        return dias if dias >= 0 else 0

    def get_trimestre_actual(self):
        """
        Determina el trimestre actual del embarazo.
        """
        semanas = self.get_edad_gestacional_actual()
        if not semanas:
            return None

        if semanas <= 13:
            return 1
        elif semanas <= 27:
            return 2
        else:
            return 3

    def get_semanas_restantes(self):
        """
        Calcula cuántas semanas faltan hasta la FPP.
        """
        if self.estado != 'en_curso':
            return 0

        semanas_actuales = self.get_edad_gestacional_actual()
        if semanas_actuales:
            return max(0, 40 - semanas_actuales)
        return None

    def get_fecha_parto_estimada(self):
        """
        Retorna la FPP (corregida si existe, o calculada de FUR).
        """
        return self.fpp_corregida_eco or self.fecha_probable_parto or self.calcular_fpp()

    # -------------------------------------------------------------------------
    # CÁLCULOS DE IMC
    # -------------------------------------------------------------------------

    def calcular_imc_pregestacional(self):
        """
        Calcula el IMC pre-gestacional.
        IMC = peso (kg) / (talla (m))^2
        """
        if not self.peso_pregestacional or not self.talla_madre:
            return None

        talla_metros = self.talla_madre / 100
        imc = float(self.peso_pregestacional) / (talla_metros ** 2)
        return round(imc, 2)

    def clasificar_imc(self):
        """
        Clasifica el IMC pre-gestacional según OMS.
        """
        imc = self.imc_pregestacional or self.calcular_imc_pregestacional()

        if not imc:
            return None

        if imc < 18.5:
            return "Bajo peso"
        elif imc < 25:
            return "Peso normal"
        elif imc < 30:
            return "Sobrepeso"
        elif imc < 35:
            return "Obesidad grado I"
        elif imc < 40:
            return "Obesidad grado II"
        else:
            return "Obesidad grado III (mórbida)"

    # -------------------------------------------------------------------------
    # EVALUACIÓN DE RIESGO
    # -------------------------------------------------------------------------

    def verificar_complicaciones(self):
        """
        Verifica si hay al menos una complicación registrada.
        """
        complicaciones = [
            self.diabetes_gestacional,
            self.hipertension_gestacional,
            self.preeclampsia,
            self.eclampsia,
            self.sindrome_hellp,
            self.amenaza_parto_prematuro,
            self.ruptura_prematura_membranas,
            self.placenta_previa,
            self.desprendimiento_placenta,
            self.placenta_accreta,
            self.restriccion_crecimiento,
            self.polihidramnios,
            self.oligohidramnios,
            self.colestasis_intrahepatica,
            self.anemia_gestacional,
            self.infeccion_urinaria_recurrente,
            self.amenaza_aborto,
        ]
        return any(complicaciones)

    def evaluar_nivel_riesgo(self):
        """
        Evalúa y retorna el nivel de riesgo del embarazo.
        Basado en factores obstétricos, médicos y complicaciones.
        """
        riesgo = 0

        # Factores de la paciente
        if self.paciente:
            edad = self.paciente.calcular_edad()
            if edad:
                if edad < 18:
                    riesgo += 15
                elif edad > 35:
                    riesgo += 10
                if edad > 40:
                    riesgo += 20

            if self.paciente.diabetes_previa:
                riesgo += 20
            if self.paciente.hipertension_previa:
                riesgo += 15
            if self.paciente.preeclampsia_previa:
                riesgo += 25
            if self.paciente.cesareas >= 2:
                riesgo += 15

        # Tipo de embarazo
        if self.tipo_embarazo != 'unico':
            riesgo += 20

        # IMC
        imc = self.imc_pregestacional
        if imc:
            if imc < 18.5:
                riesgo += 10
            elif imc >= 30:
                riesgo += 15

        # Complicaciones del embarazo actual
        if self.preeclampsia:
            riesgo += 30
        if self.eclampsia:
            riesgo += 50
        if self.sindrome_hellp:
            riesgo += 40
        if self.placenta_previa:
            riesgo += 25
        if self.desprendimiento_placenta:
            riesgo += 35
        if self.restriccion_crecimiento:
            riesgo += 20
        if self.diabetes_gestacional:
            riesgo += 15

        # Clasificar nivel de riesgo
        if riesgo >= 50:
            return 'muy_alto'
        elif riesgo >= 30:
            return 'alto'
        elif riesgo >= 15:
            return 'medio'
        else:
            return 'bajo'

    def get_complicaciones_listado(self):
        """
        Retorna un listado de todas las complicaciones presentes.
        """
        complicaciones = []

        if self.diabetes_gestacional:
            complicaciones.append('Diabetes Gestacional')
        if self.hipertension_gestacional:
            complicaciones.append('Hipertensión Gestacional')
        if self.preeclampsia:
            severidad = f" ({self.preeclampsia_severidad})" if self.preeclampsia_severidad else ""
            complicaciones.append(f'Preeclampsia{severidad}')
        if self.eclampsia:
            complicaciones.append('Eclampsia')
        if self.sindrome_hellp:
            complicaciones.append('Síndrome HELLP')
        if self.amenaza_parto_prematuro:
            complicaciones.append('Amenaza de Parto Prematuro')
        if self.ruptura_prematura_membranas:
            complicaciones.append('Ruptura Prematura de Membranas')
        if self.placenta_previa:
            tipo = f" ({self.placenta_previa_tipo})" if self.placenta_previa_tipo else ""
            complicaciones.append(f'Placenta Previa{tipo}')
        if self.desprendimiento_placenta:
            complicaciones.append('Desprendimiento Prematuro de Placenta')
        if self.placenta_accreta:
            complicaciones.append('Placenta Accreta')
        if self.restriccion_crecimiento:
            complicaciones.append('Restricción del Crecimiento Fetal')
        if self.polihidramnios:
            complicaciones.append('Polihidramnios')
        if self.oligohidramnios:
            complicaciones.append('Oligohidramnios')
        if self.colestasis_intrahepatica:
            complicaciones.append('Colestasis Intrahepática')
        if self.anemia_gestacional:
            complicaciones.append('Anemia Gestacional')
        if self.infeccion_urinaria_recurrente:
            complicaciones.append(f'ITU Recurrente ({self.numero_itus} episodios)')
        if self.amenaza_aborto:
            complicaciones.append('Amenaza de Aborto')
        if self.cerclaje_realizado:
            complicaciones.append('Cerclaje Cervical Realizado')

        return complicaciones


# =============================================================================
# MODELO SECUNDARIO: COMPLICACIÓN DE EMBARAZO (DETALLADA)
# =============================================================================

class ComplicacionEmbarazo(models.Model):
    """
    Registro detallado de cada complicación durante el embarazo.
    Permite un seguimiento más granular que los campos booleanos del Embarazo.
    """

    TIPOS_COMPLICACION = (
        ('diabetes_gestacional', 'Diabetes Gestacional'),
        ('hipertension', 'Hipertensión Gestacional'),
        ('preeclampsia_leve', 'Preeclampsia Leve'),
        ('preeclampsia_grave', 'Preeclampsia Grave'),
        ('eclampsia', 'Eclampsia'),
        ('sindrome_hellp', 'Síndrome HELLP'),
        ('amenaza_aborto', 'Amenaza de Aborto'),
        ('amenaza_parto_prematuro', 'Amenaza de Parto Prematuro'),
        ('rpp', 'Ruptura Prematura de Membranas'),
        ('placenta_previa', 'Placenta Previa'),
        ('dppni', 'Desprendimiento Prematuro Placenta'),
        ('placenta_accreta', 'Placenta Accreta'),
        ('rciu', 'Restricción Crecimiento Intrauterino'),
        ('polihidramnios', 'Polihidramnios'),
        ('oligohidramnios', 'Oligohidramnios'),
        ('colestasis', 'Colestasis Intrahepática'),
        ('anemia', 'Anemia Gestacional'),
        ('itu', 'Infección Urinaria'),
        ('corioamnionitis', 'Corioamnionitis'),
        ('incompetencia_cervical', 'Incompetencia Cervical'),
        ('hemorragia_anteparto', 'Hemorragia Anteparto'),
        ('otra', 'Otra Complicación')
    )

    SEVERIDAD_CHOICES = (
        ('leve', 'Leve'),
        ('moderada', 'Moderada'),
        ('grave', 'Grave'),
        ('critica', 'Crítica')
    )

    id = models.AutoField(primary_key=True)

    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        related_name='complicaciones_detalladas',
        help_text="Embarazo al que pertenece esta complicación"
    )

    tipo_complicacion = models.CharField(
        max_length=100,
        choices=TIPOS_COMPLICACION
    )

    fecha_diagnostico = models.DateField(
        help_text="Fecha en que se diagnosticó la complicación"
    )

    edad_gestacional_diagnostico = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Edad gestacional al momento del diagnóstico (semanas)"
    )

    severidad = models.CharField(
        max_length=20,
        choices=SEVERIDAD_CHOICES,
        default='moderada'
    )

    descripcion = models.TextField(
        help_text="Descripción detallada de la complicación"
    )

    sintomas = models.TextField(
        blank=True,
        null=True,
        help_text="Síntomas presentados"
    )

    hallazgos_clinicos = models.TextField(
        blank=True,
        null=True,
        help_text="Hallazgos clínicos relevantes"
    )

    tratamiento = models.TextField(
        blank=True,
        null=True,
        help_text="Tratamiento instaurado"
    )

    medicamentos = models.TextField(
        blank=True,
        null=True,
        help_text="Medicamentos utilizados"
    )

    requirio_hospitalizacion = models.BooleanField(
        default=False
    )

    fecha_hospitalizacion = models.DateField(
        blank=True,
        null=True
    )

    dias_hospitalizacion = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )

    requirio_uci = models.BooleanField(
        default=False,
        help_text="¿Requirió ingreso a UCI?"
    )

    resuelto = models.BooleanField(
        default=False,
        help_text="¿La complicación se resolvió?"
    )

    fecha_resolucion = models.DateField(
        blank=True,
        null=True
    )

    secuelas = models.TextField(
        blank=True,
        null=True,
        help_text="Secuelas resultantes de la complicación"
    )

    # Auditoría
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='complicaciones_creadas'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    modificado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='complicaciones_modificadas'
    )

    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'complicaciones_embarazo'
        managed = False
        ordering = ['-fecha_diagnostico']
        verbose_name = "Complicación de Embarazo"
        verbose_name_plural = "Complicaciones de Embarazos"

    def __str__(self):
        return f"{self.get_tipo_complicacion_display()} - {self.embarazo}"