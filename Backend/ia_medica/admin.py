"""=============================================================================
ADMIN: IA MÉDICA
=============================================================================
Panel de administración para el sistema de IA Médico
=============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AnalisisCNN,
    AnalisisLaboratorioML,
    ConfiguracionModeloIA,
    ConsultaIA,
    DatasetEntrenamientoIA,
    EstadisticasIA,
    ImagenEcografica,
    ModeloCNNConfig,
)


@admin.register(ConsultaIA)
class ConsultaIAAdmin(admin.ModelAdmin):
    """Consultaiaadmin"""
    list_display = [
        "id",
        "usuario",
        "categoria",
        "idioma_detectado",
        "confianza_badge",
        "fecha_consulta",
        "util_badge",
    ]
    list_filter = [
        "categoria",
        "idioma_detectado",
        "util",
        "requiere_ml",
        "fecha_consulta",
    ]
    search_fields = [
        "consulta_original",
        "consulta_procesada",
        "respuesta_ia",
        "usuario__email",
    ]
    readonly_fields = ["fecha_consulta", "tiempo_respuesta_ms"]

    fieldsets = (
        ("Información Básica", {"fields": ("usuario", "paciente", "fecha_consulta")}),
        (
            "Consulta",
            {
                "fields": (
                    "consulta_original",
                    "consulta_procesada",
                    "idioma_detectado",
                    "categoria",
                ),
            },
        ),
        (
            "Respuesta IA",
            {"fields": ("respuesta_ia", "confianza", "tiempo_respuesta_ms")},
        ),
        (
            "Machine Learning",
            {"fields": ("requiere_ml", "resultado_ml"), "classes": ("collapse",)},
        ),
        (
            "Feedback",
            {
                "fields": ("util", "rating", "comentario_feedback"),
                "classes": ("collapse",),
            },
        ),
    )

    def confianza_badge(self, obj):
        """Confianza badge"""
        color = (
            "green"
            if obj.confianza >= 90
            else "orange"
            if obj.confianza >= 70
            else "red"
        )
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, obj.confianza,
        )

    confianza_badge.short_description = "Confianza"

    def util_badge(self, obj):
        """Util badge"""
        if obj.util is None:
            return format_html('<span style="color: gray;">Sin feedback</span>')
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if obj.util else "red",
            "✓ Útil" if obj.util else "✗ No útil",
        )

    util_badge.short_description = "Útil"


@admin.register(AnalisisLaboratorioML)
class AnalisisLaboratorioMLAdmin(admin.ModelAdmin):
    """Analisislaboratoriomladmin"""
    list_display = [
        "id",
        "paciente",
        "tipo_analisis",
        "riesgo_badge",
        "confianza_badge",
        "fecha_analisis",
        "validado_badge",
    ]
    list_filter = [
        "tipo_analisis",
        "riesgo_detectado",
        "validado_por_medico",
        "fecha_analisis",
    ]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno", "prediccion"]
    readonly_fields = ["fecha_analisis", "tiempo_procesamiento_ms"]

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "paciente",
                    "resultado_lab",
                    "consulta_ia",
                    "tipo_analisis",
                    "fecha_analisis",
                ),
            },
        ),
        ("Datos de Entrada", {"fields": ("datos_entrada",)}),
        (
            "Predicción ML",
            {
                "fields": (
                    "prediccion",
                    "riesgo_detectado",
                    "probabilidad",
                    "confianza_modelo",
                    "tiempo_procesamiento_ms",
                ),
            },
        ),
        (
            "Resultados",
            {
                "fields": (
                    "patologias_detectadas",
                    "alertas_criticas",
                    "valores_fuera_rango",
                    "tendencia_temporal",
                ),
            },
        ),
        ("Recomendaciones", {"fields": ("recomendaciones", "acciones_sugeridas")}),
        (
            "Modelo Usado",
            {"fields": ("modelo_usado", "version_modelo"), "classes": ("collapse",)},
        ),
        (
            "Validación Médica",
            {
                "fields": (
                    "validado_por_medico",
                    "medico_validador",
                    "fecha_validacion",
                    "notas_validacion",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def riesgo_badge(self, obj):
        """Riesgo badge"""
        colors = {
            "bajo": "green",
            "medio": "orange",
            "alto": "red",
            "critico": "darkred",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.riesgo_detectado, "gray"),
            obj.get_riesgo_detectado_display(),
        )

    riesgo_badge.short_description = "Riesgo"

    def confianza_badge(self, obj):
        """Confianza badge"""
        color = (
            "green"
            if obj.confianza_modelo >= 90
            else "orange"
            if obj.confianza_modelo >= 70
            else "red"
        )
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, obj.confianza_modelo,
        )

    confianza_badge.short_description = "Confianza"

    def validado_badge(self, obj):
        """Validado badge"""
        if obj.validado_por_medico:
            return format_html('<span style="color: green;">✓ Validado</span>')
        return format_html('<span style="color: orange;">⚠ Pendiente</span>')

    validado_badge.short_description = "Estado"


@admin.register(DatasetEntrenamientoIA)
class DatasetEntrenamientoIAAdmin(admin.ModelAdmin):
    """Datasetentrenamientoiaadmin"""
    list_display = [
        "id",
        "tipo_dato",
        "categoria_medica",
        "idioma",
        "fuente",
        "validado_badge",
        "usado_badge",
        "fecha_creacion",
    ]
    list_filter = [
        "tipo_dato",
        "fuente",
        "idioma",
        "validado",
        "usado_entrenamiento",
        "especialidad",
    ]
    search_fields = ["texto_entrada", "texto_salida", "categoria_medica", "keywords"]
    readonly_fields = ["fecha_creacion", "fecha_modificacion", "fecha_ultimo_uso"]

    fieldsets = (
        (
            "Clasificación",
            {
                "fields": (
                    "tipo_dato",
                    "fuente",
                    "idioma",
                    "especialidad",
                    "categoria_medica",
                ),
            },
        ),
        ("Contenido", {"fields": ("texto_entrada", "texto_salida")}),
        ("Metadatos Médicos", {"fields": ("keywords", "etiquetas")}),
        (
            "Datos Estructurados (ML)",
            {"fields": ("datos_estructurados",), "classes": ("collapse",)},
        ),
        ("Validación", {"fields": ("validado", "validador", "fecha_validacion")}),
        (
            "Uso en Entrenamiento",
            {
                "fields": ("usado_entrenamiento", "fecha_ultimo_uso", "efectividad"),
                "classes": ("collapse",),
            },
        ),
        (
            "Auditoría",
            {
                "fields": ("fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )

    def validado_badge(self, obj):
        """Validado badge"""
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if obj.validado else "orange",
            "✓ Validado" if obj.validado else "⚠ Pendiente",
        )

    validado_badge.short_description = "Validado"

    def usado_badge(self, obj):
        """Usado badge"""
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if obj.usado_entrenamiento else "gray",
            "✓ Usado" if obj.usado_entrenamiento else "- No usado",
        )

    usado_badge.short_description = "Usado"


@admin.register(ConfiguracionModeloIA)
class ConfiguracionModeloIAAdmin(admin.ModelAdmin):
    """Configuracionmodeloiaadmin"""
    list_display = [
        "nombre_modelo",
        "version",
        "tipo_modelo",
        "estado_badge",
        "activo_badge",
        "precision_badge",
        "fecha_creacion",
    ]
    list_filter = ["tipo_modelo", "estado", "activo", "fecha_creacion"]
    search_fields = ["nombre_modelo", "descripcion"]
    readonly_fields = [
        "fecha_creacion",
        "fecha_actualizacion",
        "total_predicciones",
        "ultima_prediccion",
    ]

    fieldsets = (
        (
            "Identificación",
            {"fields": ("nombre_modelo", "tipo_modelo", "version", "descripcion")},
        ),
        ("Estado", {"fields": ("estado", "activo")}),
        (
            "Métricas de Rendimiento",
            {"fields": ("precision", "recall", "f1_score", "accuracy")},
        ),
        (
            "Configuración",
            {"fields": ("parametros", "features_usadas"), "classes": ("collapse",)},
        ),
        (
            "Entrenamiento",
            {
                "fields": ("dataset_entrenamiento", "fecha_entrenamiento", "epocas"),
                "classes": ("collapse",),
            },
        ),
        (
            "Archivos del Modelo",
            {
                "fields": ("ruta_modelo", "ruta_vectorizer", "ruta_scaler"),
                "classes": ("collapse",),
            },
        ),
        (
            "Uso en Producción",
            {
                "fields": (
                    "total_predicciones",
                    "predicciones_correctas",
                    "ultima_prediccion",
                ),
            },
        ),
        (
            "Metadatos",
            {
                "fields": (
                    "creado_por",
                    "fecha_creacion",
                    "fecha_actualizacion",
                    "notas",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def estado_badge(self, obj):
        """Estado badge"""
        colors = {
            "desarrollo": "gray",
            "entrenamiento": "blue",
            "prueba": "orange",
            "produccion": "green",
            "deprecado": "red",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.estado, "gray"),
            obj.get_estado_display(),
        )

    estado_badge.short_description = "Estado"

    def activo_badge(self, obj):
        """Activo badge"""
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if obj.activo else "red",
            "✓ Activo" if obj.activo else "✗ Inactivo",
        )

    activo_badge.short_description = "Activo"

    def precision_badge(self, obj):
        """Precision badge"""
        color = (
            "green"
            if obj.precision >= 90
            else "orange"
            if obj.precision >= 70
            else "red"
        )
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, obj.precision,
        )

    precision_badge.short_description = "Precisión"


@admin.register(EstadisticasIA)
class EstadisticasIAAdmin(admin.ModelAdmin):
    """Estadisticasiaadmin"""
    list_display = [
        "fecha",
        "total_consultas",
        "total_analisis_ml",
        "alertas_criticas_generadas",
        "precision_badge",
        "rating_badge",
    ]
    list_filter = ["fecha"]
    readonly_fields = ["actualizado_en"]

    fieldsets = (
        ("Periodo", {"fields": ("fecha",)}),
        (
            "Consultas",
            {
                "fields": (
                    "total_consultas",
                    "consultas_por_categoria",
                    "tiempo_respuesta_promedio_ms",
                ),
            },
        ),
        (
            "Análisis ML",
            {
                "fields": (
                    "total_analisis_ml",
                    "alertas_criticas_generadas",
                    "patologias_detectadas",
                ),
            },
        ),
        ("Precisión", {"fields": ("precision_promedio", "confianza_promedio")}),
        (
            "Feedback",
            {"fields": ("total_feedback", "feedback_positivo", "rating_promedio")},
        ),
        ("Usuarios", {"fields": ("usuarios_activos", "nuevos_usuarios")}),
        ("Metadatos", {"fields": ("actualizado_en",)}),
    )

    def precision_badge(self, obj):
        """Precision badge"""
        color = (
            "green"
            if obj.precision_promedio >= 90
            else "orange"
            if obj.precision_promedio >= 70
            else "red"
        )
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, obj.precision_promedio,
        )

    precision_badge.short_description = "Precisión"

    def rating_badge(self, obj):
        """Rating badge"""
        stars = "⭐" * int(obj.rating_promedio)
        return format_html("<span>{} ({:.1f})</span>", stars, obj.rating_promedio)

    rating_badge.short_description = "Rating"


# =============================================================================
# ADMIN CNN
# =============================================================================


@admin.register(ImagenEcografica)
class ImagenEcograficaAdmin(admin.ModelAdmin):
    """Imagenecograficaadmin"""
    list_display = (
        "id",
        "paciente",
        "tipo_imagen",
        "estado",
        "fecha_subida",
        "tamanio_mb",
        "es_principal",
    )
    list_filter = ("tipo_imagen", "estado", "fecha_subida", "es_principal")
    search_fields = ("paciente__nombre", "paciente__apellido_paterno", "descripcion")
    readonly_fields = (
        "fecha_subida",
        "fecha_actualizacion",
        "resolucion_ancho",
        "resolucion_alto",
    )
    raw_id_fields = ("paciente", "subida_por")


@admin.register(AnalisisCNN)
class AnalisisCNNAdmin(admin.ModelAdmin):
    """Analisiscnnadmin"""
    list_display = (
        "id",
        "imagen",
        "modelo_usado",
        "resultado",
        "confianza_porcentaje",
        "fecha_analisis",
        "validado_por_medico",
    )
    list_filter = ("modelo_usado", "resultado", "validado_por_medico", "fecha_analisis")
    search_fields = ("imagen__paciente__nombre", "notas_medico")
    readonly_fields = ("fecha_analisis",)
    raw_id_fields = ("imagen", "realizado_por", "medico_validador")


@admin.register(ModeloCNNConfig)
class ModeloCNNConfigAdmin(admin.ModelAdmin):
    """Modelocnnconfigadmin"""
    list_display = (
        "nombre",
        "codigo",
        "version",
        "estado",
        "accuracy",
        "total_predicciones",
    )
    list_filter = ("estado", "arquitectura")
    search_fields = ("nombre", "codigo", "descripcion")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion", "total_predicciones")
