"""=============================================================================
MODELOS: IA MÉDICA - Sistema de Asistente Inteligente
=============================================================================
Modelos para el sistema de IA médico con machine learning
=============================================================================
"""

from django.contrib.auth import get_user_model
from django.db import models

from laboratorio.models import ResultadoLaboratorio
from pacientes.models import Paciente

User = get_user_model()


class ConsultaIA(models.Model):
    """Registro de consultas realizadas al asistente IA"""

    CATEGORIA_CHOICES = [
        ("preeclampsia", "Preeclampsia"),
        ("diabetes", "Diabetes Gestacional"),
        ("rciu", "Restricción Crecimiento Intrauterino"),
        ("laboratorio", "Análisis de Laboratorio"),
        ("edad_gestacional", "Edad Gestacional"),
        ("general", "Consulta General"),
        ("emergencia", "Emergencia Obstétrica"),
    ]

    IDIOMA_CHOICES = [
        ("es", "Español"),
        ("en", "Inglés"),
        ("auto", "Auto-detectado"),
    ]

    # Identificación
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="consultas_ia",
    )
    paciente = models.ForeignKey(
        Paciente, on_delete=models.SET_NULL, null=True, blank=True,
    )

    # Consulta
    consulta_original = models.TextField(help_text="Texto original de la consulta")
    consulta_procesada = models.TextField(help_text="Texto procesado/normalizado")
    idioma_detectado = models.CharField(
        max_length=10, choices=IDIOMA_CHOICES, default="auto",
    )
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)

    # Respuesta
    respuesta_ia = models.TextField(help_text="Respuesta generada por la IA")
    confianza = models.FloatField(default=0.0, help_text="Nivel de confianza (0-100)")

    # Análisis ML
    requiere_ml = models.BooleanField(
        default=False, help_text="Si requiere análisis ML avanzado",
    )
    resultado_ml = models.JSONField(
        null=True, blank=True, help_text="Resultados del análisis ML",
    )

    # Feedback
    util = models.BooleanField(
        null=True, blank=True, help_text="¿Fue útil la respuesta",
    )
    rating = models.IntegerField(null=True, blank=True, help_text="Calificación 1-5")
    comentario_feedback = models.TextField(
        blank=True, help_text="Comentario del usuario",
    )

    # Metadatos
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    tiempo_respuesta_ms = models.IntegerField(
        default=0, help_text="Tiempo de procesamiento en ms",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        """Meta"""
        ordering = ["-fecha_consulta"]
        verbose_name = "Consulta IA"
        verbose_name_plural = "Consultas IA"
        indexes = [
            models.Index(fields=["-fecha_consulta"]),
            models.Index(fields=["usuario", "-fecha_consulta"]),
            models.Index(fields=["categoria"]),
        ]

    def __str__(self):
        """Str"""
        email = getattr(self.usuario, "email", str(self.usuario_id))
        return f"{email} - {self.categoria} - {self.fecha_consulta.strftime('%d/%m/%Y %H:%M')}"


class AnalisisLaboratorioML(models.Model):
    """Análisis de laboratorio usando Machine Learning"""

    TIPO_ANALISIS_CHOICES = [
        ("hemograma", "Hemograma Completo"),
        ("glucosa", "Glucosa / Diabetes"),
        ("funcion_hepatica", "Función Hepática"),
        ("funcion_renal", "Función Renal"),
        ("proteinas", "Proteínas / Proteinuria"),
        ("tiroides", "Perfil Tiroideo"),
        ("completo", "Análisis Completo"),
    ]

    RIESGO_CHOICES = [
        ("bajo", "Riesgo Bajo"),
        ("medio", "Riesgo Medio"),
        ("alto", "Riesgo Alto"),
        ("critico", "Riesgo Crítico"),
    ]

    # Relaciones
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="analisis_ml",
    )
    resultado_lab = models.ForeignKey(
        ResultadoLaboratorio, on_delete=models.CASCADE, null=True, blank=True,
    )
    consulta_ia = models.ForeignKey(
        ConsultaIA, on_delete=models.SET_NULL, null=True, blank=True,
    )

    # Tipo de análisis
    tipo_analisis = models.CharField(max_length=50, choices=TIPO_ANALISIS_CHOICES)

    # Datos de entrada (valores de laboratorio)
    datos_entrada = models.JSONField(help_text="Valores de laboratorio analizados")

    # Predicción ML
    prediccion = models.CharField(max_length=200, help_text="Predicción del modelo ML")
    riesgo_detectado = models.CharField(max_length=20, choices=RIESGO_CHOICES)
    probabilidad = models.FloatField(help_text="Probabilidad de la predicción (0-1)")
    confianza_modelo = models.FloatField(
        default=0.0, help_text="Confianza del modelo (0-100)",
    )

    # Patologías detectadas
    patologias_detectadas = models.JSONField(
        default=list, help_text="Lista de patologías detectadas",
    )
    alertas_criticas = models.JSONField(
        default=list, help_text="Alertas críticas generadas",
    )

    # Recomendaciones
    recomendaciones = models.JSONField(
        default=list, help_text="Recomendaciones basadas en ML",
    )
    acciones_sugeridas = models.JSONField(
        default=list, help_text="Acciones inmediatas sugeridas",
    )

    # Comparación con valores normales
    valores_fuera_rango = models.JSONField(
        default=list, help_text="Valores fuera de rango",
    )
    tendencia_temporal = models.JSONField(
        null=True, blank=True, help_text="Análisis de tendencia",
    )

    # Metadatos del modelo
    modelo_usado = models.CharField(max_length=100, default="RandomForest_v1")
    version_modelo = models.CharField(max_length=20, default="1.0")
    fecha_analisis = models.DateTimeField(auto_now_add=True)
    tiempo_procesamiento_ms = models.IntegerField(default=0)

    # Validación médica
    validado_por_medico = models.BooleanField(default=False)
    medico_validador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validaciones_ml",
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    notas_validacion = models.TextField(blank=True)

    class Meta:
        """Meta"""
        ordering = ["-fecha_analisis"]
        verbose_name = "Análisis ML Laboratorio"
        verbose_name_plural = "Análisis ML Laboratorio"
        indexes = [
            models.Index(fields=["-fecha_analisis"]),
            models.Index(fields=["paciente", "-fecha_analisis"]),
            models.Index(fields=["riesgo_detectado"]),
        ]

    def __str__(self):
        """Str"""
        return f"{self.paciente.nombre} - {self.tipo_analisis} - Riesgo: {self.riesgo_detectado}"


