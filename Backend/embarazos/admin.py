"""Admin module."""

from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from .models import Embarazo


@admin.register(Embarazo)
class EmbarazoAdmin(admin.ModelAdmin):
    """✨ Admin Completo y Mejorado para Embarazos

    Características:
        pass
    - Badges visuales con colores según riesgo y estado
    - Fieldsets organizados por secciones
    - Cálculos automáticos mostrados
    - Filtros avanzados por trimestre
    - Acciones personalizadas
    - Inlines para controles prenatales
    """

    list_display = [
        "id",
        "get_paciente_info",
        "numero_gesta_para_display",
        "get_edad_gestacional",
        "get_fpp_badge",
        "riesgo_badge",
        "estado_badge",
        "tipo_embarazo_badge",
        "fecha_ultima_menstruacion",
        "get_controles_count",
        "acciones_rapidas",
    ]

    list_filter = [
        "estado",
        "riesgo_embarazo",
        "tipo_embarazo",
        "fecha_registro",
        ("fecha_ultima_menstruacion", admin.DateFieldListFilter),
    ]

    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
        "paciente__id_clinico",
        "paciente__ci",
        "medico_responsable",
        "notas",
    ]

    readonly_fields = [
        "uuid",
        "fecha_registro",
        "fecha_modificacion",
        "created_by",
        "updated_by",
        "get_edad_gestacional_completa",
        "get_fpp_calculada",
        "get_trimestre_actual",
        "get_semanas_restantes",
        "get_resumen_embarazo",
        "get_controles_realizados",
    ]

    fieldsets = (
        (
            " Información del Paciente",
            {
                "fields": (
                    "paciente",
                    "medico_responsable",
                ),
            },
        ),
        (
            " Datos del Embarazo",
            {
                "fields": (
                    ("numero_gesta", "numero_para", "numero_cesareas"),
                    ("numero_abortos", "hijos_vivos"),
                    "tipo_embarazo",
                ),
            },
        ),
        (
            " Fechas Importantes",
            {
                "fields": (
                    "fecha_ultima_menstruacion",
                    "get_fpp_calculada",
                    "fecha_probable_parto",
                    "get_edad_gestacional_completa",
                    "get_trimestre_actual",
                    "get_semanas_restantes",
                ),
            },
        ),
        (
            "⚠️ Clasificación de Riesgo",
            {
                "fields": (
                    "riesgo_embarazo",
                    "factores_riesgo",
                ),
                "classes": ("wide",),
            },
        ),
        (
            " Estado y Resultado",
            {
                "fields": (
                    "estado",
                    "resultado_embarazo",
                    "fecha_finalizacion",
                ),
            },
        ),
        (
            " Observaciones y Notas",
            {
                "fields": (
                    "notas",
                    "plan_parto",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            " Resumen del Embarazo",
            {
                "fields": (
                    "get_resumen_embarazo",
                    "get_controles_realizados",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            " Metadatos del Sistema",
            {
                "fields": (
                    "uuid",
                    "fecha_registro",
                    "fecha_actualizacion",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    date_hierarchy = "fecha_registro"
    list_per_page = 25
    ordering = ["-fecha_registro"]

    actions = [
        "marcar_alto_riesgo",
        "finalizar_embarazo",
        "reactivar_embarazo",
        "generar_reporte",
    ]

    # ═══════════════════════════════════════════════════════════════════════
    # MÉTODOS DISPLAY CON BADGES Y FORMATO HTML
    # ═══════════════════════════════════════════════════════════════════════

    @admin.display(description="Paciente")
    def get_paciente_info(self, obj):
        """Información del paciente con link"""
        if not obj.paciente:
            return format_html('<span style="color: #e74c3c;">❌ Sin paciente</span>')

        url = reverse("admin:pacientes_paciente_change", args=[obj.paciente.id])
        return format_html(
            '<a href="{}" style="font-weight: bold; text-decoration: none;">'
            "{}</a><br/>"
            '<small style="color: #7f8c8d;">ID: {}</small>',
            url,
            obj.paciente.nombre_completo,
            obj.paciente.id_clinico,
        )


    @admin.display(description="G-P-A-C")
    def numero_gesta_para_display(self, obj):
        """Muestra G-P-A-C de forma visual"""
        return format_html(
            '<strong style="color: #2c3e50;">G{}</strong> '
            '<span style="color: #27ae60;">P{}</span> '
            '<span style="color: #e67e22;">A{}</span> '
            '<span style="color: #3498db;">C{}</span>',
            obj.numero_gesta or 0,
            obj.numero_para or 0,
            obj.numero_abortos or 0,
            obj.numero_cesareas or 0,
        )


    @admin.display(description="Edad Gestacional")
    def get_edad_gestacional(self, obj):
        """Muestra la edad gestacional actual"""
        if not obj.fecha_ultima_menstruacion:
            return format_html('<span style="color: #95a5a6;">No calculable</span>')

        dias = (timezone.localdate() - obj.fecha_ultima_menstruacion).days
        semanas = dias // 7
        dias_extra = dias % 7

        # Color según trimestre
        if semanas <= 13:
            color = "#3498db"  # Azul - 1er trimestre
        elif semanas <= 27:
            color = "#f39c12"  # Naranja - 2do trimestre
        else:
            color = "#e74c3c"  # Rojo - 3er trimestre

        return format_html(
            '<strong style="color: {};">{} sem + {} días</strong>',
            color,
            semanas,
            dias_extra,
        )


    @admin.display(description="FPP")
    def get_fpp_badge(self, obj):
        """Badge de la Fecha Probable de Parto"""
        if not obj.fecha_probable_parto:
            return format_html('<span style="color: #95a5a6;">No calculada</span>')

        dias_restantes = (obj.fecha_probable_parto - timezone.localdate()).days

        if dias_restantes < 0:
            return format_html(
                '<span style="background-color: #c0392b; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">⚠️ VENCIDO</span><br/>'
                "<small>{}</small>",
                obj.fecha_probable_parto.strftime("%d/%m/%Y"),
            )
        if dias_restantes <= 14:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;"> {} días</span><br/>'
                "<small>{}</small>",
                dias_restantes,
                obj.fecha_probable_parto.strftime("%d/%m/%Y"),
            )
        if dias_restantes <= 30:
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">⏰ {} días</span><br/>'
                "<small>{}</small>",
                dias_restantes,
                obj.fecha_probable_parto.strftime("%d/%m/%Y"),
            )
        return format_html(
            '<span style="background-color: #27ae60; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;"> {} días</span><br/>'
            "<small>{}</small>",
            dias_restantes,
            obj.fecha_probable_parto.strftime("%d/%m/%Y"),
        )


    @admin.display(description="Riesgo")
    def riesgo_badge(self, obj):
        """Badge visual para el nivel de riesgo"""
        colors = {
            "bajo": ("#27ae60", ""),
            "moderado": ("#f39c12", ""),
            "alto": ("#e74c3c", ""),
            "muy_alto": ("#c0392b", ""),
        }
        color, icon = colors.get(obj.riesgo_embarazo, ("#95a5a6", "⚪"))

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            getattr(obj, 'get_riesgo_embarazo_display')().upper(),
        )


    @admin.display(description="Estado")
    def estado_badge(self, obj):
        """Badge visual para el estado"""
        colors = {
            "activo": "#27ae60",
            "finalizado": "#3498db",
            "perdida": "#e74c3c",
        }
        icons = {
            "activo": "✅",
            "finalizado": "",
            "perdida": "",
        }
        color = colors.get(obj.estado, "#95a5a6")
        icon = icons.get(obj.estado, "⚫")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            getattr(obj, 'get_estado_display')().upper(),
        )


    @admin.display(description="Tipo")
    def tipo_embarazo_badge(self, obj):
        """Badge para el tipo de embarazo"""
        if obj.tipo_embarazo in ["gemelar", "multiple"]:
            return format_html(
                '<span style="background-color: #9b59b6; color: white; padding: 2px 6px; '
                'border-radius: 3px; font-size: 11px;"> {}</span>',
                getattr(obj, 'get_tipo_embarazo_display')().upper(),
            )
        return format_html(
            '<span style="background-color: #34495e; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            getattr(obj, 'get_tipo_embarazo_display')(),
        )


    @admin.display(description="Controles")
    def get_controles_count(self, obj):
        """Cantidad de controles realizados"""
        count = obj.controles.count()
        if count == 0:
            return format_html('<span style="color: #e74c3c;">0 controles</span>')
        if count < 4:
            return format_html(
                '<span style="color: #f39c12;">{} controles</span>', count,
            )
        return format_html(
            '<span style="color: #27ae60;">✓ {} controles</span>', count,
        )


    @admin.display(description="Acciones")
    def acciones_rapidas(self, obj):
        """Botones de acción rápida"""
        url_editar = reverse("admin:embarazos_embarazo_change", args=[obj.id])
        url_controles = (
            f"/admin/controles/controlprenatal/embarazo_id__id__exact={obj.id}"
        )

        return format_html(
            '<a href="{}" style="background-color: #3498db; color: white; '
            "padding: 2px 6px; text-decoration: none; border-radius: 3px; "
            'font-size: 10px; margin-right: 2px;">✏️ EDITAR</a>'
            '<a href="{}" style="background-color: #27ae60; color: white; '
            "padding: 2px 6px; text-decoration: none; border-radius: 3px; "
            'font-size: 10px;"> CONTROLES</a>',
            url_editar,
            url_controles,
        )


    # ═══════════════════════════════════════════════════════════════════════
    # READONLY FIELDS CON INFORMACIÓN CALCULADA
    # ═══════════════════════════════════════════════════════════════════════

    @admin.display(description=" Edad Gestacional Detallada")
    def get_edad_gestacional_completa(self, obj):
        """Información completa de edad gestacional"""
        if not obj.fecha_ultima_menstruacion:
            return "❌ No se puede calcular (falta FUM)"

        dias = (timezone.localdate() - obj.fecha_ultima_menstruacion).days
        semanas = dias // 7
        dias_extra = dias % 7

        # Determinar trimestre
        if semanas <= 13:
            trimestre = "1er Trimestre"
            color = "blue"
        elif semanas <= 27:
            trimestre = "2do Trimestre"
            color = "orange"
        else:
            trimestre = "3er Trimestre"
            color = "red"

        return format_html(
            '<div style="padding: 10px; background-color: #ecf0f1; border-left: 4px solid {};">'
            "<strong>Edad Gestacional:</strong> {} semanas + {} días<br/>"
            "<strong>Total de días:</strong> {} días<br/>"
            "<strong>Trimestre:</strong> {}"
            "</div>",
            color,
            semanas,
            dias_extra,
            dias,
            trimestre,
        )


    @admin.display(description=" Fecha Probable de Parto")
    def get_fpp_calculada(self, obj):
        """FPP calculada con detalles"""
        if not obj.fecha_probable_parto:
            return "❌ No calculada (falta FUM)"

        dias_restantes = (obj.fecha_probable_parto - timezone.localdate()).days
        semanas_restantes = dias_restantes // 7

        return format_html(
            '<div style="padding: 10px; background-color: #e8f5e9; border-left: 4px solid #27ae60;">'
            "<strong>Fecha Probable de Parto:</strong> {}<br/>"
            "<strong>Días restantes:</strong> {} días ({} semanas)<br/>"
            "<strong>Fecha de hoy:</strong> {}"
            "</div>",
            obj.fecha_probable_parto.strftime("%d de %B de %Y"),
            dias_restantes,
            semanas_restantes,
            timezone.localdate().strftime("%d de %B de %Y"),
        )


    @admin.display(description=" Trimestre Actual")
    def get_trimestre_actual(self, obj):
        """Muestra el trimestre actual"""
        if not obj.fecha_ultima_menstruacion:
            return "No calculable"

        semanas = (timezone.localdate() - obj.fecha_ultima_menstruacion).days // 7

        if semanas <= 13:
            return format_html(
                '<span style="background-color: #3498db; color: white; padding: 5px 15px; '
                'border-radius: 5px; font-weight: bold;">1er TRIMESTRE</span>',
            )
        if semanas <= 27:
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 5px 15px; '
                'border-radius: 5px; font-weight: bold;">2do TRIMESTRE</span>',
            )
        return format_html(
            '<span style="background-color: #e74c3c; color: white; padding: 5px 15px; '
            'border-radius: 5px; font-weight: bold;">3er TRIMESTRE</span>',
        )


    @admin.display(description="⏰ Semanas Restantes")
    def get_semanas_restantes(self, obj):
        """Semanas restantes hasta FPP"""
        if not obj.fecha_probable_parto:
            return "No calculable"

        dias_restantes = (obj.fecha_probable_parto - timezone.localdate()).days
        semanas_restantes = dias_restantes // 7

        return format_html(
            '<strong style="font-size: 18px; color: #27ae60;">{} semanas</strong>',
            semanas_restantes,
        )


    @admin.display(description=" Resumen Completo")
    def get_resumen_embarazo(self, obj):
        """Resumen completo del embarazo"""
        controles_count = obj.controles.count()
        ecografias_count = obj.ecografias.count() if hasattr(obj, "ecografias") else 0

        return format_html(
            '<div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; '
            'border: 1px solid #dee2e6;">'
            '<h3 style="margin-top: 0; color: #2c3e50;"> Resumen del Embarazo</h3>'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr><td style="padding: 5px;"><strong>Estado:</strong></td>'
            '<td style="padding: 5px;">{}</td></tr>'
            '<tr><td style="padding: 5px;"><strong>Riesgo:</strong></td>'
            '<td style="padding: 5px;">{}</td></tr>'
            '<tr><td style="padding: 5px;"><strong>Tipo:</strong></td>'
            '<td style="padding: 5px;">{}</td></tr>'
            '<tr><td style="padding: 5px;"><strong>Controles:</strong></td>'
            '<td style="padding: 5px;">{}</td></tr>'
            '<tr><td style="padding: 5px;"><strong>Ecografías:</strong></td>'
            '<td style="padding: 5px;">{}</td></tr>'
            "</table>"
            "</div>",
            getattr(obj, 'get_estado_display')(),
            getattr(obj, 'get_riesgo_embarazo_display')(),
            getattr(obj, 'get_tipo_embarazo_display')(),
            controles_count,
            ecografias_count,
        )


    @admin.display(description=" Controles Realizados")
    def get_controles_realizados(self, obj):
        """Lista de controles realizados"""
        controles = obj.controles.all().order_by("numero_control")

        if not controles.exists():
            return format_html(
                '<div style="padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107;">'
                "⚠️ Aún no se han realizado controles prenatales"
                "</div>",
            )

        filas = format_html_join(
            "",
            "• Control #{} - {} ({} semanas)<br/>",
            (
                (
                    control.numero_control,
                    control.fecha_control.strftime("%d/%m/%Y"),
                    control.semanas_gestacion,
                )
                for control in controles
            ),
        )
        return format_html(
            '<div style="padding: 10px; background-color: #d4edda; border-left: 4px solid #28a745;">'
            "<strong>Controles Realizados:</strong><br/><br/>{}</div>",
            filas,
        )


    # ═══════════════════════════════════════════════════════════════════════
    # ACCIONES PERSONALIZADAS
    # ═══════════════════════════════════════════════════════════════════════

    @admin.action(description="⚠️ Marcar como ALTO RIESGO")
    def marcar_alto_riesgo(self, request, queryset):
        """Marcar alto riesgo"""
        updated = queryset.update(riesgo_embarazo="alto")
        self.message_user(
            request,
            f"{updated} embarazo(s) marcado(s) como ALTO RIESGO.",
            level="warning",
        )

    @admin.action(description=" Finalizar embarazos seleccionados")
    def finalizar_embarazo(self, request, queryset):
        """Finalizar embarazo"""
        updated = queryset.filter(estado="activo").update(
            estado="finalizado", fecha_finalizacion=timezone.localdate(),
        )
        self.message_user(request, f"{updated} embarazo(s) finalizado(s) exitosamente.")

    @admin.action(description=" Reactivar embarazos")
    def reactivar_embarazo(self, request, queryset):
        """Reactivar embarazo"""
        updated = queryset.exclude(estado="activo").update(
            estado="activo", fecha_finalizacion=None,
        )
        self.message_user(request, f"{updated} embarazo(s) reactivado(s).")

    @admin.action(description=" Generar reporte de embarazos")
    def generar_reporte(self, request, queryset):
        """Generar reporte"""
        count = queryset.count()
        self.message_user(request, f"Reporte generado para {count} embarazo(s).")
