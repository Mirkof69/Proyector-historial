from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente
from controles.models import ControlPrenatal
from usuarios.models import Usuario
from decimal import Decimal


class TipoExamen(models.Model):
    """Catálogo de tipos de exámenes de laboratorio"""
    
    CATEGORIA_CHOICES = [
        ('hematologia', 'Hematología'),
        ('bioquimica', 'Bioquímica'),
        ('inmunologia', 'Inmunología'),
        ('microbiologia', 'Microbiología'),
        ('urinalisis', 'Urianálisis'),
        ('serologia', 'Serología'),
        ('hormonal', 'Hormonal'),
        ('genetica', 'Genética'),
    ]
    
    nombre = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Nombre del Examen',
        help_text='Ej: Hemograma Completo, Glucosa en Ayunas'
    )
    
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Código interno del examen'
    )
    
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoría'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del examen'
    )
    
    preparacion = models.TextField(
        blank=True,
        verbose_name='Preparación',
        help_text='Indicaciones de preparación para el paciente'
    )
    
    tiempo_resultado = models.IntegerField(
        default=24,
        validators=[MinValueValidator(1)],
        verbose_name='Tiempo de Resultado (horas)',
        help_text='Tiempo estimado para obtener resultados'
    )
    
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio (Bs)',
        help_text='Precio del examen en bolivianos'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si el examen está disponible'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tipos_examenes'
        verbose_name = 'Tipo de Examen'
        verbose_name_plural = 'Tipos de Exámenes'
        ordering = ['categoria', 'nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['categoria']),
        ]
    
    def get_examenes_realizados_mes(self):
        """Obtiene la cantidad de exámenes realizados este mes"""
        from datetime import datetime
        from django.utils import timezone
        
        ahora = timezone.now()
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.examenes.filter(
            fecha_solicitud__gte=inicio_mes,
            estado='completado'
        ).count()
    
    def get_tiempo_promedio_resultado(self):
        """Calcula el tiempo promedio de resultados en días"""
        examenes_completados = self.examenes.filter(
            estado='completado',
            fecha_resultado__isnull=False
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
        urgentes = self.examenes.filter(prioridad__in=['urgente', 'stat']).count()
        return round((urgentes / total) * 100, 1)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ExamenLaboratorio(models.Model):
    """Solicitud de examen de laboratorio"""
    
    ESTADO_CHOICES = [
        ('solicitado', 'Solicitado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('normal', 'Normal'),
        ('urgente', 'Urgente'),
        ('stat', 'STAT (Inmediato)'),
    ]
    
    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='examenes_laboratorio',
        verbose_name='Paciente'
    )
    
    control_prenatal = models.ForeignKey(
        ControlPrenatal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='examenes',
        verbose_name='Control Prenatal Asociado'
    )
    
    tipo_examen = models.ForeignKey(
        TipoExamen,
        on_delete=models.PROTECT,
        related_name='examenes',
        verbose_name='Tipo de Examen'
    )
    
    medico_solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='examenes_solicitados',
        limit_choices_to={'rol': 'medico'},
        verbose_name='Médico Solicitante'
    )
    
    # Datos del examen
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Solicitud'
    )
    
    fecha_muestra = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Toma de Muestra'
    )
    
    fecha_resultado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Resultado'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='solicitado',
        verbose_name='Estado'
    )
    
    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDAD_CHOICES,
        default='normal',
        verbose_name='Prioridad'
    )
    
    indicaciones = models.TextField(
        blank=True,
        verbose_name='Indicaciones Clínicas',
        help_text='Motivo de la solicitud e indicaciones'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones generales del examen'
    )
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'examenes_laboratorio'
        verbose_name = 'Examen de Laboratorio'
        verbose_name_plural = 'Exámenes de Laboratorio'
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['paciente', '-fecha_solicitud']),
            models.Index(fields=['estado']),
            models.Index(fields=['-fecha_solicitud']),
        ]
    
    @property
    def dias_desde_solicitud(self):
        """Días transcurridos desde la solicitud"""
        from datetime import datetime
        from django.utils import timezone
        
        if self.fecha_solicitud:
            ahora = timezone.now()
            diferencia = ahora - self.fecha_solicitud
            return diferencia.days
        return None
    
    @property
    def esta_pendiente(self):
        """Verifica si el examen está pendiente"""
        return self.estado in ['solicitado', 'en_proceso']
    
    @property
    def esta_vencido(self):
        """Verifica si el examen excedió el tiempo esperado"""
        if self.estado == 'completado':
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
        alertas = {
            'normal': 'success',
            'urgente': 'warning', 
            'stat': 'danger'
        }
        return alertas.get(self.prioridad, 'info')
    
    def get_costo_total_estimado(self):
        """Calcula el costo total estimado incluyendo procesamiento"""
        costo_base = self.tipo_examen.precio
        
        # Factores adicionales según prioridad
        if self.prioridad == 'urgente':
            costo_base *= Decimal('1.5')  # 50% adicional
        elif self.prioridad == 'stat':
            costo_base *= Decimal('2.0')  # 100% adicional
            
        return costo_base
    
    # Métodos para el admin
    def tiempo_total_proceso(self):
        """Obtiene el tiempo total del proceso en horas (método para admin)"""
        return self.get_tiempo_total_proceso()
    
    def costo_total_estimado(self):
        """Obtiene el costo total estimado (método para admin)"""
        return self.get_costo_total_estimado()
    
    def __str__(self):
        return f"{self.tipo_examen.nombre} - {self.paciente.nombre_completo} ({self.get_estado_display()})"


