"""Tasks module."""
import logging

from celery import shared_task
from django.db import OperationalError, transaction
from django.db.models import F

logger = logging.getLogger("ia_medica")


@shared_task(bind=True, max_retries=3, acks_late=True, reject_on_worker_lost=True)
def analizar_imagen_task(self, imagen_id, modelo, user_id=None):
    """Tarea Celery para analizar una imagen ecográfica de forma asíncrona.
    acks_late+reject_on_worker_lost garantiza que la tarea no se pierda si el worker falla.
    """
    from .models import AnalisisCNN, ImagenEcografica, ModeloCNNConfig
    from .services.cnn_service import cnn_service

    logger.info(
        "Iniciando análisis asíncrono para imagen ID %s con modelo %s",
        imagen_id,
        modelo,
    )

    try:
        instancia = ImagenEcografica.objects.select_for_update(skip_locked=True).get(
            id=imagen_id,
        )
    except ImagenEcografica.DoesNotExist:
        logger.error("Imagen ID %s no encontrada.", imagen_id)
        return {"status": "error", "message": "Imagen no encontrada"}

    try:
        if instancia.estado != "procesando":
            instancia.estado = "procesando"
            instancia.save(update_fields=["estado"])

        imagen_path = instancia.imagen.path

        resultado = cnn_service.analizar_imagen(imagen_path, modelo)

        with transaction.atomic():
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.filter(id=user_id).first() if user_id else None

            analisis, _created = AnalisisCNN.objects.update_or_create(
                imagen=instancia,
                defaults={
                    "realizado_por": user,
                    "modelo_usado": resultado.get("modelo_usado", modelo),
                    "version_modelo": resultado.get("version_modelo", "1.0.0"),
                    "resultado": resultado.get("resultado", "indeterminado"),
                    "confianza": resultado.get("confianza", 0.0),
                    "score_general": resultado.get("score_general", 0.0),
                    "predicciones": resultado.get("predicciones", []),
                    "clases_detectadas": resultado.get("clases_detectadas", []),
                    "bounding_boxes": resultado.get("bounding_boxes"),
                    "estructuras_detectadas": resultado.get(
                        "estructuras_detectadas", {},
                    ),
                    "medidas_estimadas": resultado.get("medidas_estimadas"),
                    "anomalias_detectadas": resultado.get("anomalias_detectadas", []),
                    "alertas": resultado.get("alertas", []),
                    "recomendaciones": resultado.get("recomendaciones", []),
                    "tiempo_procesamiento_ms": resultado.get(
                        "tiempo_procesamiento_ms", 0,
                    ),
                    "mapa_calor": resultado.get("mapa_calor")
                    or resultado.get("gradcam_base64", ""),
                    "bpd_mm": resultado.get("bpd_mm"),
                    "hc_mm": resultado.get("hc_mm"),
                    "ac_mm": resultado.get("ac_mm"),
                    "fl_mm": resultado.get("fl_mm"),
                    "shap_valores": resultado.get("shap_valores", {}),
                    "riesgo_preeclampsia": resultado.get("riesgo_preeclampsia", 0.0),
                    "riesgo_parto_prematuro": resultado.get(
                        "riesgo_parto_prematuro", 0.0,
                    ),
                    "nivel_riesgo": resultado.get("nivel_riesgo", "BAJO"),
                    "patologias": resultado.get("patologias", []),
                    "tiempo_inferencia_ms": resultado.get("tiempo_inferencia_ms"),
                },
            )

            if resultado.get("resultado") not in (
                "indeterminado",
                "servicio_no_disponible",
            ):
                instancia.estado = "analizada"
            else:
                instancia.estado = "error"

            instancia.save(update_fields=["estado"])

            ModeloCNNConfig.objects.filter(codigo=modelo).update(
                total_predicciones=F("total_predicciones") + 1,
            )

        logger.info(
            "Análisis asíncrono completado: imagen=%s, resultado=%s",
            getattr(instancia, 'id', None),
            getattr(analisis, 'resultado', 'indeterminado'),
        )
        return {"status": "success", "analisis_id": getattr(analisis, 'id', None)}

    except OperationalError as e:
        logger.error("Error de base de datos en análisis CNN: %s", e)
        try:
            self.retry(countdown=30, exc=e)
        except self.MaxRetriesExceededError:
            logger.error(
                "Se excedió el máximo de reintentos para la imagen %s", imagen_id,
            )
        return {"status": "error", "message": str(e)}

    except Exception as e:
        logger.error("Error en tarea asíncrona de análisis CNN: %s", e)
        try:
            instancia.estado = "error"
            instancia.save(update_fields=["estado"])
        except Exception:
            pass

        try:
            self.retry(countdown=2**self.request.retries * 60)
        except self.MaxRetriesExceededError:
            logger.error(
                "Se excedió el máximo de reintentos para la imagen %s", imagen_id,
            )

        return {"status": "error", "message": str(e)}
