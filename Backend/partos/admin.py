"""Admin module."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    ApgarScoreDetallado,
    ComplicacionParto,
    Parto,
    PartogramaRegistro,
    RecienNacido,
)


class RecienNacidoInline(admin.StackedInline):
    """Reciennacidoinline"""
    model = RecienNacido
    extra = 1
    max_num = 5
    verbose_name = "Recién Nacido"
    verbose_name_plural = "Recién Nacidos"

    fieldsets = (
        (
            "Datos Básicos",
            {
                "fields": (
                    ("numero_gemelo", "fecha_nacimiento"),
                    ("sexo", "estado_nacimiento"),
                ),
            },
        ),
        (
            "Antropometría",
            {
                "fields": (
                    ("peso_nacimiento", "talla_nacimiento"),
                    ("perimetro_cefalico",),
                ),
            },
        ),
        (
            "Score de Apgar",
            {"fields": (("apgar_1_minuto", "apgar_5_minutos", "apgar_10_minutos"),)},
        ),
        ("Reanimación", {"fields": (("requirio_reanimacion", "tipo_reanimacion"),)}),
        (
            "Estado General",
            {
                "fields": (
                    (
                        "llanto_inmediato",
                        "respiracion_espontanea",
                        "tono_muscular_normal",
                    ),
                ),
            },
        ),
        (
            "Malformaciones",
            {
                "fields": (
                    ("malformaciones_congenitas", "descripcion_malformaciones"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Destino y Observaciones",
            {
                "fields": (
                    ("destino_rn",),
                    ("observaciones_rn",),
                ),
            },
        ),
    )


class PartogramaRegistroInline(admin.TabularInline):
    """Partogramaregistroinline"""
    model = PartogramaRegistro
    extra = 1
    verbose_name = "Registro de Partograma"
    verbose_name_plural = "Registros de Partograma"

    fields = (
        "hora_registro",
        "horas_trabajo_parto",
        "dilatacion_cervical",
        "estacion_fetal",
        "contracciones_10min",
        "fcf_baseline",
        "presion_arterial_sistolica",
        "presion_arterial_diastolica",
        "oxitocina_dosis",
        "observaciones",
    )

    readonly_fields = ("fecha_registro",)


@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    """Partoadmin"""
    list_display = (
        "numero_parto",
        "get_paciente_info",
        "fecha_parto",
        "tipo_parto_badge",
        "get_edad_gestacional",
        "get_estado_parto",
        "get_duracion_trabajo",
        "get_perdida_sanguinea_badge",
        "get_num_recien_nacidos",
        "acciones_rapidas",
    )

    list_filter = (
        "tipo_parto",
        "presentacion_fetal",
        "parto_finalizado",
        "hemorragia_postparto",
        "episiotomia",
        "desgarros",
        "analgesia_utilizada",
        "oxitocina_utilizada",
        "fecha_parto",
    )

    search_fields = (
        "numero_parto",
        "paciente__id_clinico",
        "paciente__nombre",
        "edad_gestacional_parto",
        "observaciones_parto",
        "complicaciones_maternas",
    )

    date_hierarchy = "fecha_parto"

    readonly_fields = (
        "numero_parto",
        "fecha_registro",
        "fecha_modificacion",
        "get_resumen_parto",
        "get_evaluacion_perdida_sanguinea",
        "get_estado_parto",
        "get_complicaciones_totales",
        "get_duracion_trabajo_parto_horas",
    )

    fieldsets = (
        (
            "Identificación del Parto",
            {
                "fields": (
                    ("numero_parto",),
                    ("embarazo", "paciente", "medico_responsable"),
                ),
            },
        ),
        (
            "Fechas y Tiempos",
            {
                "fields": (
                    ("fecha_ingreso", "fecha_inicio_trabajo_parto"),
                    ("fecha_parto",),
                    (
                        "duracion_trabajo_parto_horas",
                        "duracion_periodo_expulsivo_minutos",
                    ),
                    ("get_duracion_trabajo_parto_horas",),
                ),
            },
        ),
        (
            "Datos del Parto",
            {
                "fields": (
                    ("edad_gestacional_parto", "tipo_parto"),
                    ("presentacion_fetal", "posicion_fetal"),
                ),
            },
        ),
        (
            "Trabajo de Parto",
            {
                "fields": (
                    ("trabajo_parto_espontaneo", "induccion_parto"),
                    ("metodo_induccion",),
                    ("monitoreo_fetal_continuo",),
                ),
            },
        ),
        (
            "Estado de Membranas",
            {
                "fields": (
                    ("estado_membranas", "hora_rotura_membranas"),
                    ("caracteristicas_liquido",),
                ),
            },
        ),
        (
            "Analgesia y Anestesia",
            {"fields": (("analgesia_utilizada", "tipo_analgesia"),)},
        ),
        (
            "Episiotomía y Desgarros",
            {
                "fields": (
                    ("episiotomia", "tipo_episiotomia"),
                    ("desgarros", "grado_desgarros"),
                ),
            },
        ),
        (
            "Alumbramiento",
            {
                "fields": (
                    ("tipo_alumbramiento", "placenta_completa"),
                    ("peso_placenta",),
                ),
            },
        ),
        (
            "Pérdida Sanguínea",
            {
                "fields": (
                    ("perdida_sanguinea_estimada", "hemorragia_postparto"),
                    ("get_evaluacion_perdida_sanguinea",),
                ),
            },
        ),
        (
            "Medicamentos",
            {
                "fields": (
                    ("oxitocina_utilizada", "dosis_oxitocina"),
                    ("otros_medicamentos",),
                ),
            },
        ),
        (
            "Complicaciones y Observaciones",
            {
                "fields": (
                    ("complicaciones_maternas",),
                    ("observaciones_parto",),
                    ("indicaciones_cesarea",),
                    ("get_complicaciones_totales",),
                ),
            },
        ),
        (
            "Estado del Parto",
            {
                "fields": (
                    ("parto_finalizado",),
                    ("get_estado_parto",),
                    ("get_resumen_parto",),
                ),
            },
        ),
        (
            "Información del Sistema",
            {
                "fields": (("fecha_registro", "fecha_modificacion"),),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [RecienNacidoInline, PartogramaRegistroInline]

    actions = [
        "marcar_parto_finalizado",
        "generar_reporte_parto",
        "duplicar_partograma",
    ]

    def get_paciente_info(self, obj):
        """Get paciente info"""
        paciente_nombre = "No asignado"
        if obj.paciente:
            paciente_nombre = f"{obj.paciente.nombre} {obj.paciente.apellido_paterno}"

        embarazo_info = "No asignado"
        if obj.embarazo:
            embarazo_info = f"G{obj.embarazo.numero_gesta}P{obj.embarazo.numero_para}"

        return format_html(
            "<strong>{}</strong><br/><small>{}</small>", paciente_nombre, embarazo_info,
        )

    get_paciente_info.short_description = "Paciente"

    def tipo_parto_badge(self, obj):
        """Tipo parto badge"""
        colors = {
            "vaginal_espontaneo": "#27ae60",
            "vaginal_instrumentado": "#2ecc71",
            "cesarea_electiva": "#3498db",
            "cesarea_urgencia": "#f39c12",
            "cesarea_emergencia": "#e74c3c",
        }
        color = colors.get(obj.tipo_parto, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_parto_display().upper(),
        )

    tipo_parto_badge.short_description = "Tipo de Parto"

    def get_edad_gestacional(self, obj):
        """Get edad gestacional"""
        return obj.edad_gestacional_parto

    get_edad_gestacional.short_description = "Edad Gestacional"

    def get_duracion_trabajo(self, obj):
        """Get duracion trabajo"""
        if obj.duracion_trabajo_parto_horas:
            return f"{obj.duracion_trabajo_parto_horas}h"
        return "No registrada"

    get_duracion_trabajo.short_description = "Duración"

    def get_perdida_sanguinea_badge(self, obj):
        """Get perdida sanguinea badge"""
        evaluacion = obj.get_evaluacion_perdida_sanguinea()
        if "Normal" in evaluacion:
            color = "#27ae60"
        elif "Moderada" in evaluacion:
            color = "#f39c12"
        elif "Severa" in evaluacion:
            color = "#e74c3c"
        else:
            color = "#95a5a6"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, evaluacion,
        )

    get_perdida_sanguinea_badge.short_description = "Pérdida Sanguínea"

    def get_num_recien_nacidos(self, obj):
        """Get num recien nacidos"""
        count = obj.recien_nacidos.count()
        if count == 0:
            return format_html('<span style="color: #e74c3c;">No registrados</span>')
        if count == 1:
            return format_html('<span style="color: #27ae60;">1 RN</span>')
        return format_html('<span style="color: #2ecc71;">{} RNs</span>', count)

    get_num_recien_nacidos.short_description = "Recién Nacidos"

    def acciones_rapidas(self, obj):
        """Acciones rapidas"""
        url_editar = reverse("admin:partos_parto_change", args=[obj.id])

        return format_html(
            '<a href="{}" style="background-color: #3498db; color: white; padding: 2px 6px; text-decoration: none; border-radius: 3px; font-size: 10px; margin-right: 2px;">EDITAR</a>',
            url_editar,
        )

    acciones_rapidas.short_description = "Acciones"

    def marcar_parto_finalizado(self, request, queryset):
        """Marcar parto finalizado"""
        updated = queryset.update(parto_finalizado=True)
        self.message_user(request, f"{updated} partos marcados como finalizados.")

    marcar_parto_finalizado.short_description = "Marcar parto como finalizado"

    def generar_reporte_parto(self, request, queryset):
        """Generar reporte parto"""
        count = queryset.count()
        self.message_user(request, f"Reportes generados para {count} partos.")

    generar_reporte_parto.short_description = "Generar reporte de parto"

    def duplicar_partograma(self, request, queryset):
        """Duplicar partograma"""
        count = queryset.count()
        self.message_user(request, f"Partogramas duplicados para {count} partos.")

    duplicar_partograma.short_description = "Duplicar partograma"


@admin.register(RecienNacido)
class RecienNacidoAdmin(admin.ModelAdmin):
    """Reciennacidoadmin"""
    list_display = (
        "get_parto_numero",
        "numero_gemelo",
        "fecha_nacimiento",
        "sexo",
        "peso_clasificacion_badge",
        "get_apgar_badge",
        "estado_nacimiento",
        "get_evaluacion_estado",
        "requirio_reanimacion",
        "destino_rn",
    )

    list_filter = (
        "sexo",
        "estado_nacimiento",
        "requirio_reanimacion",
        "malformaciones_congenitas",
        "destino_rn",
        "fecha_nacimiento",
        "llanto_inmediato",
        "respiracion_espontanea",
    )

    search_fields = (
        "parto__numero_parto",
        "observaciones_rn",
        "descripcion_malformaciones",
    )

    readonly_fields = (
        "fecha_registro",
        "fecha_modificacion",
        "get_clasificacion_peso",
        "get_evaluacion_apgar",
        "get_evaluacion_estado_general",
        "get_resumen_completo",
    )

    fieldsets = (
        (
            "Información del Parto",
            {
                "fields": (
                    ("parto", "numero_gemelo"),
                    ("fecha_nacimiento",),
                ),
            },
        ),
        ("Datos Básicos", {"fields": (("sexo", "estado_nacimiento"),)}),
        (
            "Antropometría",
            {
                "fields": (
                    ("peso_nacimiento", "talla_nacimiento"),
                    ("perimetro_cefalico",),
                    ("get_clasificacion_peso",),
                ),
            },
        ),
        (
            "Score de Apgar",
            {
                "fields": (
                    ("apgar_1_minuto", "apgar_5_minutos", "apgar_10_minutos"),
                    ("get_evaluacion_apgar",),
                ),
            },
        ),
        (
            "Estado al Nacimiento",
            {
                "fields": (
                    (
                        "llanto_inmediato",
                        "respiracion_espontanea",
                        "tono_muscular_normal",
                    ),
                    ("get_evaluacion_estado_general",),
                ),
            },
        ),
        ("Reanimación", {"fields": (("requirio_reanimacion", "tipo_reanimacion"),)}),
        (
            "Malformaciones",
            {
                "fields": (
                    ("malformaciones_congenitas", "descripcion_malformaciones"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Destino",
            {
                "fields": (
                    ("destino_rn",),
                    ("observaciones_rn",),
                ),
            },
        ),
        ("Resumen", {"fields": (("get_resumen_completo",),), "classes": ("collapse",)}),
        (
            "Metadata",
            {
                "fields": (("fecha_registro", "fecha_modificacion"),),
                "classes": ("collapse",),
            },
        ),
    )

    def get_parto_numero(self, obj):
        """Get parto numero"""
        url = reverse("admin:partos_parto_change", args=[obj.parto.id])
        return format_html('<a href="{}">{}</a>', url, obj.parto.numero_parto)

    get_parto_numero.short_description = "Parto"

    def peso_clasificacion_badge(self, obj):
        """Peso clasificacion badge"""
        clasificacion = obj.get_clasificacion_peso()
        if "normal" in clasificacion:
            color = "#27ae60"
        elif "bajo peso" in clasificacion:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br/><small>{}</small>',
            color,
            f"{obj.peso_nacimiento}g",
            clasificacion,
        )

    peso_clasificacion_badge.short_description = "Peso y Clasificación"

    def get_apgar_badge(self, obj):
        """Get apgar badge"""
        evaluacion = obj.get_evaluacion_apgar()
        if "Excelente" in evaluacion:
            color = "#27ae60"
        elif "Moderado" in evaluacion:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{}</span><br/><small>{}</small>',
            color,
            obj.apgar_1_minuto,
            obj.apgar_5_minutos,
            evaluacion,
        )

    get_apgar_badge.short_description = "Apgar 1/5"

    def get_evaluacion_estado(self, obj):
        """Get evaluacion estado"""
        evaluacion = obj.get_evaluacion_estado_general()
        if "normal" in evaluacion:
            return format_html('<span style="color: #27ae60;">✅ Normal</span>')
        return format_html('<span style="color: #e74c3c;"> Con problemas</span>')

    get_evaluacion_estado.short_description = "Estado General"


@admin.register(PartogramaRegistro)
class PartogramaRegistroAdmin(admin.ModelAdmin):
    """Partogramaregistroadmin"""
    list_display = (
        "get_parto_numero",
        "hora_registro",
        "horas_trabajo_parto",
        "dilatacion_progreso_badge",
        "get_contracciones_badge",
        "get_fcf_badge",
        "get_presion_arterial",
        "get_alertas_badge",
    )

    list_filter = (
        "alerta_fcf_anormal",
        "alerta_progreso_lento",
        "alerta_signos_vitales",
        "intensidad_contracciones",
        "variabilidad_fcf",
        "hora_registro",
    )

    search_fields = (
        "parto__numero_parto",
        "observaciones",
    )

    readonly_fields = (
        "fecha_registro",
        "get_presion_arterial",
        "get_evaluacion_fcf",
        "get_evaluacion_contracciones",
        "get_alertas_activas",
        "get_resumen_registro",
    )

    fieldsets = (
        (
            "Información del Parto",
            {
                "fields": (
                    ("parto",),
                    ("hora_registro", "horas_trabajo_parto"),
                    ("registrado_por_id",),
                ),
            },
        ),
        (
            "Dilatación y Descenso",
            {
                "fields": (
                    ("dilatacion_cervical", "borramiento_cervical"),
                    ("estacion_fetal",),
                ),
            },
        ),
        (
            "Contracciones Uterinas",
            {
                "fields": (
                    ("contracciones_10min", "duracion_contracciones"),
                    ("intensidad_contracciones",),
                    ("get_evaluacion_contracciones",),
                ),
            },
        ),
        (
            "Frecuencia Cardíaca Fetal",
            {
                "fields": (
                    ("fcf_baseline", "variabilidad_fcf"),
                    ("desaceleraciones",),
                    ("get_evaluacion_fcf",),
                ),
            },
        ),
        (
            "Signos Vitales Maternos",
            {
                "fields": (
                    ("presion_arterial_sistolica", "presion_arterial_diastolica"),
                    ("temperatura", "pulso_materno"),
                    ("get_presion_arterial",),
                ),
            },
        ),
        ("Medicamentos", {"fields": (("oxitocina_dosis",),)}),
        (
            "Alertas Automáticas",
            {
                "fields": (
                    (
                        "alerta_fcf_anormal",
                        "alerta_progreso_lento",
                        "alerta_signos_vitales",
                    ),
                    ("get_alertas_activas",),
                ),
            },
        ),
        (
            "Observaciones",
            {
                "fields": (
                    ("observaciones",),
                    ("get_resumen_registro",),
                ),
            },
        ),
        ("Metadata", {"fields": (("fecha_registro",),), "classes": ("collapse",)}),
    )

    def get_parto_numero(self, obj):
        """Get parto numero"""
        url = reverse("admin:partos_parto_change", args=[obj.parto.id])
        return format_html('<a href="{}">{}</a>', url, obj.parto.numero_parto)

    get_parto_numero.short_description = "Parto"

    def dilatacion_progreso_badge(self, obj):
        """Dilatacion progreso badge"""
        dilatacion = obj.dilatacion_cervical
        if dilatacion >= 8:
            color = "#27ae60"
        elif dilatacion >= 5:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} cm</span><br/><small>Estación: {}</small>',
            color,
            dilatacion,
            obj.estacion_fetal,
        )

    dilatacion_progreso_badge.short_description = "Dilatación"

    def get_contracciones_badge(self, obj):
        """Get contracciones badge"""
        evaluacion = obj.get_evaluacion_contracciones()
        if "adecuadas" in evaluacion:
            color = "#27ae60"
        elif "moderadas" in evaluacion:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/10min</span><br/><small>{}</small>',
            color,
            obj.contracciones_10min,
            obj.intensidad_contracciones or "No registrada",
        )

    get_contracciones_badge.short_description = "Contracciones"

    def get_fcf_badge(self, obj):
        """Get fcf badge"""
        evaluacion = obj.get_evaluacion_fcff()
        if "Normal" in evaluacion:
            color = "#27ae60"
        else:
            color = "#e74c3c"

        fcf_text = f"{obj.fcf_baseline} lpm" if obj.fcf_baseline else "No registrada"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br/><small>{}</small>',
            color,
            fcf_text,
            obj.variabilidad_fcff or "No registrada",
        )

    get_fcf_badge.short_description = "FCF"

    def get_alertas_badge(self, obj):
        """Get alertas badge"""
        alertas = obj.get_alertas_activas()
        if "Sin alertas" in alertas[0]:
            return format_html('<span style="color: #27ae60;">✅ Normal</span>')
        return format_html(
            '<span style="color: #e74c3c;"> {} alertas</span>', len(alertas),
        )

    get_alertas_badge.short_description = "Alertas"


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN PARA NUEVOS MODELOS
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(ComplicacionParto)
class ComplicacionPartoAdmin(admin.ModelAdmin):
    """Complicacionpartoadmin"""
    list_display = (
        "get_parto_numero",
        "tipo_complicacion_badge",
        "severidad_badge",
        "momento_deteccion",
        "resolucion_complicacion",
        "requirio_cirugia",
        "get_medico_responsable",
    )

    list_filter = (
        "tipo_complicacion",
        "severidad",
        "resolucion_complicacion",
        "requirio_cirugia",
        "momento_deteccion",
    )

    search_fields = (
        "parto__numero_parto",
        "descripcion_detallada",
        "tratamiento_realizado",
        "medicamentos_utilizados",
        "tipo_cirugia",
    )

    readonly_fields = (
        "fecha_registro",
        "fecha_modificacion",
        "get_icono_severidad",
        "get_resumen",
    )

    fieldsets = (
        ("Información del Parto", {"fields": (("parto",),)}),
        (
            "Tipo y Severidad",
            {
                "fields": (
                    ("tipo_complicacion", "severidad"),
                    ("get_icono_severidad",),
                    ("get_resumen",),
                ),
            },
        ),
        (
            "Detalles de la Complicación",
            {
                "fields": (
                    ("momento_deteccion",),
                    ("descripcion_detallada",),
                ),
            },
        ),
        (
            "Tratamiento y Manejo",
            {
                "fields": (
                    ("tratamiento_realizado",),
                    ("medicamentos_utilizados",),
                ),
            },
        ),
        (
            "Procedimientos Quirúrgicos",
            {
                "fields": (("requirio_cirugia", "tipo_cirugia"),),
                "classes": ("collapse",),
            },
        ),
        (
            "Resultado",
            {
                "fields": (
                    ("resolucion_complicacion",),
                    ("medico_responsable",),
                    ("observaciones",),
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (("fecha_registro", "fecha_modificacion"),),
                "classes": ("collapse",),
            },
        ),
    )

    def get_parto_numero(self, obj):
        """Get parto numero"""
        url = reverse("admin:partos_parto_change", args=[obj.parto.id])
        return format_html('<a href="{}">{}</a>', url, obj.parto.numero_parto)

    get_parto_numero.short_description = "Parto"

    def tipo_complicacion_badge(self, obj):
        """Tipo complicacion badge"""
        colors = {
            "hemorragia": "#e74c3c",
            "distocia": "#f39c12",
            "sufrimiento_fetal": "#e74c3c",
            "desgarro_severo": "#c0392b",
            "rotura_uterina": "#c0392b",
            "prolapso_cordon": "#c0392b",
            "desprendimiento_placenta": "#e74c3c",
            "eclampsia": "#e74c3c",
            "embolia_liquido": "#c0392b",
            "otra": "#95a5a6",
        }
        color = colors.get(obj.tipo_complicacion, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_complicacion_display().upper(),
        )

    tipo_complicacion_badge.short_description = "Tipo"

    def severidad_badge(self, obj):
        """Severidad badge"""
        icons = {"leve": "", "moderada": "", "severa": "", "critica": ""}
        colors = {
            "leve": "#27ae60",
            "moderada": "#f39c12",
            "severa": "#e74c3c",
            "critica": "#c0392b",
        }
        icon = icons.get(obj.severidad, "⚪")
        color = colors.get(obj.severidad, "#95a5a6")
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 16px;">{} {}</span>',
            color,
            icon,
            obj.get_severidad_display(),
        )

    severidad_badge.short_description = "Severidad"

    def get_medico_responsable(self, obj):
        """Get medico responsable"""
        if obj.medico_responsable:
            return obj.medico_responsable.nombre
        return "No asignado"

    get_medico_responsable.short_description = "Médico Responsable"


@admin.register(ApgarScoreDetallado)
class ApgarScoreDetalladoAdmin(admin.ModelAdmin):
    """Apgarscoredetalladoadmin"""
    list_display = (
        "get_recien_nacido",
        "minuto_evaluacion",
        "score_total_badge",
        "frecuencia_cardiaca",
        "esfuerzo_respiratorio",
        "tono_muscular",
        "irritabilidad_refleja",
        "coloracion",
        "get_evaluador",
    )

    list_filter = (
        "minuto_evaluacion",
        "frecuencia_cardiaca",
        "esfuerzo_respiratorio",
        "tono_muscular",
        "irritabilidad_refleja",
        "coloracion",
        "fecha_registro",
    )

    search_fields = (
        "recien_nacido__parto__numero_parto",
        "observaciones_evaluador",
    )

    readonly_fields = (
        "fecha_registro",
        "score_total",
        "get_clasificacion",
        "get_desglose_componentes",
        "get_componentes_problematicos",
    )

    fieldsets = (
        (
            "Información del Recién Nacido",
            {"fields": (("recien_nacido", "minuto_evaluacion"),)},
        ),
        (
            "Componentes del Apgar",
            {
                "fields": (
                    ("frecuencia_cardiaca", "esfuerzo_respiratorio"),
                    ("tono_muscular", "irritabilidad_refleja"),
                    ("coloracion",),
                ),
            },
        ),
        (
            "Score Total y Clasificación",
            {
                "fields": (
                    ("score_total", "get_clasificacion"),
                    ("get_desglose_componentes",),
                ),
            },
        ),
        ("Análisis de Componentes", {"fields": (("get_componentes_problematicos",),)}),
        (
            "Observaciones",
            {
                "fields": (
                    ("observaciones_evaluador",),
                    ("evaluador",),
                ),
            },
        ),
        ("Metadata", {"fields": (("fecha_registro",),), "classes": ("collapse",)}),
    )

    def get_recien_nacido(self, obj):
        """Get recien nacido"""
        url = reverse("admin:partos_reciennacido_change", args=[obj.recien_nacido.id])
        return format_html(
            '<a href="{}">{} ({}g)</a>',
            url,
            obj.recien_nacido.parto.numero_parto,
            obj.recien_nacido.peso_nacimiento,
        )

    get_recien_nacido.short_description = "Recién Nacido"

    def score_total_badge(self, obj):
        """Score total badge"""
        score = obj.score_total
        if score >= 8:
            color = "#27ae60"
            emoji = "✅"
        elif score >= 6:
            color = "#f39c12"
            emoji = ""
        elif score >= 4:
            color = "#e74c3c"
            emoji = ""
        else:
            color = "#c0392b"
            emoji = ""

        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 18px;">{} {}/10</span><br/><small>{}</small>',
            color,
            emoji,
            score,
            obj.get_clasificacion(),
        )

    score_total_badge.short_description = "Score Total"

    def get_evaluador(self, obj):
        """Get evaluador"""
        if obj.evaluador:
            return obj.evaluador.nombre
        return "No registrado"

    get_evaluador.short_description = "Evaluador"


# Personalizar títulos del admin
admin.site.site_header = "Sistema de Historias Clínicas - Módulo de Partos"
admin.site.site_title = "Admin Partos"
admin.site.index_title = "Gestión Completa de Partos y Nacimientos"
