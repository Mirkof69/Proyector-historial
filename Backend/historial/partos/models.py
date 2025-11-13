from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class Parto(models.Model):
    """Modelo principal del Parto"""
    
    TIPO_PARTO_CHOICES = [
        ('vaginal_espontaneo', 'Vaginal Espontáneo'),
        ('vaginal_instrumentado', 'Vaginal Instrumentado'),
        ('cesarea_electiva', 'Cesárea Electiva'),
        ('cesarea_urgencia', 'Cesárea de Urgencia'),
        ('cesarea_emergencia', 'Cesárea de Emergencia'),
    ]
    
    PRESENTACION_CHOICES = [
        ('cefalica', 'Cefálica'),
        ('podalica', 'Podálica'),
        ('transversa', 'Transversa'),
        ('oblicua', 'Oblicua'),
    ]
    
    POSICION_CHOICES = [
        ('oia', 'Occípito Ilíaca Anterior'),
        ('oip', 'Occípito Ilíaca Posterior'),
        ('oit', 'Occípito Ilíaca Transversa'),
        ('oda', 'Occípito Derecha Anterior'),
        ('odp', 'Occípito Derecha Posterior'),
        ('odt', 'Occípito Derecha Transversa'),
    ]
    
    MEMBRANAS_CHOICES = [
        ('integras', 'Membranas Íntegras'),
        ('rotas_espontaneas', 'Rotura Espontánea'),
        ('rotas_artificiales', 'Rotura Artificial'),
    ]
    
    # Relaciones usando strings para evitar imports circulares
    embarazo_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID del Embarazo',
        help_text='Relación con el embarazo'
    )
    
    paciente_id = models.IntegerField(
        verbose_name='ID del Paciente',
        help_text='Relación con el paciente'
    )
    
    medico_responsable_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID del Médico Responsable',
        help_text='Médico que atiende el parto'
    )
    
    # Identificación
    numero_parto = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de Parto',
        help_text='Número único del parto'
    )
    
    # Fechas y tiempos
    fecha_ingreso = models.DateTimeField(
        verbose_name='Fecha y Hora de Ingreso'
    )
    
    fecha_inicio_trabajo_parto = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Inicio del Trabajo de Parto'
    )
    
    fecha_parto = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha y Hora del Parto'
    )
    
    # Datos del parto
    edad_gestacional_parto = models.CharField(
        max_length=10,
        verbose_name='Edad Gestacional al Parto',
        help_text='Ej: 39+2'
    )
    
    tipo_parto = models.CharField(
        max_length=30,
        choices=TIPO_PARTO_CHOICES,
        verbose_name='Tipo de Parto'
    )
    
    presentacion_fetal = models.CharField(
        max_length=20,
        choices=PRESENTACION_CHOICES,
        default='cefalica',
        verbose_name='Presentación Fetal'
    )
    
    posicion_fetal = models.CharField(
        max_length=20,
        choices=POSICION_CHOICES,
        blank=True,
        verbose_name='Posición Fetal'
    )
    
    # Estado de membranas
    estado_membranas = models.CharField(
        max_length=30,
        choices=MEMBRANAS_CHOICES,
        default='integras',
        verbose_name='Estado de Membranas'
    )
    
    hora_rotura_membranas = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Rotura de Membranas'
    )
    
    caracteristicas_liquido = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Características del Líquido Amniótico',
        help_text='Claro, meconial, sanguinolento'
    )
    
    # Duración del trabajo de parto (simplificado)
    duracion_trabajo_parto_horas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Duración Total del Trabajo de Parto (horas)'
    )
    
    duracion_periodo_expulsivo_minutos = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(600)],
        verbose_name='Duración del Período Expulsivo (minutos)'
    )
    
    # Analgesia y anestesia
    analgesia_utilizada = models.BooleanField(
        default=False,
        verbose_name='¿Se utilizó analgesia?'
    )
    
    tipo_analgesia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tipo de Analgesia',
        help_text='Epidural, raquídea, general, local'
    )
    
    # Episiotomía y desgarros
    episiotomia = models.BooleanField(
        default=False,
        verbose_name='¿Se realizó episiotomía?'
    )
    
    tipo_episiotomia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo de Episiotomía'
    )
    
    desgarros = models.BooleanField(
        default=False,
        verbose_name='¿Hubo desgarros?'
    )
    
    grado_desgarros = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Grado y Localización de Desgarros'
    )
    
    # Alumbramiento
    tipo_alumbramiento = models.CharField(
        max_length=50,
        choices=[
            ('espontaneo', 'Espontáneo'),
            ('dirigido', 'Dirigido'),
            ('manual', 'Manual'),
        ],
        default='espontaneo',
        verbose_name='Tipo de Alumbramiento'
    )
    
    placenta_completa = models.BooleanField(
        default=True,
        verbose_name='¿Placenta completa?'
    )
    
    peso_placenta = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(100), MaxValueValidator(1000)],
        verbose_name='Peso de la Placenta (g)'
    )
    
    # Pérdida sanguínea
    perdida_sanguinea_estimada = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5000)],
        verbose_name='Pérdida Sanguínea Estimada (ml)'
    )
    
    hemorragia_postparto = models.BooleanField(
        default=False,
        verbose_name='¿Hemorragia postparto?'
    )
    
    # Complicaciones
    complicaciones_maternas = models.TextField(
        blank=True,
        verbose_name='Complicaciones Maternas',
        help_text='Describir cualquier complicación durante el parto'
    )
    
    # Medicamentos utilizados
    oxitocina_utilizada = models.BooleanField(
        default=False,
        verbose_name='¿Se utilizó oxitocina?'
    )
    
    dosis_oxitocina = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Dosis de Oxitocina',
        help_text='UI totales utilizadas'
    )
    
    otros_medicamentos = models.TextField(
        blank=True,
        verbose_name='Otros Medicamentos Utilizados'
    )
    
    # Observaciones y notas
    observaciones_parto = models.TextField(
        blank=True,
        verbose_name='Observaciones del Parto'
    )
    
    indicaciones_cesarea = models.TextField(
        blank=True,
        verbose_name='Indicaciones de Cesárea',
        help_text='Solo completar si es cesárea'
    )
    
    # Estado final
    parto_finalizado = models.BooleanField(
        default=False,
        verbose_name='¿Parto finalizado?'
    )
    
    # Información adicional del trabajo de parto
    trabajo_parto_espontaneo = models.BooleanField(
        default=True,
        verbose_name='¿Trabajo de parto espontáneo?'
    )
    
    induccion_parto = models.BooleanField(
        default=False,
        verbose_name='¿Se indujo el parto?'
    )
    
    metodo_induccion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Método de Inducción',
        help_text='Prostaglandinas, oxitocina, amniotomía'
    )
    
    # Monitoreo fetal
    monitoreo_fetal_continuo = models.BooleanField(
        default=False,
        verbose_name='¿Monitoreo fetal continuo?'
    )
    
    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'partos'
        ordering = ['-fecha_parto']
        verbose_name = 'Parto'
        verbose_name_plural = 'Partos'
        indexes = [
            models.Index(fields=['paciente_id', '-fecha_parto']),
            models.Index(fields=['fecha_parto']),
            models.Index(fields=['tipo_parto']),
            models.Index(fields=['numero_parto']),
        ]
    
    def save(self, *args, **kwargs):
        # Generar número de parto automáticamente
        if not self.numero_parto:
            year = timezone.now().year
            last_parto = Parto.objects.filter(
                fecha_registro__year=year
            ).order_by('-numero_parto').first()
            
            if last_parto and last_parto.numero_parto:
                try:
                    last_number = int(last_parto.numero_parto.split('-')[-1])
                    new_number = last_number + 1
                except:
                    new_number = 1
            else:
                new_number = 1
            
            self.numero_parto = f"PARTO-{year}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
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
        elif perdida < 1000:
            return "🟡 Moderada (500-1000ml)"
        elif perdida < 1500:
            return "🔴 Severa (1000-1500ml)"
        else:
            return "🚨 Muy severa (> 1500ml)"
    
    def get_estado_parto(self):
        """Devuelve el estado actual del parto"""
        if self.parto_finalizado:
            return "✅ Finalizado"
        elif self.fecha_inicio_trabajo_parto:
            return "🟡 En trabajo de parto"
        else:
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
        
        return complicaciones if complicaciones else ["Sin complicaciones registradas"]
    
    def __str__(self):
        return f"Parto {self.numero_parto} - Paciente ID: {self.paciente_id} - {self.get_tipo_parto_display()}"


