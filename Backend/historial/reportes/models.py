from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json
from datetime import datetime, timedelta
from django.utils import timezone


class TipoReporte(models.Model):
    """Tipos de reportes disponibles en el sistema - VERSION MEJORADA"""
    
    CATEGORIA_CHOICES = [
        ('estadistico', '📊 Estadísticas y Métricas'),
        ('paciente', '👤 Reportes de Pacientes'),
        ('institucional', '🏥 Reportes Institucionales'),
        ('regulatorio', '📋 Cumplimiento Regulatorio'),
        ('clinico', '🩺 Reportes Clínicos'),
        ('financiero', '💰 Reportes Financieros'),
    ]
    
    FRECUENCIA_CHOICES = [
        ('bajo_demanda', '🔄 Generar cuando se necesite'),
        ('diario', '📅 Todos los días'),
        ('semanal', '📆 Cada semana'),
        ('mensual', '🗓️ Mensualmente'),
        ('trimestral', '📊 Cada 3 meses'),
        ('anual', '📈 Anualmente'),
    ]
    
    # INFORMACIÓN BÁSICA
    nombre = models.CharField(
        max_length=200, 
        verbose_name='📝 Nombre del Reporte',
        help_text='Ej: Reporte de Pacientes del Mes'
    )
    
    codigo = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='🔖 Código Único',
        help_text='Código interno (se genera automáticamente si se deja vacío)',
        blank=True
    )
    
    descripcion = models.TextField(
        verbose_name='📄 Descripción',
        help_text='Describe qué información incluye este reporte'
    )
    
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name='📂 Categoría del Reporte'
    )
    
    frecuencia = models.CharField(
        max_length=20,
        choices=FRECUENCIA_CHOICES,
        default='bajo_demanda',
        verbose_name='⏰ ¿Con qué frecuencia se genera?'
    )
    
    # CONFIGURACIÓN SIMPLE
    automatico = models.BooleanField(
        default=False,
        verbose_name='🤖 ¿Generar automáticamente?',
        help_text='Si está activado, el reporte se generará según la frecuencia seleccionada'
    )
    
    requiere_parametros = models.BooleanField(
        default=False,
        verbose_name='🔧 ¿Requiere parámetros adicionales?',
        help_text='Indica si el usuario debe configurar parámetros específicos'
    )
    
    confidencial = models.BooleanField(
        default=False,
        verbose_name='🔒 ¿Es confidencial?',
        help_text='Solo usuarios autorizados podrán ver este reporte'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='✅ ¿Está activo?'
    )
    
    # FILTROS DISPONIBLES
    incluir_fecha_inicio = models.BooleanField(
        default=True,
        verbose_name='📅 ¿Permitir filtrar por fecha de inicio?'
    )
    
    incluir_fecha_fin = models.BooleanField(
        default=True,
        verbose_name='📅 ¿Permitir filtrar por fecha de fin?'
    )
    
    incluir_paciente = models.BooleanField(
        default=False,
        verbose_name='👤 ¿Permitir filtrar por paciente específico?'
    )
    
    incluir_medico = models.BooleanField(
        default=False,
        verbose_name='👨‍⚕️ ¿Permitir filtrar por médico?'
    )
    
    incluir_servicio = models.BooleanField(
        default=False,
        verbose_name='🏥 ¿Permitir filtrar por servicio médico?'
    )
    
    # PERMISOS DE ACCESO
    permitir_medico = models.BooleanField(
        default=True,
        verbose_name='👨‍⚕️ ¿Los médicos pueden generar este reporte?'
    )
    
    permitir_enfermero = models.BooleanField(
        default=False,
        verbose_name='👩‍⚕️ ¿Los enfermeros pueden generar este reporte?'
    )
    
    permitir_administrador = models.BooleanField(
        default=True,
        verbose_name='👔 ¿Los administradores pueden generar este reporte?'
    )
    
    permitir_director = models.BooleanField(
        default=True,
        verbose_name='🏢 ¿El director médico puede generar este reporte?'
    )
    
    # FORMATOS DISPONIBLES
    formato_pdf = models.BooleanField(
        default=True,
        verbose_name='📄 ¿Disponible en PDF?',
        help_text='Formato ideal para imprimir y compartir'
    )
    
    formato_excel = models.BooleanField(
        default=True,
        verbose_name='📊 ¿Disponible en Excel?',
        help_text='Formato ideal para análisis de datos'
    )
    
    formato_csv = models.BooleanField(
        default=False,
        verbose_name='📋 ¿Disponible en CSV?',
        help_text='Formato simple para importar en otros sistemas'
    )
    
    formato_json = models.BooleanField(
        default=False,
        verbose_name='⚙️ ¿Disponible en JSON?',
        help_text='Formato para integración con otros sistemas'
    )
    
    # CONFIGURACIÓN TÉCNICA (OPCIONAL)
    plantilla_sql = models.TextField(
        blank=True,
        verbose_name='⚙️ Consulta SQL personalizada (Solo para expertos)',
        help_text='Dejar vacío para usar la consulta predeterminada'
    )
    
    # CAMPOS COMPATIBLES CON VERSION ANTERIOR
    parametros_esquema = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Parámetros Esquema (Interno)',
        help_text='Estructura interna - no modificar manualmente'
    )
    
    roles_autorizados = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Roles Autorizados (Interno)',
        help_text='Lista interna - se calcula automáticamente'
    )
    
    campos_requeridos = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Campos Requeridos (Interno)',
        help_text='Lista interna - se calcula automáticamente'
    )
    
    formato_salida = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Formatos de Salida (Interno)',
        help_text='Lista interna - se calcula automáticamente'
    )
    
    # METADATOS
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tipos_reporte'
        ordering = ['categoria', 'nombre']
        verbose_name = 'Tipo de Reporte'
        verbose_name_plural = 'Tipos de Reporte'
    
    def save(self, *args, **kwargs):
        # Generar código automáticamente si está vacío
        if not self.codigo:
            import re
            codigo_base = re.sub(r'[^A-Za-z0-9]', '_', self.nombre.upper())[:20]
            self.codigo = f"RPT_{codigo_base}"
        
        # Actualizar campos JSON automáticamente
        self.roles_autorizados = self.get_roles_autorizados()
        self.formato_salida = self.get_formatos_disponibles()
        self.campos_requeridos = self.get_campos_requeridos()
        
        super().save(*args, **kwargs)
    
    def get_roles_autorizados(self):
        """Obtiene lista de roles autorizados"""
        roles = []
        if self.permitir_medico:
            roles.append('medico')
        if self.permitir_enfermero:
            roles.append('enfermero')
        if self.permitir_administrador:
            roles.append('administrador')
        if self.permitir_director:
            roles.append('director')
        return roles
    
    def get_formatos_disponibles(self):
        """Obtiene lista de formatos disponibles"""
        formatos = []
        if self.formato_pdf:
            formatos.append('pdf')
        if self.formato_excel:
            formatos.append('excel')
        if self.formato_csv:
            formatos.append('csv')
        if self.formato_json:
            formatos.append('json')
        return formatos
    
    def get_campos_requeridos(self):
        """Obtiene lista de campos requeridos"""
        campos = []
        if self.incluir_fecha_inicio:
            campos.append('fecha_inicio')
        if self.incluir_fecha_fin:
            campos.append('fecha_fin')
        if self.incluir_paciente:
            campos.append('filtro_paciente')
        if self.incluir_medico:
            campos.append('filtro_medico')
        if self.incluir_servicio:
            campos.append('filtro_servicio')
        return campos
    
    def get_roles_autorizados_display(self):
        roles = []
        if self.permitir_medico:
            roles.append('Médicos')
        if self.permitir_enfermero:
            roles.append('Enfermeros')
        if self.permitir_administrador:
            roles.append('Administradores')
        if self.permitir_director:
            roles.append('Director Médico')
        return ', '.join(roles) if roles else 'Sin acceso configurado'
    
    def get_formatos_disponibles_display(self):
        formatos = []
        if self.formato_pdf:
            formatos.append('PDF')
        if self.formato_excel:
            formatos.append('Excel')
        if self.formato_csv:
            formatos.append('CSV')
        if self.formato_json:
            formatos.append('JSON')
        return ', '.join(formatos) if formatos else 'Sin formatos configurados'
    
    def __str__(self):
        return f"{self.nombre}"


