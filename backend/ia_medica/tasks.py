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

    # select_for_update solo vale dentro de una transacción: fuera de ella
    # PostgreSQL lanza TransactionManagementError y la tarea fallaba siempre
    # en esta línea. Se reserva la imagen y se suelta el bloqueo enseguida.
    with transaction.atomic():
        instancia = (
            ImagenEcografica.objects.select_for_update(skip_locked=True).filter(id=imagen_id).first()
        )
        if instancia is not None:
            instancia.estado = "procesando"
            instancia.save(update_fields=["estado"])
    if instancia is None:
        if ImagenEcografica.objects.filter(id=imagen_id).exists():
            logger.info("Imagen %s ya la está analizando otro worker.", imagen_id)
            return {"status": "en_curso", "message": "La imagen ya se está analizando"}
        logger.error("Imagen ID %s no encontrada.", imagen_id)
        return {"status": "error", "message": "Imagen no encontrada"}

    try:

        imagen_path = instancia.imagen.path

        resultado = cnn_service.analizar_imagen(imagen_path, modelo)

        with transaction.atomic():
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.filter(id=user_id).first() if user_id else None

            campos = {f.name for f in AnalisisCNN._meta.get_fields()}
            defaults = {k: v for k, v in resultado.items() if k in campos}
            defaults["realizado_por"] = user
            analisis, _created = AnalisisCNN.objects.update_or_create(imagen=instancia, defaults=defaults)

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
