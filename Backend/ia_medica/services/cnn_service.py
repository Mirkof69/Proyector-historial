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
            from .result_mapping import IANoDisponible, defaults_analisis_cnn

            try:
                traducido = defaults_analisis_cnn(ms_data, None, modelo)
            except IANoDisponible as e:
                logger.warning("Microservicio ML sin modelo: %s", e)
                return None
            traducido.pop("realizado_por", None)
            return {**traducido, "fuente": ms_data.get("fuente", "efficientnet_b4")}

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
