from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario
from decimal import Decimal
import os


class Ecografia(models.Model):
    """Modelo principal de Ecografía Obstétrica"""
    
    TIPO_CHOICES = [
        ('primer_trimestre', 'Primer Trimestre (6-14 sem)'),
        ('segundo_trimestre', 'Segundo Trimestre (14-28 sem)'),
        ('tercer_trimestre', 'Tercer Trimestre (28-42 sem)'),
        ('doppler', 'Doppler'),
        ('4d', 'Ecografía 4D'),
        ('genetica', 'Ecografía Genética'),
        ('morfologica', 'Ecografía Morfológica'),
    ]
    
    INDICACION_CHOICES = [
        ('control_rutina', 'Control de Rutina'),
        ('sospecha_malformacion', 'Sospecha de Malformación'),
        ('control_crecimiento', 'Control de Crecimiento'),
        ('evaluacion_bienestar', 'Evaluación de Bienestar Fetal'),
        ('sangrado', 'Sangrado'),
        ('screening_genetico', 'Screening Genético'),
        ('evaluacion_cervical', 'Evaluación Cervical'),
        ('doppler_materno', 'Doppler Materno'),
        ('doppler_fetal', 'Doppler Fetal'),
        ('otro', 'Otro'),
    ]
    
    CALIDAD_CHOICES = [
        ('excelente', 'Excelente'),
        ('buena', 'Buena'),
        ('regular', 'Regular'),
        ('limitada', 'Limitada'),
    ]
    
    # Relaciones
    embarazo = models.ForeignKey(
        Embarazo, 
        on_delete=models.CASCADE, 
        related_name='ecografias',
        verbose_name='Embarazo'
    )
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE, 
        related_name='ecografias',
        verbose_name='Paciente'
    )
    medico = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ecografias_realizadas',
        limit_choices_to={'rol': 'medico'},
        verbose_name='Médico Ecografista'
    )
    
    # Datos básicos
    fecha_ecografia = models.DateField(verbose_name='Fecha de Ecografía')
    tipo_ecografia = models.CharField(
        max_length=30, 
        choices=TIPO_CHOICES, 
        verbose_name='Tipo de Ecografía'
    )
    indicacion = models.CharField(
        max_length=50, 
        choices=INDICACION_CHOICES, 
        default='control_rutina',
        verbose_name='Indicación'
    )
    
    # Edad gestacional
    edad_gestacional_semanas = models.IntegerField(
        validators=[MinValueValidator(4), MaxValueValidator(42)],
        verbose_name='Edad Gestacional (semanas)'
    )
    edad_gestacional_dias = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name='Días adicionales'
    )
    
    # Evaluación general
    numero_fetos = models.IntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Número de Fetos'
    )
    vitalidad_fetal = models.BooleanField(
        default=True, 
        verbose_name='Vitalidad Fetal'
    )
    frecuencia_cardiaca_fetal = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(90), MaxValueValidator(180)],
        verbose_name='FCF (lpm)'
    )
    
    # Líquido amniótico
    indice_liquido_amniotico = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='ILA (cm)'
    )
    bolsillo_maximo = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='Bolsillo Máximo (cm)'
    )
    
    # Placenta
    localizacion_placenta = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='Localización Placenta'
    )
    grado_madurez_placenta = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        verbose_name='Grado de Madurez Placenta'
    )
    
    # Calidad del estudio
    calidad_estudio = models.CharField(
        max_length=20,
        choices=CALIDAD_CHOICES,
        default='buena',
        verbose_name='Calidad del Estudio'
    )
    
    limitaciones_tecnicas = models.TextField(
        blank=True,
        verbose_name='Limitaciones Técnicas',
        help_text='Ej: Posición fetal, obesidad materna, oligohidramnios'
    )
    
    # Conclusiones
    diagnostico = models.TextField(
        verbose_name='Diagnóstico Ecográfico'
    )
    observaciones = models.TextField(
        blank=True, 
        verbose_name='Observaciones y Recomendaciones'
    )
    
    # Seguimiento
    requiere_seguimiento = models.BooleanField(
        default=False,
        verbose_name='Requiere Seguimiento'
    )
    proxima_ecografia_recomendada = models.DateField(
        null=True,
        blank=True,
        verbose_name='Próxima Ecografía Recomendada'
    )
    
    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ecografias'
        ordering = ['-fecha_ecografia']
        verbose_name = 'Ecografía'
        verbose_name_plural = 'Ecografías'
        indexes = [
            models.Index(fields=['paciente', '-fecha_ecografia']),
            models.Index(fields=['embarazo', '-fecha_ecografia']),
            models.Index(fields=['fecha_ecografia']),
        ]
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar FCF según edad gestacional
        if self.frecuencia_cardiaca_fetal:
            if self.edad_gestacional_semanas < 12 and self.frecuencia_cardiaca_fetal < 110:
                raise ValidationError('FCF muy baja para edad gestacional temprana')
    
    def get_edad_gestacional_texto(self):
        """Devuelve edad gestacional en formato texto"""
        return f"{self.edad_gestacional_semanas}+{self.edad_gestacional_dias} semanas"
    
    def get_percentil_ila(self):
        """Calcula percentil de ILA según edad gestacional"""
        if not self.indice_liquido_amniotico:
            return None
        
        # Valores aproximados de referencia
        referencias_ila = {
            16: {'p5': 7.3, 'p50': 12.1, 'p95': 18.5},
            20: {'p5': 8.1, 'p50': 14.1, 'p95': 21.2},
            24: {'p5': 8.3, 'p50': 14.7, 'p95': 22.3},
            28: {'p5': 8.4, 'p50': 14.6, 'p95': 21.9},
            32: {'p5': 7.7, 'p50': 14.4, 'p95': 20.4},
            36: {'p5': 7.0, 'p50': 13.2, 'p95': 19.0},
            40: {'p5': 5.9, 'p50': 11.7, 'p95': 16.6},
        }
        
        # Buscar la semana más cercana
        semana_ref = min(referencias_ila.keys(), 
                        key=lambda x: abs(x - self.edad_gestacional_semanas))
        
        ref = referencias_ila[semana_ref]
        ila_valor = float(self.indice_liquido_amniotico)
        
        if ila_valor <= ref['p5']:
            return "Oligohidramnios (< p5)"
        elif ila_valor >= ref['p95']:
            return "Polihidramnios (> p95)"
        else:
            return "Normal (p5-p95)"
    
    def get_estado_liquido_amniotico(self):
        """Evalúa el estado del líquido amniótico"""
        if not self.indice_liquido_amniotico:
            return "No evaluado"
        
        ila = float(self.indice_liquido_amniotico)
        
        if ila < 5:
            return "🔴 Oligohidramnios severo"
        elif ila < 8:
            return "🟡 Oligohidramnios"
        elif ila > 25:
            return "🔴 Polihidramnios severo"
        elif ila > 20:
            return "🟡 Polihidramnios"
        else:
            return "✅ Normal"
    
    def get_evaluacion_fcf(self):
        """Evalúa la frecuencia cardíaca fetal"""
        if not self.frecuencia_cardiaca_fetal:
            return "No evaluada"
        
        fcf = self.frecuencia_cardiaca_fetal
        
        if fcf < 110:
            return "🔴 Bradicardia fetal"
        elif fcf > 160:
            return "🔴 Taquicardia fetal"
        else:
            return "✅ Normal"
    
    def __str__(self):
        return f"Ecografía {self.get_tipo_ecografia_display()} - {self.paciente.nombre_completo} - {self.fecha_ecografia}"
    
    @property
    def edad_gestacional_completa(self):
        return f"{self.edad_gestacional_semanas}+{self.edad_gestacional_dias}"