class ReporteGenerado(models.Model):
    """Registro de reportes generados - VERSION MEJORADA"""
    
    ESTADO_CHOICES = [
        ('pendiente', '⏳ Pendiente'),
        ('procesando', '⚙️ Procesando'),
        ('completado', '✅ Completado'),
        ('error', '❌ Error'),
        ('expirado', '⏰ Expirado'),
    ]
    
    FORMATO_CHOICES = [
        ('pdf', '📄 PDF'),
        ('excel', '📊 Excel'),
        ('csv', '📋 CSV'),
        ('json', '⚙️ JSON'),
    ]
    
    # INFORMACIÓN BÁSICA
    tipo_reporte = models.ForeignKey(
        TipoReporte,
        on_delete=models.CASCADE,
        verbose_name='📊 Tipo de Reporte'
    )
    
    usuario_solicitante = models.IntegerField(
        verbose_name='👤 Usuario que solicitó el reporte'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='📈 Estado del reporte'
    )
    
    formato = models.CharField(
        max_length=10,
        choices=FORMATO_CHOICES,
        default='pdf',
        verbose_name='📄 Formato de descarga'
    )
    
    # PARÁMETROS Y FILTROS
    parametros = models.JSONField(
        default=dict,
        verbose_name='Parámetros del Reporte (Interno)',
        help_text='Parámetros internos del reporte'
    )
    
    fecha_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name='📅 Fecha de inicio del período'
    )
    
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name='📅 Fecha de fin del período'
    )
    
    filtro_paciente = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='👤 Paciente específico (ID)'
    )
    
    filtro_medico = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='👨‍⚕️ Médico específico (ID)'
    )
    
    filtro_servicio = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='🏥 Servicio médico'
    )
    
    # FECHAS IMPORTANTES
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name='🕐 Fecha de solicitud'
    )
    
    fecha_procesamiento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='⚙️ Inicio de procesamiento'
    )
    
    fecha_completado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='✅ Fecha de completado'
    )
    
    fecha_expiracion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='⏰ Fecha de expiración'
    )
    
    # INFORMACIÓN DEL ARCHIVO
    ruta_archivo = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='📁 Ruta del archivo'
    )
    
    tamaño_archivo = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='📏 Tamaño del archivo (bytes)'
    )
    
    hash_archivo = models.CharField(
        max_length=128,
        blank=True,
        verbose_name='🔐 Hash de seguridad del archivo'
    )
    
    accesos_descarga = models.IntegerField(
        default=0,
        verbose_name='📥 Número de descargas'
    )
    
    # RESUMEN DE RESULTADOS
    total_registros = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='📊 Total de registros incluidos'
    )
    
    datos_resumen = models.JSONField(
        default=dict,
        verbose_name='Datos de Resumen (Interno)',
        help_text='Resumen interno de los datos'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='📝 Observaciones adicionales'
    )
    
    # MANEJO DE ERRORES
    mensaje_error = models.TextField(
        blank=True,
        verbose_name='❌ Mensaje de error'
    )
    
    tiempo_procesamiento = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='⏱️ Tiempo de procesamiento (segundos)'
    )
    
    class Meta:
        db_table = 'reportes_generados'
        ordering = ['-fecha_solicitud']
        verbose_name = 'Reporte Generado'
        verbose_name_plural = 'Reportes Generados'
    
    def save(self, *args, **kwargs):
        if not self.fecha_expiracion:
            self.fecha_expiracion = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def esta_expirado(self):
        return timezone.now() > self.fecha_expiracion if self.fecha_expiracion else False
    
    def get_tamaño_archivo_display(self):
        if self.tamaño_archivo:
            if self.tamaño_archivo > 1024 * 1024:
                return f"{self.tamaño_archivo / (1024 * 1024):.1f} MB"
            elif self.tamaño_archivo > 1024:
                return f"{self.tamaño_archivo / 1024:.1f} KB"
            else:
                return f"{self.tamaño_archivo} bytes"
        return "Tamaño no disponible"
    
    def get_tiempo_procesamiento_display(self):
        if self.tiempo_procesamiento:
            if self.tiempo_procesamiento > 60:
                minutos = self.tiempo_procesamiento // 60
                segundos = self.tiempo_procesamiento % 60
                return f"{minutos}m {segundos}s"
            else:
                return f"{self.tiempo_procesamiento}s"
        return "N/A"
    
    def __str__(self):
        return f"{self.tipo_reporte.nombre} - {self.fecha_solicitud.date()}"


