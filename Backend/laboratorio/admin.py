"""=============================================================================
CONFIGURACIÓN DEL ADMIN DE DJANGO - MÓDULO DE LABORATORIO
=============================================================================
Interfaz administrativa completa para gestionar:
    pass
- Tipos de exámenes
- Valores de referencia
- Exámenes de laboratorio
- Resultados de laboratorio

Características:
    pass
- Filtros por fecha, estado, tipo de examen
- Búsqueda inteligente
- Edición inline de resultados
- Acciones en batch
- Campos de solo lectura calculados
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ExamenLaboratorio,
    ImagenLaboratorio,
    ResultadoLaboratorio,
    TipoExamen,
    ValorReferencia,
)

# =============================================================================
# INLINE ADMINS
# =============================================================================


class ValorReferenciaInline(admin.TabularInline):
    """Valores de referencia inline para TipoExamen"""

    model = ValorReferencia
    extra = 1
    fields = (
        "parametro",
        "valor_minimo",
        "valor_maximo",
        "valor_normal",
        "unidad",
        "es_critico_bajo",
        "es_critico_alto",
        "condicion",
    )


class ResultadoLaboratorioInline(admin.TabularInline):
    """Resultados inline para ExamenLaboratorio"""

    model = ResultadoLaboratorio
    extra = 0
    fields = (
        "valor_referencia",
        "valor_numerico",
        "valor_texto",
        "unidad",
        "estado_badge",
        "observaciones",
    )
    readonly_fields = ("estado_badge",)

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        """Badge visual del estado del resultado"""
        if obj.es_critico:
            color = "#ff4d4"
            texto = " CRÍTICO"
        elif not obj.es_normal:
            color = "#faad14"
            texto = " ANORMAL"
        else:
            color = "#52c41a"
            texto = " NORMAL"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            texto,
        )



# =============================================================================
# TIPO DE EXAMEN ADMIN
# =============================================================================


@admin.register(TipoExamen)
class TipoExamenAdmin(admin.ModelAdmin):
    """Administración de Tipos de Exámenes"""

    list_display = (
        "codigo",
        "nombre",
        "categoria_badge",
        "total_valores_referencia",
        "total_examenes",
        "activo",
    )

    list_filter = (
        "categoria",
        "activo",
        "fecha_creacion",
    )

    search_fields = (
        "codigo",
        "nombre",
        "descripcion",
    )

    ordering = ("categoria", "nombre")

    fieldsets = (
        (
            "Información Básica",
            {"fields": ("codigo", "nombre", "categoria", "descripcion")},
        ),
        ("Configuración", {"fields": ("activo",)}),
        (
            "Metadata",
            {
                "fields": ("fecha_creacion", "fecha_actualizacion"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("fecha_creacion", "fecha_actualizacion")

    inlines = [ValorReferenciaInline]

    @admin.display(description="Categoría")
    def categoria_badge(self, obj):
        """Badge de categoría con color"""
        colores = {
            "hematologia": "#722ed1",
            "bioquimica": "#1890f",
            "hormonas": "#eb2f96",
            "serologia": "#52c41a",
            "microbiologia": "#faad14",
            "orina": "#13c2c2",
            "coagulacion": "#f5222d",
            "otros": "#8c8c8c",
        }
        color = colores.get(obj.categoria, "#8c8c8c")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            getattr(obj, 'get_categoria_display')(),
        )


    @admin.display(description="Valores Referencia")
    def total_valores_referencia(self, obj):
        """Total de valores de referencia definidos"""
        count = obj.valores_referencia.count()
        return format_html("<strong>{}</strong> parámetros", count)


    @admin.display(description="Exámenes Realizados")
    def total_examenes(self, obj):
        """Total de exámenes realizados"""
        count = obj.examenes.count()
        return format_html("<strong>{}</strong> exámenes", count)



# =============================================================================
# VALOR DE REFERENCIA ADMIN
# =============================================================================


@admin.register(ValorReferencia)
class ValorReferenciaAdmin(admin.ModelAdmin):
    """Administración de Valores de Referencia"""

    list_display = (
        "parametro",
        "tipo_examen",
        "rango_completo",
        "unidad",
        "condicion",
        "tiene_criticos",
    )

    list_filter = (
        "tipo_examen__categoria",
        "tipo_examen",
        "unidad",
    )

    search_fields = (
        "parametro",
        "tipo_examen__nombre",
        "condicion",
    )

    ordering = ("tipo_examen", "parametro")

    fieldsets = (
        ("Información Básica", {"fields": ("tipo_examen", "parametro", "unidad")}),
        (
            "Valores Numéricos",
            {
                "fields": ("valor_minimo", "valor_maximo"),
                "description": "Para parámetros cuantitativos",
            },
        ),
        (
            "Valores Cualitativos",
            {
                "fields": ("valor_normal",),
                "description": "Para parámetros cualitativos (texto)",
            },
        ),
        (
            "Valores Críticos",
            {
                "fields": ("es_critico_bajo", "es_critico_alto"),
                "classes": ("collapse",),
            },
        ),
        ("Condiciones", {"fields": ("condicion",)}),
    )

    @admin.display(description="Rango de Referencia")
    def rango_completo(self, obj):
        """Mostrar rango completo con formato"""
        if obj.valor_minimo is not None and obj.valor_maximo is not None:
            return format_html(
                "<strong>{} - {}</strong> {}",
                obj.valor_minimo,
                obj.valor_maximo,
                obj.unidad or "",
            )
        if obj.valor_normal:
            return format_html("<em>{}</em>", obj.valor_normal)
        return "-"


    @admin.display(description="Valores Críticos")
    def tiene_criticos(self, obj):
        """Indica si tiene valores críticos definidos"""
        if obj.es_critico_bajo or obj.es_critico_alto:
            return format_html('<span style="color: #f5222d;">⚠️ Sí</span>')
        return "-"



# =============================================================================
# EXAMEN DE LABORATORIO ADMIN
# =============================================================================


@admin.register(ExamenLaboratorio)
class ExamenLaboratorioAdmin(admin.ModelAdmin):
    """Administración de Exámenes de Laboratorio"""

    list_display = (
        "id",
        "paciente_info",
        "tipo_examen",
        "fecha_solicitud",
        "estado_badge",
        "prioridad_badge",
        "resumen_resultados",
        "fecha_resultado",
    )

    list_filter = (
        "estado",
        "prioridad",
        "tipo_examen__categoria",
        "tipo_examen",
        "fecha_solicitud",
        "fecha_resultado",
    )

    search_fields = (
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
        "paciente__ci",
        "tipo_examen__nombre",
        "indicaciones",
    )

    date_hierarchy = "fecha_solicitud"

    ordering = ("-fecha_solicitud",)

    fieldsets = (
        (
            "Información del Examen",
            {
                "fields": (
                    "paciente",
                    "tipo_examen",
                    "fecha_solicitud",
                    "prioridad",
                    "indicaciones",
                ),
            },
        ),
        (
            "Estado y Resultados",
            {
                "fields": (
                    "estado",
                    "fecha_resultado",
                    "observaciones_generales",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_by",
                    "updated_by",
                    "fecha_creacion",
                    "fecha_actualizacion",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("fecha_creacion", "fecha_actualizacion")

    inlines = [ResultadoLaboratorioInline]

    actions = [
        "marcar_como_completado",
        "marcar_como_pendiente",
        "marcar_como_urgente",
    ]

    @admin.display(description="Paciente")
    def paciente_info(self, obj):
        """Información del paciente"""
        return format_html(
            "<strong>{}</strong><br><small>CI: {}</small>",
            obj.paciente.nombre_completo if obj.paciente else "N/A",
            obj.paciente.ci if obj.paciente else "N/A",
        )


    @admin.display(description="Estado")
    def estado_badge(self, obj):
        """Badge del estado del examen"""
        colores = {
            "pendiente": "#faad14",
            "en_proceso": "#1890f",
            "completado": "#52c41a",
            "cancelado": "#8c8c8c",
        }
        iconos = {
            "pendiente": "⏳",
            "en_proceso": "",
            "completado": "✅",
            "cancelado": "❌",
        }

        color = colores.get(obj.estado, "#8c8c8c")
        icono = iconos.get(obj.estado, "•")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icono,
            getattr(obj, 'get_estado_display')().upper(),
        )


    @admin.display(description="Prioridad")
    def prioridad_badge(self, obj):
        """Badge de prioridad"""
        colores = {
            "normal": "#52c41a",
            "urgente": "#faad14",
            "emergencia": "#f5222d",
        }

        color = colores.get(obj.prioridad, "#8c8c8c")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            getattr(obj, 'get_prioridad_display')().upper(),
        )


    @admin.display(description="N / A / C")
    def resumen_resultados(self, obj):
        """Resumen de resultados"""
        try:
            resumen = obj.resumen
            if resumen.get("total", 0) == 0:
                return format_html('<em style="color: #8c8c8c;">Sin resultados</em>')

            return format_html(
                '<span style="color: #52c41a;">✓ {}</span> / '
                '<span style="color: #faad14;">⚠ {}</span> / '
                '<span style="color: #f5222d;"> {}</span>',
                resumen.get("normales", 0),
                resumen.get("anormales", 0),
                resumen.get("criticos", 0),
            )
        except Exception:
            return "-"


    # Acciones en batch
    @admin.action(description="✅ Marcar como Completado")
    def marcar_como_completado(self, request, queryset):
        """Marcar como completado"""
        updated = queryset.update(estado="completado")
        self.message_user(request, f"{updated} examen(es) marcado(s) como completado.")


    @admin.action(description="⏳ Marcar como Pendiente")
    def marcar_como_pendiente(self, request, queryset):
        """Marcar como pendiente"""
        updated = queryset.update(estado="pendiente")
        self.message_user(request, f"{updated} examen(es) marcado(s) como pendiente.")


    @admin.action(description="⚠️ Marcar como Urgente")
    def marcar_como_urgente(self, request, queryset):
        """Marcar como urgente"""
        updated = queryset.update(prioridad="urgente")
        self.message_user(request, f"{updated} examen(es) marcado(s) como urgente.")



# =============================================================================
# RESULTADO DE LABORATORIO ADMIN
# =============================================================================


@admin.register(ResultadoLaboratorio)
class ResultadoLaboratorioAdmin(admin.ModelAdmin):
    """Administración de Resultados de Laboratorio"""

    list_display = (
        "id",
        "examen_info",
        "parametro_info",
        "valor_obtenido",
        "rango_referencia",
        "estado_visual",
        "fecha_registro",
    )

    list_filter = (
        "examen__tipo_examen__categoria",
        "examen__tipo_examen",
        "es_normal",
        "es_critico",
        "fecha_registro",
    )

    search_fields = (
        "examen__paciente__nombre",
        "examen__paciente__apellido_paterno",
        "valor_referencia__parametro",
        "observaciones",
    )

    date_hierarchy = "fecha_registro"

    ordering = ("-fecha_registro",)

    fieldsets = (
        ("Examen", {"fields": ("examen", "valor_referencia")}),
        (
            "Valores",
            {
                "fields": (
                    "valor_numerico",
                    "valor_texto",
                    "unidad",
                ),
            },
        ),
        (
            "Estados Calculados",
            {
                "fields": (
                    "es_normal",
                    "es_critico",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Observaciones", {"fields": ("observaciones",)}),
        (
            "Metadata",
            {
                "fields": (
                    "created_by",
                    "updated_by",
                    "fecha_registro",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("fecha_registro",)

    @admin.display(description="Examen")
    def examen_info(self, obj):
        """Información del examen"""
        return format_html(
            "<strong>#{}</strong><br><small>{}</small>",
            obj.examen.id,
            obj.examen.tipo_examen.nombre if obj.examen.tipo_examen else "N/A",
        )


    @admin.display(description="Parámetro")
    def parametro_info(self, obj):
        """Información del parámetro"""
        if obj.valor_referencia:
            return format_html("<strong>{}</strong>", obj.valor_referencia.parametro)
        return "-"


    @admin.display(description="Valor")
    def valor_obtenido(self, obj):
        """Valor obtenido con unidad"""
        if obj.valor_numerico is not None:
            return format_html(
                '<strong style="font-size: 14px;">{}</strong> <span style="color: #8c8c8c;">{}</span>',
                obj.valor_numerico,
                obj.unidad or "",
            )
        if obj.valor_texto:
            return format_html("<em>{}</em>", obj.valor_texto)
        return "-"


    @admin.display(description="Rango Ref.")
    def rango_referencia(self, obj):
        """Rango de referencia"""
        if obj.valor_referencia:
            if obj.valor_referencia.valor_minimo is not None:
                return format_html(
                    "<small>{} - {} {}</small>",
                    obj.valor_referencia.valor_minimo,
                    obj.valor_referencia.valor_maximo,
                    obj.valor_referencia.unidad or "",
                )
            if obj.valor_referencia.valor_normal:
                return format_html(
                    "<small><em>{}</em></small>", obj.valor_referencia.valor_normal,
                )
        return "-"


    @admin.display(description="Estado")
    def estado_visual(self, obj):
        """Estado visual con badge"""
        if obj.es_critico:
            return format_html(
                '<span style="background-color: #ff4d4f; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;"> CRÍTICO</span>',
            )
        if not obj.es_normal:
            return format_html(
                '<span style="background-color: #faad14; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;"> ANORMAL</span>',
            )
        return format_html(
            '<span style="background-color: #52c41a; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;"> NORMAL</span>',
        )


    @admin.display(description="Fecha Registro")
    def fecha_registro(self, obj):
        """Fecha de registro"""
        if hasattr(obj, "fecha_creacion") and obj.fecha_creacion:
            return obj.fecha_creacion.strftime("%d/%m/%Y %H:%M")
        return "-"



# =============================================================================
# IMAGEN LABORATORIO ADMIN
# =============================================================================


@admin.register(ImagenLaboratorio)
class ImagenLaboratorioAdmin(admin.ModelAdmin):
    """Administración de Imágenes y Archivos de Laboratorio"""

    list_display = (
        "id",
        "get_examen_info",
        "tipo_archivo_badge",
        "fecha_digitalizacion",
        "get_archivo_link",
        "descripcion",
    )

    list_filter = (
        "tipo_archivo",
        "fecha_digitalizacion",
    )

    search_fields = (
        "examen__paciente__nombre",
        "examen__paciente__apellido_paterno",
        "descripcion",
    )

    readonly_fields = ("fecha_digitalizacion",)

    fieldsets = (
        ("Información del Examen", {"fields": ("examen",)}),
        (
            "Archivo",
            {
                "fields": (
                    "tipo_archivo",
                    "archivo",
                    "descripcion",
                ),
            },
        ),
        ("Metadata", {"fields": ("fecha_digitalizacion",), "classes": ("collapse",)}),
    )

    @admin.display(description="Paciente/Examen")
    def get_examen_info(self, obj):
        """Información del examen"""
        if obj.examen and obj.examen.paciente:
            return format_html(
                "<strong>{}</strong><br/><small>{}</small>",
                obj.examen.paciente.nombre_completo,
                obj.examen.tipo_examen.nombre if obj.examen.tipo_examen else "Sin tipo",
            )
        return "-"


    @admin.display(description="Tipo")
    def tipo_archivo_badge(self, obj):
        """Badge del tipo de archivo"""
        colors = {
            "hoja_resultados": "#3498db",
            "hemograma": "#e74c3c",
            "bioquimica": "#2ecc71",
            "serologia": "#9b59b6",
            "orina": "#f39c12",
            "otro": "#95a5a6",
        }
        color = colors.get(obj.tipo_archivo, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            getattr(obj, 'get_tipo_archivo_display')().upper(),
        )


    @admin.display(description="Archivo")
    def get_archivo_link(self, obj):
        """Link al archivo"""
        if obj.archivo:
            return format_html(
                '<a href="{}" target="_blank"> Ver archivo</a>', obj.archivo.url,
            )
        return "-"



# =============================================================================
# CONFIGURACIÓN DEL SITIO ADMIN
# =============================================================================

# Personalizar títulos del admin
admin.site.site_header = "Sistema de Historias Clínicas - Laboratorio"
admin.site.site_title = "Admin Laboratorio"
admin.site.index_title = "Gestión de Laboratorio Clínico"