class ValorReferencia(models.Model):
    """Valores de referencia para resultados de laboratorio"""
    
    UNIDAD_CHOICES = [
        ('mg/dL', 'mg/dL'),
        ('g/dL', 'g/dL'),
        ('mmol/L', 'mmol/L'),
        ('mEq/L', 'mEq/L'),
        ('pg/mL', 'pg/mL'),
        ('ng/mL', 'ng/mL'),
        ('UI/L', 'UI/L'),
        ('U/L', 'U/L'),
        ('%', '%'),
        ('células/mm³', 'células/mm³'),
        ('10³/µL', '10³/µL'),
        ('10⁶/µL', '10⁶/µL'),
        ('segundos', 'segundos'),
        ('ratio', 'ratio'),
        ('cualitativo', 'Cualitativo'),
    ]
    
    tipo_examen = models.ForeignKey(
        TipoExamen,
        on_delete=models.CASCADE,
        related_name='valores_referencia',
        verbose_name='Tipo de Examen'
    )
    
    parametro = models.CharField(
        max_length=200,
        verbose_name='Parámetro',
        help_text='Ej: Hemoglobina, Glucosa, Hematocrito'
    )
    
    valor_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Mínimo'
    )
    
    valor_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Máximo'
    )
    
    valor_normal = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Valor Normal',
        help_text='Para valores cualitativos (Ej: Negativo, Positivo)'
    )
    
    unidad = models.CharField(
        max_length=50,
        choices=UNIDAD_CHOICES,
        verbose_name='Unidad de Medida'
    )
    
    condicion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Condición',
        help_text='Ej: En ayunas, Embarazadas primer trimestre'
    )
    
    es_critico_bajo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Crítico Bajo',
        help_text='Valor por debajo del cual se considera crítico'
    )
    
    es_critico_alto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Crítico Alto',
        help_text='Valor por encima del cual se considera crítico'
    )
    
    class Meta:
        db_table = 'valores_referencia'
        verbose_name = 'Valor de Referencia'
        verbose_name_plural = 'Valores de Referencia'
        ordering = ['tipo_examen', 'parametro']
        unique_together = ['tipo_examen', 'parametro', 'condicion']
    
    def get_rango_completo(self):
        """Obtiene el rango completo como string"""
        if self.valor_minimo and self.valor_maximo:
            return f"{self.valor_minimo} - {self.valor_maximo} {self.unidad}"
        elif self.valor_normal:
            return f"{self.valor_normal}"
        else:
            return "Rango no definido"
    
    def evaluar_valor(self, valor_numerico):
        """Evalúa si un valor está normal, anormal o crítico"""
        if not valor_numerico:
            return {'estado': 'sin_valor', 'mensaje': 'Sin valor para evaluar'}
        
        valor = float(valor_numerico)
        
        # Verificar valores críticos
        if self.es_critico_bajo and valor < float(self.es_critico_bajo):
            return {
                'estado': 'critico_bajo',
                'es_critico': True,
                'es_normal': False,
                'mensaje': f'Valor crítico bajo: {valor} < {self.es_critico_bajo}'
            }
        
        if self.es_critico_alto and valor > float(self.es_critico_alto):
            return {
                'estado': 'critico_alto',
                'es_critico': True,
                'es_normal': False,
                'mensaje': f'Valor crítico alto: {valor} > {self.es_critico_alto}'
            }
        
        # Verificar rangos normales
        if self.valor_minimo and self.valor_maximo:
            if float(self.valor_minimo) <= valor <= float(self.valor_maximo):
                return {
                    'estado': 'normal',
                    'es_critico': False,
                    'es_normal': True,
                    'mensaje': f'Valor normal: {self.valor_minimo} ≤ {valor} ≤ {self.valor_maximo}'
                }
            else:
                return {
                    'estado': 'anormal',
                    'es_critico': False,
                    'es_normal': False,
                    'mensaje': f'Valor fuera de rango: {valor} (normal: {self.valor_minimo}-{self.valor_maximo})'
                }
        
        # Si no hay rangos definidos, considerar normal
        return {
            'estado': 'sin_rango',
            'es_critico': False,
            'es_normal': True,
            'mensaje': 'No hay rangos de referencia definidos'
        }
    
    def __str__(self):
        rango = f"{self.valor_minimo}-{self.valor_maximo}" if self.valor_minimo and self.valor_maximo else self.valor_normal
        return f"{self.tipo_examen.nombre} - {self.parametro}: {rango} {self.unidad}"