class BiometriaFetal(models.Model):
    """Mediciones biométricas del feto"""
    
    ecografia = models.OneToOneField(
        Ecografia, 
        on_delete=models.CASCADE, 
        related_name='biometria',
        verbose_name='Ecografía'
    )
    
    # Mediciones cefálicas
    diametro_biparietal = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='DBP (mm)',
        help_text='Diámetro Biparietal'
    )
    circunferencia_cefalica = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='CC (mm)',
        help_text='Circunferencia Cefálica'
    )
    diametro_occipito_frontal = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='DOF (mm)',
        help_text='Diámetro Occípito-Frontal'
    )
    
    # Mediciones abdominales
    circunferencia_abdominal = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='CA (mm)',
        help_text='Circunferencia Abdominal'
    )
    diametro_abdominal_transverso = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='DAT (mm)'
    )
    
    # Mediciones de extremidades
    longitud_femur = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='LF (mm)',
        help_text='Longitud del Fémur'
    )
    longitud_humero = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='LH (mm)',
        help_text='Longitud del Húmero'
    )
    longitud_tibia = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='LT (mm)',
        help_text='Longitud de la Tibia'
    )
    longitud_radio = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='LR (mm)',
        help_text='Longitud del Radio'
    )
    
    # Peso fetal estimado
    peso_fetal_estimado = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name='Peso Fetal Est. (g)'
    )
    percentil_peso = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Percentil de Peso'
    )
    
    # Mediciones adicionales
    diametro_transverso_cerebelo = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='DTC (mm)',
        help_text='Diámetro Transverso del Cerebelo'
    )
    
    cisterna_magna = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Cisterna Magna (mm)'
    )
    
    # Cálculos automáticos
    relacion_cc_ca = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Relación CC/CA'
    )
    
    relacion_lf_ca = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Relación LF/CA'
    )
    
    class Meta:
        db_table = 'biometria_fetal'
        verbose_name = 'Biometría Fetal'
        verbose_name_plural = 'Biometrías Fetales'
    
    def calcular_peso_fetal_hadlock(self):
        """Calcula peso fetal usando fórmula de Hadlock"""
        if not all([self.diametro_biparietal, self.circunferencia_cefalica, 
                   self.circunferencia_abdominal, self.longitud_femur]):
            return None
        
        import math
        
        # Fórmula de Hadlock (log10)
        log_peso = (1.335 - 
                   0.0034 * float(self.circunferencia_abdominal) * float(self.longitud_femur) +
                   0.0316 * float(self.diametro_biparietal) +
                   0.0457 * float(self.circunferencia_abdominal) +
                   0.1623 * float(self.longitud_femur))
        
        peso_gramos = int(10 ** log_peso)
        return peso_gramos
    
    def calcular_relaciones(self):
        """Calcula relaciones biométricas"""
        if self.circunferencia_cefalica and self.circunferencia_abdominal:
            self.relacion_cc_ca = round(
                float(self.circunferencia_cefalica) / float(self.circunferencia_abdominal), 2
            )
        
        if self.longitud_femur and self.circunferencia_abdominal:
            self.relacion_lf_ca = round(
                float(self.longitud_femur) / float(self.circunferencia_abdominal), 2
            )
    
    def get_evaluacion_crecimiento(self):
        """Evalúa el crecimiento fetal"""
        if not self.percentil_peso:
            return "No evaluado"
        
        if self.percentil_peso < 10:
            return "🔴 Restricción del crecimiento fetal"
        elif self.percentil_peso > 90:
            return "🔴 Macrosomía fetal"
        else:
            return "✅ Crecimiento normal"
    
    def save(self, *args, **kwargs):
        # Calcular relaciones automáticamente
        self.calcular_relaciones()
        
        # Calcular peso fetal si no está establecido
        if not self.peso_fetal_estimado:
            peso_calculado = self.calcular_peso_fetal_hadlock()
            if peso_calculado:
                self.peso_fetal_estimado = peso_calculado
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Biometría - {self.ecografia}"