class RecienNacido(models.Model):
    """Modelo para registrar datos del recién nacido"""
    
    SEXO_CHOICES = [
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('indeterminado', 'Indeterminado'),
    ]
    
    ESTADO_CHOICES = [
        ('vivo', 'Vivo'),
        ('mortinato', 'Mortinato'),
        ('muerte_neonatal', 'Muerte Neonatal'),
    ]
    
    # Relaciones
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name='recien_nacidos',
        verbose_name='Parto'
    )
    
    # Datos básicos
    numero_gemelo = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Número de Gemelo',
        help_text='1 para único, 2,3,4,5 para múltiples'
    )
    
    fecha_nacimiento = models.DateTimeField(
        verbose_name='Fecha y Hora de Nacimiento'
    )
    
    sexo = models.CharField(
        max_length=20,
        choices=SEXO_CHOICES,
        verbose_name='Sexo'
    )
    
    estado_nacimiento = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='vivo',
        verbose_name='Estado al Nacimiento'
    )
    
    # Medidas antropométricas
    peso_nacimiento = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(6000)],
        verbose_name='Peso al Nacimiento (g)'
    )
    
    talla_nacimiento = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(20), MaxValueValidator(60)],
        verbose_name='Talla al Nacimiento (cm)'
    )
    
    perimetro_cefalico = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(50)],
        verbose_name='Perímetro Cefálico (cm)'
    )
    
    # Score de Apgar
    apgar_1_minuto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Apgar 1 minuto'
    )
    
    apgar_5_minutos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Apgar 5 minutos'
    )
    
    apgar_10_minutos = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Apgar 10 minutos'
    )
    
    # Reanimación
    requirio_reanimacion = models.BooleanField(
        default=False,
        verbose_name='¿Requirió reanimación?'
    )
    
    tipo_reanimacion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Tipo de Reanimación',
        help_text='Estimulación, O2, VPP, masaje cardíaco, intubación'
    )
    
    # Malformaciones y patología
    malformaciones_congenitas = models.BooleanField(
        default=False,
        verbose_name='¿Malformaciones congénitas?'
    )
    
    descripcion_malformaciones = models.TextField(
        blank=True,
        verbose_name='Descripción de Malformaciones'
    )
    
    # Destino del recién nacido
    destino_rn = models.CharField(
        max_length=100,
        choices=[
            ('alojamiento_conjunto', 'Alojamiento Conjunto'),
            ('neonatologia', 'Neonatología'),
            ('uci_neonatal', 'UCI Neonatal'),
            ('traslado', 'Traslado a otro centro'),
            ('fallecido', 'Fallecido'),
        ],
        default='alojamiento_conjunto',
        verbose_name='Destino del Recién Nacido'
    )
    
    # Datos adicionales
    llanto_inmediato = models.BooleanField(
        default=True,
        verbose_name='¿Llanto inmediato?'
    )
    
    respiracion_espontanea = models.BooleanField(
        default=True,
        verbose_name='¿Respiración espontánea?'
    )
    
    tono_muscular_normal = models.BooleanField(
        default=True,
        verbose_name='¿Tono muscular normal?'
    )
    
    # Observaciones
    observaciones_rn = models.TextField(
        blank=True,
        verbose_name='Observaciones del Recién Nacido'
    )
    
    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recien_nacidos'
        ordering = ['parto', 'numero_gemelo']
        verbose_name = 'Recién Nacido'
        verbose_name_plural = 'Recién Nacidos'
        unique_together = ['parto', 'numero_gemelo']
        indexes = [
            models.Index(fields=['parto', 'numero_gemelo']),
            models.Index(fields=['fecha_nacimiento']),
            models.Index(fields=['peso_nacimiento']),
        ]
    
    def get_clasificacion_peso(self):
        """Clasifica el peso del recién nacido"""
        peso = self.peso_nacimiento
        
        if peso < 1000:
            return "🔴 Extremadamente bajo peso (< 1000g)"
        elif peso < 1500:
            return "🔴 Muy bajo peso (< 1500g)"
        elif peso < 2500:
            return "🟡 Bajo peso (< 2500g)"
        elif peso <= 4000:
            return "✅ Peso normal (2500-4000g)"
        elif peso <= 4500:
            return "🟡 Macrosomía leve (4000-4500g)"
        else:
            return "🔴 Macrosomía severa (> 4500g)"
    
    def get_evaluacion_apgar(self):
        """Evalúa el score de Apgar"""
        apgar_5 = self.apgar_5_minutos
        
        if apgar_5 >= 8:
            return "✅ Excelente (8-10)"
        elif apgar_5 >= 6:
            return "🟡 Moderado (6-7)"
        elif apgar_5 >= 4:
            return "🔴 Bajo (4-5)"
        else:
            return "🚨 Crítico (0-3)"
    
    def get_edad_gestacional_nacimiento(self):
        """Clasificación por edad gestacional"""
        # Esto requeriría calcular desde la fecha de nacimiento
        # Por ahora retornamos un placeholder
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
            return f"🔴 Problemas: {', '.join(problemas)}"
        else:
            return "✅ Estado general normal"
    
    def __str__(self):
        gemelo_str = f" (Gemelo {self.numero_gemelo})" if self.numero_gemelo > 1 else ""
        return f"RN - {self.parto.numero_parto}{gemelo_str} - {self.peso_nacimiento}g - Apgar {self.apgar_5_minutos}"


