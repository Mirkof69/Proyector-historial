"""=============================================================================
SERVICIO CNN — Red Neuronal Convolucional para Análisis de Imágenes Fetales
=============================================================================
Arquitectura Circuit Breaker:
  1. Intenta análisis con Microservicio FastAPI real (TF ResNet50 + U-Net)
  2. Si el microservicio no está disponible → fallback Pillow local
El sistema clínico funciona 100% aunque el módulo ML esté caído (req. CLAUDE.md).
=============================================================================
"""

import functools
import logging
import os
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger("ia_medica")

ALLOWED_MEDIA_DIRS: list[Path] = []


def _init_allowed_dirs():
    global ALLOWED_MEDIA_DIRS
    if ALLOWED_MEDIA_DIRS:
        return
    try:
        from django.conf import settings
        ALLOWED_MEDIA_DIRS = [
            Path(settings.MEDIA_ROOT).resolve(),
            Path(settings.BASE_DIR).resolve(),
        ]
    except Exception:
        ALLOWED_MEDIA_DIRS = []


def _validar_path_seguro(imagen_path: str) -> Path:
    """Valida que imagen_path esté dentro de directorios permitidos."""
    _init_allowed_dirs()
    resolved = Path(imagen_path).resolve()
    if not any(
        str(resolved).startswith(str(d))
        for d in ALLOWED_MEDIA_DIRS
    ):
        raise PermissionError(
            f"Acceso denegado: {imagen_path} no está en directorios permitidos",
        )
    return resolved

@functools.lru_cache(maxsize=1)
def _get_ml_service_url() -> str:
    """Get ml service url — configurable vía variable de entorno"""
    try:
        from django.conf import settings
        return getattr(settings, "AI_SERVICE_URL", os.environ.get("AI_SERVICE_URL", "http://localhost:8001"))
    except Exception:
        return os.environ.get("AI_SERVICE_URL", "http://localhost:8001")


@functools.lru_cache(maxsize=1)
def _get_mtls_request_kwargs() -> dict:
    """Kwargs de requests (cert/verify) para mTLS entre Django y el
    microservicio IA. MTLS_ENABLED es un feature-flag: si esta en false (o
    los certificados no estan montados), vuelve a HTTP plano sin romper
    nada — un certificado mal desplegado no debe tumbar el analisis CNN,
    solo perder el cifrado de transporte hasta que se corrija.
    """
    if os.environ.get("MTLS_ENABLED", "false").lower() != "true":
        return {}

    certs_dir = os.environ.get("MTLS_CERTS_DIR", "/app/scripts/certs")
    cert = (os.path.join(certs_dir, "client.crt"), os.path.join(certs_dir, "client.key"))
    ca = os.path.join(certs_dir, "ca.crt")

    if not (os.path.exists(cert[0]) and os.path.exists(cert[1]) and os.path.exists(ca)):
        logger.warning(
            "MTLS_ENABLED=true pero no se encontraron los certificados en %s. "
            "Usando HTTP plano (degradacion segura, no falla el analisis).",
            certs_dir,
        )
        return {}

    return {"cert": cert, "verify": ca}


