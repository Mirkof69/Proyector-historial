from django.db import models
from pacientes.models import Paciente
import uuid

class Embarazo(models.Model):
    TIPOS = (
        ('simple', 'Simple'),
        ('gemelar', 'Gemelar'),
        ('multiple', 'Múltiple'),
    )
    
    RIESGOS = (
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    )
    
    ESTADOS = (
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
        ('perdida', 'Pérdida'),
    )
    
    # Campos del modelo
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE, 
        db_column='paciente_id',
        related_name='embarazos'
    )
    numero_gesta = models.IntegerField()
    fecha_ultima_menstruacion = models.DateField()
    fecha_probable_parto = models.DateField(blank=True, null=True)
    tipo_embarazo = models.CharField(max_length=50, choices=TIPOS, default='simple')
    riesgo_embarazo = models.CharField(max_length=50, choices=RIESGOS, default='bajo')
    estado = models.CharField(max_length=50, choices=ESTADOS, default='activo')
    notas = models.TextField(blank=True, null=True)
    medico_responsable = models.CharField(max_length=100, blank=True, null=True, db_column='medico_responsable')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'embarazos'
        ordering = ['-fecha_registro']
        # managed = False  ← ELIMINADO
    
    def __str__(self):
        return f"Embarazo {self.numero_gesta} - {self.paciente.id_clinico}"