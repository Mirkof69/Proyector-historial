from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django import forms
from django.core.cache import cache
from datetime import timedelta, datetime
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import (
    TipoReporte, ReporteGenerado, DashboardKPI,
    AlertaMedica, AuditoriaReporte
)


class OpcionesDinamicas:
    """Clase DEFINITIVA para manejar opciones dinámicas con cache y manejo robusto de errores"""
    
    @staticmethod
    def obtener_tipos_reporte():
        """Obtiene todos los tipos de reporte disponibles con cache"""
        cache_key = 'tipos_reporte_opciones'
        opciones = cache.get(cache_key)
        if opciones is None:
            try:
                from .models import TipoReporte
                opciones = list(TipoReporte.objects.filter(activo=True).values_list('id', 'nombre'))
                cache.set(cache_key, opciones, 300)  # 5 minutos
            except Exception:
                opciones = [(None, "Error al cargar tipos de reporte")]
        return opciones
    
    @staticmethod
    def obtener_pacientes_activos():
        """Obtiene pacientes activos con formato optimizado - COMPLETAMENTE CORREGIDO"""
        cache_key = 'pacientes_activos_opciones'
        opciones = cache.get(cache_key)
        if opciones is None:
            try:
                from pacientes.models import Paciente
                # USANDO CAMPOS CORRECTOS: apellido_paterno, apellido_materno
                pacientes = Paciente.objects.filter(activo=True).only(
                    'id', 'nombre', 'apellido_paterno', 'apellido_materno', 'id_clinico'
                )[:100]
                opciones = []
                for p in pacientes:
                    # Construir nombre completo con apellidos correctos
                    apellidos = p.apellido_paterno or ''
                    if hasattr(p, 'apellido_materno') and p.apellido_materno:
                        apellidos += f" {p.apellido_materno}"
                    nombre_completo = f"{p.nombre} {apellidos} ({p.id_clinico or f'ID: {p.id}'})"
                    opciones.append((p.id, nombre_completo))
                cache.set(cache_key, opciones, 600)  # 10 minutos
            except Exception as e:
                opciones = [(None, f"Error al cargar pacientes: {str(e)[:50]}")]
        return opciones
    
    @staticmethod
    def obtener_usuarios_medicos():
        """Obtiene usuarios médicos con cache - COMPLETAMENTE CORREGIDO"""
        cache_key = 'medicos_opciones'
        opciones = cache.get(cache_key)
        if opciones is None:
            try:
                from usuarios.models import Usuario
                # USANDO CAMPOS CORRECTOS: apellido_paterno, apellido_materno
                medicos = Usuario.objects.filter(rol='medico', activo=True).only(
                    'id', 'nombre', 'apellido_paterno', 'apellido_materno'
                )[:50]
                opciones = []
                for m in medicos:
                    # Construir nombre completo con apellidos correctos
                    apellidos = m.apellido_paterno or ''
                    if hasattr(m, 'apellido_materno') and m.apellido_materno:
                        apellidos += f" {m.apellido_materno}"
                    nombre_completo = f"Dr. {m.nombre} {apellidos} (ID: {m.id})"
                    opciones.append((m.id, nombre_completo))
                cache.set(cache_key, opciones, 600)
            except Exception as e:
                opciones = [(None, f"Error al cargar médicos: {str(e)[:50]}")]
        return opciones
    
    @staticmethod
    def obtener_embarazos_activos():
        """Obtiene embarazos activos con información de paciente"""
        cache_key = 'embarazos_activos_opciones'
        opciones = cache.get(cache_key)
        if opciones is None:
            try:
                from embarazos.models import Embarazo
                # Usar select_related para optimizar consulta
                embarazos = Embarazo.objects.filter(
                    estado='activo'
                ).select_related('paciente').only(
                    'id', 'numero_gesta', 'paciente__nombre', 'paciente__apellido_paterno'
                )[:50]
                opciones = []
                for e in embarazos:
                    try:
                        if hasattr(e, 'paciente') and e.paciente:
                            descripcion = f"Embarazo {e.numero_gesta} - {e.paciente.nombre} {e.paciente.apellido_paterno}"
                        else:
                            descripcion = f"Embarazo ID: {e.id} - Gesta: {e.numero_gesta}"
                        opciones.append((e.id, descripcion))
                    except AttributeError:
                        descripcion = f"Embarazo ID: {e.id}"
                        opciones.append((e.id, descripcion))
                cache.set(cache_key, opciones, 300)
            except Exception as e:
                opciones = [(None, f"Error al cargar embarazos: {str(e)[:50]}")]
        return opciones
    
    @staticmethod
    def obtener_servicios_medicos():
        """Lista completa de servicios médicos predefinidos"""
        return [
            ('ginecologia', 'Ginecología'),
            ('obstetricia', 'Obstetricia'),
            ('ecografia', 'Ecografía'),
            ('ecografia_3d', 'Ecografía 3D/4D'),
            ('laboratorio', 'Laboratorio'),
            ('consulta_externa', 'Consulta Externa'),
            ('emergencias', 'Emergencias'),
            ('cirugia', 'Cirugía Ginecológica'),
            ('cirugia_obstetrica', 'Cirugía Obstétrica'),
            ('medicina_materno_fetal', 'Medicina Materno-Fetal'),
            ('planificacion_familiar', 'Planificación Familiar'),
            ('menopausia', 'Consulta de Menopausia'),
            ('adolescentes', 'Ginecología de Adolescentes'),
            ('oncologia_ginecologica', 'Oncología Ginecológica'),
            ('fertilidad', 'Medicina Reproductiva'),
        ]
    
    @staticmethod
    def obtener_consultas_predefinidas():
        """Consultas SQL predefinidas optimizadas para KPIs del sistema médico"""
        return [
            # PACIENTES
            ('pacientes_total', 'Total de Pacientes Activos', 
             'SELECT COUNT(*) FROM pacientes WHERE activo = true'),
            ('pacientes_mes_actual', 'Pacientes Nuevos Este Mes', 
             "SELECT COUNT(*) FROM pacientes WHERE fecha_registro >= DATE_TRUNC('month', CURRENT_DATE) AND activo = true"),
            ('pacientes_semana', 'Pacientes Nuevos Esta Semana', 
             "SELECT COUNT(*) FROM pacientes WHERE fecha_registro >= DATE_TRUNC('week', CURRENT_DATE) AND activo = true"),
            
            # EMBARAZOS
            ('embarazos_activos', 'Embarazos Activos Totales', 
             "SELECT COUNT(*) FROM embarazos WHERE estado = 'activo'"),
            ('embarazos_alto_riesgo', 'Embarazos de Alto Riesgo', 
             "SELECT COUNT(*) FROM embarazos WHERE riesgo_embarazo = 'alto' AND estado = 'activo'"),
            ('embarazos_gemelar', 'Embarazos Gemelares Activos', 
             "SELECT COUNT(*) FROM embarazos WHERE tipo_embarazo = 'gemelar' AND estado = 'activo'"),
            
            # CONTROLES PRENATALES
            ('controles_mes', 'Controles Prenatales Este Mes', 
             "SELECT COUNT(*) FROM controles_prenatales WHERE fecha_control >= DATE_TRUNC('month', CURRENT_DATE)"),
            ('controles_pendientes', 'Controles Pendientes (>30 días)', 
             "SELECT COUNT(*) FROM embarazos e LEFT JOIN controles_prenatales cp ON e.id = cp.embarazo_id WHERE e.estado = 'activo' AND (cp.fecha_control IS NULL OR cp.fecha_control < CURRENT_DATE - INTERVAL '30 days')"),
            ('promedio_controles', 'Promedio de Controles por Embarazo', 
             "SELECT ROUND(AVG(control_count), 2) FROM (SELECT COUNT(*) as control_count FROM controles_prenatales GROUP BY embarazo_id) AS subquery"),
            
            # ECOGRAFÍAS
            ('ecografias_mes', 'Ecografías Realizadas Este Mes', 
             "SELECT COUNT(*) FROM ecografias WHERE fecha_ecografia >= DATE_TRUNC('month', CURRENT_DATE)"),
            ('ecografias_trimestre', 'Ecografías por Trimestre', 
             "SELECT COUNT(*) FROM ecografias WHERE trimestre_gestacional = 1 AND fecha_ecografia >= CURRENT_DATE - INTERVAL '3 months'"),
            
            # PARTOS
            ('partos_mes', 'Partos Este Mes', 
             "SELECT COUNT(*) FROM partos WHERE fecha_parto >= DATE_TRUNC('month', CURRENT_DATE)"),
            ('cesarea_rate', 'Tasa de Cesáreas (%)', 
             "SELECT ROUND((COUNT(CASE WHEN tipo_parto = 'cesarea' THEN 1 END)::float / COUNT(*) * 100), 2) FROM partos WHERE fecha_parto >= DATE_TRUNC('month', CURRENT_DATE)"),
            
            # CITAS Y AGENDA
            ('citas_pendientes', 'Citas Pendientes', 
             "SELECT COUNT(*) FROM citas WHERE estado = 'programada' AND fecha_cita >= CURRENT_DATE"),
            ('citas_hoy', 'Citas Programadas Hoy', 
             "SELECT COUNT(*) FROM citas WHERE DATE(fecha_cita) = CURRENT_DATE"),
            ('citas_perdidas', 'Citas Perdidas Este Mes', 
             "SELECT COUNT(*) FROM citas WHERE estado = 'perdida' AND fecha_cita >= DATE_TRUNC('month', CURRENT_DATE)"),
            
            # ALERTAS Y SEGURIDAD
            ('alertas_activas', 'Alertas Médicas Activas', 
             "SELECT COUNT(*) FROM alertas_medicas WHERE estado = 'activa'"),
            ('alertas_criticas', 'Alertas Críticas Pendientes', 
             "SELECT COUNT(*) FROM alertas_medicas WHERE prioridad = 'critica' AND estado = 'activa'"),
            
            # CALCULADORAS Y ANÁLISIS
            ('calculadoras_uso_mes', 'Uso de Calculadoras Este Mes', 
             "SELECT COUNT(*) FROM calculadoras_resultados WHERE fecha_calculo >= DATE_TRUNC('month', CURRENT_DATE)"),
            ('riesgo_preeclampsia', 'Pacientes con Riesgo Alto de Preeclampsia', 
             "SELECT COUNT(*) FROM calculadoras_resultados WHERE tipo_calculo = 'preeclampsia' AND resultado_riesgo = 'alto' AND fecha_calculo >= CURRENT_DATE - INTERVAL '30 days'"),
            
            # PRODUCTIVIDAD
            ('usuarios_activos', 'Usuarios Activos del Sistema', 
             "SELECT COUNT(*) FROM usuarios WHERE activo = true"),
            ('sesiones_mes', 'Sesiones Iniciadas Este Mes', 
             "SELECT COUNT(*) FROM auditoria_reportes WHERE accion = 'login' AND fecha_accion >= DATE_TRUNC('month', CURRENT_DATE)"),
        ]