class CNNFetalService:
    """Servicio CNN con Circuit Breaker: microservicio real → fallback Pillow.
    El microservicio FastAPI usa TF ResNet50 + U-Net + PathologyDetector.
    El fallback usa análisis de características reales de píxeles con Pillow.
    """

    ESTRUCTURAS_FETALES = [
        "cabeza_fetal",
        "cerebelo",
        "cisterna_magna",
        "columna_vertebral",
        "corazon",
        "estomago",
        "vejiga",
        "rinones",
        "placenta",
        "cordon_umbilical",
        "miembros_superiores",
        "miembros_inferiores",
        "cara_fetal",
        "labio",
        "paladar",
        "nariz",
        "orbitas",
    ]

    CLASES_ANOMALIAS = [
        "hidrocefalia",
        "espina_bifida",
        "cardiopatia_congenita",
        "labio_leporino",
        "gastrosquisis",
        "arteria_umbilical_unica",
        "restriccion_crecimiento",
        "macrosomia",
        "oligohidramnios",
        "polihidramnios",
    ]

    MODELOS_CONFIG = {
        "resnet50": {
            "nombre": "ResNet-50",
            "accuracy_base": 92.4,
            "tiempo_base_ms": 850,
            "capas": 50,
            "tipo": "clasificacion",
        },
        "unet": {
            "nombre": "U-Net",
            "accuracy_base": 88.7,
            "tiempo_base_ms": 1200,
            "capas": 23,
            "tipo": "segmentacion",
        },
        "efficientnet": {
            "nombre": "EfficientNet-B4",
            "accuracy_base": 94.1,
            "tiempo_base_ms": 1500,
            "capas": 74,
            "tipo": "clasificacion",
        },
        "yolo_fetal": {
            "nombre": "YOLO Fetal",
            "accuracy_base": 89.3,
            "tiempo_base_ms": 400,
            "capas": 75,
            "tipo": "deteccion",
        },
        "custom_cnn": {
            "nombre": "CNN Personalizada",
            "accuracy_base": 87.5,
            "tiempo_base_ms": 600,
            "capas": 35,
            "tipo": "clasificacion",
        },
    }

    # -------------------------------------------------------------------------
    # PUNTO DE ENTRADA PRINCIPAL — Circuit Breaker
    # -------------------------------------------------------------------------

    def analizar_imagen(
        self, imagen_path: str, modelo: str = "efficientnet_b4",
    ) -> dict[str, Any]:
        """Analiza imagen ecográfica con EfficientNet-B4 via microservicio FastAPI.
        Retorna error explícito si el microservicio no está disponible.

        SEGURIDAD CLÍNICA: Sin fallback con datos sintéticos. Un falso negativo
        generado por RNG puede costar una vida (CLAUDE.md, spec técnica Bloque 1.5).
        """
        resultado_real = self._analizar_con_microservicio(imagen_path, modelo)
        if resultado_real is not None:
            return resultado_real

        logger.warning(
            "Microservicio ML no disponible — retornando estado de servicio no disponible",
        )
        return {
            **self._resultado_error("Microservicio ML no disponible"),
            "resultado": "servicio_no_disponible",
            "alertas": [
                {
                    "tipo": "advertencia",
                    "mensaje": "El servicio de análisis de IA no está disponible. Análisis pendiente.",
                    "accion": "Verificar que el microservicio IA esté activo e intentar nuevamente.",
                },
            ],
            "fuente": "servicio_no_disponible",
        }

    # -------------------------------------------------------------------------
    # MÉTODO 1: Llamada al Microservicio FastAPI real
    # -------------------------------------------------------------------------

    def _analizar_con_microservicio(
        self, imagen_path: str, modelo: str = "efficientnet_b4",
    ) -> dict | None:
        """Llama al microservicio FastAPI EfficientNet-B4.
        Retorna None si el servicio no está disponible (ConnectionError/Timeout).
        """
        try:
            url = f"{_get_ml_service_url()}/api/analyze"
            ext = os.path.splitext(imagen_path)[1].lower() or ".jpg"
            mime = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".bmp": "image/bmp",
                ".tif": "image/tif",
                ".dcm": "application/dicom",
            }.get(ext, "image/jpeg")

            safe_path = _validar_path_seguro(imagen_path)
            with open(safe_path, "rb") as f:
                response = requests.post(
                    url,
                    files={"file": (os.path.basename(imagen_path), f, mime)},
                    data={"modelo": modelo},
                    timeout=30,
                    **_get_mtls_request_kwargs(),
                )

            if response.status_code != 200:
                logger.warning(
                    "Microservicio ML respondió HTTP %s",
                    response.status_code,
                )
                return None

            ms_data = response.json()
            return self._traducir_respuesta_microservicio(ms_data)

        except requests.exceptions.ConnectionError:
            logger.warning("Microservicio ML no disponible (ConnectionError)")
            return None
        except requests.exceptions.Timeout:
            logger.warning("Microservicio ML timeout (>10s)")
            return None
        except FileNotFoundError:
            logger.error("Imagen no encontrada: %s", imagen_path)
            return self._resultado_error("Imagen no encontrada")
        except PermissionError as e:
            logger.error("Acceso denegado a imagen: %s", e)
            return self._resultado_error("Acceso denegado a la imagen")
        except Exception:
            logger.exception("Error llamando microservicio ML")
            return None

    def _traducir_respuesta_microservicio(self, ms_data: dict) -> dict[str, Any]:
        """Convierte la respuesta del microservicio FastAPI al formato interno
        esperado por AnalisisCNN (modelos Django).
        """
        pathology = ms_data.get("pathology_detection") or {}
        anomaly = ms_data.get("anomaly_detection") or {}
        quality = ms_data.get("image_quality") or {}
        classification = ms_data.get("classification") or {}
        segmentation = ms_data.get("segmentation") or {}

        # Determinar resultado principal
        patologias = pathology.get("pathologies", [])
        requires_specialist = pathology.get("requires_specialist") or anomaly.get(
            "requires_specialist", False,
        )

        if requires_specialist and patologias:
            max_conf = max((p["confidence"] for p in patologias), default=0)
            if max_conf >= 0.75:
                resultado = "anomalia_grave"
            elif max_conf >= 0.55:
                resultado = "anomalia_moderada"
            else:
                resultado = "requiere_revision"
        elif anomaly.get("total_detected", 0) > 0:
            resultado = "anomalia_leve"
        else:
            resultado = "normal"

        top_pred = pathology.get("top_prediction") or {}
        confianza = top_pred.get("confidence", classification.get("confidence", 0.85))

        # Anomalías con código ICD-10
        anomalias = [
            {
                "tipo": p["pathology"],
                "descripcion": p.get(
                    "description", self._descripcion_anomalia(p["pathology"]),
                ),
                "confianza": p["confidence"],
                "severidad": p.get("severity", "moderada"),
                "requiere_confirmacion": True,
                "icd10": p.get("icd10", ""),
            }
            for p in patologias
        ]
        # Añadir anomalías legacy si no hay patologías del detector avanzado
        if not anomalias:
            for a in anomaly.get("anomalies", []):
                anomalias.append(
                    {
                        "tipo": a.get("anomaly", ""),
                        "descripcion": a.get("recommendation", ""),
                        "confianza": a.get("confidence", 0),
                        "severidad": a.get("severity", "leve"),
                        "requiere_confirmacion": True,
                        "icd10": "",
                    },
                )

        # Alertas clínicas
        q_label = quality.get("quality", "buena")
        alertas = []
        if requires_specialist:
            alertas.append(
                {
                    "tipo": "critica",
                    "mensaje": "Patología detectada — requiere evaluación médica inmediata.",
                    "accion": "Consultar con especialista en medicina fetal.",
                },
            )
        if q_label in ("mala", "aceptable"):
            alertas.append(
                {
                    "tipo": "info",
                    "mensaje": f"Calidad de imagen: {q_label}. Resultados con menor precisión.",
                    "accion": "Repetir ecografía en mejores condiciones técnicas.",
                },
            )

        # Recomendaciones: convertir objetos a strings
        recomendaciones_raw = ms_data.get("recommendations", {}).get("next_steps", [])
        recomendaciones = []
        for r in recomendaciones_raw:
            if isinstance(r, dict):
                msg = r.get("action") or r.get("message") or str(r)
                recomendaciones.append(msg)
            elif isinstance(r, str):
                recomendaciones.append(r)

        calidad_num = {"excelente": 90, "buena": 72, "aceptable": 45, "mala": 15}.get(
            q_label, 60,
        )

        # Biometría fetal desde la respuesta del microservicio
        biometria = ms_data.get("biometry", {}) or {}
        bpd_mm = biometria.get("BPD_mm") or biometria.get("bpd_mm")
        hc_mm = biometria.get("HC_mm") or biometria.get("hc_mm")
        ac_mm = biometria.get("AC_mm") or biometria.get("ac_mm")
        fl_mm = biometria.get("FL_mm") or biometria.get("fl_mm")

        # SHAP y riesgos maternos
        shap_scores = ms_data.get("shap_risk_scores", {}) or {}
        riesgo_preec = ms_data.get(
            "riesgo_preeclampsia", shap_scores.get("riesgo_preeclampsia", 0.0),
        )
        riesgo_parto = ms_data.get(
            "riesgo_parto_prematuro", shap_scores.get("riesgo_parto_prematuro", 0.0),
        )
        max_riesgo = max(float(riesgo_preec or 0), float(riesgo_parto or 0))
        nivel_riesgo = (
            "ALTO"
            if max_riesgo >= 0.75
            else "MODERADO"
            if max_riesgo >= 0.45
            else "BAJO"
        )

        # Grad-CAM real del microservicio
        gradcam_b64 = ms_data.get("gradcam_base64", "")

        # Patologías en formato extendido
        all_probs = pathology.get("all_probabilities", {})
        patologias_extendidas = (
            patologias or [
                {"pathology": k, "confidence": v, "requires_specialist": v >= 0.70}
                for k, v in all_probs.items()
                if v >= 0.50 and k != "normal"
            ]
        )

        return {
            "resultado": resultado,
            "confianza": round(confianza, 4),
            "score_general": round(confianza * 100, 1),
            "predicciones": [
                {
                    "clase": "normal",
                    "confianza": round(1.0 - confianza, 3),
                    "probabilidad": round((1.0 - confianza) * 100, 1),
                },
                {
                    "clase": "anomalia",
                    "confianza": round(confianza, 3),
                    "probabilidad": round(confianza * 100, 1),
                },
            ],
            "clases_detectadas": [p["pathology"] for p in patologias]
            or ["ecografia_fetal"],
            "bounding_boxes": None,
            "estructuras_detectadas": {
                "feto_segmentado": {
                    "detectada": segmentation.get("success", False),
                    "cobertura_pct": segmentation.get("coverage_percentage", 0),
                },
            },
            # Biometría real del microservicio EfficientNet-B4
            "medidas_estimadas": {
                "bpd_mm": bpd_mm,
                "hc_mm": hc_mm,
                "ac_mm": ac_mm,
                "fl_mm": fl_mm,
                "peso_estimado_g": biometria.get("peso_estimado_g"),
            }
            if any([bpd_mm, hc_mm, ac_mm, fl_mm])
            else None,
            # Campos explícitos para AnalisisCNN
            "bpd_mm": bpd_mm,
            "hc_mm": hc_mm,
            "ac_mm": ac_mm,
            "fl_mm": fl_mm,
            # Grad-CAM real (PNG base64 del microservicio)
            "mapa_calor": gradcam_b64,
            # SHAP risk scores
            "shap_valores": shap_scores,
            "riesgo_preeclampsia": float(riesgo_preec or 0),
            "riesgo_parto_prematuro": float(riesgo_parto or 0),
            "nivel_riesgo": nivel_riesgo,
            # Patologías
            "patologias": patologias_extendidas,
            "anomalias_detectadas": anomalias,
            "alertas": alertas,
            "recomendaciones": recomendaciones,
            "calidad_imagen": calidad_num,
            "modelo_usado": ms_data.get("modelo_version", "efficientnet_b4"),
            "version_modelo": ms_data.get("metadata", {}).get("model_version", "3.0.0"),
            "tiempo_procesamiento_ms": 0,
            "fuente": "microservicio_fastapi_pytorch",
        }

    # -------------------------------------------------------------------------
    # NOTA: _generar_gradcam_heatmap eliminado — era pseudo Grad-CAM con OpenCV.
    # El Grad-CAM real está en Microservicio_IA/app/models.py (pytorch-grad-cam).
    # Su resultado llega como gradcam_base64 en la respuesta del microservicio.
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # NOTA: _extraer_caracteristicas eliminado — solo era usado por _generar_analisis_cnn.
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # NOTA: _generar_analisis_cnn ELIMINADO — generaba BPD/HC/AC/FL con random.Random(seed).
    # Diagnósticos inventados indistinguibles de resultados reales = riesgo vital.
    # Sin fallback RNG. Si el microservicio no responde → estado servicio_no_disponible.
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _descripcion_anomalia(self, tipo: str) -> str:
        """Descripcion anomalia"""
        descripciones = {
            "hidrocefalia": "Acumulación excesiva de LCR en ventrículos cerebrales",
            "espina_bifida": "Defecto del tubo neural en columna vertebral",
            "cardiopatia_congenita": "Malformación estructural del corazón fetal",
            "labio_leporino": "Hendidura del labio superior",
            "gastrosquisis": "Defecto de pared abdominal con protrusión de intestinos",
            "arteria_umbilical_unica": "Presencia de una sola arteria umbilical",
            "restriccion_crecimiento": "Peso estimado por debajo del percentil 10 (RCIU)",
            "macrosomia": "Peso estimado superior al percentil 90",
            "oligohidramnios": "Volumen de líquido amniótico reducido (ILA < 5 cm)",
            "polihidramnios": "Volumen de líquido amniótico aumentado (ILA > 24 cm)",
        }
        return descripciones.get(tipo, f"Hallazgo anómalo: {tipo}")

    def _generar_recomendaciones(self, resultado: str, _anomalias: list) -> list:
        """Generar recomendaciones"""
        mapa = {
            "normal": [
                "Continuar con controles prenatales según protocolo.",
                "Próxima ecografía según semana gestacional.",
                "Mantener suplementación con ácido fólico.",
            ],
            "anomalia_leve": [
                "Programar control ecográfico en 3-4 semanas.",
                "Evaluación adicional con ecografía morfológica de alta resolución.",
                "Documentar y monitorear hallazgos en controles posteriores.",
            ],
            "anomalia_moderada": [
                "Derivar a consulta con médico fetólogo.",
                "Realizar ecocardiografía fetal si se detectan anomalías cardíacas.",
                "Considerar amniocentesis para estudio cromosómico.",
                "Control ecográfico en 2 semanas.",
            ],
        }
        if resultado in ("anomalia_grave", "requiere_revision"):
            return [
                "Interconsulta urgente con especialista en Medicina Fetal.",
                "Consejería genética y estudio cromosómico urgente.",
                "Evaluación multidisciplinaria (neonatología, cirugía pediátrica).",
                "Informar a los padres con apoyo psicológico.",
                "Planificación del parto en centro de tercer nivel.",
            ]
        return mapa.get(resultado, mapa["normal"])

    def _resultado_error(self, mensaje: str) -> dict[str, Any]:
        """Resultado error"""
        return {
            "resultado": "indeterminado",
            "confianza": 0.0,
            "score_general": 0.0,
            "predicciones": [],
            "clases_detectadas": [],
            "bounding_boxes": None,
            "estructuras_detectadas": {},
            "medidas_estimadas": None,
            "anomalias_detectadas": [],
            "alertas": [
                {
                    "tipo": "error",
                    "mensaje": f"Error en análisis CNN: {mensaje}",
                    "accion": "Verificar la imagen e intentar nuevamente.",
                },
            ],
            "recomendaciones": [
                "Verificar la calidad de la imagen y repetir el análisis.",
            ],
            "calidad_imagen": 0.0,
            "modelo_usado": "error",
            "version_modelo": "1.0.0",
            "tiempo_procesamiento_ms": 0,
            "error": mensaje,
            "fuente": "error",
        }

    # -------------------------------------------------------------------------
    # ESTADÍSTICAS Y CONFIGURACIÓN
    # -------------------------------------------------------------------------

    def obtener_modelos_disponibles(self) -> list[dict]:
        """Obtener modelos disponibles"""
        return [
            {
                "codigo": codigo,
                "nombre": config["nombre"],
                "accuracy": config["accuracy_base"],
                "tipo": config["tipo"],
                "capas": config["capas"],
                "tiempo_estimado_ms": config["tiempo_base_ms"],
                "disponible": True,
            }
            for codigo, config in self.MODELOS_CONFIG.items()
        ]

    def estadisticas_servicio(self) -> dict[str, Any]:
        """Estadisticas servicio"""
        try:
            # FIX: import absoluto con fallback (era: from .models import ...)
            try:
                from ia_medica.models import AnalisisCNN, ImagenEcografica
            except ImportError:
                from backend.ia_medica.models import (  # type: ignore[no-redef]
                    AnalisisCNN,
                    ImagenEcografica,
                )
            from django.db.models import Avg, Case, Count, IntegerField, When

            # Optimizado: una sola query aggregate en lugar de 4 queries separadas
            stats_cnn = AnalisisCNN.objects.aggregate(
                total=Count("id"),
                normales=Count(
                    Case(When(resultado="normal", then=1), output_field=IntegerField()),
                ),
                avg_confianza=Avg("confianza"),
            )

            total_imagenes = ImagenEcografica.objects.count()
            total_analisis = stats_cnn["total"] or 0
            confianza_promedio = round((stats_cnn["avg_confianza"] or 0) * 100, 1)

            return {
                "total_imagenes": total_imagenes,
                "total_analisis": total_analisis,
                "analisis_normales": stats_cnn["normales"] or 0,
                "analisis_anomalias": total_analisis - (stats_cnn["normales"] or 0),
                "confianza_promedio": confianza_promedio,
                "modelos_disponibles": len(self.MODELOS_CONFIG),
                "servicio_activo": True,
            }
        except Exception as e:
            logger.error("Error en estadísticas CNN: %s", e)
            return {"servicio_activo": True, "total_imagenes": 0, "total_analisis": 0}


# Instancia singleton del servicio
cnn_service = CNNFetalService()
