from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    CalculoClinico,
    EdadGestacional,
    IndiceMasaCorporal,
    GananciaPeso,
    PuntajeBishop,
    RiesgoPreeclampsia,
    DiabetesGestacional,
    IndiceLiquidoAmniotico,
    PesoFetal,
    PuntajeApgar,
    RMIOvario,
    RiesgoEndometrio,
    PresionArterialMedia,
    SuperficieCorporal,
)


# ============================================================================
# INLINES
# ============================================================================

class EdadGestacionalInline(admin.StackedInline):
    model = EdadGestacional
    extra = 0
    can_delete = False
    readonly_fields = ['fum', 'fecha_calculo', 'semanas', 'dias', 'fpp', 'trimestre']


class IMCInline(admin.StackedInline):
    model = IndiceMasaCorporal
    extra = 0
    can_delete = False
    readonly_fields = ['peso', 'altura', 'imc', 'clasificacion', 'ganancia_peso_recomendada_min', 'ganancia_peso_recomendada_max']


class GananciaPesoInline(admin.StackedInline):
    model = GananciaPeso
    extra = 0
    can_delete = False


class BishopInline(admin.StackedInline):
    model = PuntajeBishop
    extra = 0
    can_delete = False


class RiesgoPreeclampsiaInline(admin.StackedInline):
    model = RiesgoPreeclampsia
    extra = 0
    can_delete = False


class DiabetesGestacionalInline(admin.StackedInline):
    model = DiabetesGestacional
    extra = 0
    can_delete = False


class ILAInline(admin.StackedInline):
    model = IndiceLiquidoAmniotico
    extra = 0
    can_delete = False


class PesoFetalInline(admin.StackedInline):
    model = PesoFetal
    extra = 0
    can_delete = False


class ApgarInline(admin.StackedInline):
    model = PuntajeApgar
    extra = 0
    can_delete = False


class RMIOvarioInline(admin.StackedInline):
    model = RMIOvario
    extra = 0
    can_delete = False


class RiesgoEndometrioInline(admin.StackedInline):
    model = RiesgoEndometrio
    extra = 0
    can_delete = False


class PAMInline(admin.StackedInline):
    model = PresionArterialMedia
    extra = 0
    can_delete = False


class SuperficieCorporalInline(admin.StackedInline):
    model = SuperficieCorporal
    extra = 0
    can_delete = False


# ============================================================================
# ADMIN PRINCIPAL
# ============================================================================