# FORMS OPTIMIZADOS CON DROPDOWNS DINÁMICOS
class TipoReporteAdminForm(forms.ModelForm):
    """Form DEFINITIVO para TipoReporte con dropdowns dinámicos y validaciones"""
    
    consulta_predefinida = forms.ChoiceField(
        choices=[('', '--- Seleccionar consulta predefinida ---')],
        required=False,
        help_text="Selecciona una consulta predefinida para generar el reporte automáticamente",
        widget=forms.Select(attrs={
            'class': 'form-control consulta-selector',
            'onchange': 'actualizarConsultaSQL(this);'
        })
    )
    
    class Meta:
        model = TipoReporte
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'plantilla_sql': forms.Textarea(attrs={
                'rows': 6, 
                'class': 'form-control sql-editor',
                'placeholder': 'SELECT campo FROM tabla WHERE condicion = valor',
                'style': 'font-family: "Courier New", monospace;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar consultas predefinidas
        consultas = OpcionesDinamicas.obtener_consultas_predefinidas()
        consulta_choices = [('', '--- Seleccionar consulta predefinida ---')]
        
        for codigo, nombre, consulta in consultas:
            label = f"{nombre}: {consulta[:60]}{'...' if len(consulta) > 60 else ''}"
            consulta_choices.append((consulta, label))
        
        self.fields['consulta_predefinida'].choices = consulta_choices
        
        # Mejorar campos existentes
        for field_name in ['categoria', 'frecuencia']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'style': 'width: 100%;'
                })


class ReporteGeneradoAdminForm(forms.ModelForm):
    """Form DEFINITIVO para ReporteGenerado con selecciones dinámicas y validaciones"""
    
    tipo_reporte_selector = forms.ChoiceField(
        choices=[('', '--- Seleccionar tipo de reporte ---')],
        required=False,
        help_text="Selecciona el tipo de reporte a generar",
        widget=forms.Select(attrs={'class': 'form-control tipo-reporte-selector'})
    )
    
    paciente_selector = forms.ChoiceField(
        choices=[('', '--- Todos los pacientes ---')],
        required=False,
        help_text="Selecciona un paciente específico (opcional)",
        widget=forms.Select(attrs={'class': 'form-control paciente-selector'})
    )
    
    medico_selector = forms.ChoiceField(
        choices=[('', '--- Todos los médicos ---')],
        required=False,
        help_text="Selecciona un médico específico (opcional)",
        widget=forms.Select(attrs={'class': 'form-control medico-selector'})
    )
    
    servicio_selector = forms.ChoiceField(
        choices=[('', '--- Todos los servicios ---')],
        required=False,
        help_text="Selecciona un servicio específico (opcional)",
        widget=forms.Select(attrs={'class': 'form-control servicio-selector'})
    )
    
    class Meta:
        model = ReporteGenerado
        fields = '__all__'
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_expiracion': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar todas las opciones dinámicamente con manejo robusto de errores
        try:
            self.fields['tipo_reporte_selector'].choices = [
                ('', '--- Seleccionar tipo de reporte ---')
            ] + list(OpcionesDinamicas.obtener_tipos_reporte())
        except Exception:
            pass
        
        try:
            self.fields['paciente_selector'].choices = [
                ('', '--- Todos los pacientes ---')
            ] + list(OpcionesDinamicas.obtener_pacientes_activos())
        except Exception:
            pass
        
        try:
            self.fields['medico_selector'].choices = [
                ('', '--- Todos los médicos ---')
            ] + list(OpcionesDinamicas.obtener_usuarios_medicos())
        except Exception:
            pass
        
        self.fields['servicio_selector'].choices = [
            ('', '--- Todos los servicios ---')
        ] + list(OpcionesDinamicas.obtener_servicios_medicos())


class DashboardKPIAdminForm(forms.ModelForm):
    """Form DEFINITIVO para KPIs con consultas predefinidas y validaciones"""
    
    consulta_predefinida = forms.ChoiceField(
        choices=[('', '--- Usar consulta personalizada ---')],
        required=False,
        help_text="Selecciona una consulta predefinida o escribe una personalizada",
        widget=forms.Select(attrs={
            'class': 'form-control consulta-kpi-selector',
            'onchange': 'actualizarConsultaKPI(this);'
        })
    )
    
    class Meta:
        model = DashboardKPI
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'consulta_sql': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control sql-editor',
                'placeholder': 'SELECT COUNT(*) FROM tabla WHERE condicion = true',
                'style': 'font-family: "Courier New", monospace;'
            }),
            'valor_actual': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'valor_anterior': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'meta_minima': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'meta_optima': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'orden_dashboard': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar consultas predefinidas para KPIs
        consultas = OpcionesDinamicas.obtener_consultas_predefinidas()
        self.fields['consulta_predefinida'].choices = [
            ('', '--- Usar consulta personalizada ---')
        ] + [(consulta, f"{nombre}: {consulta[:45]}{'...' if len(consulta) > 45 else ''}") 
             for codigo, nombre, consulta in consultas]


