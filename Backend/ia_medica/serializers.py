"""=============================================================================
SERIALIZERS — IA Médica CNN
=============================================================================
"""

from rest_framework import serializers

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

# ── Serializers originales ─────────────────────────────────────────────────


class ConsultaIASerializer(serializers.ModelSerializer):
    """Consultaiaserializer"""
    class Meta:
        """Meta"""
        model = ConsultaIA
        fields = "__all__"


class AnalisisLaboratorioMLSerializer(serializers.ModelSerializer):
    """Analisislaboratoriomlserializer"""
    class Meta:
        """Meta"""
        model = AnalisisLaboratorioML
        fields = "__all__"


class DatasetEntrenamientoIASerializer(serializers.ModelSerializer):
    """Datasetentrenamientoiaserializer"""
    class Meta:
        """Meta"""
        model = DatasetEntrenamientoIA
        fields = "__all__"


class ConfiguracionModeloIASerializer(serializers.ModelSerializer):
    """Configuracionmodeloiaserializer"""
    class Meta:
        """Meta"""
        model = ConfiguracionModeloIA
        fields = "__all__"


class EstadisticasIASerializer(serializers.ModelSerializer):
    """Estadisticasiaserializer"""
    class Meta:
        """Meta"""
        model = EstadisticasIA
        fields = "__all__"


# ── Serializers CNN ────────────────────────────────────────────────────────


class AnalisisCNNSerializer(serializers.ModelSerializer):
    """Serializer completo del análisis CNN."""

    confianza_porcentaje = serializers.ReadOnlyField()
    es_normal = serializers.ReadOnlyField()
    requiere_atencion = serializers.ReadOnlyField()
    url_mapa_calor = serializers.SerializerMethodField()
    sugerencia_diagnostica_data = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = AnalisisCNN
        fields = "__all__"
        read_only_fields = ("fecha_analisis",)

    def get_sugerencia_diagnostica_data(self, obj):
        """Get sugerencia diagnostica"""
        if obj.sugerencia_diagnostica:
            return obj.sugerencia_diagnostica
        # Buscar la predicción con máxima confianza
        mejores = sorted(
            (p for p in (obj.predicciones or []) if p.get("confianza", 0) > 0),
            key=lambda p: p["confianza"], reverse=True,
        )
        if mejores:
            mejor = mejores[0]
            clase = mejor.get("clase", "normal")
            confianza = mejor["confianza"]
        elif obj.patologias:
            clase = obj.patologias[0]
            confianza = obj.score_general / 100.0 if obj.score_general else 0
        else:
            clase = "normal"
            confianza = max(obj.score_general / 100.0 if obj.score_general else 0, obj.confianza or 0)

        icd10_map = {
            "hidrocefalia": ("Q03", "Acumulacion de liquido en ventriculos cerebrales"),
            "anencefalia": ("Q00", "Ausencia parcial o total de cerebro"),
            "espina_bifida": ("Q05", "Defecto del tubo neural con exposicion medular"),
            "cardiopatia_congenita": ("Q24", "Malformacion cardiaca congenita"),
            "labio_leporino": ("Q36", "Fisura del labio superior"),
            "atresia_duodenal": ("Q41", "Obstruccion duodenal congenita"),
            "oligohidramnios": ("O41", "Disminucion del liquido amniotico"),
            "polihidramnios": ("O40", "Aumento excesivo del liquido amniotico"),
            "restriccion_crecimiento": ("O36.5", "Restriccion del crecimiento fetal"),
            "macrosomia_fetal": ("O33.5", "Crecimiento fetal excesivo"),
            "placenta_previa": ("O44", "Placenta que cubre el orificio cervical"),
            "muerte_fetal": ("O36.4", "Muerte fetal intrauterina"),
            "embarazo_multiple": ("O30", "Embarazo multiple"),
            "preeclampsia_signos": ("O14", "Signos de preeclampsia"),
            "normal": ("Z34", "Control prenatal de rutina"),
        }
        icd10, desc = icd10_map.get(clase, ("", ""))
        return {
            "patologia": clase,
            "confianza": round(float(confianza), 4),
            "descripcion": desc,
            "icd10": icd10,
            "recomendacion": "Evaluacion especializada recomendada." if clase != "normal" else "Control prenatal de rutina.",
        }

    def get_url_mapa_calor(self, obj):
        """Get url mapa calor"""
        if obj.mapa_calor:
            return obj.mapa_calor
        return None

    def validate_confianza(self, value):
        """Validate confianza"""
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError("Confianza debe estar entre 0.0 y 1.0")
        return value

    def validate_score_general(self, value):
        """Validate score general"""
        if not 0.0 <= value <= 100.0:
            raise serializers.ValidationError("Score general debe estar entre 0 y 100")
        return value

    def validate_riesgo_preeclampsia(self, value):
        """Validate riesgo preeclampsia"""
        if value is not None and not 0.0 <= value <= 1.0:
            raise serializers.ValidationError(
                "Riesgo de preeclampsia debe estar entre 0.0 y 1.0",
            )
        return value

    def validate_riesgo_parto_prematuro(self, value):
        """Validate riesgo parto prematuro"""
        if value is not None and not 0.0 <= value <= 1.0:
            raise serializers.ValidationError(
                "Riesgo de parto prematuro debe estar entre 0.0 y 1.0",
            )
        return value

    def validate_bpd_mm(self, value):
        """Validate bpd mm"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("BPD debe ser un valor positivo en mm")
        return value

    def validate_hc_mm(self, value):
        """Validate hc mm"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("HC debe ser un valor positivo en mm")
        return value

    def validate_ac_mm(self, value):
        """Validate ac mm"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("AC debe ser un valor positivo en mm")
        return value

    def validate_fl_mm(self, value):
        """Validate fl mm"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("FL debe ser un valor positivo en mm")
        return value


