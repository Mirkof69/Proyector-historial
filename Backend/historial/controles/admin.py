# =============================================================================
# ADMINISTRACIÓN DE CONTROLES PRENATALES
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: controles
# Descripción: Configuración del panel de administración para controles prenatales.
#              Incluye filtros personalizados, alertas visuales, estadísticas.
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime
import csv

from .models import ControlPrenatal


# =============================================================================
# FILTROS PERSONALIZADOS
# =============================================================================

class AlertasListFilter(admin.SimpleListFilter):
    """
    Filtro personalizado para controles con alertas médicas.
    """
    title = 'Alertas Médicas'
    parameter_name = 'alertas'

    def lookups(self, request, model_admin):
        return (
            ('hipertension', 'Hipertensión (PA ≥ 140/90)'),
            ('hipertension_severa', 'Hipertensión Severa (PA ≥ 160/110)'),
            ('fcf_anormal', 'FCF Anormal'),
            ('proteinuria', 'Proteinuria Positiva'),
            ('edema_severo', 'Edema Severo'),
            ('movimientos_ausentes', 'Movimientos Ausentes'),
            ('todas', 'Cualquier Alerta'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'hipertension':
            return queryset.filter(
                Q(presion_arterial_sistolica__gte=140) |
                Q(presion_arterial_diastolica__gte=90)
            )
        elif self.value() == 'hipertension_severa':
            return queryset.filter(
                Q(presion_arterial_sistolica__gte=160) |
                Q(presion_arterial_diastolica__gte=110)
            )
        elif self.value() == 'fcf_anormal':
            return queryset.filter(
                Q(frecuencia_cardiaca_fetal__lt=110) |
                Q(frecuencia_cardiaca_fetal__gt=160)
            )
        elif self.value() == 'proteinuria':
            return queryset.filter(
                proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3']
            )
        elif self.value() == 'edema_severo':
            return queryset.filter(edema='severo')
        elif self.value() == 'movimientos_ausentes':
            return queryset.filter(movimientos_fetales='ausentes')
        elif self.value() == 'todas':
            return queryset.filter(
                Q(presion_arterial_sistolica__gte=140) |
                Q(presion_arterial_diastolica__gte=90) |
                Q(frecuencia_cardiaca_fetal__lt=110) |
                Q(frecuencia_cardiaca_fetal__gt=160) |
                Q(proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3']) |
                Q(edema='severo') |
                Q(movimientos_fetales='ausentes')
            ).distinct()


class TrimestreListFilter(admin.SimpleListFilter):
    """
    Filtro personalizado por trimestre de embarazo.
    """
    title = 'Trimestre'
    parameter_name = 'trimestre'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Primer Trimestre (≤ 13 sem)'),
            ('2', 'Segundo Trimestre (14-27 sem)'),
            ('3', 'Tercer Trimestre (> 27 sem)'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(semanas_gestacion__lte=13)
        elif self.value() == '2':
            return queryset.filter(semanas_gestacion__gt=13, semanas_gestacion__lte=27)
        elif self.value() == '3':
            return queryset.filter(semanas_gestacion__gt=27)


class IMCListFilter(admin.SimpleListFilter):
    """
    Filtro por clasificación de IMC.
    """
    title = 'IMC'
    parameter_name = 'imc'

    def lookups(self, request, model_admin):
        return (
            ('bajo', 'Bajo Peso (< 18.5)'),
            ('normal', 'Normal (18.5-24.9)'),
            ('sobrepeso', 'Sobrepeso (25-29.9)'),
            ('obesidad', 'Obesidad (≥ 30)'),
        )

    def queryset(self, request, queryset):
        # Este filtro puede ser lento en bases grandes
        if self.value() == 'bajo':
            ids = []
            for c in queryset:
                imc = c.calcular_imc()
                if imc and imc < 18.5:
                    ids.append(c.id)
            return queryset.filter(id__in=ids)
        elif self.value() == 'normal':
            ids = []
            for c in queryset:
                imc = c.calcular_imc()
                if imc and 18.5 <= imc < 25:
                    ids.append(c.id)
            return queryset.filter(id__in=ids)
        elif self.value() == 'sobrepeso':
            ids = []
            for c in queryset:
                imc = c.calcular_imc()
                if imc and 25 <= imc < 30:
                    ids.append(c.id)
            return queryset.filter(id__in=ids)
        elif self.value() == 'obesidad':
            ids = []
            for c in queryset:
                imc = c.calcular_imc()
                if imc and imc >= 30:
                    ids.append(c.id)
            return queryset.filter(id__in=ids)


# =============================================================================
# ADMIN PRINCIPAL DE CONTROLES PRENATALES
# =============================================================================

@admin.register(ControlPrenatal)
class ControlPrenatalAdmin(admin.ModelAdmin):
    """
    Configuración del administrador de controles prenatales.

    Características:
    - Vista detallada con alertas visuales
    - Filtros avanzados por alertas, trimestre, IMC
    - Acciones masivas de exportación
    - Búsqueda por paciente, embarazo
    - Visualización con colores según riesgo
    """

    # =========================================================================
    # CONFIGURACIÓN DE LISTADO
    # =========================================================================

    list_display = [
        'numero_control_badge',
        'fecha_control_display',
        'paciente_nombre',
        'edad_gestacional_display',
        'presion_arterial_display',
        'fcf_display',
        'peso_display',
        'alertas_badge',
        'medico_display',
    ]

    list_display_links = ['numero_control_badge', 'fecha_control_display']

    list_filter = [
        AlertasListFilter,
        TrimestreListFilter,
        IMCListFilter,
        'fecha_control',
        'presentacion_fetal',
        'edema',
        'proteinuria',
        'movimientos_fetales',
    ]

    search_fields = [
        'numero_control',
        'embarazo__paciente__nombres',
        'embarazo__paciente__apellidos',
        'embarazo__paciente__cedula_identidad',
        'medico__nombres',
        'medico__apellidos',
        'diagnostico',
        'observaciones',
    ]

    ordering = ['-fecha_control']

    list_per_page = 25

    date_hierarchy = 'fecha_control'

    # =========================================================================
    # CONFIGURACIÓN DE FORMULARIO
    # =========================================================================

    fieldsets = (
        ('Identificación del Control', {
            'fields': (
                'embarazo',
                'numero_control',
                'fecha_control',
            )
        }),
        ('Edad Gestacional', {
            'fields': (
                'semanas_gestacion',
                'dias_gestacion',
            )
        }),
        ('Mediciones Antropométricas', {
            'fields': (
                'peso_actual',
                'peso_pregestacional',
                'talla',
                'altura_uterina',
            ),
            'description': 'Peso en kg, talla y altura uterina en cm'
        }),
        ('Signos Vitales Maternos', {
            'fields': (
                'presion_arterial_sistolica',
                'presion_arterial_diastolica',
                'frecuencia_cardiaca',
                'temperatura',
            )
        }),
        ('Evaluación Fetal', {
            'fields': (
                'frecuencia_cardiaca_fetal',
                'presentacion_fetal',
                'movimientos_fetales',
            )
        }),
        ('Examen Físico', {
            'fields': (
                'edema',
                'proteinuria',
                'glucosa',
                'hemoglobina',
            ),
            'classes': ('collapse',)
        }),
        ('Evaluación Clínica', {
            'fields': (
                'sintomas_actuales',
                'diagnostico',
                'tratamiento_indicado',
                'examenes_solicitados',
            ),
            'classes': ('collapse',)
        }),
        ('Seguimiento', {
            'fields': (
                'proxima_cita',
                'observaciones',
            )
        }),
        ('Personal Médico', {
            'fields': (
                'medico',
                'enfermero',
            )
        }),
        ('Auditoría', {
            'fields': (
                'creado_por',
                'fecha_creacion',
                'modificado_por',
                'fecha_modificacion',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'fecha_creacion',
        'fecha_modificacion',
    ]

    # =========================================================================
    # ACCIONES MASIVAS
    # =========================================================================

    actions = [
        'exportar_csv',
        'marcar_alto_riesgo',
        'generar_reporte_alertas',
    ]

    @admin.action(description='Exportar a CSV')
    def exportar_csv(self, request, queryset):
        """Exporta los controles seleccionados a CSV."""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="controles_prenatales_{timezone.now().strftime("%Y%m%d")}.csv"'

        # BOM para Excel
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Número Control', 'Fecha', 'Paciente', 'Cédula',
            'Edad Gestacional', 'Peso', 'IMC', 'PA Sistólica', 'PA Diastólica',
            'FCF', 'Médico', 'Alertas'
        ])

        for control in queryset:
            paciente = control.embarazo.paciente if control.embarazo else None
            medico = control.medico
            imc = control.calcular_imc()

            # Detectar alertas
            tiene_alertas = (
                (control.presion_arterial_sistolica and control.presion_arterial_sistolica >= 140) or
                (control.presion_arterial_diastolica and control.presion_arterial_diastolica >= 90) or
                (control.frecuencia_cardiaca_fetal and (control.frecuencia_cardiaca_fetal < 110 or control.frecuencia_cardiaca_fetal > 160))
            )

            writer.writerow([
                control.id,
                control.numero_control,
                control.fecha_control.strftime('%d/%m/%Y') if control.fecha_control else '',
                f"{paciente.nombres} {paciente.apellidos}" if paciente else '',
                paciente.cedula_identidad if paciente else '',
                f"{control.semanas_gestacion}+{control.dias_gestacion or 0}" if control.semanas_gestacion else '',
                control.peso_actual or '',
                round(imc, 2) if imc else '',
                control.presion_arterial_sistolica or '',
                control.presion_arterial_diastolica or '',
                control.frecuencia_cardiaca_fetal or '',
                f"{medico.nombres} {medico.apellidos}" if medico and hasattr(medico, 'nombres') else '',
                'SÍ' if tiene_alertas else 'NO',
            ])

        self.message_user(request, f'{queryset.count()} control(es) exportado(s).')
        return response

    @admin.action(description='Identificar controles de ALTO RIESGO')
    def marcar_alto_riesgo(self, request, queryset):
        """Identifica y muestra controles de alto riesgo."""
        alto_riesgo = []

        for control in queryset:
            alertas = []

            if control.presion_arterial_sistolica and control.presion_arterial_sistolica >= 160:
                alertas.append('HTA SEVERA')
            if control.frecuencia_cardiaca_fetal and control.frecuencia_cardiaca_fetal < 110:
                alertas.append('BRADICARDIA')
            if control.proteinuria in ['positiva_2', 'positiva_3']:
                alertas.append('PROTEINURIA SEVERA')
            if control.movimientos_fetales == 'ausentes':
                alertas.append('SIN MOVIMIENTOS')

            if alertas:
                paciente = control.embarazo.paciente if control.embarazo else None
                alto_riesgo.append(
                    f"Control #{control.numero_control} - {paciente.nombres if paciente else 'Sin paciente'} - {', '.join(alertas)}"
                )

        if alto_riesgo:
            self.message_user(
                request,
                f'CONTROLES DE ALTO RIESGO ({len(alto_riesgo)}): ' + ' | '.join(alto_riesgo),
                level='warning'
            )
        else:
            self.message_user(request, 'No se encontraron controles de alto riesgo en la selección.')

    @admin.action(description='Generar reporte de alertas')
    def generar_reporte_alertas(self, request, queryset):
        """Genera un reporte estadístico de alertas."""
        total = queryset.count()

        hipertension = queryset.filter(
            Q(presion_arterial_sistolica__gte=140) |
            Q(presion_arterial_diastolica__gte=90)
        ).count()

        fcf_anormal = queryset.filter(
            Q(frecuencia_cardiaca_fetal__lt=110) |
            Q(frecuencia_cardiaca_fetal__gt=160)
        ).count()

        proteinuria = queryset.filter(
            proteinuria__in=['positiva_1', 'positiva_2', 'positiva_3']
        ).count()

        reporte = f"""
        REPORTE DE ALERTAS:
        - Total controles analizados: {total}
        - Con hipertensión: {hipertension} ({round(hipertension/total*100, 1)}%)
        - Con FCF anormal: {fcf_anormal} ({round(fcf_anormal/total*100, 1)}%)
        - Con proteinuria: {proteinuria} ({round(proteinuria/total*100, 1)}%)
        """

        self.message_user(request, reporte)

    # =========================================================================
    # MÉTODOS DE VISUALIZACIÓN PERSONALIZADOS
    # =========================================================================

    def numero_control_badge(self, obj):
        """Muestra el número de control con badge."""
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">#{}</span>',
            obj.numero_control
        )
    numero_control_badge.short_description = 'N° Control'

    def fecha_control_display(self, obj):
        """Muestra la fecha formateada."""
        if obj.fecha_control:
            return obj.fecha_control.strftime('%d/%m/%Y')
        return '-'
    fecha_control_display.short_description = 'Fecha'
    fecha_control_display.admin_order_field = 'fecha_control'

    def paciente_nombre(self, obj):
        """Muestra el nombre del paciente."""
        if obj.embarazo and obj.embarazo.paciente:
            paciente = obj.embarazo.paciente
            return f"{paciente.nombres} {paciente.apellidos}"
        return '-'
    paciente_nombre.short_description = 'Paciente'

    def edad_gestacional_display(self, obj):
        """Muestra la edad gestacional formateada."""
        if obj.semanas_gestacion is not None:
            dias = obj.dias_gestacion or 0
            semanas = obj.semanas_gestacion

            # Color según trimestre
            if semanas <= 13:
                color = '#3498db'  # Azul - Primer trimestre
            elif semanas <= 27:
                color = '#27ae60'  # Verde - Segundo trimestre
            else:
                color = '#f39c12'  # Naranja - Tercer trimestre

            return format_html(
                '<span style="color: {}; font-weight: bold;">{} + {} sem</span>',
                color, semanas, dias
            )
        return '-'
    edad_gestacional_display.short_description = 'EG'

    def presion_arterial_display(self, obj):
        """Muestra la PA con color según nivel de riesgo."""
        if obj.presion_arterial_sistolica and obj.presion_arterial_diastolica:
            pas = obj.presion_arterial_sistolica
            pad = obj.presion_arterial_diastolica

            # Determinar color
            if pas >= 160 or pad >= 110:
                color = '#e74c3c'  # Rojo - Severa
                texto = f'{pas}/{pad} ⚠'
            elif pas >= 140 or pad >= 90:
                color = '#f39c12'  # Naranja - Moderada
                texto = f'{pas}/{pad} ⚠'
            elif pas >= 120 or pad >= 80:
                color = '#f1c40f'  # Amarillo - Elevada
                texto = f'{pas}/{pad}'
            else:
                color = '#27ae60'  # Verde - Normal
                texto = f'{pas}/{pad}'

            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, texto
            )
        return '-'
    presion_arterial_display.short_description = 'PA (mmHg)'

    def fcf_display(self, obj):
        """Muestra FCF con color según normalidad."""
        if obj.frecuencia_cardiaca_fetal:
            fcf = obj.frecuencia_cardiaca_fetal

            if fcf < 110:
                color = '#e74c3c'  # Rojo - Bradicardia
                texto = f'{fcf} ⚠ BAJO'
            elif fcf > 160:
                color = '#f39c12'  # Naranja - Taquicardia
                texto = f'{fcf} ⚠ ALTO'
            elif fcf < 120 or fcf > 150:
                color = '#f1c40f'  # Amarillo - Límite
                texto = f'{fcf}'
            else:
                color = '#27ae60'  # Verde - Normal
                texto = f'{fcf}'

            return format_html(
                '<span style="color: {}; font-weight: bold;">{} lpm</span>',
                color, texto
            )
        return '-'
    fcf_display.short_description = 'FCF'

    def peso_display(self, obj):
        """Muestra peso e IMC."""
        if obj.peso_actual:
            imc = obj.calcular_imc()
            if imc:
                if imc < 18.5:
                    color = '#e74c3c'  # Rojo - Bajo peso
                elif imc >= 30:
                    color = '#f39c12'  # Naranja - Obesidad
                else:
                    color = '#27ae60'  # Verde - Normal

                return format_html(
                    '<span style="color: {};">{} kg<br/>IMC: {}</span>',
                    color,
                    round(float(obj.peso_actual), 1),
                    round(imc, 1)
                )
            return f"{round(float(obj.peso_actual), 1)} kg"
        return '-'
    peso_display.short_description = 'Peso / IMC'

    def alertas_badge(self, obj):
        """Muestra badge de alertas."""
        alertas = []

        if obj.presion_arterial_sistolica and obj.presion_arterial_sistolica >= 140:
            alertas.append('HTA')
        if obj.presion_arterial_diastolica and obj.presion_arterial_diastolica >= 90:
            alertas.append('HTA')
        if obj.frecuencia_cardiaca_fetal and (obj.frecuencia_cardiaca_fetal < 110 or obj.frecuencia_cardiaca_fetal > 160):
            alertas.append('FCF')
        if obj.proteinuria in ['positiva_1', 'positiva_2', 'positiva_3']:
            alertas.append('PROT')
        if obj.edema == 'severo':
            alertas.append('EDEMA')
        if obj.movimientos_fetales == 'ausentes':
            alertas.append('MOV')

        # Eliminar duplicados
        alertas = list(set(alertas))

        if alertas:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold; font-size: 10px;">{}</span>',
                ' | '.join(alertas)
            )
        else:
            return format_html(
                '<span style="color: #27ae60;">✓ Normal</span>'
            )
    alertas_badge.short_description = 'Alertas'

    def medico_display(self, obj):
        """Muestra el médico que realizó el control."""
        if obj.medico:
            if hasattr(obj.medico, 'nombres'):
                return f"{obj.medico.nombres} {obj.medico.apellidos}"
            return str(obj.medico)
        return '-'
    medico_display.short_description = 'Médico'