@admin.register(CalculoClinico)
class CalculoClinicoAdmin(admin.ModelAdmin):
    """Administración principal de cálculos clínicos"""
    
    list_display = [
        'id',
        'tipo_calculo_badge',
        'paciente_link',
        'embarazo_link',
        'resultado_preview',
        'realizado_por_nombre',
        'fecha_calculo_formateada',
    ]
    
    list_filter = [
        'tipo_calculo',
        'fecha_calculo',
        'realizado_por',
    ]
    
    search_fields = [
        'paciente__nombre',
        'paciente__apellido_paterno',
        'paciente__id_clinico',
        'interpretacion',
    ]
    
    readonly_fields = [
        'tipo_calculo',
        'paciente',
        'embarazo',
        'control_prenatal',
        'parametros_entrada_formatted',
        'resultados_formatted',
        'interpretacion',
        'realizado_por',
        'fecha_calculo',
    ]
    
    date_hierarchy = 'fecha_calculo'
    
    fieldsets = (
        ('Información General', {
            'fields': ('tipo_calculo', 'paciente', 'embarazo', 'control_prenatal')
        }),
        ('Datos de Entrada', {
            'fields': ('parametros_entrada_formatted',),
            'classes': ('collapse',)
        }),
        ('Resultados', {
            'fields': ('resultados_formatted', 'interpretacion')
        }),
        ('Metadatos', {
            'fields': ('realizado_por', 'fecha_calculo', 'observaciones'),
            'classes': ('collapse',)
        }),
    )
    
    def get_inlines(self, request, obj):
        """Mostrar inline según tipo de cálculo"""
        if not obj:
            return []
        
        inlines_map = {
            'edad_gestacional': [EdadGestacionalInline],
            'imc': [IMCInline],
            'ganancia_peso': [GananciaPesoInline],
            'bishop': [BishopInline],
            'preeclampsia': [RiesgoPreeclampsiaInline],
            'diabetes_gestacional': [DiabetesGestacionalInline],
            'ila': [ILAInline],
            'peso_fetal': [PesoFetalInline],
            'apgar': [ApgarInline],
            'rmi_ovario': [RMIOvarioInline],
            'riesgo_endometrio': [RiesgoEndometrioInline],
            'pam': [PAMInline],
            'superficie_corporal': [SuperficieCorporalInline],
        }
        
        return inlines_map.get(obj.tipo_calculo, [])
    
    def tipo_calculo_badge(self, obj):
        """Badge visual por tipo de cálculo"""
        colors = {
            'edad_gestacional': '#3498db',
            'imc': '#2ecc71',
            'ganancia_peso': '#27ae60',
            'bishop': '#9b59b6',
            'preeclampsia': '#e74c3c',
            'diabetes_gestacional': '#e67e22',
            'ila': '#1abc9c',
            'peso_fetal': '#34495e',
            'apgar': '#16a085',
            'rmi_ovario': '#c0392b',
            'riesgo_endometrio': '#d35400',
            'pam': '#2980b9',
            'superficie_corporal': '#8e44ad',
        }
        
        icons = {
            'edad_gestacional': '📅',
            'imc': '⚖️',
            'ganancia_peso': '📊',
            'bishop': '🔍',
            'preeclampsia': '⚠️',
            'diabetes_gestacional': '🩺',
            'ila': '💧',
            'peso_fetal': '👶',
            'apgar': '💯',
            'rmi_ovario': '🔬',
            'riesgo_endometrio': '📋',
            'pam': '❤️',
            'superficie_corporal': '📐',
        }
        
        color = colors.get(obj.tipo_calculo, '#95a5a6')
        icon = icons.get(obj.tipo_calculo, '📊')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold; display: inline-block;">'
            '{} {}</span>',
            color,
            icon,
            obj.get_tipo_calculo_display()
        )
    tipo_calculo_badge.short_description = 'Tipo de Cálculo'
    
    def paciente_link(self, obj):
        """Link al paciente"""
        url = reverse('admin:pacientes_paciente_change', args=[obj.paciente.id])
        return format_html(
            '<a href="{}" style="font-weight: bold;">{}</a><br>'
            '<small style="color: #666;">{}</small>',
            url,
            obj.paciente.nombre_completo,
            obj.paciente.id_clinico
        )
    paciente_link.short_description = 'Paciente'
    
    def embarazo_link(self, obj):
        """Link al embarazo"""
        if obj.embarazo:
            url = reverse('admin:embarazos_embarazo_change', args=[obj.embarazo.id])
            return format_html(
                '<a href="{}">Ver Embarazo</a>',
                url
            )
        return format_html('<span style="color: #999;">-</span>')
    embarazo_link.short_description = 'Embarazo'
    
    def resultado_preview(self, obj):
        """Preview del resultado principal"""
        return format_html(
            '<div style="background: #f8f9fa; padding: 8px; border-radius: 4px; max-width: 300px;">'
            '<strong>{}</strong>'
            '</div>',
            obj.interpretacion[:100] + ('...' if len(obj.interpretacion) > 100 else '')
        )
    resultado_preview.short_description = 'Resultado'
    
    def realizado_por_nombre(self, obj):
        """Nombre del usuario que realizó el cálculo"""
        if obj.realizado_por:
            return f"{obj.realizado_por.nombre} {obj.realizado_por.apellido_paterno}"
        return format_html('<span style="color: #999;">Sistema</span>')
    realizado_por_nombre.short_description = 'Realizado Por'
    
    def fecha_calculo_formateada(self, obj):
        """Fecha formateada"""
        return obj.fecha_calculo.strftime('%d/%m/%Y %H:%M')
    fecha_calculo_formateada.short_description = 'Fecha'
    
    def parametros_entrada_formatted(self, obj):
        """Formato JSON bonito para parámetros"""
        return format_html(
            '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">{}</pre>',
            json.dumps(obj.parametros_entrada, indent=2, ensure_ascii=False)
        )
    parametros_entrada_formatted.short_description = 'Parámetros de Entrada'
    
    def resultados_formatted(self, obj):
        """Formato JSON bonito para resultados"""
        return format_html(
            '<pre style="background: #e8f5e9; padding: 10px; border-radius: 4px; overflow-x: auto;">{}</pre>',
            json.dumps(obj.resultados, indent=2, ensure_ascii=False)
        )
    resultados_formatted.short_description = 'Resultados'
    
    def has_add_permission(self, request):
        """No permitir agregar desde admin (solo vía API)"""
        return False


