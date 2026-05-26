"""=============================================================================
ADMIN CONFIGURATION - CALCULADORAS Y LABORATORIO
=============================================================================
"""

from django.contrib import admin

from .models import BiomarcadorMOM, CalculadoraRiesgo, MedicionEcografica
from .models_laboratorio import Bioquimica, Hemograma, MarcadorEmbarazo

# =============================================================================
# LABORATORIO CLÍNICO
# =============================================================================


@admin.register(Hemograma)
class HemogramaAdmin(admin.ModelAdmin):
    """Admin para hemogramas completos"""

    list_display = [
        "paciente",
        "fecha_toma",
        "semanas_gestacion",
        "hemoglobina",
        "leucocitos",
        "plaquetas",
        "clasificacion",
        "es_critico",
    ]
    list_filter = [
        "clasificacion",
        "es_critico",
        "fecha_toma",
        ("embarazo", admin.EmptyFieldListFilter),
    ]
    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
    ]
    readonly_fields = [
        "clasificacion",
        "es_critico",
        "alertas",
        "interpretacion_automatica",
        "fecha_resultado",
        "fecha_creacion",
        "fecha_modificacion",
    ]
    fieldsets = (
        (
            "Información del Paciente",
            {"fields": ("paciente", "embarazo", "medico_solicitante")},
        ),
        ("Fechas", {"fields": ("fecha_toma", "fecha_resultado", "semanas_gestacion")}),
        (
            "Eritrograma",
            {
                "fields": (
                    "hemoglobina",
                    "hematocrito",
                    "eritrocitos",
                    "vcm",
                    "hcm",
                    "chcm",
                    "rdw",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Leucograma",
            {
                "fields": (
                    "leucocitos",
                    "neutrofilos",
                    "linfocitos",
                    "monocitos",
                    "eosinofilos",
                    "basofilos",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Plaquetas", {"fields": ("plaquetas", "vpm")}),
        (
            "Clasificación Automática",
            {
                "fields": (
                    "clasificacion",
                    "es_critico",
                    "alertas",
                    "interpretacion_automatica",
                ),
            },
        ),
        (
            "Observaciones",
            {"fields": ("observaciones_medicas",), "classes": ("collapse",)},
        ),
    )
    date_hierarchy = "fecha_toma"
    ordering = ["-fecha_toma"]


@admin.register(Bioquimica)
class BioquimicaAdmin(admin.ModelAdmin):
    """Admin para bioquímicas completas"""

    list_display = [
        "paciente",
        "fecha_toma",
        "semanas_gestacion",
        "glucosa_ayunas",
        "creatinina",
        "got_ast",
        "es_critico",
    ]
    list_filter = [
        "es_critico",
        "fecha_toma",
        ("embarazo", admin.EmptyFieldListFilter),
    ]
    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
    ]
    readonly_fields = [
        "clasificacion",
        "alertas",
        "es_critico",
        "interpretacion_automatica",
        "fecha_resultado",
        "fecha_creacion",
        "fecha_modificacion",
    ]
    fieldsets = (
        (
            "Información del Paciente",
            {"fields": ("paciente", "embarazo", "medico_solicitante")},
        ),
        ("Fechas", {"fields": ("fecha_toma", "fecha_resultado", "semanas_gestacion")}),
        (
            "Metabolismo Glucosa",
            {
                "fields": ("glucosa_ayunas", "glucosa_postprandial", "hba1c"),
                "classes": ("collapse",),
            },
        ),
        (
            "Función Renal",
            {"fields": ("creatinina", "urea", "acido_urico"), "classes": ("collapse",)},
        ),
        (
            "Función Hepática",
            {
                "fields": (
                    "got_ast",
                    "gpt_alt",
                    "bilirrubina_total",
                    "bilirrubina_directa",
                    "fosfatasa_alcalina",
                    "albumina",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Electrolitos",
            {
                "fields": ("sodio", "potasio", "cloro", "calcio", "magnesio"),
                "classes": ("collapse",),
            },
        ),
        (
            "Lípidos",
            {
                "fields": ("colesterol_total", "ldl", "hdl", "trigliceridos"),
                "classes": ("collapse",),
            },
        ),
        ("Otros", {"fields": ("proteinas_totales", "ldh"), "classes": ("collapse",)}),
        (
            "Clasificación Automática",
            {
                "fields": (
                    "clasificacion",
                    "es_critico",
                    "alertas",
                    "interpretacion_automatica",
                ),
            },
        ),
        (
            "Observaciones",
            {"fields": ("observaciones_medicas",), "classes": ("collapse",)},
        ),
    )
    date_hierarchy = "fecha_toma"
    ordering = ["-fecha_toma"]


@admin.register(MarcadorEmbarazo)
class MarcadorEmbarazoAdmin(admin.ModelAdmin):
    """Admin para marcadores de embarazo"""

    list_display = [
        "paciente",
        "embarazo",
        "fecha_toma",
        "semanas_gestacion",
        "dias_adicionales",
        "papp_a_mom",
        "plgf_mom",
        "ratio_sflt_plgf",
    ]
    list_filter = ["fecha_toma", "semanas_gestacion"]
    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
    ]
    readonly_fields = [
        "beta_hcg_mom",
        "papp_a_mom",
        "free_bhcg_mom",
        "plgf_mom",
        "sflt1_mom",
        "ratio_sflt_plgf",
        "clasificacion",
        "alertas",
        "interpretacion_automatica",
        "fecha_creacion",
    ]
    fieldsets = (
        (
            "Información del Paciente",
            {"fields": ("paciente", "embarazo", "medico_solicitante")},
        ),
        (
            "Edad Gestacional",
            {"fields": ("fecha_toma", "semanas_gestacion", "dias_adicionales")},
        ),
        (
            "Marcadores Crudos",
            {
                "fields": ("beta_hcg", "papp_a", "free_bhcg", "plg", "sflt1"),
                "description": "Valores medidos en laboratorio",
            },
        ),
        (
            "Valores MoM (Calculados)",
            {
                "fields": (
                    "beta_hcg_mom",
                    "papp_a_mom",
                    "free_bhcg_mom",
                    "plgf_mom",
                    "sflt1_mom",
                    "ratio_sflt_plgf",
                ),
                "description": "Múltiplos de la Mediana ajustados",
            },
        ),
        (
            "Interpretación",
            {"fields": ("clasificacion", "alertas", "interpretacion_automatica")},
        ),
    )
    date_hierarchy = "fecha_toma"
    ordering = ["-fecha_toma"]


# =============================================================================
# CALCULADORAS FMF
# =============================================================================


@admin.register(CalculadoraRiesgo)
class CalculadoraRiesgoAdmin(admin.ModelAdmin):
    """Admin para calculadoras de riesgo"""

    list_display = [
        "paciente",
        "tipo",
        "fecha_calculo",
        "edad_gestacional_semanas",
        "riesgo_porcentaje",
        "categoria_riesgo",
    ]
    list_filter = ["tipo", "categoria_riesgo", "fecha_calculo"]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno"]
    readonly_fields = [
        "riesgo_porcentaje",
        "riesgo_ratio",
        "categoria_riesgo",
        "interpretacion_clinica",
        "recomendaciones",
        "conducta_sugerida",
        "fecha_calculo",
        "imc",
    ]
    date_hierarchy = "fecha_calculo"
    ordering = ["-fecha_calculo"]


@admin.register(BiomarcadorMOM)
class BiomarcadorMOMAdmin(admin.ModelAdmin):
    """Admin para biomarcadores MoM"""

    list_display = [
        "calculadora",
        "marcador",
        "valor_crudo",
        "mom_calculado",
        "dentro_rango",
        "fecha_medicion",
    ]
    list_filter = ["marcador", "dentro_rango"]
    readonly_fields = [
        "mediana_esperada",
        "mediana_base",
        "mom_calculado",
        "correccion_peso",
        "correccion_etnia",
        "correccion_tabaco",
        "correccion_diabetes",
        "dentro_rango",
        "interpretacion",
    ]


@admin.register(MedicionEcografica)
class MedicionEcograficaAdmin(admin.ModelAdmin):
    """Admin para mediciones ecográficas"""

    list_display = [
        "calculadora",
        "crl_mm",
        "nt_mm",
        "bpd_mm",
        "efw_gramos",
        "fecha_medicion",
    ]
    readonly_fields = ["nt_percentil", "efw_percentil", "crl_percentil"]