class DatasetEntrenamientoIA(models.Model):
    """Dataset para entrenar modelos de IA médica"""

    TIPO_DATO_CHOICES = [
        ("consulta_respuesta", "Par Consulta-Respuesta"),
        ("caso_clinico", "Caso Clínico"),
        ("laboratorio", "Resultado de Laboratorio"),
        ("diagnostico", "Diagnóstico"),
        ("protocolo", "Protocolo Médico"),
    ]

    FUENTE_CHOICES = [
        ("manual", "Ingreso Manual"),
        ("literatura", "Literatura Médica"),
        ("guias_clinicas", "Guías Clínicas"),
        ("casos_reales", "Casos Reales (Anonimizados)"),
        ("acog", "Guías ACOG"),
        ("who", "Guías OMS/WHO"),
    ]

    # Clasificación
    tipo_dato = models.CharField(max_length=50, choices=TIPO_DATO_CHOICES)
    fuente = models.CharField(max_length=50, choices=FUENTE_CHOICES)
    idioma = models.CharField(max_length=10, default="es")

    # Contenido
    texto_entrada = models.TextField(
        help_text="Texto de entrada (consulta, síntomas, etc.)",
    )
    texto_salida = models.TextField(
        help_text="Texto esperado de salida (respuesta, diagnóstico)",
    )

    # Metadatos médicos
    especialidad = models.CharField(max_length=100, default="Ginecología y Obstetricia")
    categoria_medica = models.CharField(max_length=100)
    keywords = models.JSONField(default=list, help_text="Palabras clave médicas")

    # Datos estructurados (para ML)
    datos_estructurados = models.JSONField(
        null=True, blank=True, help_text="Datos en formato ML",
    )
    etiquetas = models.JSONField(default=list, help_text="Etiquetas para clasificación")

    # Validación
    validado = models.BooleanField(default=False)
    validador = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)

    # Uso
    usado_entrenamiento = models.BooleanField(default=False)
    fecha_ultimo_uso = models.DateTimeField(null=True, blank=True)
    efectividad = models.FloatField(
        null=True, blank=True, help_text="Efectividad en entrenamiento",
    )

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        """Meta"""
        ordering = ["-fecha_creacion"]
        verbose_name = "Dataset Entrenamiento IA"
        verbose_name_plural = "Datasets Entrenamiento IA"
        indexes = [
            models.Index(fields=["tipo_dato"]),
            models.Index(fields=["categoria_medica"]),
            models.Index(fields=["validado"]),
        ]

    def __str__(self):
        """Str"""
        return f"{self.tipo_dato} - {self.categoria_medica} - {self.idioma}"