class AlertaMedicaAdminForm(forms.ModelForm):
    """Form DEFINITIVO para AlertaMedica con selecciones dinámicas y validaciones"""
    
    paciente_selector = forms.ChoiceField(
        choices=[('', '--- Sin paciente asociado ---')],
        required=False,
        help_text="Selecciona el paciente relacionado con la alerta",
        widget=forms.Select(attrs={'class': 'form-control paciente-alerta-selector'})
    )
    
    embarazo_selector = forms.ChoiceField(
        choices=[('', '--- Sin embarazo asociado ---')],
        required=False,
        help_text="Selecciona el embarazo relacionado con la alerta",
        widget=forms.Select(attrs={'class': 'form-control embarazo-selector'})
    )
    
    medico_responsable_selector = forms.ChoiceField(
        choices=[('', '--- Sin médico asignado ---')],
        required=False,
        help_text="Selecciona el médico responsable de la alerta",
        widget=forms.Select(attrs={'class': 'form-control medico-alerta-selector'})
    )
    
    class Meta:
        model = AlertaMedica
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'accion_recomendada': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'protocolo_seguimiento': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'comentario_revision': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'comentario_resolucion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'fecha_vencimiento': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'valor_actual': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'valor_umbral': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'tiempo_escalamiento_horas': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar todas las opciones dinámicamente
        try:
            self.fields['paciente_selector'].choices = [
                ('', '--- Sin paciente asociado ---')
            ] + list(OpcionesDinamicas.obtener_pacientes_activos())
        except Exception:
            pass
        
        try:
            self.fields['embarazo_selector'].choices = [
                ('', '--- Sin embarazo asociado ---')
            ] + list(OpcionesDinamicas.obtener_embarazos_activos())
        except Exception:
            pass
        
        try:
            self.fields['medico_responsable_selector'].choices = [
                ('', '--- Sin médico asignado ---')
            ] + list(OpcionesDinamicas.obtener_usuarios_medicos())
        except Exception:
            pass


