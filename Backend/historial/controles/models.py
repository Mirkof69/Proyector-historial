from django.db import models
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class ControlPrenatal(models.Model):
    """
    Modelo COMPLETO para registro de controles prenatales
    Almacena signos vitales, mediciones obstétricas y evaluación clínica
    """
    
    # Choices para campos selectivos
    PRESENTACION_CHOICES = [
        ('cefalica', 'Cefálica'),
        ('podalica', 'Podálica'),
        ('transversa', 'Transversa'),
        ('oblicua', 'Oblicua'),
    ]
    
    MOVIMIENTOS_CHOICES = [
        ('presentes', 'Presentes'),
        ('ausentes', 'Ausentes'),
        ('disminuidos', 'Disminuidos'),
        ('aumentados', 'Aumentados'),
    ]
    
    EDEMA_CHOICES = [
        ('no', 'No'),
        ('leve', 'Leve'),
        ('moderado', 'Moderado'),
        ('severo', 'Severo'),
        ('generalizado', 'Generalizado'),
    ]
    
    PROTEINURIA_CHOICES = [
        ('negativa', 'Negativa'),
        ('trazas', 'Trazas'),
        ('positiva_1', '+'),
        ('positiva_2', '++'),
        ('positiva_3', '+++'),
        ('positiva_4', '++++'),
    ]
    
    # ========== RELACIONES ==========
    embarazo_id = models.ForeignKey(
        Embarazo,
        on_delete=models.CASCADE,
        related_name='controles',
        db_column='embarazo_id',
        verbose_name='Embarazo'
    )
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='controles_prenatales',
        db_column='paciente_id',
        verbose_name='Paciente'
    )
    
    medico_id = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controles_realizados',
        db_column='medico_id',
        verbose_name='Médico'
    )
    
    # ========== DATOS DEL CONTROL ==========
    numero_control = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Número de Control',
        help_text='Número secuencial del control (1, 2, 3...)'
    )
    
    fecha_control = models.DateField(
        verbose_name='Fecha del Control',
        help_text='Fecha en que se realizó el control prenatal'
    )
    
    semanas_gestacion = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(42)],
        verbose_name='Semanas de Gestación',
        help_text='Semanas completas de gestación al momento del control'
    )
    
    dias_gestacion = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name='Días adicionales',
        help_text='Días adicionales a las semanas completas (0-6)'
    )
    
    # ========== MEDICIONES ANTROPOMÉTRICAS ==========
    peso_actual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('30.0')), MaxValueValidator(Decimal('200.0'))],
        verbose_name='Peso Actual (kg)',
        help_text='Peso actual de la gestante en kilogramos'
    )
    
    peso_pregestacional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('30.0')), MaxValueValidator(Decimal('200.0'))],
        verbose_name='Peso Pre-gestacional (kg)',
        help_text='Peso antes del embarazo en kilogramos'
    )
    
    talla = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('130.0')), MaxValueValidator(Decimal('200.0'))],
        verbose_name='Talla (cm)',
        help_text='Talla de la gestante en centímetros'
    )
    
    # ========== SIGNOS VITALES MATERNOS ==========
    presion_arterial_sistolica = models.IntegerField(
        validators=[MinValueValidator(70), MaxValueValidator(220)],
        verbose_name='Presión Arterial Sistólica (mmHg)',
        help_text='Presión sistólica en mmHg'
    )
    
    presion_arterial_diastolica = models.IntegerField(
        validators=[MinValueValidator(40), MaxValueValidator(140)],
        verbose_name='Presión Arterial Diastólica (mmHg)',
        help_text='Presión diastólica en mmHg'
    )
    
    frecuencia_cardiaca = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(200)],
        verbose_name='Frecuencia Cardíaca Materna (lpm)',
        help_text='Frecuencia cardíaca materna en latidos por minuto'
    )
    
    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('35.0')), MaxValueValidator(Decimal('42.0'))],
        verbose_name='Temperatura (°C)',
        help_text='Temperatura corporal en grados Celsius'
    )
    
    # ========== MEDICIONES OBSTÉTRICAS ==========
    altura_uterina = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('50.0'))],
        verbose_name='Altura Uterina (cm)',
        help_text='Altura del fondo uterino en centímetros'
    )
    
    frecuencia_cardiaca_fetal = models.IntegerField(
        validators=[MinValueValidator(90), MaxValueValidator(180)],
        verbose_name='Frecuencia Cardíaca Fetal (lpm)',
        help_text='Frecuencia cardíaca fetal en latidos por minuto (normal: 110-160)'
    )
    
    presentacion_fetal = models.CharField(
        max_length=20,
        choices=PRESENTACION_CHOICES,
        null=True,
        blank=True,
        verbose_name='Presentación Fetal',
        help_text='Posición del feto en el útero'
    )
    
    movimientos_fetales = models.CharField(
        max_length=20,
        choices=MOVIMIENTOS_CHOICES,
        null=True,
        blank=True,
        default='presentes',
        verbose_name='Movimientos Fetales',
        help_text='Percepción de movimientos fetales por la madre'
    )
    
    # ========== EVALUACIÓN CLÍNICA ==========
    edema = models.CharField(
        max_length=20,
        choices=EDEMA_CHOICES,
        default='no',
        verbose_name='Edema',
        help_text='Presencia y severidad de edema'
    )
    
    proteinuria = models.CharField(
        max_length=20,
        choices=PROTEINURIA_CHOICES,
        default='negativa',
        verbose_name='Proteinuria',
        help_text='Resultado de proteinuria en orina'
    )
    
    # ========== OBSERVACIONES ==========
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales del control prenatal'
    )
    
    # ========== METADATA ==========
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro',
        help_text='Fecha y hora en que se registró el control en el sistema'
    )
    
    class Meta:
        db_table = 'controles_prenatales'
        verbose_name = 'Control Prenatal'
        verbose_name_plural = 'Controles Prenatales'
        ordering = ['-fecha_control', '-numero_control']
        # ✅ UNIQUE_TOGETHER ELIMINADO - AHORA SE PERMITEN MÚLTIPLES CONTROLES
        indexes = [
            models.Index(fields=['embarazo_id', '-fecha_control']),
            models.Index(fields=['paciente', '-fecha_control']),
            models.Index(fields=['fecha_control']),
            models.Index(fields=['-fecha_registro']),
        ]
    
    def __str__(self):
        return f"Control #{self.numero_control} - {self.paciente.nombre} {self.paciente.apellido_paterno} - {self.fecha_control}"
    
    # ========== MÉTODOS DE CÁLCULO ==========
    
    @property
    def edad_gestacional_texto(self):
        """Retorna la edad gestacional formateada"""
        return f"{self.semanas_gestacion}+{self.dias_gestacion or 0}"
    
    @property
    def edad_gestacional_dias(self):
        """Retorna edad gestacional en días totales"""
        return (self.semanas_gestacion * 7) + (self.dias_gestacion or 0)
    
    @property
    def trimestre(self):
        """Determina el trimestre del embarazo"""
        semanas = self.semanas_gestacion
        if semanas < 13:
            return 1
        elif semanas < 27:
            return 2
        else:
            return 3
    
    @property
    def imc(self):
        """Calcula el Índice de Masa Corporal (IMC)"""
        if self.peso_actual and self.talla:
            talla_m = float(self.talla) / 100
            imc = float(self.peso_actual) / (talla_m * talla_m)
            return round(imc, 2)
        return None
    
    @property
    def clasificacion_imc(self):
        """Clasifica el IMC según OMS"""
        imc = self.imc
        if imc:
            if imc < 18.5:
                return "Bajo peso"
            elif imc < 25:
                return "Normal"
            elif imc < 30:
                return "Sobrepeso"
            else:
                return "Obesidad"
        return None
    
    @property
    def presion_arterial_media(self):
        """Calcula la Presión Arterial Media (PAM)"""
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            pam = (self.presion_arterial_sistolica + (2 * self.presion_arterial_diastolica)) / 3
            return round(pam, 2)
        return None
    
    @property
    def ganancia_peso(self):
        """Calcula la ganancia de peso"""
        if self.peso_actual and self.peso_pregestacional:
            ganancia = float(self.peso_actual) - float(self.peso_pregestacional)
            return round(ganancia, 1)
        return None
    
    @property
    def ganancia_peso_semanal(self):
        """Calcula ganancia de peso promedio por semana"""
        if self.ganancia_peso and self.semanas_gestacion > 0:
            return round(self.ganancia_peso / self.semanas_gestacion, 2)
        return None
    
    @property
    def ganancia_peso_esperada(self):
        """Calcula ganancia de peso esperada según IMC pregestacional"""
        if not self.peso_pregestacional or not self.talla:
            return None
        
        talla_m = float(self.talla) / 100
        imc_pre = float(self.peso_pregestacional) / (talla_m * talla_m)
        
        if imc_pre < 18.5:
            ganancia_total = (12.5, 18.0)
        elif imc_pre < 25:
            ganancia_total = (11.5, 16.0)
        elif imc_pre < 30:
            ganancia_total = (7.0, 11.5)
        else:
            ganancia_total = (5.0, 9.0)
        
        semanas = self.semanas_gestacion
        if semanas < 13:
            return (1, 2)
        else:
            proporcion = (semanas - 13) / 27
            min_esperada = 1 + (ganancia_total[0] - 1) * proporcion
            max_esperada = 2 + (ganancia_total[1] - 2) * proporcion
            return (round(min_esperada, 1), round(max_esperada, 1))
    
    @property
    def altura_uterina_esperada(self):
        """Calcula altura uterina esperada"""
        if self.semanas_gestacion >= 20:
            return (self.semanas_gestacion - 2, self.semanas_gestacion + 2)
        return None
    
    @property
    def diferencia_altura_uterina(self):
        """Diferencia entre altura uterina medida y esperada"""
        esperada = self.altura_uterina_esperada
        if esperada and self.altura_uterina:
            promedio = (esperada[0] + esperada[1]) / 2
            return round(float(self.altura_uterina) - promedio, 1)
        return None
    
    def tiene_hipertension(self):
        """Verifica si hay hipertensión (PA >= 140/90)"""
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            return (self.presion_arterial_sistolica >= 140 or 
                    self.presion_arterial_diastolica >= 90)
        return False
    
    def tiene_prehipertension(self):
        """Verifica si hay pre-hipertensión (PA >= 120/80)"""
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            return (self.presion_arterial_sistolica >= 120 or 
                    self.presion_arterial_diastolica >= 80)
        return False
    
    def fcf_es_anormal(self):
        """Verifica si la FCF está fuera del rango normal (110-160 lpm)"""
        if self.frecuencia_cardiaca_fetal:
            return (self.frecuencia_cardiaca_fetal < 110 or 
                    self.frecuencia_cardiaca_fetal > 160)
        return False
    
    def tiene_alertas_criticas(self):
        """Verifica si hay alguna alerta crítica"""
        alertas = []
        
        if self.tiene_hipertension():
            alertas.append('hipertension')
        
        if self.fcf_es_anormal():
            alertas.append('fcf_anormal')
        
        if self.edema in ['severo', 'generalizado']:
            alertas.append('edema_severo')
        
        if self.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']:
            alertas.append('proteinuria_positiva')
        
        if self.movimientos_fetales == 'ausentes':
            alertas.append('movimientos_ausentes')
        
        return len(alertas) > 0
    
    def riesgo_preeclampsia(self):
        """Evalúa riesgo de preeclampsia"""
        riesgo = 0
        factores = []
        
        if self.tiene_hipertension():
            riesgo += 3
            factores.append('Hipertensión')
        
        if self.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']:
            riesgo += 3
            factores.append('Proteinuria')
        
        if self.edema in ['severo', 'generalizado']:
            riesgo += 2
            factores.append('Edema severo')
        
        if self.imc and self.imc >= 30:
            riesgo += 1
            factores.append('Obesidad')
        
        if riesgo >= 5:
            nivel = 'ALTO'
        elif riesgo >= 3:
            nivel = 'MODERADO'
        elif riesgo > 0:
            nivel = 'BAJO'
        else:
            nivel = 'MÍNIMO'
        
        return {
            'nivel': nivel,
            'puntuacion': riesgo,
            'factores': factores
        }
    
    def estado_nutricional(self):
        """Evaluación completa del estado nutricional"""
        resultado = {
            'imc': self.imc,
            'clasificacion': self.clasificacion_imc,
            'ganancia_peso': self.ganancia_peso,
            'ganancia_semanal': self.ganancia_peso_semanal,
            'ganancia_esperada': self.ganancia_peso_esperada,
            'estado': 'Normal'
        }
        
        if self.ganancia_peso and self.ganancia_peso_esperada:
            min_esp, max_esp = self.ganancia_peso_esperada
            if self.ganancia_peso < min_esp:
                resultado['estado'] = 'Ganancia insuficiente'
            elif self.ganancia_peso > max_esp:
                resultado['estado'] = 'Ganancia excesiva'
        
        return resultado
    
    def crecimiento_fetal(self):
        """Evalúa el crecimiento fetal"""
        resultado = {
            'altura_uterina': float(self.altura_uterina) if self.altura_uterina else None,
            'esperada': self.altura_uterina_esperada,
            'diferencia': self.diferencia_altura_uterina,
            'estado': 'Normal'
        }
        
        if self.diferencia_altura_uterina:
            if self.diferencia_altura_uterina < -3:
                resultado['estado'] = 'Posible RCIU'
            elif self.diferencia_altura_uterina > 3:
                resultado['estado'] = 'Posible macrosomía'
        
        return resultado
    
    def get_alertas(self):
        """Retorna lista de alertas detectadas"""
        alertas = []
        
        if self.tiene_hipertension():
            alertas.append({
                'tipo': 'critico',
                'categoria': 'presion_arterial',
                'mensaje': 'HIPERTENSIÓN DETECTADA',
                'valor': f'{self.presion_arterial_sistolica}/{self.presion_arterial_diastolica} mmHg',
                'recomendacion': 'Evaluar preeclampsia. Considerar hospitalización.'
            })
        elif self.tiene_prehipertension():
            alertas.append({
                'tipo': 'advertencia',
                'categoria': 'presion_arterial',
                'mensaje': 'Pre-hipertensión',
                'valor': f'{self.presion_arterial_sistolica}/{self.presion_arterial_diastolica} mmHg',
                'recomendacion': 'Monitoreo estrecho. Control en 7 días.'
            })
        
        if self.fcf_es_anormal():
            alertas.append({
                'tipo': 'critico',
                'categoria': 'fcf',
                'mensaje': 'FCF ANORMAL',
                'valor': f'{self.frecuencia_cardiaca_fetal} lpm',
                'recomendacion': 'Realizar NST inmediatamente.'
            })
        
        if self.edema in ['severo', 'generalizado']:
            alertas.append({
                'tipo': 'critico',
                'categoria': 'edema',
                'mensaje': 'EDEMA SEVERO',
                'valor': self.get_edema_display(),
                'recomendacion': 'Alto riesgo preeclampsia.'
            })
        
        if self.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3', 'positiva_4']:
            nivel = self.get_proteinuria_display()
            alertas.append({
                'tipo': 'critico',
                'categoria': 'proteinuria',
                'mensaje': f'PROTEINURIA POSITIVA ({nivel})',
                'valor': nivel,
                'recomendacion': 'Proteinuria 24h. Función renal.'
            })
        
        if self.movimientos_fetales == 'ausentes':
            alertas.append({
                'tipo': 'critico',
                'categoria': 'movimientos',
                'mensaje': 'MOVIMIENTOS FETALES AUSENTES',
                'valor': 'Ausentes',
                'recomendacion': 'EMERGENCIA: NST inmediato.'
            })
        
        imc = self.imc
        if imc:
            if imc < 18.5:
                alertas.append({
                    'tipo': 'advertencia',
                    'categoria': 'nutricional',
                    'mensaje': 'BAJO PESO',
                    'valor': f'IMC: {imc}',
                    'recomendacion': 'Evaluación nutricional.'
                })
            elif imc >= 30:
                alertas.append({
                    'tipo': 'advertencia',
                    'categoria': 'nutricional',
                    'mensaje': 'OBESIDAD',
                    'valor': f'IMC: {imc}',
                    'recomendacion': 'Dieta supervisada.'
                })
        
        if self.temperatura and float(self.temperatura) >= 38:
            alertas.append({
                'tipo': 'critico',
                'categoria': 'temperatura',
                'mensaje': 'FIEBRE',
                'valor': f'{self.temperatura} °C',
                'recomendacion': 'Investigar foco infeccioso.'
            })
        
        riesgo_pe = self.riesgo_preeclampsia()
        if riesgo_pe['nivel'] in ['ALTO', 'MODERADO']:
            alertas.append({
                'tipo': 'critico' if riesgo_pe['nivel'] == 'ALTO' else 'advertencia',
                'categoria': 'preeclampsia',
                'mensaje': f'RIESGO {riesgo_pe["nivel"]} DE PREECLAMPSIA',
                'valor': f'{riesgo_pe["puntuacion"]} puntos',
                'recomendacion': f'Factores: {", ".join(riesgo_pe["factores"])}'
            })
        
        return alertas
    
    def generar_reporte_completo(self):
        """Genera un reporte completo del control"""
        return {
            'control': {
                'numero': self.numero_control,
                'fecha': self.fecha_control.strftime('%d/%m/%Y'),
                'edad_gestacional': self.edad_gestacional_texto,
                'trimestre': self.trimestre,
            },
            'paciente': {
                'nombre': f"{self.paciente.nombre} {self.paciente.apellido_paterno}",
                'id_clinico': self.paciente.id_clinico,
            },
            'signos_vitales': {
                'presion_arterial': f"{self.presion_arterial_sistolica}/{self.presion_arterial_diastolica}",
                'pam': self.presion_arterial_media,
                'fc_materna': self.frecuencia_cardiaca,
                'temperatura': float(self.temperatura) if self.temperatura else None,
            },
            'mediciones_obstetricas': {
                'altura_uterina': float(self.altura_uterina) if self.altura_uterina else None,
                'fcf': self.frecuencia_cardiaca_fetal,
                'presentacion': self.get_presentacion_fetal_display() if self.presentacion_fetal else None,
                'movimientos': self.get_movimientos_fetales_display() if self.movimientos_fetales else None,
            },
            'estado_nutricional': self.estado_nutricional(),
            'evaluacion_crecimiento': self.crecimiento_fetal(),
            'riesgo_preeclampsia': self.riesgo_preeclampsia(),
            'alertas': self.get_alertas(),
            'observaciones': self.observaciones,
        }
    
    def save(self, *args, **kwargs):
        """Override save para validaciones adicionales"""
        if self.presion_arterial_sistolica and self.presion_arterial_diastolica:
            if self.presion_arterial_sistolica <= self.presion_arterial_diastolica:
                raise ValueError("La presión sistólica debe ser mayor que la diastólica")
        
        if not self.paciente_id and self.embarazo_id:
            self.paciente = self.embarazo_id.paciente
        
        super().save(*args, **kwargs)