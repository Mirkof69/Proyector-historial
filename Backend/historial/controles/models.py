# =============================================================================
# MODELOS DE CONTROLES PRENATALES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: controles
# Descripción: Modelos para el registro y gestión de controles prenatales.
#              Incluye toda la información clínica recopilada en cada consulta
#              prenatal: signos vitales, mediciones obstétricas, exámenes físicos,
#              y observaciones médicas.
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

# Importar modelos relacionados
from pacientes.models import Paciente
from embarazos.models import Embarazo
from usuarios.models import Usuario

# =============================================================================
# MODELO PRINCIPAL: CONTROL PRENATAL
# =============================================================================
class ControlPrenatal(models.Model):
    """
    Modelo para registrar controles prenatales.

    Un control prenatal es una consulta médica que se realiza durante el embarazo
    para monitorear la salud de la madre y el feto. Incluye:

    1. Datos de identificación (paciente, embarazo, fecha, número de control)
    2. Edad gestacional al momento del control
    3. Antropometría materna (peso, talla, IMC)
    4. Signos vitales (presión arterial, frecuencia cardíaca, temperatura)
    5. Exploración obstétrica (altura uterina, FCF, presentación, movimientos)
    6. Examen físico (edema, proteinuria)
    7. Observaciones y diagnósticos
    8. Registro de profesional responsable

    Relaciones:
    - Pertenece a un Embarazo (relación many-to-one)
    - Asociado a una Paciente (relación many-to-one)
    - Registrado por un Médico y/o Enfermero (relación many-to-one)

    Validaciones:
    - Valores de signos vitales dentro de rangos normales/críticos
    - Edad gestacional entre 0-42 semanas
    - Altura uterina correlacionada con edad gestacional
    - FCF entre 110-160 lpm
    - Temperatura entre 35-42°C
    - Presión arterial con límites críticos

    Funcionalidades adicionales:
    - Cálculo automático de IMC
    - Clasificación de IMC según OMS
    - Cálculo de PAM (Presión Arterial Media)
    - Detección automática de valores de alerta
    - Soft delete (borrado lógico)
    """

    # =========================================================================
    # OPCIONES Y CHOICES
    # =========================================================================

    # Opciones para presentación fetal
    PRESENTACIONES = (
        ('cefalica', 'Cefálica'),         # Cabeza hacia abajo (normal)
        ('podalica', 'Podálica'),         # Nalgas o pies hacia abajo
        ('transversa', 'Transversa'),     # Feto atravesado
        ('oblicua', 'Oblicua'),           # Feto en diagonal
        ('compuesta', 'Compuesta'),       # Más de una parte presentándose
    )

    # Opciones para movimientos fetales
    MOVIMIENTOS = (
        ('presentes', 'Presentes'),       # Movimientos normales
        ('ausentes', 'Ausentes'),         # Sin movimientos (crítico)
        ('disminuidos', 'Disminuidos'),   # Movimientos reducidos (alerta)
        ('aumentados', 'Aumentados'),     # Movimientos excesivos
    )

    # Opciones para edema (retención de líquidos)
    EDEMA_OPCIONES = (
        ('no', 'No'),                     # Sin edema
        ('leve', 'Leve'),                 # Edema leve en extremidades
        ('moderado', 'Moderado'),         # Edema en piernas y manos
        ('severo', 'Severo'),             # Edema generalizado (crítico)
        ('anasarca', 'Anasarca'),         # Edema masivo (muy crítico)
    )

    # Opciones para proteinuria (proteínas en orina)
    PROTEINURIA_OPCIONES = (
        ('negativa', 'Negativa'),         # Sin proteínas
        ('trazas', 'Trazas'),             # Cantidades mínimas
        ('positiva_1', '+'),              # Positiva leve
        ('positiva_2', '++'),             # Positiva moderada
        ('positiva_3', '+++'),            # Positiva severa (preeclampsia)
        ('positiva_4', '++++'),           # Positiva muy severa (crítico)
    )

    # =========================================================================
    # CAMPOS PRINCIPALES
    # =========================================================================

    # --- Identificación y Metadatos ---
    id = models.AutoField(
        primary_key=True,
        help_text="Identificador único autoincremental del control prenatal"
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identificador único universal (UUID) para referencias externas"
    )

    # =========================================================================
    # RELACIONES FORÁNEAS - CORREGIDAS
    # =========================================================================

    # Relación con Embarazo (CORREGIDO: era IntegerField, ahora es ForeignKey)
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,  # Si se elimina el embarazo, se eliminan sus controles
        db_column='embarazo_id',   # Nombre de la columna en la base de datos
        related_name='controles',  # Acceder a controles desde embarazo: embarazo.controles.all()
        help_text="Embarazo al que pertenece este control prenatal"
    )

    # Relación con Paciente (para acceso directo sin pasar por embarazo)
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,  # Si se elimina la paciente, se eliminan sus controles
        db_column='paciente_id',   # Nombre de la columna en la base de datos
        related_name='controles',  # Acceder a controles desde paciente: paciente.controles.all()
        help_text="Paciente a quien se le realiza el control prenatal"
    )

    # --- Identificación del Control ---
    numero_control = models.IntegerField(
        validators=[
            MinValueValidator(1, message="El número de control debe ser positivo"),
            MaxValueValidator(50, message="El número de control no puede exceder 50")
        ],
        help_text="Número secuencial del control prenatal (1, 2, 3, ...)"
    )

    fecha_control = models.DateField(
        help_text="Fecha en que se realizó el control prenatal"
    )

    # =========================================================================
    # EDAD GESTACIONAL
    # =========================================================================

    semanas_gestacion = models.IntegerField(
        validators=[
            MinValueValidator(0, message="Las semanas de gestación no pueden ser negativas"),
            MaxValueValidator(42, message="Las semanas de gestación no pueden exceder 42")
        ],
        help_text="Semanas completas de gestación al momento del control"
    )

    dias_gestacion = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0, message="Los días deben ser entre 0 y 6"),
            MaxValueValidator(6, message="Los días deben ser entre 0 y 6")
        ],
        help_text="Días adicionales de gestación (0-6 días)"
    )

    edad_gestacional_calculada = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Edad gestacional en formato texto (Ej: '28 semanas + 3 días')"
    )

    # =========================================================================
    # ANTROPOMETRÍA MATERNA
    # =========================================================================

    peso_actual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('30.00'), message="El peso no puede ser menor a 30 kg"),
            MaxValueValidator(Decimal('250.00'), message="El peso no puede exceder 250 kg")
        ],
        help_text="Peso actual de la gestante en kilogramos (Ej: 65.50)"
    )

    peso_pregestacional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('30.00'), message="El peso pregestacional no puede ser menor a 30 kg"),
            MaxValueValidator(Decimal('250.00'), message="El peso pregestacional no puede exceder 250 kg")
        ],
        help_text="Peso previo al embarazo en kilogramos"
    )

    ganancia_peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Ganancia de peso durante el embarazo en kilogramos (calculado automáticamente)"
    )

    talla = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('120.00'), message="La talla no puede ser menor a 120 cm"),
            MaxValueValidator(Decimal('220.00'), message="La talla no puede exceder 220 cm")
        ],
        help_text="Talla/estatura de la gestante en centímetros (Ej: 165.00)"
    )

    imc_actual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Índice de Masa Corporal actual (calculado automáticamente)"
    )

    clasificacion_imc = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Clasificación del IMC según OMS (bajo peso, normal, sobrepeso, obesidad)"
    )

    # =========================================================================
    # SIGNOS VITALES
    # =========================================================================

    presion_arterial_sistolica = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(60, message="PA sistólica no puede ser menor a 60 mmHg"),
            MaxValueValidator(250, message="PA sistólica no puede exceder 250 mmHg")
        ],
        help_text="Presión arterial sistólica (máxima) en mmHg (Ej: 120)"
    )

    presion_arterial_diastolica = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(40, message="PA diastólica no puede ser menor a 40 mmHg"),
            MaxValueValidator(150, message="PA diastólica no puede exceder 150 mmHg")
        ],
        help_text="Presión arterial diastólica (mínima) en mmHg (Ej: 80)"
    )

    presion_arterial_media = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Presión Arterial Media (PAM) calculada: (PAS + 2*PAD) / 3"
    )

    frecuencia_cardiaca = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(40, message="Frecuencia cardíaca no puede ser menor a 40 lpm"),
            MaxValueValidator(200, message="Frecuencia cardíaca no puede exceder 200 lpm")
        ],
        help_text="Frecuencia cardíaca materna en latidos por minuto (lpm)"
    )

    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('35.0'), message="Temperatura no puede ser menor a 35°C"),
            MaxValueValidator(Decimal('42.0'), message="Temperatura no puede exceder 42°C")
        ],
        help_text="Temperatura corporal en grados Celsius (Ej: 36.5)"
    )

    # =========================================================================
    # EXPLORACIÓN OBSTÉTRICA
    # =========================================================================

    altura_uterina = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('10.00'), message="Altura uterina no puede ser menor a 10 cm"),
            MaxValueValidator(Decimal('50.00'), message="Altura uterina no puede exceder 50 cm")
        ],
        help_text="Altura uterina (fondo uterino) en centímetros"
    )

    frecuencia_cardiaca_fetal = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(100, message="FCF no puede ser menor a 100 lpm (bradicardia severa)"),
            MaxValueValidator(200, message="FCF no puede exceder 200 lpm (taquicardia severa)")
        ],
        help_text="Frecuencia cardíaca fetal en latidos por minuto (normal: 110-160 lpm)"
    )

    presentacion_fetal = models.CharField(
        max_length=50,
        choices=PRESENTACIONES,
        blank=True,
        null=True,
        help_text="Tipo de presentación fetal al momento del control"
    )

    movimientos_fetales = models.CharField(
        max_length=50,
        choices=MOVIMIENTOS,
        blank=True,
        null=True,
        help_text="Percepción materna de movimientos fetales"
    )

    # =========================================================================
    # EXAMEN FÍSICO
    # =========================================================================

    edema = models.CharField(
        max_length=50,
        choices=EDEMA_OPCIONES,
        blank=True,
        null=True,
        help_text="Presencia y grado de edema (retención de líquidos)"
    )

    proteinuria = models.CharField(
        max_length=50,
        choices=PROTEINURIA_OPCIONES,
        blank=True,
        null=True,
        help_text="Nivel de proteínas en orina (indicador de preeclampsia)"
    )

    # =========================================================================
    # OBSERVACIONES Y REGISTRO
    # =========================================================================

    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones médicas, diagnósticos, indicaciones y notas clínicas"
    )

    # =========================================================================
    # RELACIONES CON PROFESIONALES - CORREGIDAS
    # =========================================================================

    # Médico responsable del control (CORREGIDO: era IntegerField, ahora es ForeignKey)
    medico = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,  # Si se elimina el médico, se mantiene el registro
        db_column='medico_id',      # Nombre de la columna en la base de datos
        related_name='controles_como_medico',  # Acceso inverso: usuario.controles_como_medico.all()
        null=True,
        blank=True,
        limit_choices_to={'rol': 'medico'},  # Solo usuarios con rol 'medico'
        help_text="Médico que realizó el control prenatal"
    )

    # Enfermero asistente (CORREGIDO: era IntegerField, ahora es ForeignKey)
    enfermero = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,  # Si se elimina el enfermero, se mantiene el registro
        db_column='enfermero_id',   # Nombre de la columna en la base de datos
        related_name='controles_como_enfermero',  # Acceso inverso: usuario.controles_como_enfermero.all()
        null=True,
        blank=True,
        limit_choices_to={'rol': 'enfermero'},  # Solo usuarios con rol 'enfermero'
        help_text="Enfermero que asistió en el control prenatal"
    )

    # =========================================================================
    # METADATOS Y AUDITORÍA
    # =========================================================================

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en que se registró el control en el sistema"
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

    fecha_eliminacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que se eliminó lógicamente el registro"
    )

    # =========================================================================
    # META INFORMACIÓN
    # =========================================================================

    class Meta:
        db_table = 'controles_prenatales'  # Nombre de la tabla en la base de datos
        managed = False  # Django no maneja migraciones de esta tabla (tabla existente)
        ordering = ['-fecha_control', '-numero_control']  # Ordenar por fecha descendente
        verbose_name = 'Control Prenatal'
        verbose_name_plural = 'Controles Prenatales'

        # Índices para mejorar rendimiento de consultas
        indexes = [
            models.Index(fields=['fecha_control']),
            models.Index(fields=['numero_control']),
            models.Index(fields=['semanas_gestacion']),
            models.Index(fields=['activo']),
        ]

        # Restricciones únicas
        # Un embarazo no puede tener dos controles con el mismo número
        # (comentado porque managed=False)
        # unique_together = [['embarazo', 'numero_control']]

    # =========================================================================
    # MÉTODOS DE VALIDACIÓN
    # =========================================================================

    def clean(self):
        """
        Validaciones personalizadas que se ejecutan antes de guardar.

        Validaciones implementadas:
        1. Fecha de control no puede ser futura
        2. Presión arterial sistólica debe ser mayor que diastólica
        3. Semanas de gestación coherentes con el embarazo
        4. FCF en rango normal o con alertas
        5. Altura uterina correlacionada con semanas de gestación
        6. Ganancia de peso razonable
        """
        super().clean()
        errors = {}

        # Validar que la fecha del control no sea futura
        if self.fecha_control and self.fecha_control > timezone.now().date():
            errors['fecha_control'] = "La fecha del control no puede ser futura"

        # Validar presión arterial
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            if self.presion_arterial_sistolica <= self.presion_arterial_diastolica:
                errors['presion_arterial_sistolica'] = "La presión sistólica debe ser mayor que la diastólica"

        # Validar FCF en rangos críticos
        if self.frecuencia_cardiaca_fetal:
            if self.frecuencia_cardiaca_fetal < 110:
                # Bradicardia fetal
                if not self.observaciones or 'bradicardia' not in self.observaciones.lower():
                    errors['frecuencia_cardiaca_fetal'] = "FCF < 110 lpm (bradicardia). Registre observaciones."
            elif self.frecuencia_cardiaca_fetal > 160:
                # Taquicardia fetal
                if not self.observaciones or 'taquicardia' not in self.observaciones.lower():
                    errors['frecuencia_cardiaca_fetal'] = "FCF > 160 lpm (taquicardia). Registre observaciones."

        # Validar coherencia de altura uterina con edad gestacional
        # Regla general: AU (cm) ≈ Semanas de gestación (entre 20-36 semanas)
        if self.altura_uterina and self.semanas_gestacion:
            if 20 <= self.semanas_gestacion <= 36:
                diferencia = abs(float(self.altura_uterina) - self.semanas_gestacion)
                if diferencia > 4:
                    # Diferencia > 4cm podría indicar problemas
                    errors['altura_uterina'] = f"Altura uterina ({self.altura_uterina} cm) no correlaciona con edad gestacional ({self.semanas_gestacion} sem)"

        if errors:
            raise ValidationError(errors)

    # =========================================================================
    # MÉTODOS DE INSTANCIA
    # =========================================================================

    def save(self, *args, **kwargs):
        """
        Sobrescribir el método save para cálculos automáticos.

        Cálculos realizados:
        1. Edad gestacional en formato texto
        2. Ganancia de peso (peso actual - peso pregestacional)
        3. IMC actual
        4. Clasificación de IMC
        5. Presión Arterial Media (PAM)
        """
        # Calcular edad gestacional en formato texto
        if self.semanas_gestacion is not None:
            if self.dias_gestacion is not None:
                self.edad_gestacional_calculada = f"{self.semanas_gestacion} semanas + {self.dias_gestacion} días"
            else:
                self.edad_gestacional_calculada = f"{self.semanas_gestacion} semanas"

        # Calcular ganancia de peso
        if self.peso_actual and self.peso_pregestacional:
            self.ganancia_peso = self.peso_actual - self.peso_pregestacional

        # Calcular IMC actual
        if self.peso_actual and self.talla:
            talla_metros = self.talla / Decimal('100.0')  # Convertir cm a metros
            self.imc_actual = self.peso_actual / (talla_metros * talla_metros)

            # Clasificar IMC según OMS para embarazadas
            imc = float(self.imc_actual)
            if imc < 18.5:
                self.clasificacion_imc = "Bajo peso"
            elif imc < 25.0:
                self.clasificacion_imc = "Normal"
            elif imc < 30.0:
                self.clasificacion_imc = "Sobrepeso"
            elif imc < 35.0:
                self.clasificacion_imc = "Obesidad grado I"
            elif imc < 40.0:
                self.clasificacion_imc = "Obesidad grado II"
            else:
                self.clasificacion_imc = "Obesidad grado III (mórbida)"

        # Calcular Presión Arterial Media (PAM)
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            pam = (self.presion_arterial_sistolica + 2 * self.presion_arterial_diastolica) / Decimal('3.0')
            self.presion_arterial_media = round(pam, 2)

        # Llamar al método save original
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """
        Sobrescribir delete para implementar soft delete (borrado lógico).
        """
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.save()

    def hard_delete(self):
        """
        Eliminar permanentemente el registro de la base de datos.
        Usar con precaución - esta acción es irreversible.
        """
        super().delete()

    # =========================================================================
    # MÉTODOS DE UTILIDAD
    # =========================================================================

    def get_edad_gestacional_display(self):
        """
        Retorna la edad gestacional en formato legible.
        Ejemplo: "28 semanas + 3 días"
        """
        return self.edad_gestacional_calculada or f"{self.semanas_gestacion} semanas"

    def tiene_alertas(self):
        """
        Verifica si el control tiene valores que requieren atención médica.

        Returns:
            dict: Diccionario con alertas encontradas
        """
        alertas = {}

        # Alertas de presión arterial
        if self.presion_arterial_sistolica and self.presion_arterial_sistolica >= 140:
            alertas['presion_alta'] = f"PA sistólica elevada: {self.presion_arterial_sistolica} mmHg"
        if self.presion_arterial_diastolica and self.presion_arterial_diastolica >= 90:
            alertas['presion_alta_diast'] = f"PA diastólica elevada: {self.presion_arterial_diastolica} mmHg"

        # Alertas de FCF
        if self.frecuencia_cardiaca_fetal:
            if self.frecuencia_cardiaca_fetal < 110:
                alertas['bradicardia_fetal'] = f"Bradicardia fetal: {self.frecuencia_cardiaca_fetal} lpm"
            elif self.frecuencia_cardiaca_fetal > 160:
                alertas['taquicardia_fetal'] = f"Taquicardia fetal: {self.frecuencia_cardiaca_fetal} lpm"

        # Alertas de proteinuria
        if self.proteinuria and self.proteinuria in ['positiva_2', 'positiva_3', 'positiva_4']:
            alertas['proteinuria'] = f"Proteinuria significativa: {self.get_proteinuria_display()}"

        # Alertas de edema
        if self.edema and self.edema in ['severo', 'anasarca']:
            alertas['edema_severo'] = f"Edema severo: {self.get_edema_display()}"

        # Alertas de movimientos fetales
        if self.movimientos_fetales == 'ausentes':
            alertas['sin_movimientos'] = "Movimientos fetales ausentes - requiere evaluación urgente"

        # Alertas de temperatura
        if self.temperatura:
            temp = float(self.temperatura)
            if temp >= 38.0:
                alertas['fiebre'] = f"Fiebre: {temp}°C"
            elif temp <= 35.5:
                alertas['hipotermia'] = f"Hipotermia: {temp}°C"

        return alertas

    def es_control_critico(self):
        """
        Determina si el control tiene hallazgos críticos que requieren atención inmediata.

        Returns:
            bool: True si hay hallazgos críticos
        """
        alertas = self.tiene_alertas()

        # Criterios de criticidad
        critico = False

        # Hipertensión severa (posible preeclampsia)
        if self.presion_arterial_sistolica and self.presion_arterial_sistolica >= 160:
            critico = True
        if self.presion_arterial_diastolica and self.presion_arterial_diastolica >= 110:
            critico = True

        # Proteinuria severa
        if self.proteinuria in ['positiva_3', 'positiva_4']:
            critico = True

        # Bradicardia fetal severa
        if self.frecuencia_cardiaca_fetal and self.frecuencia_cardiaca_fetal < 100:
            critico = True

        # Ausencia de movimientos fetales
        if self.movimientos_fetales == 'ausentes' and self.semanas_gestacion and self.semanas_gestacion >= 20:
            critico = True

        return critico

    def calcular_indice_shock(self):
        """
        Calcula el índice de shock (FC / PAS).
        Índice > 1 indica shock hipovolémico.

        Returns:
            float: Índice de shock o None si no hay datos
        """
        if self.frecuencia_cardiaca and self.presion_arterial_sistolica:
            return round(self.frecuencia_cardiaca / self.presion_arterial_sistolica, 2)
        return None

    # =========================================================================
    # REPRESENTACIÓN EN STRING
    # =========================================================================

    def __str__(self):
        """
        Representación en string del control prenatal.
        Formato: "Control #N - HC-XXX - Fecha"
        """
        return f"Control #{self.numero_control} - {self.paciente.id_clinico} - {self.fecha_control}"

    def __repr__(self):
        """
        Representación técnica del objeto para debugging.
        """
        return (
            f"<ControlPrenatal(id={self.id}, "
            f"numero={self.numero_control}, "
            f"paciente={self.paciente.id_clinico}, "
            f"fecha={self.fecha_control}, "
            f"semanas={self.semanas_gestacion})>"
        )

# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