# ============================================================================
# ADMIN MODELOS ESPECÍFICOS (Solo lectura)
# ============================================================================

@admin.register(EdadGestacional)
class EdadGestacionalAdmin(admin.ModelAdmin):
    list_display = ['calculo_link', 'fum', 'edad_gestacional_texto', 'fpp', 'trimestre_badge', 'fecha_calculo']
    list_filter = ['trimestre', 'fecha_calculo']
    search_fields = ['calculo__paciente__nombre', 'calculo__paciente__apellido_paterno']
    readonly_fields = ['calculo', 'fum', 'fecha_calculo', 'semanas', 'dias', 'fpp', 'trimestre']
    
    def calculo_link(self, obj):
        url = reverse('admin:calculadoras_calculoclinico_change', args=[obj.calculo.id])
        return format_html('<a href="{}">Ver Cálculo #{}</a>', url, obj.calculo.id)
    calculo_link.short_description = 'Cálculo'
    
    def edad_gestacional_texto(self, obj):
        return f"{obj.semanas}s {obj.dias}d"
    edad_gestacional_texto.short_description = 'Edad Gestacional'
    
    def trimestre_badge(self, obj):
        colors = {1: '#3498db', 2: '#2ecc71', 3: '#e74c3c'}
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.trimestre, '#95a5a6'),
            f"{obj.trimestre}° Trimestre"
        )
    trimestre_badge.short_description = 'Trimestre'
    
    def has_add_permission(self, request):
        return False


@admin.register(IndiceMasaCorporal)
class IMCAdmin(admin.ModelAdmin):
    list_display = ['calculo_link', 'peso', 'altura', 'imc_badge', 'clasificacion_badge', 'ganancia_recomendada']
    list_filter = ['clasificacion']
    readonly_fields = ['calculo', 'peso', 'altura', 'imc', 'clasificacion', 'ganancia_peso_recomendada_min', 'ganancia_peso_recomendada_max']
    
    def calculo_link(self, obj):
        url = reverse('admin:calculadoras_calculoclinico_change', args=[obj.calculo.id])
        return format_html('<a href="{}">Ver Cálculo #{}</a>', url, obj.calculo.id)
    calculo_link.short_description = 'Cálculo'
    
    def imc_badge(self, obj):
        return format_html(
            '<strong style="font-size: 16px; color: #2c3e50;">{}</strong>',
            obj.imc
        )
    imc_badge.short_description = 'IMC'
    
    def clasificacion_badge(self, obj):
        colors = {
            'bajo_peso': '#e67e22',
            'normal': '#27ae60',
            'sobrepeso': '#f39c12',
            'obesidad_i': '#e74c3c',
            'obesidad_ii': '#c0392b',
            'obesidad_iii': '#8b0000',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.clasificacion, '#95a5a6'),
            obj.get_clasificacion_display()
        )
    clasificacion_badge.short_description = 'Clasificación'
    
    def ganancia_recomendada(self, obj):
        if obj.ganancia_peso_recomendada_min and obj.ganancia_peso_recomendada_max:
            return f"{obj.ganancia_peso_recomendada_min} - {obj.ganancia_peso_recomendada_max} kg"
        return '-'
    ganancia_recomendada.short_description = 'Ganancia Recomendada'
    
    def has_add_permission(self, request):
        return False


