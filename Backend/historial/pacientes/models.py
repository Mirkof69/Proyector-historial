# =============================================================================
# MODELOS DE PACIENTES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: pacientes
# Descripción: Modelo completo de pacientes con historial médico obstétrico detallado.
#              Incluye antecedentes personales, familiares, gineco-obstétricos,
#              factores de riesgo, hábitos, datos socioeconómicos y contactos de emergencia.
# Autor: Sistema de Gestión Médica
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

# =============================================================================
# MODELO PRINCIPAL: PACIENTE
# =============================================================================
class Paciente(models.Model):
    """
    Modelo completo de paciente con historial médico obstétrico detallado.

    Este modelo almacena toda la información relevante de una paciente, incluyendo:

    1. DATOS BÁSICOS:
       - Identificación (nombre, cédula, ID clínico)
       - Datos demográficos (fecha de nacimiento, género, contacto)
       - Información de contacto y dirección

    2. HISTORIAL MÉDICO:
       - Antecedentes personales (enfermedades previas, cirugías, hospitalizaciones)
       - Antecedentes familiares (enfermedades hereditarias)
       - Alergias (medicamentosas, alimentarias, otras)
       - Medicamentos actuales
       - Inmunizaciones

    3. ANTECEDENTES GINECO-OBSTÉTRICOS:
       - Historia menstrual (menarquia, ciclos, dismenorrea)
       - Antecedentes anticonceptivos
       - Fórmula obstétrica GPAC (Gestas, Partos, Abortos, Cesáreas)
       - Detalles de embarazos previos
       - Complicaciones previas

    4. FACTORES DE RIESGO:
       - Enfermedades crónicas (diabetes, hipertensión)
       - Complicaciones obstétricas previas (preeclampsia, eclampsia, hemorragias)
       - Factores anatómicos (cirugía uterina, malformaciones)

    5. HÁBITOS:
       - Tabaquismo
       - Consumo de alcohol
       - Consumo de drogas

    6. DATOS SOCIOECONÓMICOS:
       - Nivel educativo
       - Ocupación
       - Estado civil
       - Situación de vivienda
       - Acceso a servicios básicos

    7. SEGURO MÉDICO:
       - Tipo de seguro
       - Número de póliza

    8. CONTACTOS DE EMERGENCIA:
       - Datos de contactos primario y secundario

    Funcionalidades:
    - Cálculo automático de edad
    - Generación de fórmula obstétrica GPAC
    - Evaluación de factores de riesgo
    - Cálculo de índice de riesgo (0-100)
    - Soft delete (borrado lógico)
    """

    # =========================================================================
    # OPCIONES Y CHOICES
    # =========================================================================

    GENEROS = (
        ('femenino', 'Femenino'),
        ('masculino', 'Masculino'),
        ('otro', 'Otro'),
    )

    ESTADOS_CIVILES = (
        ('soltera', 'Soltera'),
        ('casada', 'Casada'),
        ('divorciada', 'Divorciada'),
        ('viuda', 'Viuda'),
        ('union_libre', 'Unión Libre'),
    )

    NIVELES_EDUCATIVOS = (
        ('sin_estudios', 'Sin Estudios'),
        ('primaria_incompleta', 'Primaria Incompleta'),
        ('primaria_completa', 'Primaria Completa'),
        ('secundaria_incompleta', 'Secundaria Incompleta'),
        ('secundaria_completa', 'Secundaria Completa'),
        ('tecnico', 'Técnico'),
        ('universitario_incompleto', 'Universitario Incompleto'),
        ('universitario_completo', 'Universitario Completo'),
        ('postgrado', 'Postgrado'),
    )

    TIPOS_SEGURO = (
        ('publico', 'Seguro Público'),
        ('privado', 'Seguro Privado'),
        ('mixto', 'Seguro Mixto'),
        ('ninguno', 'Sin Seguro'),
    )

    # =========================================================================
    # CAMPOS DE IDENTIFICACIÓN
    # =========================================================================

    id = models.AutoField(
        primary_key=True,
        help_text="Identificador único autoincremental"
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identificador único universal (UUID) para referencias externas"
    )

    id_clinico = models.CharField(
        max_length=50,
        unique=True,
        help_text="Identificador clínico único del paciente (Ej: HC-001234)",
        error_messages={
            'unique': 'ID Clínico duplicado'
        }
    )

    cedula_identidad = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Cédula de identidad o documento nacional de identificación",
        error_messages={
            'unique': 'Cédula de Identidad duplicada'
        }
    )

    # =========================================================================
    # DATOS PERSONALES BÁSICOS
    # =========================================================================

    nombre = models.CharField(
        max_length=100,
        help_text="Nombre(s) del paciente"
    )

    apellido_paterno = models.CharField(
        max_length=100,
        help_text="Apellido paterno"
    )

    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Apellido materno"
    )

    fecha_nacimiento = models.DateField(
        help_text="Fecha de nacimiento del paciente"
    )

    genero = models.CharField(
        max_length=20,
        choices=GENEROS,
        help_text="Género del paciente"
    )

    # =========================================================================
    # DATOS DE CONTACTO
    # =========================================================================

    telefono_principal = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número de teléfono principal"
    )

    telefono_secundario = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número de teléfono secundario/alternativo"
    )

    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Correo electrónico"
    )

    direccion = models.TextField(
        blank=True,
        null=True,
        help_text="Dirección completa de residencia"
    )

    ciudad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Ciudad de residencia"
    )

    departamento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Departamento/Estado/Provincia"
    )

    codigo_postal = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Código postal"
    )

    # =========================================================================
    # HISTORIAL MÉDICO COMPLETO
    # =========================================================================

    antecedentes_personales = models.TextField(
        blank=True,
        null=True,
        help_text="Enfermedades previas, cirugías, hospitalizaciones, traumas"
    )

    antecedentes_familiares = models.TextField(
        blank=True,
        null=True,
        help_text="Enfermedades hereditarias, problemas obstétricos familiares, causas de muerte en familiares cercanos"
    )

    alergias = models.TextField(
        blank=True,
        null=True,
        help_text="Alergias medicamentosas, alimentarias, ambientales y otras reacciones alérgicas conocidas"
    )

    medicamentos_actuales = models.TextField(
        blank=True,
        null=True,
        help_text="Medicamentos que toma regularmente con dosis y frecuencia"
    )

    inmunizaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Vacunas recibidas con fechas (tétanos, influenza, COVID-19, etc.)"
    )

    # =========================================================================
    # ANTECEDENTES GINECO-OBSTÉTRICOS DETALLADOS
    # =========================================================================

    # --- Historia Menstrual ---
    fecha_primera_menstruacion = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de la menarquia (primera menstruación)"
    )

    edad_menarquia = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(8, message="La edad de menarquia no puede ser menor a 8 años"),
            MaxValueValidator(20, message="La edad de menarquia no puede ser mayor a 20 años")
        ],
        help_text="Edad en años al momento de la primera menstruación"
    )

    ciclos_regulares = models.BooleanField(
        default=True,
        help_text="¿Ciclos menstruales regulares?"
    )

    duracion_ciclo = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(21, message="Duración del ciclo no puede ser menor a 21 días"),
            MaxValueValidator(45, message="Duración del ciclo no puede ser mayor a 45 días")
        ],
        help_text="Duración del ciclo menstrual en días (normal: 28 días)"
    )

    duracion_menstruacion = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(2, message="Duración de la menstruación no puede ser menor a 2 días"),
            MaxValueValidator(10, message="Duración de la menstruación no puede ser mayor a 10 días")
        ],
        help_text="Días de sangrado menstrual (normal: 3-7 días)"
    )

    dismenorrea = models.BooleanField(
        default=False,
        help_text="¿Presenta dolor menstrual (dismenorrea)?"
    )

    intensidad_dismenorrea = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('leve', 'Leve'),
            ('moderada', 'Moderada'),
            ('severa', 'Severa'),
        ],
        help_text="Intensidad del dolor menstrual"
    )

    # --- Antecedentes Anticonceptivos ---
    metodo_anticonceptivo_previo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Método anticonceptivo usado previamente (DIU, píldoras, inyección, etc.)"
    )

    tiempo_uso_anticonceptivo = models.IntegerField(
        blank=True,
        null=True,
        help_text="Tiempo de uso del método anticonceptivo en meses"
    )

    fecha_suspension_anticonceptivo = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha en que suspendió el uso del método anticonceptivo"
    )

    # =========================================================================
    # ANTECEDENTES OBSTÉTRICOS (FÓRMULA GPAC)
    # =========================================================================

    gestas = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de gestas no puede ser negativo"),
            MaxValueValidator(20, message="El número de gestas parece excesivo")
        ],
        help_text="Total de embarazos (incluyendo embarazo actual si está embarazada)"
    )

    partos = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de partos no puede ser negativo"),
            MaxValueValidator(20, message="El número de partos parece excesivo")
        ],
        help_text="Partos a término (≥37 semanas)"
    )

    abortos = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de abortos no puede ser negativo"),
            MaxValueValidator(20, message="El número de abortos parece excesivo")
        ],
        help_text="Abortos espontáneos o inducidos (<20 semanas)"
    )

    cesareas = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de cesáreas no puede ser negativo"),
            MaxValueValidator(10, message="El número de cesáreas parece excesivo")
        ],
        help_text="Cesáreas previas"
    )

    ectopicos = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de ectópicos no puede ser negativo"),
            MaxValueValidator(5, message="El número de ectópicos parece excesivo")
        ],
        help_text="Embarazos ectópicos (fuera del útero)"
    )

    molas = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de molas no puede ser negativo"),
            MaxValueValidator(5, message="El número de molas parece excesivo")
        ],
        help_text="Embarazos molares"
    )

    hijos_vivos = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de hijos vivos no puede ser negativo"),
            MaxValueValidator(20, message="El número de hijos vivos parece excesivo")
        ],
        help_text="Hijos vivos actualmente"
    )

    hijos_muertos = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de hijos muertos no puede ser negativo")
        ],
        help_text="Hijos fallecidos (muertes neonatales o infantiles)"
    )

    # =========================================================================
    # DETALLES DE EMBARAZOS PREVIOS
    # =========================================================================

    complicaciones_embarazos_previos = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción detallada de complicaciones en embarazos previos"
    )

    peso_maximo_recien_nacido = models.DecimalField(
        max_digits=6,
        decimal_places=0,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('500'), message="Peso mínimo: 500 gramos"),
            MaxValueValidator(Decimal('7000'), message="Peso máximo: 7000 gramos")
        ],
        help_text="Peso máximo de recién nacido en gramos (macrosomía >4000g)"
    )

    peso_minimo_recien_nacido = models.DecimalField(
        max_digits=6,
        decimal_places=0,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('500'), message="Peso mínimo: 500 gramos"),
            MaxValueValidator(Decimal('7000'), message="Peso máximo: 7000 gramos")
        ],
        help_text="Peso mínimo de recién nacido en gramos (bajo peso <2500g)"
    )

    partos_prematuros_previos = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="El número de partos prematuros no puede ser negativo")
        ],
        help_text="Número de partos prematuros (<37 semanas)"
    )

    # =========================================================================
    # FACTORES DE RIESGO MÉDICO
    # =========================================================================

    diabetes_previa = models.BooleanField(
        default=False,
        help_text="Diabetes preexistente (tipo 1, tipo 2, o gestacional previa)"
    )

    hipertension_previa = models.BooleanField(
        default=False,
        help_text="Hipertensión arterial crónica"
    )

    preeclampsia_previa = models.BooleanField(
        default=False,
        help_text="Antecedente de preeclampsia en embarazos previos"
    )

    eclampsia_previa = models.BooleanField(
        default=False,
        help_text="Antecedente de eclampsia (convulsiones por preeclampsia)"
    )

    hemorragia_postparto_previa = models.BooleanField(
        default=False,
        help_text="Antecedente de hemorragia postparto"
    )

    cirugia_uterina_previa = models.BooleanField(
        default=False,
        help_text="Cirugías uterinas previas (miomectomía, etc.)"
    )

    incompetencia_cervical = models.BooleanField(
        default=False,
        help_text="Incompetencia cervical (cuello uterino débil)"
    )

    malformaciones_uterinas = models.BooleanField(
        default=False,
        help_text="Malformaciones uterinas congénitas"
    )

    enfermedades_tiroideas = models.BooleanField(
        default=False,
        help_text="Enfermedades de la tiroides (hipotiroidismo, hipertiroidismo)"
    )

    enfermedades_autoinmunes = models.BooleanField(
        default=False,
        help_text="Enfermedades autoinmunes (lupus, síndrome antifosfolípidos, etc.)"
    )

    enfermedades_cardiovasculares = models.BooleanField(
        default=False,
        help_text="Enfermedades cardiovasculares"
    )

    enfermedades_renales = models.BooleanField(
        default=False,
        help_text="Enfermedades renales crónicas"
    )

    epilepsia = models.BooleanField(
        default=False,
        help_text="Epilepsia u otros trastornos convulsivos"
    )

    asma = models.BooleanField(
        default=False,
        help_text="Asma bronquial"
    )

    trombofilia = models.BooleanField(
        default=False,
        help_text="Trastornos de coagulación (trombofilia)"
    )

    vih = models.BooleanField(
        default=False,
        help_text="VIH/SIDA"
    )

    hepatitis = models.BooleanField(
        default=False,
        help_text="Hepatitis B o C"
    )

    otras_enfermedades_cronicas = models.TextField(
        blank=True,
        null=True,
        help_text="Otras enfermedades crónicas no listadas"
    )

    # =========================================================================
    # HÁBITOS Y ESTILO DE VIDA
    # =========================================================================

    fuma = models.BooleanField(
        default=False,
        help_text="¿Fuma actualmente?"
    )

    cigarrillos_dia = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0, message="El número de cigarrillos no puede ser negativo"),
            MaxValueValidator(100, message="El número de cigarrillos parece excesivo")
        ],
        help_text="Número de cigarrillos por día"
    )

    ex_fumadora = models.BooleanField(
        default=False,
        help_text="¿Dejó de fumar?"
    )

    tiempo_sin_fumar_meses = models.IntegerField(
        blank=True,
        null=True,
        help_text="Meses desde que dejó de fumar"
    )

    consume_alcohol = models.BooleanField(
        default=False,
        help_text="¿Consume alcohol?"
    )

    frecuencia_alcohol = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        choices=[
            ('ocasional', 'Ocasional (menos de 1 vez/mes)'),
            ('mensual', 'Mensual (1-3 veces/mes)'),
            ('semanal', 'Semanal (1-3 veces/semana)'),
            ('diaria', 'Diaria'),
        ],
        help_text="Frecuencia del consumo de alcohol"
    )

    consume_drogas = models.BooleanField(
        default=False,
        help_text="¿Consume drogas recreativas o ilícitas?"
    )

    tipo_drogas = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Tipo de drogas consumidas (marihuana, cocaína, etc.)"
    )

    ejercicio_fisico = models.BooleanField(
        default=False,
        help_text="¿Realiza ejercicio físico regularmente?"
    )

    frecuencia_ejercicio = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Frecuencia del ejercicio físico"
    )

    # =========================================================================
    # CONTACTOS DE EMERGENCIA
    # =========================================================================

    # --- Contacto de Emergencia Principal ---
    contacto_emergencia_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre completo del contacto de emergencia principal"
    )

    contacto_emergencia_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono del contacto de emergencia principal"
    )

    contacto_emergencia_relacion = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Relación con el contacto de emergencia (esposo, madre, hermana, etc.)"
    )

    # --- Contacto de Emergencia Secundario ---
    contacto_emergencia2_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre completo del contacto de emergencia secundario"
    )

    contacto_emergencia2_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono del contacto de emergencia secundario"
    )

    contacto_emergencia2_relacion = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Relación con el contacto de emergencia secundario"
    )

    # =========================================================================
    # DATOS SOCIOECONÓMICOS
    # =========================================================================

    nivel_educativo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        choices=NIVELES_EDUCATIVOS,
        help_text="Nivel educativo alcanzado"
    )

    ocupacion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Ocupación u oficio actual"
    )

    estado_civil = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=ESTADOS_CIVILES,
        help_text="Estado civil actual"
    )

    vive_con = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Con quién vive (esposo, padres, sola, etc.)"
    )

    situacion_vivienda = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        choices=[
            ('propia', 'Vivienda Propia'),
            ('alquilada', 'Vivienda Alquilada'),
            ('familiar', 'Vivienda de Familiar'),
            ('prestada', 'Vivienda Prestada'),
            ('otra', 'Otra Situación'),
        ],
        help_text="Situación de la vivienda"
    )

    tipo_vivienda = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        choices=[
            ('casa', 'Casa'),
            ('apartamento', 'Apartamento'),
            ('cuarto', 'Cuarto'),
            ('rancho', 'Rancho/Choza'),
            ('otro', 'Otro'),
        ],
        help_text="Tipo de vivienda"
    )

    acceso_agua_potable = models.BooleanField(
        default=True,
        help_text="¿Tiene acceso a agua potable?"
    )

    acceso_alcantarillado = models.BooleanField(
        default=True,
        help_text="¿Tiene acceso a alcantarillado o sistema de eliminación de excretas?"
    )

    acceso_electricidad = models.BooleanField(
        default=True,
        help_text="¿Tiene acceso a electricidad?"
    )

    # =========================================================================
    # SEGURO MÉDICO
    # =========================================================================

    tiene_seguro = models.BooleanField(
        default=False,
        help_text="¿Tiene seguro médico?"
    )

    tipo_seguro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        choices=TIPOS_SEGURO,
        help_text="Tipo de seguro médico"
    )

    nombre_aseguradora = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre de la aseguradora o institución"
    )

    numero_seguro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Número de póliza o carnet de seguro"
    )

    vigencia_seguro_hasta = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de vigencia del seguro"
    )

    # =========================================================================
    # METADATOS Y AUDITORÍA
    # =========================================================================

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en que se registró el paciente en el sistema"
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última modificación del registro"
    )

    # Soft delete - Borrado lógico
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el registro está activo o ha sido eliminado lógicamente"
    )

    fecha_inactivacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que se inactivó el registro"
    )

    motivo_inactivacion = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo de la inactivación del registro (fallecimiento, cambio de centro, etc.)"
    )

    # =========================================================================
    # META INFORMACIÓN
    # =========================================================================

    class Meta:
        db_table = 'pacientes'
        managed = False  # No crear migraciones (tabla existente)
        ordering = ['-fecha_registro']
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

        indexes = [
            models.Index(fields=['cedula_identidad']),
            models.Index(fields=['id_clinico']),
            models.Index(fields=['activo', 'fecha_registro']),
            models.Index(fields=['nombre', 'apellido_paterno']),
        ]

    # =========================================================================
    # MÉTODOS DE VALIDACIÓN
    # =========================================================================

    def clean(self):
        """
        Validaciones personalizadas.
        """
        super().clean()
        errors = {}

        # Validar que fecha de nacimiento no sea futura
        if self.fecha_nacimiento and self.fecha_nacimiento > timezone.now().date():
            errors['fecha_nacimiento'] = "La fecha de nacimiento no puede ser futura"

        # Validar edad mínima (debe tener al menos 10 años para registro obstétrico)
        if self.fecha_nacimiento:
            edad = self.calcular_edad()
            if edad and edad < 10:
                errors['fecha_nacimiento'] = "La paciente debe tener al menos 10 años"

        # Validar coherencia de fórmula obstétrica
        if self.gestas > 0:
            suma_resultados = self.partos + self.abortos + self.cesareas + self.ectopicos + self.molas
            if suma_resultados > self.gestas:
                errors['gestas'] = f"La suma de partos, abortos, cesáreas, ectópicos y molas ({suma_resultados}) no puede ser mayor que las gestas ({self.gestas})"

        # Validar que hijos vivos no sea mayor que partos
        if self.hijos_vivos > (self.partos + self.cesareas):
            errors['hijos_vivos'] = "El número de hijos vivos no puede ser mayor que la suma de partos y cesáreas"

        # Validar peso de recién nacidos
        if self.peso_maximo_recien_nacido and self.peso_minimo_recien_nacido:
            if self.peso_minimo_recien_nacido > self.peso_maximo_recien_nacido:
                errors['peso_minimo_recien_nacido'] = "El peso mínimo no puede ser mayor que el peso máximo"

        if errors:
            raise ValidationError(errors)

    # =========================================================================
    # MÉTODOS DE INSTANCIA
    # =========================================================================

    def save(self, *args, **kwargs):
        """
        Sobrescribir save para validaciones y cálculos automáticos.
        """
        # Ejecutar validaciones
        self.full_clean()

        # Llamar al método save original
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """
        Implementar soft delete (borrado lógico).
        """
        self.activo = False
        self.fecha_inactivacion = timezone.now()
        if not self.motivo_inactivacion:
            self.motivo_inactivacion = "Eliminación por usuario"
        self.save()

    def hard_delete(self):
        """
        Eliminar permanentemente el registro.
        Usar con precaución - esta acción es irreversible.
        """
        super().delete()

    # =========================================================================
    # MÉTODOS DE UTILIDAD
    # =========================================================================

    def calcular_edad(self):
        """
        Calcula la edad actual del paciente.

        Returns:
            int: Edad en años
        """
        if not self.fecha_nacimiento:
            return None

        today = timezone.now().date()
        edad = today.year - self.fecha_nacimiento.year

        # Ajustar si aún no ha cumplido años este año
        if (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1

        return edad

    def get_nombre_completo(self):
        """
        Retorna el nombre completo del paciente.

        Returns:
            str: Nombre completo
        """
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        else:
            return f"{self.nombre} {self.apellido_paterno}"

    def get_gpac_formatted(self):
        """
        Retorna la fórmula obstétrica GPAC formateada.

        Returns:
            str: Fórmula GPAC (Ej: "G3P2A0C1")
        """
        return f"G{self.gestas}P{self.partos}A{self.abortos}C{self.cesareas}"

    def get_paridad(self):
        """
        Clasifica la paridad de la paciente.

        Returns:
            str: Clasificación de paridad
        """
        if self.partos == 0 and self.cesareas == 0:
            return "Nulípara"
        elif self.partos + self.cesareas == 1:
            return "Primípara"
        elif 2 <= self.partos + self.cesareas <= 4:
            return "Multípara"
        elif self.partos + self.cesareas >= 5:
            return "Gran Multípara"
        else:
            return "No definida"

    def tiene_riesgo_alto(self):
        """
        Identifica si la paciente tiene factores de alto riesgo.

        Returns:
            list: Lista de factores de riesgo identificados
        """
        riesgos = []

        # Edad de riesgo
        edad = self.calcular_edad()
        if edad:
            if edad < 18:
                riesgos.append("Edad menor de 18 años (adolescente)")
            elif edad > 35:
                riesgos.append("Edad materna avanzada (>35 años)")
            if edad > 40:
                riesgos.append("Edad materna muy avanzada (>40 años)")

        # Enfermedades crónicas
        if self.diabetes_previa:
            riesgos.append("Diabetes previa")
        if self.hipertension_previa:
            riesgos.append("Hipertensión arterial crónica")
        if self.enfermedades_cardiovasculares:
            riesgos.append("Enfermedad cardiovascular")
        if self.enfermedades_renales:
            riesgos.append("Enfermedad renal crónica")
        if self.enfermedades_autoinmunes:
            riesgos.append("Enfermedad autoinmune")
        if self.epilepsia:
            riesgos.append("Epilepsia")
        if self.trombofilia:
            riesgos.append("Trombofilia")
        if self.vih:
            riesgos.append("VIH/SIDA")

        # Antecedentes obstétricos
        if self.preeclampsia_previa:
            riesgos.append("Preeclampsia previa")
        if self.eclampsia_previa:
            riesgos.append("Eclampsia previa")
        if self.cesareas >= 2:
            riesgos.append(f"Múltiples cesáreas previas ({self.cesareas})")
        if self.abortos >= 3:
            riesgos.append(f"Abortos recurrentes ({self.abortos})")
        if self.hemorragia_postparto_previa:
            riesgos.append("Hemorragia postparto previa")
        if self.cirugia_uterina_previa:
            riesgos.append("Cirugía uterina previa")
        if self.incompetencia_cervical:
            riesgos.append("Incompetencia cervical")
        if self.malformaciones_uterinas:
            riesgos.append("Malformaciones uterinas")
        if self.partos_prematuros_previos >= 1:
            riesgos.append(f"Parto prematuro previo ({self.partos_prematuros_previos})")

        # Gran multiparidad
        if self.partos + self.cesareas >= 5:
            riesgos.append(f"Gran multípara ({self.partos + self.cesareas} partos)")

        # Hábitos
        if self.fuma:
            riesgos.append(f"Tabaquismo activo ({self.cigarrillos_dia or 'N/E'} cigarrillos/día)")
        if self.consume_drogas:
            riesgos.append("Consumo de drogas")

        # Peso de recién nacidos previos
        if self.peso_maximo_recien_nacido and self.peso_maximo_recien_nacido > 4000:
            riesgos.append(f"Macrosomía previa ({self.peso_maximo_recien_nacido}g)")
        if self.peso_minimo_recien_nacido and self.peso_minimo_recien_nacido < 2500:
            riesgos.append(f"Bajo peso al nacer previo ({self.peso_minimo_recien_nacido}g)")

        return riesgos

    def get_indice_riesgo(self):
        """
        Calcula un índice numérico de riesgo (0-100).

        Este índice se basa en la suma ponderada de factores de riesgo.

        Returns:
            int: Índice de riesgo entre 0 y 100
        """
        riesgo = 0

        # Edad (máximo 20 puntos)
        edad = self.calcular_edad()
        if edad:
            if edad < 18:
                riesgo += 15
            elif edad > 35:
                riesgo += 10
            if edad > 40:
                riesgo += 20  # Acumulativo con >35

        # Enfermedades crónicas (15 puntos cada una)
        if self.diabetes_previa:
            riesgo += 15
        if self.hipertension_previa:
            riesgo += 15
        if self.enfermedades_cardiovasculares:
            riesgo += 20
        if self.enfermedades_renales:
            riesgo += 15
        if self.enfermedades_autoinmunes:
            riesgo += 15
        if self.trombofilia:
            riesgo += 15
        if self.vih:
            riesgo += 10

        # Antecedentes obstétricos graves (20 puntos)
        if self.preeclampsia_previa:
            riesgo += 20
        if self.eclampsia_previa:
            riesgo += 25
        if self.hemorragia_postparto_previa:
            riesgo += 15

        # Cesáreas múltiples (10 puntos si ≥2)
        if self.cesareas >= 2:
            riesgo += 10

        # Abortos recurrentes (15 puntos si ≥3)
        if self.abortos >= 3:
            riesgo += 15

        # Hábitos (10-25 puntos)
        if self.fuma:
            riesgo += 10
        if self.consume_drogas:
            riesgo += 25

        # Gran multiparidad (10 puntos)
        if self.partos + self.cesareas >= 5:
            riesgo += 10

        # Limitar a 100 puntos máximo
        return min(riesgo, 100)

    def get_clasificacion_riesgo(self):
        """
        Clasifica el riesgo de la paciente basado en el índice de riesgo.

        Returns:
            str: Clasificación de riesgo
        """
        indice = self.get_indice_riesgo()

        if indice == 0:
            return "Sin factores de riesgo identificados"
        elif indice < 15:
            return "Riesgo bajo"
        elif indice < 35:
            return "Riesgo moderado"
        elif indice < 60:
            return "Riesgo alto"
        else:
            return "Riesgo muy alto"

    def necesita_atencion_especializada(self):
        """
        Determina si la paciente necesita atención especializada.

        Returns:
            bool: True si necesita atención especializada
        """
        return self.get_indice_riesgo() >= 35

    # =========================================================================
    # REPRESENTACIÓN EN STRING
    # =========================================================================

    def __str__(self):
        """
        Representación en string del paciente.
        """
        return f"{self.id_clinico} - {self.get_nombre_completo()}"

    def __repr__(self):
        """
        Representación técnica del objeto para debugging.
        """
        return (
            f"<Paciente(id={self.id}, "
            f"id_clinico={self.id_clinico}, "
            f"nombre={self.get_nombre_completo()}, "
            f"edad={self.calcular_edad()}, "
            f"gpac={self.get_gpac_formatted()})>"
        )

# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