class ConfiguracionModeloIA(models.Model):
    """Configuración y versionado de modelos de IA"""

    TIPO_MODELO_CHOICES = [
        ("nlp", "Procesamiento Lenguaje Natural"),
        ("ml_laboratorio", "ML Análisis Laboratorio"),
        ("clasificacion", "Clasificación Patologías"),
        ("prediccion_riesgo", "Predicción de Riesgos"),
    ]

    ESTADO_CHOICES = [
        ("desarrollo", "En Desarrollo"),
        ("entrenamiento", "En Entrenamiento"),
        ("prueba", "En Pruebas"),
        ("produccion", "En Producción"),
        ("deprecado", "Deprecado"),
    ]

    # Identificación
    nombre_modelo = models.CharField(max_length=100, unique=True)
    tipo_modelo = models.CharField(max_length=50, choices=TIPO_MODELO_CHOICES)
    version = models.CharField(max_length=20)
    descripcion = models.TextField()

    # Estado
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="desarrollo",
    )
    activo = models.BooleanField(default=False)

    # Métricas de rendimiento
    precision = models.FloatField(default=0.0, help_text="Precisión del modelo (0-100)")
    recall = models.FloatField(default=0.0)
    f1_score = models.FloatField(default=0.0)
    accuracy = models.FloatField(default=0.0)

    # Configuración
    parametros = models.JSONField(default=dict, help_text="Hiperparámetros del modelo")
    features_usadas = models.JSONField(default=list, help_text="Features utilizadas")

    # Entrenamiento
    dataset_entrenamiento = models.TextField(help_text="Descripción del dataset usado")
    fecha_entrenamiento = models.DateTimeField(null=True, blank=True)
    epocas = models.IntegerField(default=0)

    # Archivos
    ruta_modelo = models.CharField(
        max_length=500, blank=True, help_text="Ruta al archivo del modelo",
    )
    ruta_vectorizer = models.CharField(max_length=500, blank=True)
    ruta_scaler = models.CharField(max_length=500, blank=True)

    # Uso en producción
    total_predicciones = models.IntegerField(default=0)
    predicciones_correctas = models.IntegerField(default=0)
    ultima_prediccion = models.DateTimeField(null=True, blank=True)

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notas = models.TextField(blank=True)

    class Meta:
        """Meta"""
        ordering = ["-fecha_creacion"]
        verbose_name = "Configuración Modelo IA"
        verbose_name_plural = "Configuraciones Modelos IA"
        unique_together = [["nombre_modelo", "version"]]

    def __str__(self):
        """Str"""
        return f"{self.nombre_modelo} v{self.version} - {self.estado}"