# ADMINISTRADORES DEFINITIVOS CON TODAS LAS CARACTERÍSTICAS
@admin.register(TipoReporte)
class TipoReporteAdmin(admin.ModelAdmin):
    form = TipoReporteAdminForm
    
    list_display = (
        'nombre',
        'get_codigo_display',
        'categoria_badge',
        'frecuencia_badge',
        'automatico_badge',
        'confidencial_badge',
        'activo_badge',
        'get_roles_count',
        'get_formatos_count',
        'fecha_creacion',
    )
    
    list_filter = (
        'categoria',
        'frecuencia',
        'automatico',
        'confidencial',
        'activo',
        'permitir_medico',
        'permitir_enfermero',
        'permitir_administrador',
        'fecha_creacion',
    )
    
    search_fields = ('nombre', 'codigo', 'descripcion')
    ordering = ('nombre', 'categoria')
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_modificacion',
        'get_codigo_auto_display',
        'get_resumen_configuracion',
        'get_sql_preview',
    )
    
    exclude = (
        'parametros_esquema',
        'roles_autorizados', 
        'campos_requeridos',
        'formato_salida',
    )
    
    fieldsets = (
        ('📝 Información Básica', {
            'fields': (
                ('nombre',),
                ('get_codigo_auto_display',),
                ('categoria', 'frecuencia'),
                ('descripcion',),
            )
        }),
        ('⚙️ Configuración de Generación', {
            'fields': (
                ('automatico', 'requiere_parametros'),
                ('confidencial', 'activo'),
            )
        }),
        ('🎯 Filtros Disponibles', {
            'fields': (
                ('incluir_fecha_inicio', 'incluir_fecha_fin'),
                ('incluir_paciente', 'incluir_medico'),
                ('incluir_servicio',),
            )
        }),
        ('👥 Control de Acceso', {
            'fields': (
                ('permitir_medico', 'permitir_enfermero'),
                ('permitir_administrador', 'permitir_director'),
            )
        }),
        ('📄 Formatos de Salida', {
            'fields': (
                ('formato_pdf', 'formato_excel'),
                ('formato_csv', 'formato_json'),
            )
        }),
        ('🔧 Configuración SQL', {
            'fields': (
                ('consulta_predefinida',),
                ('plantilla_sql',),
                ('get_sql_preview',),
            ),
            'classes': ('collapse',)
        }),
        ('📊 Resumen de Configuración', {
            'fields': (
                ('get_resumen_configuracion',),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).only(
            'id', 'nombre', 'codigo', 'categoria', 'frecuencia', 
            'automatico', 'confidencial', 'activo', 'fecha_creacion',
            'permitir_medico', 'permitir_enfermero', 'permitir_administrador',
            'formato_pdf', 'formato_excel', 'formato_csv', 'formato_json'
        )
    
    def get_codigo_display(self, obj):
        return obj.codigo or "🔄 Auto-generado"
    get_codigo_display.short_description = 'Código'
    
    def get_codigo_auto_display(self, obj):
        if obj.codigo:
            return f"🔖 {obj.codigo}"
        return "🔄 Se generará automáticamente al guardar"
    get_codigo_auto_display.short_description = 'Código Único'
    
    def categoria_badge(self, obj):
        colors = {
            'estadistico': '#007bff',
            'paciente': '#28a745',
            'institucional': '#ffc107',
            'regulatorio': '#dc3545',
            'clinico': '#17a2b8',
            'financiero': '#6f42c1',
        }
        color = colors.get(obj.categoria, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoría'
    
    def frecuencia_badge(self, obj):
        icons = {
            'diario': '📅',
            'semanal': '📆', 
            'mensual': '🗓️',
            'trimestral': '📊',
            'anual': '📈',
            'bajo_demanda': '🔄',
        }
        icon = icons.get(obj.frecuencia, '📋')
        
        return format_html(
            '<span style="font-size: 12px; color: #495057;"><strong>{} {}</strong></span>',
            icon, obj.get_frecuencia_display()
        )
    frecuencia_badge.short_description = 'Frecuencia'
    
    def automatico_badge(self, obj):
        if obj.automatico:
            return format_html(
                '<span style="color: #28a745; font-size: 12px; font-weight: bold;">🤖 Automático</span>'
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-size: 12px;">👤 Manual</span>'
            )
    automatico_badge.short_description = 'Generación'
    
    def confidencial_badge(self, obj):
        if obj.confidencial:
            return format_html(
                '<span style="color: #dc3545; font-size: 12px; font-weight: bold;">🔒 Confidencial</span>'
            )
        else:
            return format_html(
                '<span style="color: #28a745; font-size: 12px;">🔓 Público</span>'
            )
    confidencial_badge.short_description = 'Nivel'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="color: #28a745; font-size: 12px; font-weight: bold;">✅ Activo</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-size: 12px;">❌ Inactivo</span>'
            )
    activo_badge.short_description = 'Estado'
    
    def get_roles_count(self, obj):
        count = sum([
            obj.permitir_medico,
            obj.permitir_enfermero,
            obj.permitir_administrador,
            obj.permitir_director
        ])
        return format_html(
            '<span style="font-weight: bold; color: #007bff; font-size: 13px;">{} roles</span>',
            count
        )
    get_roles_count.short_description = 'Acceso'
    
    def get_formatos_count(self, obj):
        count = sum([
            obj.formato_pdf,
            obj.formato_excel,
            obj.formato_csv,
            obj.formato_json
        ])
        return format_html(
            '<span style="font-weight: bold; color: #28a745; font-size: 13px;">{} formatos</span>',
            count
        )
    get_formatos_count.short_description = 'Formatos'
    
    def get_sql_preview(self, obj):
        if obj.plantilla_sql:
            sql_preview = obj.plantilla_sql[:200]
            if len(obj.plantilla_sql) > 200:
                sql_preview += "..."
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 11px; max-height: 100px; overflow-y: auto;">{}</pre>',
                sql_preview
            )
        return "⚠️ Sin consulta SQL definida"
    get_sql_preview.short_description = 'Vista Previa SQL'
    
    def get_resumen_configuracion(self, obj):
        resumen = []
        
        # Filtros disponibles
        filtros = []
        if obj.incluir_fecha_inicio: filtros.append("📅 Fecha inicio")
        if obj.incluir_fecha_fin: filtros.append("📅 Fecha fin")
        if obj.incluir_paciente: filtros.append("👤 Paciente")
        if obj.incluir_medico: filtros.append("👨‍⚕️ Médico")
        if obj.incluir_servicio: filtros.append("🏥 Servicio")
        
        if filtros:
            resumen.append(f"🎯 Filtros disponibles: {', '.join(filtros)}")
        
        # Usuarios autorizados
        roles = []
        if obj.permitir_medico: roles.append("Médicos")
        if obj.permitir_enfermero: roles.append("Enfermeros")
        if obj.permitir_administrador: roles.append("Administradores")
        if obj.permitir_director: roles.append("Director")
        
        if roles:
            resumen.append(f"👥 Acceso autorizado: {', '.join(roles)}")
        
        # Formatos disponibles
        formatos = []
        if obj.formato_pdf: formatos.append("PDF")
        if obj.formato_excel: formatos.append("Excel")
        if obj.formato_csv: formatos.append("CSV")
        if obj.formato_json: formatos.append("JSON")
        
        if formatos:
            resumen.append(f"📄 Formatos de salida: {', '.join(formatos)}")
        
        # Configuración de generación
        config = []
        if obj.automatico: config.append("🤖 Generación automática")
        if obj.confidencial: config.append("🔒 Requiere autorización")
        if obj.requiere_parametros: config.append("⚙️ Requiere parámetros")
        
        if config:
            resumen.append(f"⚙️ Configuración: {', '.join(config)}")
        
        return "\n".join(resumen) if resumen else "⚠️ Sin configuración específica definida"
    get_resumen_configuracion.short_description = 'Resumen Completo'


@admin.register(ReporteGenerado)
class ReporteGeneradoAdmin(admin.ModelAdmin):
    form = ReporteGeneradoAdminForm
    
    list_display = (
        'get_reporte_info',
        'usuario_solicitante',
        'fecha_solicitud',
        'estado_badge',
        'formato_badge',
        'get_progreso_display',
        'accesos_descarga',
        'get_tamaño_display',
        'esta_expirado_badge',
    )
    
    list_filter = (
        'estado',
        'formato',
        'tipo_reporte__categoria',
        'fecha_solicitud',
        'fecha_completado',
    )
    
    search_fields = (
        'tipo_reporte__nombre',
        'usuario_solicitante',
        'filtro_paciente',
    )
    
    ordering = ('-fecha_solicitud',)
    
    readonly_fields = (
        'fecha_solicitud',
        'fecha_procesamiento',
        'fecha_completado',
        'tiempo_procesamiento',
        'tamaño_archivo',
        'hash_archivo',
        'get_progreso_detallado',
        'get_estadisticas_uso',
    )
    
    exclude = ('parametros', 'datos_resumen')
    
    fieldsets = (
        ('📊 Información del Reporte', {
            'fields': (
                ('tipo_reporte_selector', 'usuario_solicitante'),
                ('estado', 'formato'),
            )
        }),
        ('🎯 Filtros de Datos', {
            'fields': (
                ('fecha_inicio', 'fecha_fin'),
                ('paciente_selector', 'medico_selector'),
                ('servicio_selector',),
            )
        }),
        ('📄 Información del Archivo', {
            'fields': (
                ('ruta_archivo', 'tamaño_archivo'),
                ('hash_archivo', 'accesos_descarga'),
                ('fecha_expiracion',),
            )
        }),
        ('📈 Resultados y Progreso', {
            'fields': (
                ('total_registros',),
                ('observaciones',),
                ('get_progreso_detallado',),
            )
        }),
        ('📊 Estadísticas de Uso', {
            'fields': (
                ('get_estadisticas_uso',),
            ),
            'classes': ('collapse',)
        }),
        ('⚠️ Procesamiento y Errores', {
            'fields': (
                ('fecha_procesamiento', 'tiempo_procesamiento'),
                ('mensaje_error',),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tipo_reporte').only(
            'id', 'usuario_solicitante', 'fecha_solicitud', 'estado', 
            'formato', 'accesos_descarga', 'fecha_expiracion', 'tipo_reporte__nombre',
            'tipo_reporte__categoria', 'tiempo_procesamiento', 'total_registros',
            'tamaño_archivo'
        )
    
    def get_reporte_info(self, obj):
        categoria_color = {
            'estadistico': '#007bff',
            'paciente': '#28a745',
            'institucional': '#ffc107',
            'clinico': '#17a2b8',
        }.get(obj.tipo_reporte.categoria, '#6c757d')
        
        return format_html(
            '<div><strong style="font-size: 13px;">{}</strong><br/>'
            '<small style="color: {}; font-weight: bold;">📊 {}</small></div>',
            obj.tipo_reporte.nombre,
            categoria_color,
            obj.tipo_reporte.get_categoria_display()
        )
    get_reporte_info.short_description = 'Información del Reporte'
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': '#6c757d',
            'procesando': '#007bff',
            'completado': '#28a745',
            'error': '#dc3545',
            'expirado': '#fd7e14',
        }
        icons = {
            'pendiente': '⏳',
            'procesando': '⚙️',
            'completado': '✅',
            'error': '❌',
            'expirado': '⚠️',
        }
        
        color = colors.get(obj.estado, '#6c757d')
        icon = icons.get(obj.estado, '❓')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def formato_badge(self, obj):
        icons = {
            'pdf': '📄',
            'excel': '📊',
            'csv': '📋',
            'json': '⚙️',
        }
        colors = {
            'pdf': '#dc3545',
            'excel': '#28a745',
            'csv': '#ffc107',
            'json': '#17a2b8',
        }
        
        icon = icons.get(obj.formato, '📄')
        color = colors.get(obj.formato, '#6c757d')
        
        return format_html(
            '<span style="color: {}; font-size: 13px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_formato_display()
        )
    formato_badge.short_description = 'Formato'
    
    def get_progreso_display(self, obj):
        if obj.estado == 'completado':
            return format_html('<span style="color: #28a745; font-weight: bold; font-size: 12px;">✅ Completado</span>')
        elif obj.estado == 'procesando':
            return format_html('<span style="color: #007bff; font-weight: bold; font-size: 12px;">⚙️ Procesando</span>')
        elif obj.estado == 'error':
            return format_html('<span style="color: #dc3545; font-weight: bold; font-size: 12px;">❌ Error</span>')
        else:
            return format_html('<span style="color: #6c757d; font-weight: bold; font-size: 12px;">⏳ Pendiente</span>')
    get_progreso_display.short_description = 'Progreso'
    
    def get_tamaño_display(self, obj):
        if obj.tamaño_archivo:
            try:
                tamaño_bytes = int(obj.tamaño_archivo)
                if tamaño_bytes < 1024:
                    return f"{tamaño_bytes} B"
                elif tamaño_bytes < 1024 * 1024:
                    return f"{tamaño_bytes / 1024:.1f} KB"
                elif tamaño_bytes < 1024 * 1024 * 1024:
                    return f"{tamaño_bytes / (1024 * 1024):.1f} MB"
                else:
                    return f"{tamaño_bytes / (1024 * 1024 * 1024):.1f} GB"
            except (ValueError, TypeError):
                return str(obj.tamaño_archivo)
        return "---"
    get_tamaño_display.short_description = 'Tamaño'
    
    def esta_expirado_badge(self, obj):
        if obj.esta_expirado():
            return format_html('<span style="color: #dc3545; font-size: 12px; font-weight: bold;">⚠️ Expirado</span>')
        return format_html('<span style="color: #28a745; font-size: 12px; font-weight: bold;">✅ Vigente</span>')
    esta_expirado_badge.short_description = 'Vigencia'
    
    def get_progreso_detallado(self, obj):
        info = []
        
        if obj.total_registros:
            info.append(f"📊 {obj.total_registros:,} registros procesados")
        
        if obj.tiempo_procesamiento:
            try:
                segundos = int(obj.tiempo_procesamiento)
                if segundos < 60:
                    tiempo_str = f"{segundos} segundos"
                elif segundos < 3600:
                    minutos = segundos // 60
                    segundos_rest = segundos % 60
                    tiempo_str = f"{minutos}m {segundos_rest}s"
                else:
                    horas = segundos // 3600
                    minutos = (segundos % 3600) // 60
                    tiempo_str = f"{horas}h {minutos}m"
                info.append(f"⏱️ Tiempo de procesamiento: {tiempo_str}")
            except (ValueError, TypeError):
                info.append(f"⏱️ Tiempo: {obj.tiempo_procesamiento}")
        
        if obj.tamaño_archivo:
            info.append(f"📏 Tamaño: {self.get_tamaño_display(obj)}")
        
        if obj.accesos_descarga > 0:
            info.append(f"📥 {obj.accesos_descarga} descarga{'s' if obj.accesos_descarga != 1 else ''}")
        
        if obj.fecha_completado:
            info.append(f"🕐 Completado: {obj.fecha_completado.strftime('%d/%m/%Y %H:%M')}")
        
        return "\n".join(info) if info else "ℹ️ Sin información detallada disponible"
    get_progreso_detallado.short_description = 'Información Detallada'
    
    def get_estadisticas_uso(self, obj):
        estadisticas = []
        
        # Frecuencia de descarga
        if obj.accesos_descarga > 0 and obj.fecha_completado:
            dias_desde_completado = (timezone.now() - obj.fecha_completado).days
            if dias_desde_completado > 0:
                frecuencia = obj.accesos_descarga / dias_desde_completado
                estadisticas.append(f"📈 Frecuencia de descarga: {frecuencia:.2f} por día")
        
        # Eficiencia de procesamiento
        if obj.total_registros and obj.tiempo_procesamiento:
            try:
                registros_por_segundo = obj.total_registros / int(obj.tiempo_procesamiento)
                estadisticas.append(f"⚡ Velocidad: {registros_por_segundo:.2f} registros/segundo")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        # Estado del archivo
        if obj.fecha_expiracion:
            tiempo_restante = obj.fecha_expiracion - timezone.now()
            if tiempo_restante.total_seconds() > 0:
                dias_restantes = tiempo_restante.days
                estadisticas.append(f"⏰ Expira en: {dias_restantes} días")
            else:
                estadisticas.append("⚠️ Archivo expirado")
        
        return "\n".join(estadisticas) if estadisticas else "📊 Sin estadísticas de uso disponibles"
    get_estadisticas_uso.short_description = 'Estadísticas de Uso'


@admin.register(DashboardKPI)
class DashboardKPIAdmin(admin.ModelAdmin):
    form = DashboardKPIAdminForm
    
    list_display = (
        'nombre',
        'categoria_badge',
        'tipo_badge',
        'valor_actual_display',
        'tendencia_badge',
        'estado_vs_meta_badge',
        'ultima_actualizacion_display',
        'activo_badge',
    )
    
    list_filter = (
        'categoria',
        'tipo',
        'activo',
        'frecuencia_actualizacion',
        'visible_medico',
        'visible_administrador',
    )
    
    search_fields = ('nombre', 'codigo', 'descripcion')
    ordering = ('orden_dashboard', 'categoria', 'nombre')
    
    readonly_fields = (
        'ultima_actualizacion',
        'fecha_creacion',
        'fecha_modificacion',
        'get_rendimiento_kpi',
        'get_analisis_tendencia',
        'get_sql_preview',
    )
    
    exclude = ('parametros_calculo', 'roles_autorizados')
    
    fieldsets = (
        ('📊 Información Básica', {
            'fields': (
                ('nombre', 'codigo'),
                ('categoria', 'tipo'),
                ('descripcion',),
            )
        }),
        ('⚙️ Configuración del Cálculo', {
            'fields': (
                ('consulta_predefinida',),
                ('consulta_sql',),
                ('get_sql_preview',),
                ('frecuencia_actualizacion',),
            )
        }),
        ('📈 Valores y Metas', {
            'fields': (
                ('valor_actual', 'valor_anterior'),
                ('meta_minima', 'meta_optima'),
                ('unidad_medida',),
            )
        }),
        ('👀 Control de Visibilidad', {
            'fields': (
                ('activo',),
                ('visible_medico', 'visible_administrador'),
                ('visible_director',),
                ('orden_dashboard',),
            )
        }),
        ('🎨 Configuración Visual', {
            'fields': (
                ('icono',),
            )
        }),
        ('📊 Análisis y Rendimiento', {
            'fields': (
                ('get_rendimiento_kpi',),
                ('get_analisis_tendencia',),
                ('ultima_actualizacion',),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).only(
            'id', 'nombre', 'categoria', 'tipo', 'valor_actual', 
            'valor_anterior', 'activo', 'ultima_actualizacion', 'unidad_medida',
            'meta_minima', 'meta_optima', 'orden_dashboard'
        )
    
    def categoria_badge(self, obj):
        colors = {
            'pacientes': '#007bff',
            'embarazos': '#28a745',
            'controles': '#17a2b8',
            'partos': '#ffc107',
            'calculadoras': '#6f42c1',
            'calidad': '#fd7e14',
            'seguridad': '#dc3545',
            'productividad': '#20c997',
        }
        color = colors.get(obj.categoria, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoría'
    
    def tipo_badge(self, obj):
        icons = {
            'numero': '🔢',
            'porcentaje': '📊',
            'tendencia': '📈',
            'ratio': '⚖️',
            'tiempo': '⏱️',
        }
        icon = icons.get(obj.tipo, '📊')
        return f"{icon} {obj.get_tipo_display()}"
    tipo_badge.short_description = 'Tipo'
    
    def valor_actual_display(self, obj):
        """CORREGIDO: Método sin format_html anidado que causaba errores"""
        if obj.valor_actual is not None:
            try:
                valor = float(obj.valor_actual)
                unidad = obj.unidad_medida or ''
                
                if obj.tipo == 'porcentaje':
                    return f"{valor:.1f}%"
                elif obj.tipo == 'tiempo':
                    return f"{valor:.0f} {unidad}".strip()
                elif valor >= 1000:
                    return f"{valor:,.0f} {unidad}".strip()
                else:
                    return f"{valor:.2f} {unidad}".strip()
            except (ValueError, TypeError):
                return str(obj.valor_actual)
        return "Sin datos"
    valor_actual_display.short_description = 'Valor Actual'
    
    def tendencia_badge(self, obj):
        tendencia = obj.calcular_tendencia()
        
        if tendencia == 'subiendo':
            return format_html('<span style="color: #28a745; font-size: 14px; font-weight: bold;">📈 ↗️</span>')
        elif tendencia == 'bajando':
            return format_html('<span style="color: #dc3545; font-size: 14px; font-weight: bold;">📉 ↘️</span>')
        elif tendencia == 'estable':
            return format_html('<span style="color: #ffc107; font-size: 14px; font-weight: bold;">➡️ =</span>')
        else:
            return format_html('<span style="color: #6c757d; font-size: 14px;">❓ ?</span>')
    tendencia_badge.short_description = 'Tendencia'
    
    def estado_vs_meta_badge(self, obj):
        estado = obj.get_estado_vs_meta()
        
        if estado == 'optimo':
            return format_html('<span style="color: #28a745; font-size: 12px; font-weight: bold;">🎯 Óptimo</span>')
        elif estado == 'bajo_minimo':
            return format_html('<span style="color: #dc3545; font-size: 12px; font-weight: bold;">⚠️ Bajo</span>')
        elif estado == 'en_progreso':
            return format_html('<span style="color: #ffc107; font-size: 12px; font-weight: bold;">📊 Progreso</span>')
        else:
            return format_html('<span style="color: #6c757d; font-size: 12px;">❓ N/D</span>')
    estado_vs_meta_badge.short_description = 'vs Meta'
    
    def ultima_actualizacion_display(self, obj):
        """CORREGIDO: Método simplificado sin format_html anidado"""
        if obj.ultima_actualizacion:
            tiempo_transcurrido = timezone.now() - obj.ultima_actualizacion
            
            if tiempo_transcurrido.days > 7:
                return f"Hace {tiempo_transcurrido.days} días"
            elif tiempo_transcurrido.days > 0:
                return f"Hace {tiempo_transcurrido.days}d"
            elif tiempo_transcurrido.seconds > 3600:
                horas = tiempo_transcurrido.seconds // 3600
                return f"Hace {horas}h"
            else:
                minutos = tiempo_transcurrido.seconds // 60
                return f"Hace {minutos}m"
        return "Nunca actualizado"
    ultima_actualizacion_display.short_description = 'Actualizado'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: #28a745; font-size: 12px; font-weight: bold;">✅ Activo</span>')
        else:
            return format_html('<span style="color: #dc3545; font-size: 12px; font-weight: bold;">❌ Inactivo</span>')
    activo_badge.short_description = 'Estado'
    
    def get_sql_preview(self, obj):
        if obj.consulta_sql:
            sql_preview = obj.consulta_sql[:200]
            if len(obj.consulta_sql) > 200:
                sql_preview += "..."
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 11px; max-height: 100px; overflow-y: auto; font-family: \'Courier New\', monospace;">{}</pre>',
                sql_preview
            )
        return "⚠️ Sin consulta SQL definida"
    get_sql_preview.short_description = 'Vista Previa SQL'
    
    def get_rendimiento_kpi(self, obj):
        info = []
        
        tendencia = obj.calcular_tendencia()
        estado = obj.get_estado_vs_meta()
        
        info.append(f"🔄 Tendencia actual: {tendencia.upper()}")
        info.append(f"🎯 Estado vs meta: {estado.upper()}")
        
        # Calcular cumplimiento de meta
        if obj.valor_actual and obj.meta_optima:
            try:
                porcentaje_meta = (float(obj.valor_actual) / float(obj.meta_optima)) * 100
                info.append(f"📊 Cumplimiento meta óptima: {porcentaje_meta:.1f}%")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        if obj.valor_actual and obj.meta_minima:
            try:
                porcentaje_minimo = (float(obj.valor_actual) / float(obj.meta_minima)) * 100
                info.append(f"📊 Cumplimiento meta mínima: {porcentaje_minimo:.1f}%")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        # Variación respecto al valor anterior
        if obj.valor_actual and obj.valor_anterior:
            try:
                variacion = float(obj.valor_actual) - float(obj.valor_anterior)
                porcentaje_variacion = (variacion / float(obj.valor_anterior)) * 100
                signo = "+" if variacion > 0 else ""
                info.append(f"📈 Variación: {signo}{variacion:.2f} ({signo}{porcentaje_variacion:.1f}%)")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        # Información de visibilidad
        visibilidad = []
        if obj.visible_medico: visibilidad.append("Médicos")
        if obj.visible_administrador: visibilidad.append("Administradores")
        if obj.visible_director: visibilidad.append("Director")
        
        if visibilidad:
            info.append(f"👀 Visible para: {', '.join(visibilidad)}")
        
        # Orden en dashboard
        if obj.orden_dashboard:
            info.append(f"📌 Posición en dashboard: {obj.orden_dashboard}")
        
        return "\n".join(info) if info else "ℹ️ Sin información de rendimiento disponible"
    get_rendimiento_kpi.short_description = 'Información de Rendimiento'
    
    def get_analisis_tendencia(self, obj):
        analisis = []
        
        if obj.valor_actual and obj.valor_anterior:
            try:
                actual = float(obj.valor_actual)
                anterior = float(obj.valor_anterior)
                
                if actual > anterior:
                    diferencia = actual - anterior
                    porcentaje = (diferencia / anterior) * 100
                    analisis.append(f"📈 Incremento de {diferencia:.2f} ({porcentaje:.1f}%)")
                elif actual < anterior:
                    diferencia = anterior - actual
                    porcentaje = (diferencia / anterior) * 100
                    analisis.append(f"📉 Disminución de {diferencia:.2f} ({porcentaje:.1f}%)")
                else:
                    analisis.append("➡️ Valor estable (sin cambios)")
                
                # Evaluación de la tendencia
                if porcentaje > 20:
                    analisis.append("⚠️ Cambio significativo (>20%)")
                elif porcentaje > 10:
                    analisis.append("📊 Cambio moderado (10-20%)")
                elif porcentaje > 0:
                    analisis.append("📊 Cambio leve (<10%)")
                
            except (ValueError, TypeError, ZeroDivisionError):
                analisis.append("❓ No se puede calcular tendencia")
        else:
            analisis.append("📊 Insuficientes datos para análisis de tendencia")
        
        # Recomendaciones basadas en el estado
        if obj.valor_actual and obj.meta_optima:
            try:
                cumplimiento = (float(obj.valor_actual) / float(obj.meta_optima)) * 100
                if cumplimiento < 50:
                    analisis.append("🚨 Recomendación: Requiere atención inmediata")
                elif cumplimiento < 80:
                    analisis.append("⚠️ Recomendación: Necesita mejoras")
                elif cumplimiento >= 100:
                    analisis.append("✅ Recomendación: Mantener rendimiento actual")
                else:
                    analisis.append("📊 Recomendación: Buen progreso, continuar esfuerzos")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        return "\n".join(analisis) if analisis else "📊 Sin suficientes datos para análisis"
    get_analisis_tendencia.short_description = 'Análisis de Tendencia'


@admin.register(AlertaMedica)
class AlertaMedicaAdmin(admin.ModelAdmin):
    form = AlertaMedicaAdminForm
    
    list_display = (
        'titulo',
        'tipo_badge',
        'prioridad_badge',
        'estado_badge',
        'get_contexto_medico',
        'fecha_creacion',
        'tiempo_transcurrido_display',
        'get_escalamiento_info',
    )
    
    list_filter = (
        'tipo',
        'prioridad',
        'estado',
        'modulo_origen',
        'fecha_creacion',
        'escalamiento_automatico',
    )
    
    search_fields = ('titulo', 'descripcion', 'paciente_id', 'medico_responsable_id')
    ordering = ('-fecha_creacion', 'prioridad')
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_revision',
        'fecha_resolucion',
        'get_tiempo_vida_alerta',
        'get_estado_urgencia',
        'get_historial_cambios',
    )
    
    exclude = ('datos_contexto',)
    
    fieldsets = (
        ('🚨 Información de la Alerta', {
            'fields': (
                ('titulo', 'tipo'),
                ('prioridad', 'estado'),
                ('descripcion',),
            )
        }),
        ('🏥 Contexto Médico', {
            'fields': (
                ('paciente_selector', 'embarazo_selector'),
                ('medico_responsable_selector',),
                ('modulo_origen', 'registro_origen_id'),
            )
        }),
        ('📊 Valores Críticos', {
            'fields': (
                ('valor_actual', 'valor_umbral'),
                ('accion_recomendada',),
                ('protocolo_seguimiento',),
            )
        }),
        ('📅 Gestión Temporal', {
            'fields': (
                ('fecha_vencimiento',),
                ('escalamiento_automatico', 'tiempo_escalamiento_horas'),
                ('get_tiempo_vida_alerta', 'get_estado_urgencia'),
            )
        }),
        ('👥 Seguimiento y Resolución', {
            'fields': (
                ('usuario_revision_id', 'usuario_resolucion_id'),
                ('comentario_revision',),
                ('comentario_resolucion',),
            )
        }),
        ('📊 Historial de la Alerta', {
            'fields': (
                ('get_historial_cambios',),
            ),
            'classes': ('collapse',)
        }),
        ('🔔 Notificaciones', {
            'fields': (
                ('notificacion_enviada', 'recordatorio_enviado'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).only(
            'id', 'titulo', 'tipo', 'prioridad', 'estado', 'paciente_id',
            'medico_responsable_id', 'fecha_creacion', 'escalamiento_automatico',
            'tiempo_escalamiento_horas', 'fecha_vencimiento'
        )
    
    def tipo_badge(self, obj):
        colors = {
            'valor_critico': '#dc3545',
            'seguimiento_vencido': '#ffc107',
            'medicamento_contraindicado': '#fd7e14',
            'riesgo_alto': '#e83e8c',
            'resultado_anormal': '#6f42c1',
            'cita_perdida': '#20c997',
            'protocolo_incumplido': '#495057',
            'auditoria': '#17a2b8',
        }
        color = colors.get(obj.tipo, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def prioridad_badge(self, obj):
        colors = {
            'baja': '#28a745',
            'media': '#ffc107',
            'alta': '#fd7e14',
            'critica': '#dc3545',
            'emergencia': '#6f42c1',
        }
        icons = {
            'baja': '🟢',
            'media': '🟡',
            'alta': '🟠',
            'critica': '🔴',
            'emergencia': '🚨',
        }
        
        color = colors.get(obj.prioridad, '#6c757d')
        icon = icons.get(obj.prioridad, '⚪')
        
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 12px;">{} {}</span>',
            color, icon, obj.get_prioridad_display()
        )
    prioridad_badge.short_description = 'Prioridad'
    
    def estado_badge(self, obj):
        colors = {
            'activa': '#dc3545',
            'revisada': '#ffc107',
            'resuelta': '#28a745',
            'descartada': '#6c757d',
            'escalada': '#fd7e14',
        }
        color = colors.get(obj.estado, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def get_contexto_medico(self, obj):
        info = []
        if obj.paciente_id:
            info.append(f"👤 Paciente: {obj.paciente_id}")
        if obj.medico_responsable_id:
            info.append(f"👨‍⚕️ Médico: {obj.medico_responsable_id}")
        
        return format_html(
            '<div style="font-size: 11px; line-height: 1.4;">{}</div>',
            '<br/>'.join(info) if info else 'Sin contexto asociado'
        )
    get_contexto_medico.short_description = 'Contexto Médico'
    
    def tiempo_transcurrido_display(self, obj):
        """CORREGIDO: Método simplificado sin format_html anidado"""
        if not obj.fecha_creacion:
            return "Sin fecha"
        
        tiempo = timezone.now() - obj.fecha_creacion
        
        if tiempo.days > 1:
            return f"{tiempo.days} días"
        elif tiempo.seconds > 3600:
            horas = tiempo.seconds // 3600
            return f"{horas} horas"
        else:
            minutos = tiempo.seconds // 60
            return f"{minutos} min"
    tiempo_transcurrido_display.short_description = 'Tiempo'
    
    def get_escalamiento_info(self, obj):
        if obj.escalamiento_automatico and obj.tiempo_escalamiento_horas:
            return format_html(
                '<span style="color: #fd7e14; font-size: 11px; font-weight: bold;">🆙 Auto ({} hrs)</span>',
                obj.tiempo_escalamiento_horas
            )
        return format_html('<span style="color: #6c757d; font-size: 11px;">⏸️ Manual</span>')
    get_escalamiento_info.short_description = 'Escalamiento'
    
    def get_tiempo_vida_alerta(self, obj):
        if not obj.fecha_creacion:
            return "⚠️ Alerta sin fecha de creación"
        
        tiempo_vida = timezone.now() - obj.fecha_creacion
        info = []
        
        info.append(f"🕐 Creada: {obj.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
        info.append(f"⏱️ Tiempo transcurrido: {tiempo_vida}")
        
        if obj.fecha_vencimiento:
            if obj.is_vencida():
                tiempo_vencida = timezone.now() - obj.fecha_vencimiento
                info.append(f"⚠️ Vencida hace: {tiempo_vencida}")
            else:
                tiempo_restante = obj.fecha_vencimiento - timezone.now()
                info.append(f"⏰ Vence en: {tiempo_restante}")
        else:
            info.append("📅 Sin fecha de vencimiento establecida")
        
        # Información de escalamiento
        if obj.escalamiento_automatico and obj.tiempo_escalamiento_horas:
            tiempo_escalamiento = obj.fecha_creacion + timedelta(hours=obj.tiempo_escalamiento_horas)
            if timezone.now() > tiempo_escalamiento:
                tiempo_excedido = timezone.now() - tiempo_escalamiento
                info.append(f"🚨 Debe escalar (excedido por: {tiempo_excedido})")
            else:
                tiempo_hasta_escalamiento = tiempo_escalamiento - timezone.now()
                info.append(f"⏳ Escalamiento en: {tiempo_hasta_escalamiento}")
        
        return "\n".join(info)
    get_tiempo_vida_alerta.short_description = 'Cronología Completa'
    
    def get_estado_urgencia(self, obj):
        urgencia = []
        
        # Evaluar prioridad
        if obj.prioridad == 'emergencia':
            urgencia.append("🚨 EMERGENCIA MÉDICA")
        elif obj.prioridad == 'critica':
            urgencia.append("🔴 CRÍTICA - Requiere atención inmediata")
        elif obj.prioridad == 'alta':
            urgencia.append("🟠 ALTA - Requiere pronta atención")
        elif obj.prioridad == 'media':
            urgencia.append("🟡 MEDIA - Seguimiento normal")
        else:
            urgencia.append("🟢 BAJA - Sin urgencia")
        
        # Evaluar vencimiento
        if obj.is_vencida():
            urgencia.append("⚠️ ALERTA VENCIDA")
        
        # Evaluar escalamiento
        if obj.escalamiento_automatico and obj.tiempo_escalamiento_horas:
            tiempo_escalamiento = obj.fecha_creacion + timedelta(hours=obj.tiempo_escalamiento_horas)
            if timezone.now() > tiempo_escalamiento:
                urgencia.append("🆙 DEBE ESCALARSE INMEDIATAMENTE")
        
        # Evaluar estado
        if obj.estado == 'activa':
            urgencia.append("🔄 ALERTA ACTIVA - Requiere acción")
        elif obj.estado == 'resuelta':
            urgencia.append("✅ RESUELTA - Ninguna acción necesaria")
        elif obj.estado == 'descartada':
            urgencia.append("❌ DESCARTADA - Sin seguimiento")
        
        return "\n".join(urgencia) if urgencia else "📊 Estado normal"
    get_estado_urgencia.short_description = 'Evaluación de Urgencia'
    
    def get_historial_cambios(self, obj):
        historial = []
        
        historial.append(f"📅 Creada: {obj.fecha_creacion.strftime('%d/%m/%Y %H:%M') if obj.fecha_creacion else 'No disponible'}")
        
        if obj.fecha_revision:
            historial.append(f"👁️ Revisada: {obj.fecha_revision.strftime('%d/%m/%Y %H:%M')}")
            if obj.usuario_revision_id:
                historial.append(f"   👤 Por usuario: {obj.usuario_revision_id}")
        
        if obj.fecha_resolucion:
            historial.append(f"✅ Resuelta: {obj.fecha_resolucion.strftime('%d/%m/%Y %H:%M')}")
            if obj.usuario_resolucion_id:
                historial.append(f"   👤 Por usuario: {obj.usuario_resolucion_id}")
        
        # Calcular tiempo de resolución
        if obj.fecha_creacion and obj.fecha_resolucion:
            tiempo_resolucion = obj.fecha_resolucion - obj.fecha_creacion
            historial.append(f"⏱️ Tiempo total de resolución: {tiempo_resolucion}")
        
        # Estado de notificaciones
        estados_notif = []
        if obj.notificacion_enviada:
            estados_notif.append("📧 Notificación enviada")
        if obj.recordatorio_enviado:
            estados_notif.append("🔔 Recordatorio enviado")
        
        if estados_notif:
            historial.append("📬 Notificaciones:")
            historial.extend([f"   {estado}" for estado in estados_notif])
        
        return "\n".join(historial) if historial else "📊 Sin historial disponible"
    get_historial_cambios.short_description = 'Historial de Cambios'


@admin.register(AuditoriaReporte)
class AuditoriaReporteAdmin(admin.ModelAdmin):
    list_display = (
        'get_reporte_info',
        'accion_badge',
        'usuario_id',
        'fecha_accion',
        'get_ubicacion_acceso',
        'cumple_ley_badge',
    )
    
    list_filter = (
        'accion',
        'fecha_accion',
        'cumple_ley_3871',
        'reporte_generado__tipo_reporte__categoria',
    )
    
    search_fields = (
        'usuario_id',
        'direccion_ip',
        'reporte_generado__tipo_reporte__nombre',
    )
    
    ordering = ('-fecha_accion',)
    readonly_fields = ('fecha_accion', 'get_analisis_cumplimiento')
    exclude = ('detalles',)
    
    fieldsets = (
        ('📋 Información de la Auditoría', {
            'fields': (
                ('reporte_generado', 'accion'),
                ('usuario_id', 'fecha_accion'),
            )
        }),
        ('💻 Información Técnica de Acceso', {
            'fields': (
                ('direccion_ip',),
                ('user_agent',),
            )
        }),
        ('⚖️ Cumplimiento Legal (Ley 3871)', {
            'fields': (
                ('cumple_ley_3871',),
                ('justificacion_acceso',),
                ('observaciones',),
                ('get_analisis_cumplimiento',),
            )
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('reporte_generado__tipo_reporte').only(
            'id', 'accion', 'usuario_id', 'fecha_accion', 'direccion_ip', 
            'cumple_ley_3871', 'reporte_generado__tipo_reporte__nombre'
        )
    
    def get_reporte_info(self, obj):
        return format_html(
            '<div><strong style="font-size: 12px;">{}</strong><br/>'
            '<small style="color: #6c757d;">📊 {}</small></div>',
            obj.reporte_generado.tipo_reporte.nombre[:30],
            obj.reporte_generado.tipo_reporte.categoria
        )
    get_reporte_info.short_description = 'Reporte Auditado'
    
    def accion_badge(self, obj):
        colors = {
            'generacion': '#007bff',
            'descarga': '#28a745',
            'visualizacion': '#17a2b8',
            'modificacion': '#ffc107',
            'eliminacion': '#dc3545',
            'compartir': '#6f42c1',
        }
        icons = {
            'generacion': '🔧',
            'descarga': '📥',
            'visualizacion': '👁️',
            'modificacion': '✏️',
            'eliminacion': '🗑️',
            'compartir': '📤',
        }
        
        color = colors.get(obj.accion, '#6c757d')
        icon = icons.get(obj.accion, '❓')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_accion_display()
        )
    accion_badge.short_description = 'Acción Realizada'
    
    def get_ubicacion_acceso(self, obj):
        return format_html(
            '<div style="font-size: 11px;">'
            '<strong>🌐 IP:</strong> {}<br/>'
            '<small style="color: #6c757d;">🕐 {}</small>'
            '</div>',
            obj.direccion_ip or 'No registrada',
            obj.fecha_accion.strftime('%d/%m/%Y %H:%M:%S') if obj.fecha_accion else 'Sin fecha'
        )
    get_ubicacion_acceso.short_description = 'Acceso'
    
    def cumple_ley_badge(self, obj):
        if obj.cumple_ley_3871:
            return format_html(
                '<span style="color: #28a745; font-size: 12px; font-weight: bold;">✅ Cumple Ley 3871</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-size: 12px; font-weight: bold;">⚠️ Incumplimiento</span>'
            )
    cumple_ley_badge.short_description = 'Cumplimiento Legal'
    
    def get_analisis_cumplimiento(self, obj):
        analisis = []
        
        # Estado de cumplimiento principal
        if obj.cumple_ley_3871:
            analisis.append("✅ CUMPLE con los requisitos de la Ley 3871")
        else:
            analisis.append("⚠️ NO CUMPLE con los requisitos de la Ley 3871")
        
        # Análisis de justificación
        if obj.justificacion_acceso:
            analisis.append(f"📝 Justificación proporcionada: {len(obj.justificacion_acceso)} caracteres")
            if len(obj.justificacion_acceso) < 20:
                analisis.append("⚠️ Justificación muy breve - Considerar ampliación")
        else:
            analisis.append("❌ Sin justificación de acceso registrada")
        
        # Análisis de la acción
        if obj.accion == 'descarga':
            analisis.append("📥 Descarga de reporte - Verificar necesidad médica")
        elif obj.accion == 'visualizacion':
            analisis.append("👁️ Visualización de datos - Acceso de consulta")
        elif obj.accion == 'modificacion':
            analisis.append("✏️ Modificación de datos - Requiere justificación detallada")
        elif obj.accion == 'eliminacion':
            analisis.append("🗑️ Eliminación de datos - ACCIÓN CRÍTICA")
        
        # Análisis temporal
        if obj.fecha_accion:
            hora = obj.fecha_accion.hour
            if hora < 6 or hora > 22:
                analisis.append("🌙 Acceso fuera de horario laboral - Revisar justificación")
            
            # Verificar si es fin de semana
            if obj.fecha_accion.weekday() >= 5:  # Sábado=5, Domingo=6
                analisis.append("📅 Acceso en fin de semana - Verificar emergencia médica")
        
        # Recomendaciones
        recomendaciones = []
        if not obj.cumple_ley_3871:
            recomendaciones.append("🔍 Revisar y completar justificación")
            recomendaciones.append("📚 Capacitación en Ley 3871 recomendada")
        
        if obj.accion in ['modificacion', 'eliminacion']:
            recomendaciones.append("👥 Considerar aprobación de supervisor")
        
        if recomendaciones:
            analisis.append("\n📋 RECOMENDACIONES:")
            analisis.extend([f"   {rec}" for rec in recomendaciones])
        
        return "\n".join(analisis)
    get_analisis_cumplimiento.short_description = 'Análisis Detallado de Cumplimiento'


# CONFIGURACIÓN GLOBAL DEL ADMINISTRADOR
admin.site.site_header = "🏥 Sistema de Historias Clínicas Gineco-Obstétricas - Fetal Medical"
admin.site.site_title = "🩺 Reportes Médicos Inteligentes"
admin.site.index_title = "📊 Panel de Administración - Reportes y Analíticas Médicas Avanzadas"
admin.site.empty_value_display = '(Sin datos)'

# Configuración de performance y cache
admin.AdminSite.enable_nav_sidebar = True

# JavaScript personalizado para mejorar la interfaz
class Media:
    css = {
        'all': ('admin/css/reportes_admin.css',)
    }
    js = ('admin/js/reportes_admin.js',)

# Aplicar media a todas las clases de admin
for admin_class in [TipoReporteAdmin, ReporteGeneradoAdmin, DashboardKPIAdmin, AlertaMedicaAdmin, AuditoriaReporteAdmin]:
    admin_class.Media = Media