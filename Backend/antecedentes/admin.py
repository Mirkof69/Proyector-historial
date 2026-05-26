"""=============================================================================
ANTECEDENTES - ADMIN
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import AntecedenteGinecoObstetrico, AntecedentePatologico


@admin.register(AntecedenteGinecoObstetrico)
class AntecedenteGinecoObstetricoAdmin(admin.ModelAdmin):
    """Antecedenteginecoobstetricoadmin"""
    list_display = (
        "paciente",
        "get_formula_obstetrica_display",
        "get_fum",
        "menarquia_edad",
        "ciclos_menstruales",
        "metodo_anticonceptivo_actual",
        "fecha_registro",
    )

    list_filter = (
        "ciclos_menstruales",
        "gestas",
        "partos",
        "cesareas",
        "fecha_registro",
    )

    search_fields = (
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__ci",
        "metodo_anticonceptivo_actual",
    )

    readonly_fields = ("fecha_registro", "fecha_modificacion")

    fieldsets = (
        ("Paciente", {"fields": ("paciente",)}),
        (
            "Antecedentes Menstruales",
            {
                "fields": (
                    ("menarquia_edad", "ciclos_menstruales"),
                    ("duracion_ciclo_dias", "duracion_menstruacion_dias"),
                    "fecha_ultima_menstruacion",
                ),
            },
        ),
        (
            "Fórmula Obstétrica GPAC",
            {
                "fields": (
                    ("gestas", "partos"),
                    ("abortos", "cesareas"),
                    "hijos_vivos",
                ),
            },
        ),
        (
            "Anticoncepción",
            {
                "fields": (
                    "metodo_anticonceptivo_actual",
                    "tiempo_uso_anticonceptivo_meses",
                    "fecha_suspension_anticonceptivo",
                ),
            },
        ),
        (
            "Vida Sexual",
            {
                "fields": (
                    "inicio_vida_sexual_edad",
                    "numero_parejas_sexuales",
                ),
            },
        ),
        (
            "Metadatos",
            {
                "fields": (
                    "fecha_registro",
                    "fecha_modificacion",
                    "modificado_por",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_formula_obstetrica_display(self, obj):
        """Muestra fórmula GPAC con badge"""
        formula = obj.get_formula_obstetrica()
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            formula,
        )

    get_formula_obstetrica_display.short_description = "GPAC"

    def get_fum(self, obj):
        """Muestra FUM formateada"""
        if obj.fecha_ultima_menstruacion:
            return obj.fecha_ultima_menstruacion.strftime("%d/%m/%Y")
        return "-"

    get_fum.short_description = "FUM"


@admin.register(AntecedentePatologico)
class AntecedentePatologicoAdmin(admin.ModelAdmin):
    """Antecedentepatologicoadmin"""
    list_display = (
        "paciente",
        "tipo",
        "get_alergias_badge",
        "get_enfermedades_cronicas",
        "get_riesgo_badge",
        "fecha_registro",
    )

    list_filter = (
        "tipo",
        "tiene_alergias",
        "diabetes",
        "hipertension",
        "cardiopatias",
        "preeclampsia_previa",
        "eclampsia_previa",
        "fecha_registro",
    )

    search_fields = (
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__ci",
        "alergias_medicamentos",
        "alergias_alimentos",
        "otras_enfermedades",
    )

    readonly_fields = ("fecha_registro", "fecha_modificacion")

    fieldsets = (
        (
            "Paciente y Tipo",
            {
                "fields": (
                    "paciente",
                    "tipo",
                ),
            },
        ),
        (
            "⚠️ ALERGIAS (CRÍTICO)",
            {
                "fields": (
                    "tiene_alergias",
                    "alergias_medicamentos",
                    "alergias_alimentos",
                    "alergias_otras",
                ),
                "classes": ("wide",),
                "description": "IMPORTANTE: Registrar todas las alergias para evitar reacciones adversas",
            },
        ),
        (
            "Enfermedades Endocrinas",
            {
                "fields": (
                    "diabetes",
                    "diabetes_tipo",
                ),
            },
        ),
        (
            "Enfermedades Cardiovasculares",
            {
                "fields": (
                    "hipertension",
                    "cardiopatias",
                    "cardiopatia_detalle",
                ),
            },
        ),
        (
            "Enfermedades Renales",
            {
                "fields": (
                    "nefropatias",
                    "nefropatia_detalle",
                ),
            },
        ),
        (
            "Enfermedades Hematológicas",
            {
                "fields": (
                    "trastornos_coagulacion",
                    "anemia",
                ),
            },
        ),
        (
            "Enfermedades Autoinmunes",
            {
                "fields": (
                    "lupus",
                    "artritis_reumatoide",
                ),
            },
        ),
        ("Enfermedades Respiratorias", {"fields": ("asma",)}),
        (
            "Antecedentes Obstétricos",
            {
                "fields": (
                    "preeclampsia_previa",
                    "eclampsia_previa",
                    "diabetes_gestacional_previa",
                    "hemorragia_postparto_previa",
                ),
            },
        ),
        (
            "Otros",
            {
                "fields": (
                    "otras_enfermedades",
                    "cirugiasanteriores",
                ),
            },
        ),
        (
            "Metadatos",
            {
                "fields": (
                    "fecha_registro",
                    "fecha_modificacion",
                    "registrado_por",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_alergias_badge(self, obj):
        """Badge de alergias"""
        if obj.tiene_alergias:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⚠️ SÍ</span>',
            )
        return format_html(
            '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px;">NO</span>',
        )

    get_alergias_badge.short_description = "Alergias"

    def get_enfermedades_cronicas(self, obj):
        """Lista enfermedades crónicas"""
        enfermedades = []
        if obj.diabetes:
            enfermedades.append("DM")
        if obj.hipertension:
            enfermedades.append("HTA")
        if obj.cardiopatias:
            enfermedades.append("Cardio")
        if obj.asma:
            enfermedades.append("Asma")

        if enfermedades:
            return ", ".join(enfermedades)
        return "-"

    get_enfermedades_cronicas.short_description = "Enfermedades"

    def get_riesgo_badge(self, obj):
        """Badge de riesgo"""
        if obj.tiene_factores_riesgo():
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 3px;">⚠️ ALTO RIESGO</span>',
            )
        return format_html(
            '<span style="background-color: #95a5a6; color: white; padding: 3px 8px; border-radius: 3px;">Normal</span>',
        )

    get_riesgo_badge.short_description = "Riesgo"