class EstadisticasIA(models.Model):
    """Estadísticas agregadas del sistema de IA"""

    # Periodo
    fecha = models.DateField(unique=True)

    # Consultas
    total_consultas = models.IntegerField(default=0)
    consultas_por_categoria = models.JSONField(default=dict)
    tiempo_respuesta_promedio_ms = models.IntegerField(default=0)

    # Análisis ML
    total_analisis_ml = models.IntegerField(default=0)
    alertas_criticas_generadas = models.IntegerField(default=0)
    patologias_detectadas = models.JSONField(default=dict)

    # Precisión
    precision_promedio = models.FloatField(default=0.0)
    confianza_promedio = models.FloatField(default=0.0)

    # Feedback
    total_feedback = models.IntegerField(default=0)
    feedback_positivo = models.IntegerField(default=0)
    rating_promedio = models.FloatField(default=0.0)

    # Usuarios
    usuarios_activos = models.IntegerField(default=0)
    nuevos_usuarios = models.IntegerField(default=0)

    # Metadatos
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        ordering = ["-fecha"]
        verbose_name = "Estadísticas IA"
        verbose_name_plural = "Estadísticas IA"

    def __str__(self):
        """Str"""
        return f"Estadísticas IA - {self.fecha}"


# =============================================================================
# MODELOS CNN — Imágenes y Análisis por Red Neuronal Convolucional
# =============================================================================


def imagen_ecografica_upload_path(instance, filename):
    """Ruta dinámica para guardar imágenes: media/ia_medica/imagenes/YYYY/MM/DD/"""
    from django.utils import timezone

    now = timezone.localtime()
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"ia_medica/imagenes/{now.year}/{now.month:02d}/{now.day:02d}/{instance.paciente_id}_{now.strftime('%H%M%S')}.{ext}"