class PartogramaRegistro(models.Model):
    """Registro de partograma - seguimiento hora a hora del trabajo de parto"""
    
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name='partograma',
        verbose_name='Parto'
    )
    
    # Tiempo
    hora_registro = models.DateTimeField(
        verbose_name='Hora del Registro'
    )
    
    horas_trabajo_parto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(48)],
        verbose_name='Horas en Trabajo de Parto'
    )
    
    # Dilatación cervical
    dilatacion_cervical = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Dilatación Cervical (cm)'
    )
    
    borramiento_cervical = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Borramiento Cervical (%)'
    )
    
    # Descenso fetal
    estacion_fetal = models.CharField(
        max_length=10,
        verbose_name='Estación Fetal',
        help_text='Ej: -3, -2, -1, 0, +1, +2, +3'
    )
    
    # Contracciones uterinas
    contracciones_10min = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Contracciones en 10 minutos'
    )
    
    duracion_contracciones = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(120)],
        verbose_name='Duración Contracciones (segundos)'
    )
    
    intensidad_contracciones = models.CharField(
        max_length=20,
        choices=[
            ('leves', 'Leves'),
            ('moderadas', 'Moderadas'),
            ('fuertes', 'Fuertes'),
        ],
        blank=True,
        verbose_name='Intensidad de Contracciones'
    )
    
    # Frecuencia cardíaca fetal
    fcf_baseline = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(80), MaxValueValidator(200)],
        verbose_name='FCF Basal (lpm)'
    )
    
    variabilidad_fcf = models.CharField(
        max_length=20,
        choices=[
            ('ausente', 'Ausente'),
            ('minima', 'Mínima'),
            ('moderada', 'Moderada'),
            ('marcada', 'Marcada'),
        ],
        blank=True,
        verbose_name='Variabilidad FCF'
    )
    
    desaceleraciones = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Desaceleraciones',
        help_text='Tardías, variables, prolongadas'
    )
    
    # Signos vitales maternos
    presion_arterial_sistolica = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(70), MaxValueValidator(250)],
        verbose_name='Presión Arterial Sistólica (mmHg)'
    )
    
    presion_arterial_diastolica = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        verbose_name='Presión Arterial Diastólica (mmHg)'
    )
    
    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(35.0), MaxValueValidator(42.0)],
        verbose_name='Temperatura (°C)'
    )
    
    pulso_materno = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        verbose_name='Pulso Materno (lpm)'
    )
    
    # Medicamentos
    oxitocina_dosis = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Dosis de Oxitocina',
        help_text='mU/min'
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones del Registro'
    )
    
    # Alertas automáticas
    alerta_progreso_lento = models.BooleanField(
        default=False,
        verbose_name='Alerta: Progreso lento'
    )
    
    alerta_fcf_anormal = models.BooleanField(
        default=False,
        verbose_name='Alerta: FCF anormal'
    )
    
    alerta_signos_vitales = models.BooleanField(
        default=False,
        verbose_name='Alerta: Signos vitales alterados'
    )
    
    # Metadata
    registrado_por_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Usuario que registró'
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'partograma_registros'
        ordering = ['parto', 'hora_registro']
        verbose_name = 'Registro de Partograma'
        verbose_name_plural = 'Registros de Partograma'
        unique_together = ['parto', 'hora_registro']
        indexes = [
            models.Index(fields=['parto', 'hora_registro']),
            models.Index(fields=['dilatacion_cervical']),
            models.Index(fields=['fcf_baseline']),
        ]
    
    def save(self, *args, **kwargs):
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
        
        # Alerta progreso lento (esto requeriría lógica más compleja)
        # Por ahora solo un ejemplo básico
        if self.horas_trabajo_parto > 12 and self.dilatacion_cervical < 6:
            self.alerta_progreso_lento = True
    
    def get_presion_arterial(self):
        """Devuelve la presión arterial formateada"""
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            return f"{self.presion_arterial_sistolica}/{self.presion_arterial_diastolica}"
        return "No registrada"
    
    def get_evaluacion_fcf(self):
        """Evalúa la FCF"""
        if not self.fcf_baseline:
            return "No registrada"
        
        fcf = self.fcf_baseline
        
        if fcf < 110:
            return "🔴 Bradicardia"
        elif fcf > 160:
            return "🔴 Taquicardia"
        else:
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
        
        if contracciones >= 3 and intensidad == 'fuertes':
            return "✅ Contracciones adecuadas"
        elif contracciones >= 2:
            return "🟡 Contracciones moderadas"
        else:
            return "🔴 Contracciones insuficientes"
    
    def get_alertas_activas(self):
        """Devuelve las alertas activas"""
        alertas = []
        
        if self.alerta_fcf_anormal:
            alertas.append("FCF anormal")
        
        if self.alerta_progreso_lento:
            alertas.append("Progreso lento")
        
        if self.alerta_signos_vitales:
            alertas.append("Signos vitales alterados")
        
        return alertas if alertas else ["Sin alertas"]
    
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
        return f"Partograma - {self.parto.numero_parto} - {self.hora_registro.strftime('%H:%M')} - {self.dilatacion_cervical}cm"