class AnatomiaFetal(models.Model):
    """Evaluación anatómica del feto"""
    
    ecografia = models.OneToOneField(
        Ecografia, 
        on_delete=models.CASCADE, 
        related_name='anatomia',
        verbose_name='Ecografía'
    )
    
    # Sistema nervioso central
    craneo_normal = models.BooleanField(default=True, verbose_name='Cráneo Normal')
    cerebro_normal = models.BooleanField(default=True, verbose_name='Cerebro Normal')
    cerebelo_normal = models.BooleanField(default=True, verbose_name='Cerebelo Normal')
    
    # Cara
    perfil_facial_normal = models.BooleanField(default=True, verbose_name='Perfil Facial Normal')
    labios_normales = models.BooleanField(default=True, verbose_name='Labios Normales')
    
    # Tórax
    corazon_normal = models.BooleanField(default=True, verbose_name='Corazón Normal')
    pulmones_normales = models.BooleanField(default=True, verbose_name='Pulmones Normales')
    
    # Abdomen
    estomago_normal = models.BooleanField(default=True, verbose_name='Estómago Normal')
    rinones_normales = models.BooleanField(default=True, verbose_name='Riñones Normales')
    vejiga_normal = models.BooleanField(default=True, verbose_name='Vejiga Normal')
    
    # Columna vertebral
    columna_normal = models.BooleanField(default=True, verbose_name='Columna Normal')
    
    # Extremidades
    extremidades_superiores_normales = models.BooleanField(default=True, verbose_name='Extremidades Superiores Normales')
    extremidades_inferiores_normales = models.BooleanField(default=True, verbose_name='Extremidades Inferiores Normales')
    
    # Genitales
    genitales_visibles = models.BooleanField(default=False, verbose_name='Genitales Visibles')
    sexo_fetal = models.CharField(
        max_length=20,
        choices=[('masculino', 'Masculino'), ('femenino', 'Femenino'), ('indeterminado', 'Indeterminado')],
        blank=True,
        verbose_name='Sexo Fetal'
    )
    
    # Hallazgos anormales
    hallazgos_anormales = models.TextField(
        blank=True, 
        verbose_name='Hallazgos Anormales'
    )
    
    # Evaluación de marcadores de cromosomopatías
    translucencia_nucal = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Translucencia Nucal (mm)'
    )
    
    hueso_nasal_presente = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Hueso Nasal Presente'
    )
    
    class Meta:
        db_table = 'anatomia_fetal'
        verbose_name = 'Anatomía Fetal'
        verbose_name_plural = 'Anatomías Fetales'
    
    def get_evaluacion_anatomica(self):
        """Evaluación general de la anatomía"""
        campos_anatomicos = [
            'craneo_normal', 'cerebro_normal', 'cerebelo_normal',
            'perfil_facial_normal', 'labios_normales',
            'corazon_normal', 'pulmones_normales',
            'estomago_normal', 'rinones_normales', 'vejiga_normal',
            'columna_normal', 'extremidades_superiores_normales',
            'extremidades_inferiores_normales'
        ]
        
        total_campos = len(campos_anatomicos)
        campos_normales = sum(1 for campo in campos_anatomicos if getattr(self, campo, True))
        
        if campos_normales == total_campos:
            return "✅ Anatomía fetal normal"
        else:
            anormales = total_campos - campos_normales
            return f"⚠️ {anormales} hallazgo(s) anormal(es)"
    
    def get_riesgo_cromosomopatias(self):
        """Evalúa riesgo de cromosomopatías basado en marcadores"""
        if not self.translucencia_nucal:
            return "No evaluado"
        
        tn = float(self.translucencia_nucal)
        
        if tn > 3.5:
            return "🔴 Alto riesgo (TN > 3.5mm)"
        elif tn > 2.5:
            return "🟡 Riesgo intermedio (TN > 2.5mm)"
        else:
            return "✅ Bajo riesgo"
    
    def __str__(self):
        return f"Anatomía - {self.ecografia}"