class ImagenEcografica(models.Model):
    """Almacena imágenes ecográficas para análisis por CNN.
    Soporta JPEG, PNG, BMP, TIFF y DICOM.
    """

    TIPO_IMAGEN_CHOICES = [
        ("eco_2d", "Ecografía 2D"),
        ("eco_3d", "Ecografía 3D"),
        ("eco_4d", "Ecografía 4D"),
        ("doppler", "Doppler Fetal"),
        ("morfologica", "Ecografía Morfológica"),
        ("transvaginal", "Ecografía Transvaginal"),
        ("dicom", "Imagen DICOM"),
        ("otro", "Otro"),
    ]

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente de Análisis"),
        ("procesando", "Procesando"),
        ("analizada", "Analizada"),
        ("error", "Error en Análisis"),
    ]

    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="imagenes_cnn",
        help_text="Paciente dueña de la imagen",
    )
    subida_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="imagenes_subidas",
        help_text="Usuario que subió la imagen",
    )

    # Archivo
    imagen = models.ImageField(
        upload_to=imagen_ecografica_upload_path,
        help_text="Archivo de imagen ecográfica",
    )
    nombre_original = models.CharField(
        max_length=255, help_text="Nombre original del archivo",
    )
    tamanio_bytes = models.BigIntegerField(default=0, help_text="Tamaño en bytes")
    formato = models.CharField(
        max_length=20, default="jpg", help_text="Formato: jpg, png, tiff, dicom",
    )
    resolucion_ancho = models.IntegerField(default=0, help_text="Ancho en píxeles")
    resolucion_alto = models.IntegerField(default=0, help_text="Alto en píxeles")

    # Clasificación médica
    tipo_imagen = models.CharField(
        max_length=30, choices=TIPO_IMAGEN_CHOICES, default="eco_2d",
    )
    semana_gestacional = models.IntegerField(
        null=True, blank=True, help_text="Semana gestacional al momento de la imagen",
    )
    descripcion = models.TextField(
        blank=True, help_text="Descripción clínica de la imagen",
    )
    notas_tecnicas = models.TextField(
        blank=True, help_text="Notas técnicas del operador",
    )

    # Estado
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="pendiente",
    )
    es_principal = models.BooleanField(
        default=False, help_text="Imagen principal del paciente",
    )

    # Metadatos DICOM (si aplica)
    dicom_metadata = models.JSONField(
        null=True, blank=True, help_text="Metadatos DICOM extraídos",
    )

    # Timestamps
    fecha_captura = models.DateField(
        null=True, blank=True, help_text="Fecha de captura de la imagen",
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta"""
        ordering = ["-fecha_subida"]
        verbose_name = "Imagen Ecográfica CNN"
        verbose_name_plural = "Imágenes Ecográficas CNN"
        indexes = [
            models.Index(fields=["paciente", "-fecha_subida"]),
            models.Index(fields=["tipo_imagen"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        """Str"""
        return f"{self.paciente} - {self.tipo_imagen} - {self.fecha_subida.strftime('%d/%m/%Y')}"

    @property
    def url_imagen(self):
        """Url imagen"""
        if self.imagen:
            return self.imagen.url
        return None

    @property
    def tamanio_mb(self):
        """Tamanio mb"""
        return round(self.tamanio_bytes / (1024 * 1024), 2)


class AnalisisCNN(models.Model):
    """Resultado del análisis por Red Neuronal Convolucional (CNN).
    Almacena predicciones, confianza, bounding boxes y hallazgos.
    """

    MODELO_CHOICES = [
        ("resnet50", "ResNet-50 (Clasificación)"),
        ("unet", "U-Net (Segmentación)"),
        ("efficientnet", "EfficientNet-B4 (Alta Precisión)"),
        ("yolo_fetal", "YOLO Fetal (Detección)"),
        ("custom_cnn", "CNN Personalizada"),
    ]

    RESULTADO_CHOICES = [
        ("normal", "Normal"),
        ("anomalia_leve", "Anomalía Leve"),
        ("anomalia_moderada", "Anomalía Moderada"),
        ("anomalia_grave", "Anomalía Grave"),
        ("requiere_revision", "Requiere Revisión Médica"),
        ("indeterminado", "Indeterminado"),
    ]

    # Relaciones
    imagen = models.OneToOneField(
        ImagenEcografica,
        on_delete=models.CASCADE,
        related_name="analisis_cnn",
        help_text="Imagen analizada",
    )
    realizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analisis_cnn_realizados",
    )

    # Modelo CNN usado
    modelo_usado = models.CharField(
        max_length=30, choices=MODELO_CHOICES, default="resnet50",
    )
    version_modelo = models.CharField(max_length=20, default="1.0.0")

    # Resultado principal
    resultado = models.CharField(
        max_length=30, choices=RESULTADO_CHOICES, default="indeterminado",
    )
    confianza = models.FloatField(
        default=0.0, help_text="Confianza de la predicción (0.0 - 1.0)",
    )
    score_general = models.FloatField(
        default=0.0, help_text="Score general del análisis (0-100)",
    )

    # Predicciones detalladas
    predicciones = models.JSONField(
        default=list,
        help_text="Lista de predicciones: [{clase, confianza, probabilidad}]",
    )
    clases_detectadas = models.JSONField(
        default=list, help_text="Clases/estructuras anatómicas detectadas",
    )
    bounding_boxes = models.JSONField(
        null=True,
        blank=True,
        help_text="Coordenadas de detecciones: [{x, y, w, h, clase, confianza}]",
    )

    # Análisis de estructuras fetales
    estructuras_detectadas = models.JSONField(
        default=dict,
        help_text="Estructuras fetales identificadas: {cabeza, columna, corazon, etc}",
    )
    medidas_estimadas = models.JSONField(
        null=True, blank=True, help_text="Medidas estimadas por IA: {bpd, hc, ac, fl}",
    )
    anomalias_detectadas = models.JSONField(
        default=list, help_text="Lista de anomalías detectadas",
    )
    alertas = models.JSONField(default=list, help_text="Alertas clínicas generadas")
    recomendaciones = models.JSONField(
        default=list, help_text="Recomendaciones clínicas",
    )

    # Grad-CAM
    mapa_calor = models.TextField(
        blank=True, null=True, help_text="PNG base64 del mapa de calor Grad-CAM",
    )

    # Biometría fetal (medidas directas — complementan medidas_estimadas JSONB)
    bpd_mm = models.FloatField(null=True, blank=True, verbose_name="BPD (mm)")
    hc_mm = models.FloatField(null=True, blank=True, verbose_name="HC (mm)")
    ac_mm = models.FloatField(null=True, blank=True, verbose_name="AC (mm)")
    fl_mm = models.FloatField(null=True, blank=True, verbose_name="FL (mm)")

    # SHAP y riesgo materno
    riesgo_preeclampsia = models.FloatField(null=True, blank=True)
    riesgo_parto_prematuro = models.FloatField(null=True, blank=True)
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=[("BAJO", "Bajo"), ("MODERADO", "Moderado"), ("ALTO", "Alto")],
        null=True,
        blank=True,
    )
    shap_valores = models.JSONField(null=True, blank=True)
    patologias = models.JSONField(default=list, blank=True)
    sugerencia_diagnostica = models.JSONField(
        null=True, blank=True,
        help_text="Diagnóstico sugerido: {patologia, confianza, descripcion, icd10, recomendacion}",
    )

    # Tiempo de procesamiento
    tiempo_procesamiento_ms = models.IntegerField(default=0)
    tiempo_inferencia_ms = models.IntegerField(null=True, blank=True)

    # Validación médica
    validado_por_medico = models.BooleanField(default=False)
    medico_validador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validaciones_cnn",
    )
    notas_medico = models.TextField(blank=True)
    observaciones_medico = models.TextField(blank=True)
    fecha_validacion = models.DateTimeField(null=True, blank=True)

    # Reporte narrativo generado por LLM local (Ollama, vision). Los campos
    # diagnosticos (clasificacion_clinica, tipo_embarazo, patologias, etc.)
    # dentro de este JSON SIEMPRE se toman de este mismo AnalisisCNN (campos
    # arriba) — el LLM solo redacta/narra y puede agregar hallazgos visuales
    # adicionales en "hallazgos_visuales_complementarios", nunca contradice
    # ni reemplaza el diagnostico del CNN.
    reporte_narrativo_ia = models.JSONField(
        null=True, blank=True,
        help_text="Reporte narrativo generado por LLM local con vision (Ollama), grounded en el resultado real del CNN.",
    )
    reporte_narrativo_fecha = models.DateTimeField(null=True, blank=True)

    # Timestamps
    fecha_analisis = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta"""
        ordering = ["-fecha_analisis"]
        verbose_name = "Análisis CNN"
        verbose_name_plural = "Análisis CNN"
        indexes = [
            models.Index(fields=["-fecha_analisis"]),
            models.Index(fields=["resultado"]),
            models.Index(fields=["modelo_usado"]),
        ]

    def __str__(self):
        """Str"""
        return f"CNN/{self.modelo_usado} - {self.imagen.paciente} - {self.resultado} ({self.confianza * 100:.1f}%)"

    @property
    def confianza_porcentaje(self):
        """Confianza porcentaje"""
        return round(self.confianza * 100, 1)

    @property
    def es_normal(self):
        """Es normal"""
        return self.resultado == "normal"

    @property
    def requiere_atencion(self):
        """Requiere atencion"""
        return self.resultado in ["anomalia_grave", "requiere_revision"]


class ModeloCNNConfig(models.Model):
    """Configuración y métricas de los modelos CNN disponibles.
    Permite activar/desactivar modelos y ver sus métricas.
    """

    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("entrenando", "En Entrenamiento"),
        ("prueba", "En Pruebas"),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(
        max_length=30, unique=True, help_text="Identificador: resnet50, unet, etc.",
    )
    descripcion = models.TextField()
    arquitectura = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="activo")

    # Métricas del modelo
    accuracy = models.FloatField(
        default=0.0, help_text="Precisión en validación (0-100)",
    )
    sensitivity = models.FloatField(
        default=0.0, help_text="Sensibilidad/Recall (0-100)",
    )
    specificity = models.FloatField(default=0.0, help_text="Especificidad (0-100)")
    auc_roc = models.FloatField(default=0.0, help_text="AUC-ROC score (0-1)")
    f1_score = models.FloatField(default=0.0)

    # Entrenamiento
    dataset_entrenamiento = models.CharField(max_length=200, blank=True)
    total_imagenes_entrenamiento = models.IntegerField(default=0)
    epocas_entrenamiento = models.IntegerField(default=0)
    fecha_entrenamiento = models.DateTimeField(null=True, blank=True)

    # Uso
    total_predicciones = models.IntegerField(default=0)
    predicciones_hoy = models.IntegerField(default=0)
    tiempo_promedio_ms = models.IntegerField(default=0)

    # Ruta del modelo guardado
    ruta_pesos = models.CharField(max_length=500, blank=True)
    version = models.CharField(max_length=20, default="1.0.0")

    # Metadatos
    clases_detectables = models.JSONField(
        default=list, help_text="Lista de clases que puede detectar",
    )
    parametros_config = models.JSONField(default=dict)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        """Meta"""
        ordering = ["-accuracy"]
        verbose_name = "Configuración Modelo CNN"
        verbose_name_plural = "Configuraciones Modelos CNN"

    def __str__(self):
        """Str"""
        return f"{self.nombre} v{self.version} — {self.accuracy}% accuracy"