class DashboardKPI(models.Model):
    """Indicadores clave de rendimiento - VERSION MEJORADA"""
    
    TIPO_KPI_CHOICES = [
        ('numero', '🔢 Número simple'),
        ('porcentaje', '📊 Porcentaje'),
        ('tendencia', '📈 Tendencia'),
        ('ratio', '⚖️ Proporción'),
        ('tiempo', '⏱️ Tiempo promedio'),
    ]
    
    CATEGORIA_KPI_CHOICES = [
        ('pacientes', '👥 Pacientes'),
        ('embarazos', '🤰 Embarazos'),
        ('controles', '🩺 Controles Prenatales'),
        ('partos', '👶 Partos'),
        ('calculadoras', '🧮 Calculadoras Médicas'),
        ('calidad', '⭐ Calidad de Atención'),
        ('seguridad', '🛡️ Seguridad'),
        ('productividad', '📈 Productividad'),
    ]
    
    FRECUENCIA_CHOICES = [
        ('tiempo_real', '⚡ Tiempo real'),
        ('cada_hora', '🕐 Cada hora'),
        ('diario', '📅 Diario'),
        ('semanal', '📆 Semanal'),
    ]
    
    # INFORMACIÓN BÁSICA
    nombre = models.CharField(
        max_length=200, 
        verbose_name='📊 Nombre del Indicador',
        help_text='Ej: Total de Pacientes Activos'
    )
    
    codigo = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='🏷️ Código único'
    )
    
    descripcion = models.TextField(
        verbose_name='📄 Descripción',
        help_text='Explica qué mide este indicador'
    )
    
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_KPI_CHOICES,
        verbose_name='📂 Categoría'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_KPI_CHOICES,
        verbose_name='📈 Tipo de indicador'
    )
    
    # CONFIGURACIÓN DEL CÁLCULO
    consulta_sql = models.TextField(
        verbose_name='⚙️ Consulta para calcular el valor',
        help_text='Query SQL que obtiene el valor del KPI'
    )
    
    parametros_calculo = models.JSONField(
        default=dict,
        verbose_name='Parámetros de Cálculo (Interno)',
        help_text='Parámetros internos de cálculo'
    )
    
    frecuencia_actualizacion = models.CharField(
        max_length=20,
        choices=FRECUENCIA_CHOICES,
        default='diario',
        verbose_name='🔄 ¿Con qué frecuencia se actualiza?'
    )
    
    # VALORES ACTUALES
    valor_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='📊 Valor actual'
    )
    
    valor_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='📉 Valor anterior'
    )
    
    # METAS Y UMBRALES
    meta_minima = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='🎯 Meta mínima aceptable'
    )
    
    meta_optima = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='🏆 Meta óptima'
    )
    
    unidad_medida = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='📏 Unidad de medida',
        help_text='Ej: pacientes, %, minutos, días'
    )
    
    # CONFIGURACIÓN VISUAL
    color_normal = models.CharField(
        max_length=7,
        default='#28a745',
        verbose_name='Color Normal'
    )
    
    color_advertencia = models.CharField(
        max_length=7,
        default='#ffc107',
        verbose_name='Color Advertencia'
    )
    
    color_critico = models.CharField(
        max_length=7,
        default='#dc3545',
        verbose_name='Color Crítico'
    )
    
    icono = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='🎨 Icono',
        help_text='Nombre del icono (opcional)'
    )
    
    orden_dashboard = models.IntegerField(
        default=0,
        verbose_name='📋 Orden en el dashboard'
    )
    
    # CONTROL DE ACCESO
    activo = models.BooleanField(
        default=True,
        verbose_name='✅ ¿Está activo?'
    )
    
    visible_medico = models.BooleanField(
        default=True,
        verbose_name='👨‍⚕️ ¿Visible para médicos?'
    )
    
    visible_administrador = models.BooleanField(
        default=True,
        verbose_name='👔 ¿Visible para administradores?'
    )
    
    visible_director = models.BooleanField(
        default=True,
        verbose_name='🏢 ¿Visible para director?'
    )
    
    # COMPATIBILIDAD CON VERSION ANTERIOR
    roles_autorizados = models.JSONField(
        default=list,
        verbose_name='Roles Autorizados (Interno)',
        help_text='Lista interna - se calcula automáticamente'
    )
    
    # METADATOS
    ultima_actualizacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_kpis'
        ordering = ['categoria', 'orden_dashboard']
        verbose_name = 'Indicador KPI'
        verbose_name_plural = 'Indicadores KPI Dashboard'
    
    def save(self, *args, **kwargs):
        # Actualizar roles autorizados automáticamente
        roles = []
        if self.visible_medico:
            roles.append('medico')
        if self.visible_administrador:
            roles.append('administrador')
        if self.visible_director:
            roles.append('director')
        self.roles_autorizados = roles
        
        super().save(*args, **kwargs)
    
    def calcular_tendencia(self):
        if self.valor_actual and self.valor_anterior:
            diferencia = float(self.valor_actual - self.valor_anterior)
            if diferencia > 0:
                return 'subiendo'
            elif diferencia < 0:
                return 'bajando'
            else:
                return 'estable'
        return 'sin_datos'
    
    def get_estado_color(self):
        if not self.valor_actual:
            return self.color_normal
        
        valor = float(self.valor_actual)
        if self.meta_minima and valor < float(self.meta_minima):
            return self.color_critico
        elif self.meta_optima and valor >= float(self.meta_optima):
            return self.color_normal
        else:
            return self.color_advertencia
    
    def get_estado_vs_meta(self):
        if not self.valor_actual:
            return 'sin_datos'
        
        valor = float(self.valor_actual)
        if self.meta_optima and valor >= float(self.meta_optima):
            return 'optimo'
        elif self.meta_minima and valor < float(self.meta_minima):
            return 'bajo_minimo'
        else:
            return 'en_progreso'
    
    def __str__(self):
        return f"{self.nombre}"


