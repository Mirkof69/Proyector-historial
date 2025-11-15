"""
===========================================
MÓDULO: MODELS DE PARTOS
===========================================
Descripción:
    Modelos para el registro de partos y recién nacidos.
    Gestiona información completa del parto, complicaciones y datos del recién nacido.

Modelos:
    - Parto: Registro completo del parto
    - RecienNacido: Datos del recién nacido
    - ComplicacionParto: Complicaciones durante el parto

Relaciones:
    Parto -> Embarazo (ForeignKey)
    Parto -> Paciente (ForeignKey)
    Parto -> Usuario (médico) (ForeignKey)
    RecienNacido -> Parto (ForeignKey)
    ComplicacionParto -> Parto (ForeignKey)

Base de datos:
    managed = False (la BD ya existe, no migrar)

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from django.db import models
import uuid


class Parto(models.Model):
    """
    MODELO: Registro de Parto
   
    Funcionamiento:
        Almacena toda la información relacionada con un parto
        incluyendo datos del procedimiento, complicaciones y resultados
    
    Relaciones:
        - embarazo: ForeignKey a Embarazo
        - paciente: ForeignKey a Paciente
        - medico: ForeignKey a Usuario (médico responsable)
   
    Campos principales:
        - Identificación: id, uuid
        - Relaciones: embarazo, paciente, medico
        - Fecha y hora: fecha_parto, hora_inicio, hora_fin
        - Tipo y vía: tipo_parto, via_parto
        - Detalles: edad_gestacional, duracion_trabajo_parto
        - Estado: complicaciones, estado
        - Observaciones: indicaciones, procedimientos
    """

    # Tipos de parto
    TIPOS_PARTO = [
        ('eutocico', 'Eutócico (Natural)'),
        ('cesarea', 'Cesárea'),
        ('forceps', 'Fórceps'),
        ('ventosa', 'Ventosa'),
        ('inducido', 'Inducido'),
    ]

    # Vías del parto
    VIAS_PARTO = [
        ('vaginal', 'Vaginal'),
        ('abdominal', 'Abdominal (Cesárea)'),
    ]

    # Estados
    ESTADOS_PARTO = [
        ('en_curso', 'En curso'),
        ('finalizado', 'Finalizado'),
        ('complicado', 'Con complicaciones'),
    ]

    # Campos de identificación
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Relaciones (db_column para respetar BD existente)
    embarazo = models.ForeignKey(
        'embarazos.Embarazo',
        on_delete=models.CASCADE,
        related_name='partos',
        db_column='embarazo_id'
    )
    paciente = models.ForeignKey(
        'pacientes.Paciente',
        on_delete=models.CASCADE,
        related_name='partos',
        db_column='paciente_id'
    )
    medico = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partos_atendidos',
        db_column='medico_id'
    )

    # Fecha y hora del parto
    fecha_parto = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)

    # Tipo y vía del parto
    tipo_parto = models.CharField(max_length=20, choices=TIPOS_PARTO)
    via_parto = models.CharField(max_length=20, choices=VIAS_PARTO)

    # Edad gestacional al parto
    edad_gestacional_semanas = models.IntegerField()
    edad_gestacional_dias = models.IntegerField(default=0)

    # Duración del trabajo de parto (en minutos)
    duracion_trabajo_parto = models.IntegerField(null=True, blank=True)

    # Indicaciones y razones
    indicaciones = models.TextField(blank=True, null=True)

    # Anestesia utilizada
    anestesia = models.CharField(max_length=100, blank=True, null=True)

    # Procedimientos realizados
    procedimientos = models.TextField(blank=True, null=True)

    # Complicaciones
    complicaciones = models.BooleanField(default=False)
    descripcion_complicaciones = models.TextField(blank=True, null=True)

    # Estado del parto
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_PARTO,
        default='en_curso'
    )

    # Observaciones generales
    observaciones = models.TextField(blank=True, null=True)

    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'partos'
        managed = False  # No migrar, BD ya existe
        ordering = ['-fecha_parto', '-hora_inicio']
        verbose_name = 'Parto'
        verbose_name_plural = 'Partos'

    def __str__(self):
        return f"Parto {self.id} - {self.paciente.nombre_completo if self.paciente else 'N/A'} - {self.fecha_parto}"


class RecienNacido(models.Model):
    """
    MODELO: Recién Nacido
    
    Funcionamiento:
        Almacena información del recién nacido resultante del parto
        Incluye datos antropométricos, APGAR y condiciones al nacer
    
    Relaciones:
        - parto: ForeignKey a Parto
    
    Campos principales:
        - Identificación: id, numero_hijo (en caso de gemelar)
        - Datos básicos: sexo, peso, talla, perimetro_cefalico
        - Evaluación: apgar_1min, apgar_5min
        - Estado: estado_al_nacer, reanimacion
        - Observaciones: malformaciones, observaciones
    """

    # Sexos
    SEXOS = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('I', 'Indeterminado'),
    ]

    # Estados al nacer
    ESTADOS = [
        ('vivo', 'Vivo'),
        ('muerto', 'Muerto'),
        ('mortinato', 'Mortinato'),
    ]

    # Campos de identificación
    id = models.AutoField(primary_key=True)
    
    # Relación con parto
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name='recien_nacidos',
        db_column='parto_id'
    )

    # Número de hijo (en caso de parto múltiple)
    numero_hijo = models.IntegerField(default=1)

    # Datos básicos
    sexo = models.CharField(max_length=1, choices=SEXOS)
    
    # Datos antropométricos
    peso = models.DecimalField(max_digits=5, decimal_places=2)  # en gramos
    talla = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # en cm
    perimetro_cefalico = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # en cm

    # Evaluación APGAR
    apgar_1min = models.IntegerField(null=True, blank=True)
    apgar_5min = models.IntegerField(null=True, blank=True)

    # Estado al nacer
    estado_al_nacer = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='vivo'
    )

    # Reanimación
    reanimacion = models.BooleanField(default=False)
    descripcion_reanimacion = models.TextField(blank=True, null=True)

    # Malformaciones
    malformaciones = models.BooleanField(default=False)
    descripcion_malformaciones = models.TextField(blank=True, null=True)

    # Observaciones
    observaciones = models.TextField(blank=True, null=True)

    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recien_nacidos'
        managed = False  # No migrar, BD ya existe
        ordering = ['parto', 'numero_hijo']
        verbose_name = 'Recién Nacido'
        verbose_name_plural = 'Recién Nacidos'

    def __str__(self):
        return f"RN {self.numero_hijo} - Parto {self.parto_id} - {self.get_sexo_display()}"


class ComplicacionParto(models.Model):
    """
    MODELO: Complicación del Parto
    
    Funcionamiento:
        Registra complicaciones específicas durante el parto
        Permite documentar múltiples complicaciones por parto
    
    Relaciones:
        - parto: ForeignKey a Parto
    
    Campos principales:
        - tipo_complicacion: Tipo de complicación
        - descripcion: Descripción detallada
        - tratamiento: Tratamiento aplicado
        - resuelto: Si fue resuelto o no
    """

    # Tipos de complicaciones
    TIPOS_COMPLICACION = [
        ('hemorragia', 'Hemorragia'),
        ('distocia', 'Distocia'),
        ('sufrimiento_fetal', 'Sufrimiento fetal'),
        ('ruptura_uterina', 'Ruptura uterina'),
        ('prolapso_cordon', 'Prolapso de cordón'),
        ('preeclampsia', 'Preeclampsia/Eclampsia'),
        ('otra', 'Otra'),
    ]

    # Campos de identificación
    id = models.AutoField(primary_key=True)
    
    # Relación con parto
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name='complicaciones_list',
        db_column='parto_id'
    )

    # Tipo de complicación
    tipo_complicacion = models.CharField(
        max_length=50,
        choices=TIPOS_COMPLICACION
    )

    # Descripción detallada
    descripcion = models.TextField()

    # Tratamiento aplicado
    tratamiento = models.TextField(blank=True, null=True)

    # Estado de resolución
    resuelto = models.BooleanField(default=False)

    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'complicaciones_parto'
        managed = False  # No migrar, BD ya existe
        ordering = ['parto', '-fecha_registro']
        verbose_name = 'Complicación del Parto'
        verbose_name_plural = 'Complicaciones del Parto'

    def __str__(self):
        return f"{self.get_tipo_complicacion_display()} - Parto {self.parto_id}"


"""
RESUMEN DE MODELS DE PARTOS:
=============================

1. Parto:
   - Campos: 20+ campos incluyendo tipo, vía, duración, complicaciones
   - Relaciones: embarazo, paciente, medico
   - Estados: en_curso, finalizado, complicado
   
2. RecienNacido:
   - Campos: sexo, peso, talla, APGAR, estado
   - Relaciones: parto
   - Permite múltiples RN por parto (gemelos/trillizos)
   
3. ComplicacionParto:
   - Campos: tipo, descripción, tratamiento
   - Relaciones: parto
   - Permite múltiples complicaciones por parto

Total: 3 modelos completos
Líneas: ~350
=============================
"""