@admin.register(PuntajeBishop)
class BishopAdmin(admin.ModelAdmin):
    list_display = ['calculo_link', 'puntaje_badge', 'interpretacion_badge', 'dilatacion', 'borramiento']
    list_filter = ['puntaje_total']
    readonly_fields = ['calculo', 'dilatacion', 'borramiento', 'estacion', 'consistencia', 'posicion', 'puntaje_total', 'interpretacion']
    
    def calculo_link(self, obj):
        url = reverse('admin:calculadoras_calculoclinico_change', args=[obj.calculo.id])
        return format_html('<a href="{}">Ver Cálculo #{}</a>', url, obj.calculo.id)
    calculo_link.short_description = 'Cálculo'
    
    def puntaje_badge(self, obj):
        if obj.puntaje_total <= 4:
            color = '#e74c3c'
        elif obj.puntaje_total <= 6:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        return format_html(
            '<div style="text-align: center; background: {}; color: white; padding: 8px; border-radius: 50%; width: 50px; height: 50px; line-height: 34px; font-size: 20px; font-weight: bold;">{}</div>',
            color,
            obj.puntaje_total
        )
    puntaje_badge.short_description = 'Puntaje'
    
    def interpretacion_badge(self, obj):
        if obj.puntaje_total <= 4:
            color = '#e74c3c'
        elif obj.puntaje_total <= 6:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.interpretacion
        )
    interpretacion_badge.short_description = 'Interpretación'
    
    def has_add_permission(self, request):
        return False


@admin.register(RiesgoPreeclampsia)
class RiesgoPreeclampsiaAdmin(admin.ModelAdmin):
    list_display = ['calculo_link', 'nivel_riesgo_badge', 'edad', 'factores_riesgo_count', 'aspirina_badge']
    list_filter = ['nivel_riesgo', 'recomienda_aspirina']
    readonly_fields = [
        'calculo', 'edad', 'primiparidad', 'antecedente_preeclampsia', 'diabetes',
        'hipertension_cronica', 'obesidad', 'embarazo_multiple', 'enfermedad_renal',
        'enfermedad_autoinmune', 'nivel_riesgo', 'recomienda_aspirina', 'factores_riesgo_count'
    ]
    
    def calculo_link(self, obj):
        url = reverse('admin:calculadoras_calculoclinico_change', args=[obj.calculo.id])
        return format_html('<a href="{}">Ver Cálculo #{}</a>', url, obj.calculo.id)
    calculo_link.short_description = 'Cálculo'
    
    def nivel_riesgo_badge(self, obj):
        colors = {
            'bajo': '#27ae60',
            'moderado': '#f39c12',
            'alto': '#e74c3c',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.nivel_riesgo, '#95a5a6'),
            obj.get_nivel_riesgo_display()
        )
    nivel_riesgo_badge.short_description = 'Nivel de Riesgo'
    
    def aspirina_badge(self, obj):
        if obj.recomienda_aspirina:
            return format_html(
                '<span style="background: #3498db; color: white; padding: 3px 8px; border-radius: 3px;">💊 Sí</span>'
            )
        return format_html(
            '<span style="color: #999;">No</span>'
        )
    aspirina_badge.short_description = 'Aspirina'
    
    def has_add_permission(self, request):
        return False