class AlertaMedica(models.Model):
    """Sistema de alertas médicas - VERSION MEJORADA"""
    
    TIPO_ALERTA_CHOICES = [
        ('valor_critico', '🚨 Valor crítico detectado'),
        ('seguimiento_vencido', '⏰ Seguimiento vencido'),
        ('medicamento_contraindicado', '💊 Medicamento contraindicado'),
        ('riesgo_alto', '⚠️ Riesgo alto detectado'),
        ('resultado_anormal', '📊 Resultado anormal'),
        ('cita_perdida', '📅 Cita perdida'),
        ('protocolo_incumplido', '📋 Protocolo no seguido'),
        ('auditoria', '🔍 Requiere auditoría'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', '🟢 Baja'),
        ('media', '🟡 Media'),
        ('alta', '🟠 Alta'),
        ('critica', '🔴 Crítica'),
        ('emergencia', '🚨 EMERGENCIA'),
    ]
    
    ESTADO_CHOICES = [
        ('activa', '🔴 Activa'),
        ('revisada', '🟡 Revisada'),
        ('resuelta', '🟢 Resuelta'),
        ('descartada', '⚫ Descartada'),
        ('escalada', '🟠 Escalada'),
    ]
    
    MODULOS_CHOICES = [
        ('pacientes', '👤 Módulo de Pacientes'),
        ('embarazos', '🤰 Módulo de Embarazos'),
        ('controles', '🩺 Controles Prenatales'),
        ('ecografias', '📻 Ecografías'),
        ('laboratorio', '🧪 Laboratorio'),
        ('calculadoras', '🧮 Calculadoras Médicas'),
        ('partos', '👶 Partos'),
        ('sistema', '⚙️ Sistema'),
    ]
    
    # INFORMACIÓN BÁSICA
    titulo = models.CharField(
        max_length=200, 
        verbose_name='📢 Título de la alerta'
    )
    
    descripcion = models.TextField(
        verbose_name='📄 Descripción detallada'
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_ALERTA_CHOICES,
        verbose_name='🏷️ Tipo de alerta'
    )
    
    prioridad = models.CharField(
        max_length=15,
        choices=PRIORIDAD_CHOICES,
        verbose_name='⚡ Prioridad'
    )
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='activa',
        verbose_name='📊 Estado actual'
    )
    
    # CONTEXTO MÉDICO
    paciente_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='👤 ID del Paciente'
    )
    
    embarazo_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='🤰 ID del Embarazo'
    )
    
    medico_responsable_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='👨‍⚕️ ID del Médico Responsable'
    )
    
    modulo_origen = models.CharField(
        max_length=50,
        choices=MODULOS_CHOICES,
        verbose_name='📂 Módulo de origen'
    )
    
    registro_origen_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='🔗 ID del registro relacionado'
    )
    
    # COMPATIBILIDAD CON VERSION ANTERIOR
    datos_contexto = models.JSONField(
        default=dict,
        verbose_name='Datos de Contexto (Interno)',
        help_text='Datos internos de contexto'
    )
    
    # VALORES DE LA ALERTA
    valor_actual = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='📊 Valor actual'
    )
    
    valor_umbral = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='⚠️ Valor umbral'
    )
    
    # RECOMENDACIONES
    accion_recomendada = models.TextField(
        verbose_name='💡 Acción recomendada'
    )
    
    protocolo_seguimiento = models.TextField(
        blank=True,
        verbose_name='📋 Protocolo de seguimiento'
    )
    
    # FECHAS IMPORTANTES
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='🕐 Fecha de creación'
    )
    
    fecha_vencimiento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='⏰ Fecha límite'
    )
    
    fecha_revision = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='👀 Fecha de revisión'
    )
    
    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='✅ Fecha de resolución'
    )
    
    # GESTIÓN Y SEGUIMIENTO
    usuario_revision_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='👤 Usuario que revisó'
    )
    
    usuario_resolucion_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='👤 Usuario que resolvió'
    )
    
    comentario_revision = models.TextField(
        blank=True,
        verbose_name='💬 Comentario de revisión'
    )
    
    comentario_resolucion = models.TextField(
        blank=True,
        verbose_name='💬 Comentario de resolución'
    )
    
    # NOTIFICACIONES
    notificacion_enviada = models.BooleanField(
        default=False,
        verbose_name='📧 ¿Notificación enviada?'
    )
    
    recordatorio_enviado = models.BooleanField(
        default=False,
        verbose_name='🔔 ¿Recordatorio enviado?'
    )
    
    # ESCALAMIENTO
    escalamiento_automatico = models.BooleanField(
        default=False,
        verbose_name='🆙 ¿Escalamiento automático?'
    )
    
    tiempo_escalamiento_horas = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='⏱️ Tiempo para escalamiento (horas)'
    )
    
    class Meta:
        db_table = 'alertas_medicas'
        ordering = ['-fecha_creacion', '-prioridad']
        verbose_name = 'Alerta Médica'
        verbose_name_plural = 'Alertas Médicas'
        indexes = [
            models.Index(fields=['estado', 'prioridad']),
            models.Index(fields=['paciente_id', 'estado']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def is_vencida(self):
        if not self.fecha_vencimiento:
            return False
        return timezone.now() > self.fecha_vencimiento
    
    def tiempo_transcurrido(self):
        if not self.fecha_creacion:
            return timedelta(0)
        return timezone.now() - self.fecha_creacion
    
    def get_color_prioridad(self):
        colores = {
            'baja': '#28a745',
            'media': '#ffc107',
            'alta': '#fd7e14',
            'critica': '#dc3545',
            'emergencia': '#6f42c1',
        }
        return colores.get(self.prioridad, '#6c757d')
    
    def __str__(self):
        return f"{self.titulo} - {self.get_prioridad_display()}"


class AuditoriaReporte(models.Model):
    """Registro de auditoría para reportes - VERSION MEJORADA"""
    
    ACCION_CHOICES = [
        ('generacion', '📄 Generación de reporte'),
        ('descarga', '📥 Descarga'),
        ('visualizacion', '👀 Visualización'),
        ('modificacion', '✏️ Modificación'),
        ('eliminacion', '🗑️ Eliminación'),
        ('compartir', '📤 Compartir'),
    ]
    
    # INFORMACIÓN BÁSICA
    reporte_generado = models.ForeignKey(
        ReporteGenerado,
        on_delete=models.CASCADE,
        verbose_name='📊 Reporte'
    )
    
    usuario_id = models.IntegerField(
        verbose_name='👤 Usuario'
    )
    
    accion = models.CharField(
        max_length=20,
        choices=ACCION_CHOICES,
        verbose_name='⚡ Acción realizada'
    )
    
    fecha_accion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='🕐 Fecha y hora'
    )
    
    # INFORMACIÓN TÉCNICA
    direccion_ip = models.GenericIPAddressField(
        verbose_name='🌐 Dirección IP'
    )
    
    user_agent = models.TextField(
        verbose_name='💻 Navegador/Dispositivo'
    )
    
    # COMPATIBILIDAD CON VERSION ANTERIOR
    detalles = models.JSONField(
        default=dict,
        verbose_name='Detalles de la Acción (Interno)',
        help_text='Detalles internos de la acción'
    )
    
    # CUMPLIMIENTO LEGAL
    cumple_ley_3871 = models.BooleanField(
        default=True,
        verbose_name='⚖️ ¿Cumple con la Ley 3871?'
    )
    
    justificacion_acceso = models.TextField(
        blank=True,
        verbose_name='📝 Justificación del acceso'
    )
    
    # DETALLES ADICIONALES
    observaciones = models.TextField(
        blank=True,
        verbose_name='📋 Observaciones'
    )
    
    class Meta:
        db_table = 'auditoria_reportes'
        ordering = ['-fecha_accion']
        verbose_name = 'Auditoría de Reporte'
        verbose_name_plural = 'Auditorías de Reportes'
    
    def __str__(self):
        return f"{self.get_accion_display()} - {self.reporte_generado.tipo_reporte.nombre}"