class AnexosFetales(models.Model):
    """Evaluación de anexos fetales (placenta, cordón, líquido)"""
    
    ecografia = models.OneToOneField(
        Ecografia, 
        on_delete=models.CASCADE, 
        related_name='anexos',
        verbose_name='Ecografía'
    )
    
    # Placenta
    placenta_localizacion = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Localización Placenta'
    )
    placenta_grosor = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        verbose_name='Grosor Placenta (mm)'
    )
    placenta_inserccion_cordon = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Inserción del Cordón'
    )
    
    placenta_previa = models.BooleanField(
        default=False,
        verbose_name='Placenta Previa'
    )
    
    # Cordón umbilical
    numero_vasos_cordon = models.IntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name='Número de Vasos del Cordón'
    )
    circular_cordon = models.BooleanField(
        default=False, 
        verbose_name='Circular de Cordón'
    )
    
    # Líquido amniótico
    liquido_amniotico_normal = models.BooleanField(
        default=True,
        verbose_name='Líquido Amniótico Normal'
    )
    polihidramnios = models.BooleanField(
        default=False,
        verbose_name='Polihidramnios'
    )
    oligohidramnios = models.BooleanField(
        default=False,
        verbose_name='Oligohidramnios'
    )
    
    # Cérvix
    longitud_cervical = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Longitud Cervical (mm)'
    )
    
    class Meta:
        db_table = 'anexos_fetales'
        verbose_name = 'Anexos Fetales'
        verbose_name_plural = 'Anexos Fetales'
    
    def get_evaluacion_cordon(self):
        """Evalúa el cordón umbilical"""
        if self.numero_vasos_cordon == 2:
            return "⚠️ Arteria umbilical única"
        elif self.circular_cordon:
            return "🟡 Circular de cordón presente"
        else:
            return "✅ Cordón normal"
    
    def get_evaluacion_cervix(self):
        """Evalúa el cérvix"""
        if not self.longitud_cervical:
            return "No evaluado"
        
        longitud = float(self.longitud_cervical)
        
        if longitud < 25:
            return "🔴 Cérvix corto (riesgo de parto prematuro)"
        elif longitud < 30:
            return "🟡 Cérvix acortado"
        else:
            return "✅ Longitud cervical normal"
    
    def __str__(self):
        return f"Anexos - {self.ecografia}"