@admin.register(PesoFetal)
class PesoFetalAdmin(admin.ModelAdmin):
    list_display = ['calculo_link', 'semanas_gestacion', 'peso_badge', 'percentil_badge', 'clasificacion_badge']
    list_filter = ['clasificacion', 'semanas_gestacion']
    readonly_fields = ['calculo', 'semanas_gestacion', 'dbp', 'cc', 'ca', 'lf', 'peso_estimado', 'percentil', 'clasificacion']
    
    def calculo_link(self, obj):
        url = reverse('admin:calculadoras_calculoclinico_change', args=[obj.calculo.id])
        return format_html('<a href="{}">Ver Cálculo #{}</a>', url, obj.calculo.id)
    calculo_link.short_description = 'Cálculo'
    
    def peso_badge(self, obj):
        return format_html(
            '<strong style="font-size: 18px; color: #2c3e50;">{} g</strong>',
            obj.peso_estimado
        )
    peso_badge.short_description = 'Peso Estimado'
    
    def percentil_badge(self, obj):
        if obj.percentil:
            if obj.percentil < 10:
                color = '#e74c3c'
            elif obj.percentil > 90:
                color = '#e67e22'
            else:
                color = '#27ae60'
            
            return format_html(
                '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 3px; font-weight: bold;">P{}</span>',
                color,
                obj.percentil
            )
        return '-'
    percentil_badge.short_description = 'Percentil'
    
    def clasificacion_badge(self, obj):
        colors = {
            'rciu': '#c0392b',
            'peg': '#e74c3c',
            'aeg': '#27ae60',
            'geg': '#f39c12',
            'macrosomia': '#e67e22',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.clasificacion, '#95a5a6'),
            obj.get_clasificacion_display()
        )
    clasificacion_badge.short_description = 'Clasificación'
    
    def has_add_permission(self, request):
        return False


@admin.register(PuntajeApgar)
class ApgarAdmin(admin.ModelAdmin):
    list_display = ['calculo_link', 'minuto_badge', 'puntaje_badge', 'interpretacion_badge']
    list_filter = ['minuto', 'interpretacion']
    readonly_fields = [
        'calculo', 'minuto', 'frecuencia_cardiaca', 'esfuerzo_respiratorio',
        'tono_muscular', 'irritabilidad_refleja', 'coloracion', 'puntaje_total', 'interpretacion'
    ]
    
    def calculo_link(self, obj):
        url = reverse('admin:calculadoras_calculoclinico_change', args=[obj.calculo.id])
        return format_html('<a href="{}">Ver Cálculo #{}</a>', url, obj.calculo.id)
    calculo_link.short_description = 'Cálculo'
    
    def minuto_badge(self, obj):
        return format_html(
            '<span style="background: #34495e; color: white; padding: 4px 10px; border-radius: 3px; font-weight: bold;">{} min</span>',
            obj.minuto
        )
    minuto_badge.short_description = 'Minuto'
    
    def puntaje_badge(self, obj):
        if obj.puntaje_total <= 3:
            color = '#c0392b'
        elif obj.puntaje_total <= 6:
            color = '#e67e22'
        else:
            color = '#27ae60'
        
        return format_html(
            '<div style="text-align: center; background: {}; color: white; padding: 8px; border-radius: 50%; width: 50px; height: 50px; line-height: 34px; font-size: 20px; font-weight: bold;">{}</div>',
            color,
            obj.puntaje_total
        )
    puntaje_badge.short_description = 'Puntaje'
    
    def interpretacion_badge(self, obj):
        colors = {
            'critico': '#c0392b',
            'depresion_moderada': '#e67e22',
            'normal': '#27ae60',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.interpretacion, '#95a5a6'),
            obj.get_interpretacion_display()
        )
    interpretacion_badge.short_description = 'Interpretación'
    
    def has_add_permission(self, request):
        return False


# Registrar los demás modelos de forma simple
for model in [GananciaPeso, DiabetesGestacional, IndiceLiquidoAmniotico, 
              RMIOvario, RiesgoEndometrio, PresionArterialMedia, SuperficieCorporal]:
    admin.site.register(model)