# ── 5NF: Tablas normalizadas de análisis CNN ──────────────────────────────────

class PatologiaDetectadaCNN(models.Model):
    """5NF: 1 fila = 1 patología detectada en un análisis CNN.
    Reemplaza el JSONField AnalisisCNN.patologias (lista multivaluada).
    """

    analisis = models.ForeignKey(
        "AnalisisCNN",
        on_delete=models.CASCADE,
        related_name="patologias_normalizadas",
        verbose_name="Análisis CNN",
        db_index=True,
    )
    patologia = models.CharField(
        max_length=80, verbose_name="Patología", db_index=True,
    )
    confianza = models.FloatField(verbose_name="Confianza (0-1)")
    codigo_cie10 = models.CharField(max_length=10, blank=True, default="")
    descripcion = models.TextField(blank=True, default="")
    recomendacion = models.TextField(blank=True, default="")
    severidad = models.CharField(
        max_length=20,
        choices=[("alta", "Alta"), ("media-alta", "Media-Alta"), ("media", "Media"), ("baja", "Baja")],
        default="media",
        db_index=True,
    )
    requiere_especialista = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "ia_medica_patologia_detectada"
        ordering = ["-confianza"]
        verbose_name = "Patología Detectada CNN"
        verbose_name_plural = "Patologías Detectadas CNN"
        constraints = [
            models.UniqueConstraint(
                fields=["analisis", "patologia"],
                name="uq_patologia_detectada_analisis",
            )
        ]

    def __str__(self):
        return f"{self.patologia} ({self.confianza:.0%}) — {getattr(self, 'analisis_id', None)}"


class AlertaCNNAnalisis(models.Model):
    """5NF: 1 fila = 1 alerta de un análisis CNN.
    Reemplaza el JSONField AnalisisCNN.alertas (lista multivaluada).
    """

    analisis = models.ForeignKey(
        "AnalisisCNN",
        on_delete=models.CASCADE,
        related_name="alertas_normalizadas",
        verbose_name="Análisis CNN",
        db_index=True,
    )
    mensaje = models.TextField(verbose_name="Mensaje de alerta")
    severidad = models.CharField(
        max_length=10,
        choices=[("CRITICO", "Crítico"), ("ALTO", "Alto"), ("MEDIO", "Medio"), ("BAJO", "Bajo"), ("INFO", "Info")],
        default="MEDIO",
        db_index=True,
    )
    codigo = models.CharField(max_length=50, blank=True, default="", db_index=True)
    procesada = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "ia_medica_alerta_cnn"
        ordering = ["-severidad"]
        verbose_name = "Alerta de Análisis CNN"
        verbose_name_plural = "Alertas de Análisis CNN"

    def __str__(self):
        return f"[{self.severidad}] {self.mensaje[:60]}"