class ImagenEcografia(models.Model):
    """Imágenes asociadas a ecografías"""
    
    TIPO_IMAGEN_CHOICES = [
        ('biometria', 'Biometría Fetal'),
        ('anatomia', 'Anatomía Fetal'),
        ('doppler', 'Doppler'),
        ('3d_4d', '3D/4D'),
        ('placenta', 'Placenta'),
        ('cordon', 'Cordón Umbilical'),
        ('liquido_amniotico', 'Líquido Amniótico'),
        ('cervix', 'Cérvix'),
        ('anexos', 'Anexos'),
        ('general', 'Vista General'),
        ('cara_fetal', 'Cara Fetal'),
        ('corazon', 'Corazón Fetal'),
        ('columna', 'Columna Vertebral'),
        ('extremidades', 'Extremidades'),
        ('genitales', 'Genitales'),
    ]
    
    CALIDAD_CHOICES = [
        ('excelente', 'Excelente'),
        ('buena', 'Buena'),
        ('regular', 'Regular'),
        ('deficiente', 'Deficiente'),
    ]
    
    ecografia = models.ForeignKey(
        Ecografia,
        on_delete=models.CASCADE,
        related_name='imagenes',
        verbose_name='Ecografía'
    )
    
    imagen = models.ImageField(
        upload_to='ecografias/%Y/%m/%d/',
        verbose_name='Imagen',
        help_text='Formatos soportados: JPG, PNG, DICOM',
        null=True,
        blank=True
    )
    
    tipo_imagen = models.CharField(
        max_length=50,
        choices=TIPO_IMAGEN_CHOICES,
        verbose_name='Tipo de Imagen',
        null=True,
        blank=True,
        default='general'
    )
    
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título de la Imagen',
        help_text='Ej: DBP a las 20 semanas, Cara fetal 3D',
        null=True,
        blank=True,
        default='Imagen sin título'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Hallazgos visibles en la imagen'
    )
    
    calidad_imagen = models.CharField(
        max_length=20,
        choices=CALIDAD_CHOICES,
        default='buena',
        verbose_name='Calidad de Imagen'
    )
    
    mediciones_incluidas = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Mediciones en la Imagen',
        help_text='Datos de mediciones visibles en formato JSON'
    )
    
    analisis_ia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Análisis de IA',
        help_text='Resultados del análisis automático de IA'
    )
    
    fecha_captura = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Captura'
    )
    
    orden = models.PositiveIntegerField(
        default=1,
        verbose_name='Orden',
        help_text='Orden de visualización (1, 2, 3...)'
    )
    
    es_imagen_principal = models.BooleanField(
        default=False,
        verbose_name='¿Es Imagen Principal?',
        help_text='Imagen representativa de la ecografía'
    )
    
    class Meta:
        db_table = 'imagenes_ecografia'
        verbose_name = 'Imagen de Ecografía'
        verbose_name_plural = 'Imágenes de Ecografía'
        ordering = ['ecografia', 'orden']
        indexes = [
            models.Index(fields=['ecografia', 'tipo_imagen']),
            models.Index(fields=['fecha_captura']),
        ]
    
    def get_tamaño_archivo(self):
        """Obtiene el tamaño del archivo en formato legible"""
        if self.imagen and hasattr(self.imagen, 'size'):
            size = self.imagen.size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024*1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        return "Tamaño desconocido"
    
    def get_dimensiones(self):
        """Obtiene las dimensiones de la imagen"""
        try:
            from PIL import Image
            if self.imagen:
                with Image.open(self.imagen.path) as img:
                    return f"{img.width} x {img.height} px"
        except:
            pass
        return "Dimensiones desconocidas"
    
    def generar_thumbnail(self, size=(300, 300)):
        """Genera una miniatura de la imagen"""
        try:
            from PIL import Image
            
            if not self.imagen:
                return None
                
            # Ruta para el thumbnail
            thumb_name = f"thumb_{os.path.basename(self.imagen.name)}"
            thumb_path = os.path.join(
                os.path.dirname(self.imagen.path),
                'thumbnails',
                thumb_name
            )
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            
            # Generar thumbnail
            with Image.open(self.imagen.path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumb_path, 'JPEG', quality=85)
                
            return thumb_path
        except Exception as e:
            print(f"Error generando thumbnail: {e}")
            return None
    
    def analizar_con_ia(self):
        """Placeholder para análisis de IA futuro"""
        # Aquí se integraría el microservicio de IA
        analisis = {
            'procesado': True,
            'fecha_analisis': str(timezone.now()),
            'confianza': 0.0,
            'hallazgos': [],
            'mediciones_detectadas': {},
            'anomalias_detectadas': [],
            'calidad_tecnica': 'pendiente'
        }
        
        self.analisis_ia = analisis
        return analisis
    
    def save(self, *args, **kwargs):
        # Si es imagen principal, quitar flag de otras imágenes
        if self.es_imagen_principal:
            ImagenEcografia.objects.filter(
                ecografia=self.ecografia,
                es_imagen_principal=True
            ).update(es_imagen_principal=False)
        
        super().save(*args, **kwargs)
        
        # Generar thumbnail después de guardar
        self.generar_thumbnail()
    
    def __str__(self):
        return f"{self.titulo} - {self.ecografia.paciente.nombre_completo}"