class ResultadoLaboratorio(models.Model):
    """Resultados de exámenes de laboratorio"""
    
    examen = models.ForeignKey(
        ExamenLaboratorio,
        on_delete=models.CASCADE,
        related_name='resultados',
        verbose_name='Examen'
    )
    
    valor_referencia = models.ForeignKey(
        ValorReferencia,
        on_delete=models.PROTECT,
        related_name='resultados',
        verbose_name='Parámetro'
    )
    
    valor_numerico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Numérico'
    )
    
    valor_texto = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Valor Texto',
        help_text='Para resultados cualitativos'
    )
    
    es_normal = models.BooleanField(
        default=True,
        verbose_name='¿Es Normal?'
    )
    
    es_critico = models.BooleanField(
        default=False,
        verbose_name='¿Es Crítico?'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones del Resultado'
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'resultados_laboratorio'
        verbose_name = 'Resultado de Laboratorio'
        verbose_name_plural = 'Resultados de Laboratorio'
        ordering = ['examen', 'valor_referencia']
        indexes = [
            models.Index(fields=['examen']),
            models.Index(fields=['es_critico']),
            models.Index(fields=['es_normal']),
        ]
    
    def calcular_estado_automatico(self):
        """Calcula automáticamente si el resultado es normal, anormal o crítico"""
        if not self.valor_numerico or not self.valor_referencia:
            return False
            
        evaluacion = self.valor_referencia.evaluar_valor(self.valor_numerico)
        self.es_critico = evaluacion['es_critico']
        self.es_normal = evaluacion['es_normal']
        return True
    
    def get_interpretacion_medica(self):
        """Devuelve la interpretación médica del resultado"""
        if not self.valor_numerico:
            return "Sin valor numérico para interpretar"
            
        valor = float(self.valor_numerico)
        parametro = self.valor_referencia.parametro.lower()
        
        # Interpretaciones específicas por parámetro
        interpretaciones = {
            'glucosa': self._interpretar_glucosa(valor),
            'hemoglobina': self._interpretar_hemoglobina(valor),
            'hematocrito': self._interpretar_hematocrito(valor),
            'leucocitos': self._interpretar_leucocitos(valor),
            'plaquetas': self._interpretar_plaquetas(valor),
            'creatinina': self._interpretar_creatinina(valor),
            'urea': self._interpretar_urea(valor),
            'colesterol': self._interpretar_colesterol(valor),
            'trigliceridos': self._interpretar_trigliceridos(valor),
        }
        
        for key, interpretation in interpretaciones.items():
            if key in parametro:
                return interpretation
                
        # Interpretación genérica
        if self.es_critico:
            return f"⚠️ VALOR CRÍTICO: Requiere atención médica inmediata"
        elif not self.es_normal:
            return f"🔍 VALOR ANORMAL: Requiere evaluación médica"
        else:
            return f"✅ VALOR NORMAL: Dentro de rangos esperados"
    
    def _interpretar_glucosa(self, valor):
        """Interpretación específica para glucosa"""
        if valor < 70:
            return f"🔴 HIPOGLUCEMIA SEVERA ({valor} mg/dL): Administrar glucosa inmediatamente"
        elif valor < 100:
            return f"✅ GLUCOSA NORMAL ({valor} mg/dL): Valor óptimo"
        elif valor < 126:
            return f"🟡 GLUCOSA ELEVADA ({valor} mg/dL): Riesgo de prediabetes"
        elif valor < 200:
            return f"🟠 DIABETES ({valor} mg/dL): Requiere tratamiento antidiabético"
        else:
            return f"🔴 CRISIS DIABÉTICA ({valor} mg/dL): HOSPITALIZACIÓN INMEDIATA"
    
    def _interpretar_hemoglobina(self, valor):
        """Interpretación específica para hemoglobina"""
        if valor < 10:
            return f"🔴 ANEMIA SEVERA ({valor} g/dL): Considerar transfusión"
        elif valor < 12:
            return f"🟡 ANEMIA LEVE ({valor} g/dL): Suplementar hierro"
        elif valor <= 16:
            return f"✅ HEMOGLOBINA NORMAL ({valor} g/dL)"
        else:
            return f"🟠 POLICITEMIA ({valor} g/dL): Investigar causas"
    
    def _interpretar_hematocrito(self, valor):
        """Interpretación específica para hematocrito"""
        if valor < 30:
            return f"🔴 HEMATOCRITO BAJO ({valor}%): Anemia significativa"
        elif valor <= 44:
            return f"✅ HEMATOCRITO NORMAL ({valor}%)"
        else:
            return f"🟠 HEMATOCRITO ELEVADO ({valor}%): Posible deshidratación"
    
    def _interpretar_leucocitos(self, valor):
        """Interpretación específica para leucocitos"""
        if valor < 4000:
            return f"🔴 LEUCOPENIA ({valor}/μL): Riesgo de infección"
        elif valor <= 11000:
            return f"✅ LEUCOCITOS NORMALES ({valor}/μL)"
        else:
            return f"🟠 LEUCOCITOSIS ({valor}/μL): Posible infección o inflamación"
    
    def _interpretar_plaquetas(self, valor):
        """Interpretación específica para plaquetas"""
        if valor < 150000:
            return f"🔴 TROMBOCITOPENIA ({valor}/μL): Riesgo de sangrado"
        elif valor <= 400000:
            return f"✅ PLAQUETAS NORMALES ({valor}/μL)"
        else:
            return f"🟠 TROMBOCITOSIS ({valor}/μL): Riesgo de trombosis"
    
    def _interpretar_creatinina(self, valor):
        """Interpretación específica para creatinina"""
        if valor > 1.5:
            return f"🔴 CREATININA ELEVADA ({valor} mg/dL): Posible insuficiencia renal"
        elif valor <= 1.2:
            return f"✅ CREATININA NORMAL ({valor} mg/dL)"
        else:
            return f"🟡 CREATININA BORDERLINE ({valor} mg/dL): Monitorear función renal"
    
    def _interpretar_urea(self, valor):
        """Interpretación específica para urea"""
        if valor > 50:
            return f"🟠 UREA ELEVADA ({valor} mg/dL): Evaluar función renal"
        elif valor <= 40:
            return f"✅ UREA NORMAL ({valor} mg/dL)"
        else:
            return f"🟡 UREA BORDERLINE ({valor} mg/dL): Control en seguimiento"
    
    def _interpretar_colesterol(self, valor):
        """Interpretación específica para colesterol"""
        if valor < 200:
            return f"✅ COLESTEROL DESEABLE ({valor} mg/dL)"
        elif valor < 240:
            return f"🟡 COLESTEROL BORDERLINE ({valor} mg/dL): Modificar dieta"
        else:
            return f"🔴 COLESTEROL ALTO ({valor} mg/dL): Riesgo cardiovascular"
    
    def _interpretar_trigliceridos(self, valor):
        """Interpretación específica para triglicéridos"""
        if valor < 150:
            return f"✅ TRIGLICÉRIDOS NORMALES ({valor} mg/dL)"
        elif valor < 200:
            return f"🟡 TRIGLICÉRIDOS BORDERLINE ({valor} mg/dL)"
        else:
            return f"🔴 TRIGLICÉRIDOS ALTOS ({valor} mg/dL): Riesgo cardiovascular"
    
    def get_protocolo_sugerido(self):
        """Devuelve el protocolo médico sugerido"""
        if not self.valor_numerico:
            return "No se puede determinar protocolo sin valor numérico"
            
        parametro = self.valor_referencia.parametro.lower()
        
        if self.es_critico:
            if 'glucosa' in parametro:
                return self._protocolo_glucosa_critica()
            elif 'hemoglobina' in parametro or 'hematocrito' in parametro:
                return self._protocolo_anemia_severa()
            elif 'creatinina' in parametro or 'urea' in parametro:
                return self._protocolo_funcion_renal()
            else:
                return "1. Notificar al médico inmediatamente\n2. Repetir examen para confirmar\n3. Iniciar monitoreo continuo\n4. Considerar hospitalización si es necesario"
        elif not self.es_normal:
            return "1. Evaluación médica en 24-48 horas\n2. Repetir examen en 1 semana\n3. Investigar causas subyacentes\n4. Modificaciones en estilo de vida si aplica"
        else:
            return "1. Continuar con controles rutinarios\n2. Mantener hábitos saludables\n3. Próximo control según programación"
    
    def _protocolo_glucosa_critica(self):
        """Protocolo para glucosa crítica"""
        valor = float(self.valor_numerico)
        if valor < 70:
            return """HIPOGLUCEMIA SEVERA:
1. Administrar 15-20g de glucosa oral (si consciente)
2. Si inconsciente: Glucosa IV al 50% (50ml)
3. Monitorear cada 15 minutos
4. Repetir glucosa en 1 hora
5. Investigar causa de hipoglucemia
6. Ajustar medicación antidiabética"""
        else:
            return """HIPERGLUCEMIA SEVERA:
1. Hidratación endovenosa (SSN 0.9%)
2. Insulina rápida según protocolo
3. Gasometría arterial (descartar cetoacidosis)
4. Electrolitos séricos completos
5. Monitoreo horario de glucosa
6. Considerar hospitalización en UCI"""
    
    def _protocolo_anemia_severa(self):
        """Protocolo para anemia severa"""
        return """ANEMIA SEVERA:
1. Tipificación sanguínea urgente
2. Pruebas cruzadas inmediatas
3. Considerar transfusión si Hb < 7 g/dL
4. Investigar causa (hierro sérico, B12, folatos)
5. Monitoreo de signos vitales
6. Evaluar sangrado activo"""
    
    def _protocolo_funcion_renal(self):
        """Protocolo para alteración de función renal"""
        return """FUNCIÓN RENAL ALTERADA:
1. Creatinina sérica y clearance
2. Electrolitos completos (Na, K, Cl)
3. Gasometría venosa
4. Ecografía renal
5. Suspender nefrotóxicos
6. Interconsulta a nefrología"""
    
    def get_recomendaciones_paciente(self):
        """Recomendaciones específicas para el paciente"""
        parametro = self.valor_referencia.parametro.lower()
        
        if 'glucosa' in parametro and not self.es_normal:
            return """RECOMENDACIONES PARA GLUCOSA ALTERADA:
- Dieta baja en carbohidratos simples
- Ejercicio regular (30 min diarios)
- Control de peso corporal
- Monitoreo domiciliario de glucosa
- Medicación según prescripción médica"""
        
        elif 'colesterol' in parametro and not self.es_normal:
            return """RECOMENDACIONES PARA COLESTEROL ALTO:
- Dieta baja en grasas saturadas
- Aumentar consumo de fibra
- Ejercicio cardiovascular regular
- Evitar tabaco y alcohol excesivo
- Medicación si es indicada"""
        
        elif ('hemoglobina' in parametro or 'hematocrito' in parametro) and not self.es_normal:
            return """RECOMENDACIONES PARA ANEMIA:
- Dieta rica en hierro (carnes rojas, espinacas)
- Suplementos de hierro según prescripción
- Vitamina C para mejorar absorción
- Evitar té y café con comidas
- Control médico regular"""
        
        else:
            return "Seguir indicaciones médicas específicas según el resultado obtenido"
    
    def get_valores_seguimiento(self):
        """Obtiene valores históricos para seguimiento"""
        return ResultadoLaboratorio.objects.filter(
            examen__paciente=self.examen.paciente,
            valor_referencia=self.valor_referencia
        ).order_by('-fecha_registro')[:5]
    
    def calcular_tendencia(self):
        """Calcula la tendencia del parámetro (mejorando/empeorando/estable)"""
        valores_anteriores = self.get_valores_seguimiento()
        
        if len(valores_anteriores) < 2:
            return "Sin suficientes datos para tendencia"
        
        valor_actual = float(self.valor_numerico) if self.valor_numerico else 0
        valor_anterior = float(valores_anteriores[1].valor_numerico) if valores_anteriores[1].valor_numerico else 0
        
        if valor_actual == valor_anterior:
            return "📊 ESTABLE"
        
        # Determinar si el aumento es bueno o malo según el parámetro
        parametro = self.valor_referencia.parametro.lower()
        
        if valor_actual > valor_anterior:
            if any(param in parametro for param in ['glucosa', 'creatinina', 'urea', 'colesterol']):
                return "📈 EMPEORANDO (aumentando)"
            else:
                return "📈 MEJORANDO (aumentando)"
        else:
            if any(param in parametro for param in ['hemoglobina', 'hematocrito', 'plaquetas']):
                return "📉 EMPEORANDO (disminuyendo)"
            else:
                return "📉 MEJORANDO (disminuyendo)"
    
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
            fecha = valor.fecha_registro.strftime('%d/%m/%Y')
            val = valor.valor_numerico if valor.valor_numerico else valor.valor_texto
            estado = "🔴 CRÍTICO" if valor.es_critico else "⚠️ ANORMAL" if not valor.es_normal else "✅ NORMAL"
            historial.append(f"{i+1}. {fecha}: {val} {valor.valor_referencia.unidad} - {estado}")
        
        return "\n".join(historial)
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el estado al guardar"""
        self.calcular_estado_automatico()
        super().save(*args, **kwargs)
    
    def __str__(self):
        valor = self.valor_numerico if self.valor_numerico else self.valor_texto
        return f"{self.valor_referencia.parametro}: {valor} {self.valor_referencia.unidad}"