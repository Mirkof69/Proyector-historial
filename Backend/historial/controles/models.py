from django.db import models
from pacientes.models import Paciente
from embarazos.models import Embarazo
from usuarios.models import Usuario
import uuid

class ControlPrenatal(models.Model):
    PRESENTACIONES = (
        ('cefalica', 'Cefálica'),
        ('podalica', 'Podálica'),
        ('transversa', 'Transversa'),
    )
    
    MOVIMIENTOS = (
        ('presentes', 'Presentes'),
        ('ausentes', 'Ausentes'),
        ('disminuidos', 'Disminuidos'),
    )
    
    EDEMA_OPCIONES = (
        ('no', 'No'),
        ('leve', 'Leve'),
        ('moderado', 'Moderado'),
        ('severo', 'Severo'),
    )
    
    PROTEINURIA_OPCIONES = (
        ('negativa', 'Negativa'),
        ('trazas', 'Trazas'),
        ('positiva_1', '+'),
        ('positiva_2', '++'),
        ('positiva_3', '+++'),
    )
    
    # Campos principales
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # ✅ RELACIONES CORREGIDAS - ForeignKeys apropiadas
    embarazo = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        db_column='embarazo_id',
        related_name='controles'
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        db_column='paciente_id',
        related_name='controles'
    )

    numero_control = models.IntegerField()
    fecha_control = models.DateField()
    
    # Edad gestacional
    semanas_gestacion = models.IntegerField()
    dias_gestacion = models.IntegerField(blank=True, null=True)
    edad_gestacional_calculada = models.CharField(max_length=50, blank=True, null=True)
    
    # Antropometría
    peso_actual = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    peso_pregestacional = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ganancia_peso = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    talla = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    imc_actual = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    clasificacion_imc = models.CharField(max_length=50, blank=True, null=True)
    
    # Signos vitales
    presion_arterial_sistolica = models.IntegerField(blank=True, null=True)
    presion_arterial_diastolica = models.IntegerField(blank=True, null=True)
    presion_arterial_media = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    frecuencia_cardiaca = models.IntegerField(blank=True, null=True)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    
    # Exploración obstétrica
    altura_uterina = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    frecuencia_cardiaca_fetal = models.IntegerField(blank=True, null=True)
    presentacion_fetal = models.CharField(max_length=50, choices=PRESENTACIONES, blank=True, null=True)
    movimientos_fetales = models.CharField(max_length=50, choices=MOVIMIENTOS, blank=True, null=True)
    
    # Examen físico
    edema = models.CharField(max_length=50, choices=EDEMA_OPCIONES, blank=True, null=True)
    proteinuria = models.CharField(max_length=50, choices=PROTEINURIA_OPCIONES, blank=True, null=True)
    
    # Observaciones y registro
    observaciones = models.TextField(blank=True, null=True)

    # ✅ RELACIONES CORREGIDAS - ForeignKeys a Usuario
    medico = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='medico_id',
        related_name='controles_medico',
        blank=True,
        null=True
    )
    enfermero = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='enfermero_id',
        related_name='controles_enfermero',
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'controles_prenatales'
        managed = False
        ordering = ['-fecha_control']
    
    def __str__(self):
        return f"Control {self.numero_control} - Paciente {self.paciente.id_clinico}"