class AnalisisCNNResumenSerializer(serializers.ModelSerializer):
    """Serializer resumido para listados."""

    confianza_porcentaje = serializers.ReadOnlyField()

    class Meta:
        """Meta"""
        model = AnalisisCNN
        fields = [
            "id",
            "modelo_usado",
            "resultado",
            "confianza",
            "confianza_porcentaje",
            "score_general",
            "anomalias_detectadas",
            "alertas",
            "fecha_analisis",
        ]


class ImagenEcograficaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para galería."""

    url_imagen = serializers.ReadOnlyField()
    tamanio_mb = serializers.ReadOnlyField()
    paciente_nombre = serializers.SerializerMethodField()
    tiene_analisis = serializers.SerializerMethodField()
    analisis_resultado = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = ImagenEcografica
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "url_imagen",
            "nombre_original",
            "tipo_imagen",
            "estado",
            "semana_gestacional",
            "fecha_captura",
            "fecha_subida",
            "tamanio_mb",
            "resolucion_ancho",
            "resolucion_alto",
            "es_principal",
            "descripcion",
            "tiene_analisis",
            "analisis_resultado",
        ]

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        return str(obj.paciente)

    def get_tiene_analisis(self, obj):
        """Get tiene analisis"""
        return hasattr(obj, "analisis_cnn")

    def get_analisis_resultado(self, obj):
        """Get analisis resultado"""
        if hasattr(obj, "analisis_cnn"):
            return {
                "resultado": obj.analisis_cnn.resultado,
                "confianza": obj.analisis_cnn.confianza_porcentaje,
            }
        return None


class ImagenEcograficaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo con análisis incluido."""

    url_imagen = serializers.ReadOnlyField()
    tamanio_mb = serializers.ReadOnlyField()
    paciente_nombre = serializers.SerializerMethodField()
    analisis_cnn = AnalisisCNNSerializer(read_only=True)

    class Meta:
        """Meta"""
        model = ImagenEcografica
        fields = "__all__"
        read_only_fields = ("fecha_subida", "fecha_actualizacion", "subida_por")

    def get_paciente_nombre(self, obj):
        """Get paciente nombre"""
        return str(obj.paciente)


class ImagenEcograficaUploadSerializer(serializers.ModelSerializer):
    """Serializer para subida de imágenes."""

    class Meta:
        """Meta"""
        model = ImagenEcografica
        fields = [
            "paciente",
            "imagen",
            "tipo_imagen",
            "semana_gestacional",
            "descripcion",
            "notas_tecnicas",
            "fecha_captura",
            "es_principal",
        ]

    def validate_semana_gestacional(self, value):
        """Validate semana gestacional"""
        if value is not None and not 0 <= value <= 42:
            raise serializers.ValidationError(
                "Semana gestacional debe estar entre 0 y 42",
            )
        return value

    def validate_imagen(self, value):
        """Validate imagen"""
        from django.conf import settings
        nombre = value.name.lower()
        extensiones_permitidas = (
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tiff",
            ".dicom",
        )
        if not any(nombre.endswith(ext) for ext in extensiones_permitidas):
            raise serializers.ValidationError(
                f"Formato no soportado. Permitidos: {', '.join(extensiones_permitidas)}",
            )
        max_size = getattr(settings, "MAX_IMAGE_SIZE", 5 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(
                f"La imagen no puede superar los {max_size // (1024*1024)}MB.",
            )
        return value


class ModeloCNNConfigSerializer(serializers.ModelSerializer):
    """Modelocnnconfigserializer"""
    class Meta:
        """Meta"""
        model = ModeloCNNConfig
        fields = "__all__"
        read_only_fields = (
            "fecha_creacion",
            "fecha_actualizacion",
            "total_predicciones",
        )

    def validate_accuracy(self, value):
        """Validate accuracy"""
        if not 0.0 <= value <= 100.0:
            raise serializers.ValidationError("Accuracy debe estar entre 0 y 100")
        return value

    def validate_sensitivity(self, value):
        """Validate sensitivity"""
        if not 0.0 <= value <= 100.0:
            raise serializers.ValidationError("Sensitivity debe estar entre 0 y 100")
        return value

    def validate_specificity(self, value):
        """Validate specificity"""
        if not 0.0 <= value <= 100.0:
            raise serializers.ValidationError("Specificity debe estar entre 0 y 100")
        return value

    def validate_auc_roc(self, value):
        """Validate auc roc"""
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError("AUC-ROC debe estar entre 0.0 y 1.0")
        return value


class ModeloCNNConfigListSerializer(serializers.ModelSerializer):
    """Modelocnnconfiglistserializer"""
    class Meta:
        """Meta"""
        model = ModeloCNNConfig
        fields = [
            "id",
            "nombre",
            "codigo",
            "arquitectura",
            "estado",
            "accuracy",
            "sensitivity",
            "specificity",
            "auc_roc",
            "total_predicciones",
            "tiempo_promedio_ms",
            "version",
            "clases_detectables",
        ]
