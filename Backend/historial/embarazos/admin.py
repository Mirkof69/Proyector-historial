"""
===========================================
MÓDULO: ADMIN DE EMBARAZOS
===========================================
Descripción:
    Configuración del panel de administración de Django para el módulo de embarazos.
    Proporciona una interfaz gráfica completa para gestión de embarazos.

Funcionalidades:
    - Listado de embarazos con filtros y búsqueda
    - Creación y edición de embarazos
    - Acciones en masa (finalizar, marcar pérdida, cambiar riesgo)
    - Campos de solo lectura para auditoría
    - Organización en fieldsets
    - Badges de colores para estado y riesgo
    - Estadísticas en lista

Acceso:
    URL: http://localhost:8000/admin/embarazos/embarazo/
    Requiere: Usuario con is_staff=True y is_superuser=True

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from datetime import date
from .models import Embarazo


# ===========================================
# CONFIGURACIÓN DEL ADMIN DE EMBARAZOS
# ===========================================
@admin.register(Embarazo)
class EmbarazoAdmin(admin.ModelAdmin):
    """
    CLASE: Configuración del ModelAdmin para Embarazo

    Funcionamiento:
        Define cómo se muestran y gestionan los embarazos en el panel de admin
        Proporciona filtros, búsqueda, acciones en masa y organización de campos

    Características principales:
        - Lista optimizada con columnas clave y cálculos
        - Filtros por estado, tipo, riesgo
        - Búsqueda por paciente
        - Formulario organizado en secciones
        - Acciones en masa personalizadas
        - Badges de colores para mejor visualización
    """

    # ===========================================
    # CONFIGURACIÓN DE LA LISTA (list_display)
    # ===========================================
    """
    list_display: Columnas que se muestran en la lista de embarazos

    Funcionamiento:
        Define qué campos o métodos se muestran como columnas en la tabla
        Permite ordenar por estos campos haciendo clic en el encabezado
    """
    list_display = [
        'id',                          # ID del embarazo
        'paciente_info',               # Paciente (método personalizado)
        'numero_gesta',                # Número de gesta
        'semanas_gestacion_display',   # Semanas de gestación (método)
        'fecha_probable_parto',        # FPP
        'tipo_embarazo_badge',         # Tipo con badge (método)
        'riesgo_embarazo_badge',       # Riesgo con badge (método)
        'estado_badge',                # Estado con badge (método)
        'fecha_registro',              # Fecha de registro
    ]

    # ===========================================
    # CAMPOS PARA ENLACES (list_display_links)
    # ===========================================
    """
    list_display_links: Columnas que funcionan como enlaces al detalle

    Funcionamiento:
        Al hacer clic en estos campos, redirige al formulario de edición
    """
    list_display_links = ['id', 'paciente_info']

    # ===========================================
    # FILTROS LATERALES (list_filter)
    # ===========================================
    """
    list_filter: Filtros disponibles en la barra lateral

    Funcionamiento:
        Crea filtros interactivos para buscar embarazos rápidamente
        Los usuarios pueden combinar múltiples filtros
    """
    list_filter = [
        'estado',                  # Filtrar por estado
        'riesgo_embarazo',         # Filtrar por riesgo
        'tipo_embarazo',           # Filtrar por tipo
        'fecha_registro',          # Filtrar por fecha de registro
        'fecha_probable_parto',    # Filtrar por FPP
    ]

    # ===========================================
    # BÚSQUEDA (search_fields)
    # ===========================================
    """
    search_fields: Campos en los que se puede buscar

    Funcionamiento:
        Permite buscar embarazos escribiendo en el cuadro de búsqueda
        La búsqueda es case-insensitive y busca coincidencias parciales
    """
    search_fields = [
        'paciente__id_clinico',        # Buscar por ID clínico
        'paciente__nombre',            # Buscar por nombre
        'paciente__apellido_paterno',  # Buscar por apellido paterno
        'paciente__apellido_materno',  # Buscar por apellido materno
        'numero_gesta',                # Buscar por número de gesta
    ]

    # ===========================================
    # ORDENAMIENTO (ordering)
    # ===========================================
    """
    ordering: Orden por defecto de la lista

    Funcionamiento:
        Define el orden inicial de los embarazos en la lista
        El signo - indica orden descendente
    """
    ordering = ['-fecha_registro']  # Más recientes primero

    # ===========================================
    # PAGINACIÓN (list_per_page)
    # ===========================================
    """
    list_per_page: Cantidad de registros por página

    Funcionamiento:
        Divide la lista en páginas para mejor rendimiento
    """
    list_per_page = 25

    # ===========================================
    # CAMPOS DE SOLO LECTURA (readonly_fields)
    # ===========================================
    """
    readonly_fields: Campos que no se pueden editar

    Funcionamiento:
        Estos campos se muestran pero no se pueden modificar
        Útil para datos de auditoría y campos autogenerados
    """
    readonly_fields = [
        'id',                      # ID autogenerado
        'uuid',                    # UUID inmutable
        'fecha_registro',          # Timestamp automático
        'calculos_obstetricos',    # Cálculos (método)
    ]

    # ===========================================
    # ORGANIZACIÓN EN SECCIONES (fieldsets)
    # ===========================================
    """
    fieldsets: Organización de campos en secciones

    Funcionamiento:
        Agrupa campos relacionados en secciones colapsables
        Mejora la UX al editar embarazos con muchos campos
    """
    fieldsets = (
        # Sección: Información básica
        ('Información Básica', {
            'fields': (
                'id',
                'uuid',
                'paciente',
            ),
            'description': 'Identificadores y paciente del embarazo'
        }),

        # Sección: Datos obstétricos
        ('Datos Obstétricos', {
            'fields': (
                'numero_gesta',
                'fecha_ultima_menstruacion',
                'fecha_probable_parto',
            ),
            'description': 'Información fundamental del embarazo'
        }),

        # Sección: Clasificación
        ('Clasificación del Embarazo', {
            'fields': (
                'tipo_embarazo',
                'riesgo_embarazo',
                'estado',
            ),
            'description': 'Tipo, riesgo y estado actual'
        }),

        # Sección: Información adicional
        ('Información Adicional', {
            'fields': (
                'medico_responsable',
                'notas',
            ),
            'classes': ('collapse',),  # Inicialmente colapsado
            'description': 'Notas y médico responsable'
        }),

        # Sección: Cálculos obstétricos
        ('Cálculos Obstétricos', {
            'fields': (
                'calculos_obstetricos',
            ),
            'classes': ('collapse',),  # Inicialmente colapsado
            'description': 'Cálculos automáticos del embarazo'
        }),

        # Sección: Auditoría
        ('Auditoría', {
            'fields': (
                'fecha_registro',
            ),
            'classes': ('collapse',),  # Inicialmente colapsado
            'description': 'Información de registro'
        }),
    )

    # ===========================================
    # ACCIONES EN MASA (actions)
    # ===========================================
    """
    actions: Acciones que se pueden aplicar a múltiples embarazos

    Funcionamiento:
        Permiten realizar operaciones sobre embarazos seleccionados
        Aparecen en el dropdown de acciones en la lista
    """
    actions = [
        'finalizar_embarazos',
        'marcar_perdidas',
        'cambiar_a_bajo_riesgo',
        'cambiar_a_medio_riesgo',
        'cambiar_a_alto_riesgo',
    ]

    def finalizar_embarazos(self, request, queryset):
        """
        ACCIÓN: Finalizar embarazos seleccionados

        Funcionamiento:
            1. Itera sobre los embarazos seleccionados
            2. Cambia estado a 'finalizado'
            3. Muestra mensaje de confirmación

        Uso:
            Seleccionar embarazos -> Acciones -> Finalizar embarazos seleccionados
        """
        count = queryset.update(estado='finalizado')
        self.message_user(
            request,
            f'{count} embarazo(s) finalizado(s) exitosamente.'
        )

    finalizar_embarazos.short_description = "Finalizar embarazos seleccionados"

    def marcar_perdidas(self, request, queryset):
        """
        ACCIÓN: Marcar como pérdida gestacional

        Funcionamiento:
            Cambia estado a 'perdida' para los embarazos seleccionados
        """
        count = queryset.update(estado='perdida')
        self.message_user(
            request,
            f'{count} embarazo(s) marcado(s) como pérdida.'
        )

    marcar_perdidas.short_description = "Marcar como pérdida gestacional"

    def cambiar_a_bajo_riesgo(self, request, queryset):
        """
        ACCIÓN: Cambiar a bajo riesgo

        Funcionamiento:
            Cambia el nivel de riesgo a 'bajo'
        """
        count = queryset.update(riesgo_embarazo='bajo')
        self.message_user(
            request,
            f'{count} embarazo(s) cambiado(s) a bajo riesgo.'
        )

    cambiar_a_bajo_riesgo.short_description = "Cambiar a BAJO riesgo"

    def cambiar_a_medio_riesgo(self, request, queryset):
        """
        ACCIÓN: Cambiar a medio riesgo

        Funcionamiento:
            Cambia el nivel de riesgo a 'medio'
        """
        count = queryset.update(riesgo_embarazo='medio')
        self.message_user(
            request,
            f'{count} embarazo(s) cambiado(s) a medio riesgo.'
        )

    cambiar_a_medio_riesgo.short_description = "Cambiar a MEDIO riesgo"

    def cambiar_a_alto_riesgo(self, request, queryset):
        """
        ACCIÓN: Cambiar a alto riesgo

        Funcionamiento:
            Cambia el nivel de riesgo a 'alto'
        """
        count = queryset.update(riesgo_embarazo='alto')
        self.message_user(
            request,
            f'{count} embarazo(s) cambiado(s) a alto riesgo.'
        )

    cambiar_a_alto_riesgo.short_description = "Cambiar a ALTO riesgo"

    # ===========================================
    # MÉTODOS PERSONALIZADOS PARA list_display
    # ===========================================

    def paciente_info(self, obj):
        """
        MÉTODO: Mostrar información del paciente

        Funcionamiento:
            Retorna ID clínico + nombre completo del paciente

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            str: "HC-001 - María García"
        """
        try:
            return f"{obj.paciente.id_clinico} - {obj.paciente.nombre_completo}"
        except:
            return "N/A"

    paciente_info.short_description = 'Paciente'
    paciente_info.admin_order_field = 'paciente__nombre'

    def semanas_gestacion_display(self, obj):
        """
        MÉTODO: Mostrar semanas de gestación

        Funcionamiento:
            Calcula y muestra edad gestacional en formato SS+D

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            str: "28+4" o "N/A"
        """
        if obj.fecha_ultima_menstruacion:
            hoy = date.today()
            dias = (hoy - obj.fecha_ultima_menstruacion).days
            semanas = dias // 7
            dias_extra = dias % 7
            return f"{semanas}+{dias_extra}"
        return "N/A"

    semanas_gestacion_display.short_description = 'Edad Gestacional'

    def tipo_embarazo_badge(self, obj):
        """
        MÉTODO: Mostrar tipo de embarazo con badge de color

        Funcionamiento:
            Retorna HTML con el tipo en un badge de color

        Colores:
            - Simple: Azul (#007bff)
            - Gemelar: Naranja (#fd7e14)
            - Múltiple: Rojo (#dc3545)

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            SafeString: HTML del badge
        """
        colores = {
            'simple': '#007bff',    # Azul
            'gemelar': '#fd7e14',   # Naranja
            'multiple': '#dc3545',  # Rojo
        }

        color = colores.get(obj.tipo_embarazo, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_embarazo_display()
        )

    tipo_embarazo_badge.short_description = 'Tipo'
    tipo_embarazo_badge.admin_order_field = 'tipo_embarazo'

    def riesgo_embarazo_badge(self, obj):
        """
        MÉTODO: Mostrar riesgo con badge de color

        Funcionamiento:
            Retorna HTML con el riesgo en un badge de color

        Colores:
            - Bajo: Verde (#28a745)
            - Medio: Amarillo (#ffc107)
            - Alto: Rojo (#dc3545)

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            SafeString: HTML del badge
        """
        colores = {
            'bajo': '#28a745',      # Verde
            'medio': '#ffc107',     # Amarillo
            'alto': '#dc3545',      # Rojo
        }

        color = colores.get(obj.riesgo_embarazo, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_riesgo_embarazo_display()
        )

    riesgo_embarazo_badge.short_description = 'Riesgo'
    riesgo_embarazo_badge.admin_order_field = 'riesgo_embarazo'

    def estado_badge(self, obj):
        """
        MÉTODO: Mostrar estado con badge de color

        Funcionamiento:
            Retorna HTML con el estado en un badge de color

        Colores:
            - Activo: Verde (#28a745)
            - Finalizado: Azul (#007bff)
            - Pérdida: Rojo (#dc3545)

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            SafeString: HTML del badge
        """
        colores = {
            'activo': '#28a745',       # Verde
            'finalizado': '#007bff',   # Azul
            'perdida': '#dc3545',      # Rojo
        }

        color = colores.get(obj.estado, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )

    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'estado'

    def calculos_obstetricos(self, obj):
        """
        MÉTODO: Mostrar cálculos obstétricos

        Funcionamiento:
            Calcula y muestra información obstétrica del embarazo

        Parámetros:
            obj: Instancia de Embarazo

        Retorna:
            str: HTML con los cálculos
        """
        if not obj.fecha_ultima_menstruacion:
            return "No se pueden calcular (falta FUM)"

        hoy = date.today()
        dias_totales = (hoy - obj.fecha_ultima_menstruacion).days
        semanas = dias_totales // 7
        dias = dias_totales % 7

        # Calcular trimestre
        if semanas <= 13:
            trimestre = 1
        elif semanas <= 26:
            trimestre = 2
        else:
            trimestre = 3

        # Calcular días hasta parto
        if obj.fecha_probable_parto:
            dias_parto = (obj.fecha_probable_parto - hoy).days
        else:
            dias_parto = "N/A"

        # Calcular porcentaje
        porcentaje = min((dias_totales / 280) * 100, 100.0)

        html = f"""
        <div style="line-height: 1.8;">
            <strong>Edad Gestacional:</strong> {semanas}+{dias} semanas ({dias_totales} días)<br>
            <strong>Trimestre:</strong> {trimestre}°<br>
            <strong>Días hasta parto:</strong> {dias_parto}<br>
            <strong>Porcentaje completado:</strong> {porcentaje:.1f}%<br>
        </div>
        """

        return format_html(html)

    calculos_obstetricos.short_description = 'Cálculos Obstétricos'

    # ===========================================
    # SOBRESCRIBIR MÉTODOS DEL ADMIN
    # ===========================================

    def get_queryset(self, request):
        """
        MÉTODO: Obtener queryset optimizado

        Funcionamiento:
            Optimiza las queries para reducir el tiempo de carga
            Útil cuando hay muchos embarazos

        Retorna:
            QuerySet: Queryset optimizado
        """
        qs = super().get_queryset(request)

        # Optimizar con select_related para reducir queries
        qs = qs.select_related('paciente')

        return qs


"""
RESUMEN DE CONFIGURACIÓN DEL ADMIN:
====================================

Columnas en lista:
    - ID, Paciente (con ID clínico), Número Gesta, Semanas Gestación,
      FPP, Tipo (con color), Riesgo (con color), Estado (con color),
      Fecha Registro

Filtros disponibles:
    - Estado, Riesgo, Tipo, Fecha Registro, FPP

Búsqueda por:
    - ID Clínico, Nombre Paciente, Apellidos, Número Gesta

Acciones en masa:
    - Finalizar embarazos
    - Marcar como pérdida
    - Cambiar nivel de riesgo (bajo/medio/alto)

Organización:
    - 6 secciones organizadas (Información Básica, Datos Obstétricos, etc.)
    - Campos de solo lectura para auditoría y cálculos
    - Campos colapsables para información secundaria
    - Cálculos obstétricos automáticos en detalle

Características especiales:
    - Badges de color para tipo, riesgo y estado
    - Cálculo automático de edad gestacional
    - Información obstétrica completa en detalle
    - Optimización de queries con select_related
    - 25 embarazos por página

====================================
"""
