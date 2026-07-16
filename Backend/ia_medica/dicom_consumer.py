"""
Consumer Celery para eventos DICOM enviados por Orthanc via webhook/RabbitMQ.

Flujo:
  Orthanc recibe DICOM → HTTP POST a /api/dicom/webhook/ →
  Django encola tarea Celery → esta función procesa → CNN analiza → guarda en BD

Cada nueva serie DICOM queda automáticamente analizada por EfficientNet-B4
sin intervención manual del médico.
"""

import contextlib
import logging

from celery import shared_task

logger = logging.getLogger("ia_medica.dicom")


@shared_task(
    bind=True,
    name="ia_medica.procesar_estudio_dicom",
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
    queue="dicom",
)
def procesar_estudio_dicom(self, orthanc_instance_id: str, paciente_id: int | None = None, usuario_id: int | None = None):
    """Procesa un estudio DICOM recibido de Orthanc.

    Pasos:
    1. Descarga la imagen desde Orthanc REST API
    2. Crea ImagenEcografica en BD
    3. Dispara analizar_imagen_task (CNN EfficientNet-B4)
    4. Registra en auditoría

    Args:
        orthanc_instance_id: UUID de la instancia en Orthanc (e.g. "a57f-...")
        paciente_id:          ID del paciente en nuestra BD (opcional)
        usuario_id:           ID del médico que recibe el estudio (opcional)
    """
    import os
    from typing import Any, cast

    import requests
    from django.contrib.auth import get_user_model
    from django.core.files.base import ContentFile

    from ia_medica.models import ImagenEcografica
    from ia_medica.tasks import analizar_imagen_task as _analizar_imagen_task
    analizar_imagen_task = cast(Any, _analizar_imagen_task)

    ORTHANC_URL = os.environ.get("ORTHANC_URL", "http://orthanc:8042")
    ORTHANC_USER = os.environ.get("ORTHANC_USER", "fetalmedical")
    ORTHANC_PASS = os.environ.get("ORTHANC_PASS", "")
    auth = (ORTHANC_USER, ORTHANC_PASS) if ORTHANC_PASS else None

    logger.info("Procesando instancia DICOM: %s", orthanc_instance_id)

    try:
        # ── 1. Descargar imagen desde Orthanc (como PNG) ────────────────────
        png_url = f"{ORTHANC_URL}/instances/{orthanc_instance_id}/preview"
        resp = requests.get(png_url, auth=auth, timeout=30)
        resp.raise_for_status()
        imagen_bytes = resp.content
        nombre_archivo = f"dicom_{orthanc_instance_id[:8]}.png"

        # ── 2. Obtener metadatos simplificados ──────────────────────────────
        tags_url = f"{ORTHANC_URL}/instances/{orthanc_instance_id}/simplified-tags"
        tags_resp = requests.get(tags_url, auth=auth, timeout=10)
        tags = tags_resp.json() if tags_resp.ok else {}

        # ── 3. Crear ImagenEcografica en BD ─────────────────────────────────
        User = get_user_model()
        usuario = User.objects.filter(id=usuario_id).first() if usuario_id else None

        from pacientes.models import Paciente
        paciente = Paciente.objects.filter(id=paciente_id).first() if paciente_id else None
        if paciente is None:
            logger.error("No se puede procesar el DICOM %s: Paciente no encontrado (paciente_id=%s)", orthanc_instance_id, paciente_id)
            return {"status": "error", "message": f"Paciente no encontrado con id {paciente_id}"}

        imagen_obj = ImagenEcografica.objects.create(
            paciente=paciente,
            tipo_imagen="eco_2d",
            estado="pendiente",
            nombre_original=nombre_archivo,
            dicom_metadata={
                "orthanc_id": orthanc_instance_id,
                "PatientName": tags.get("PatientName", ""),
                "StudyDate": tags.get("StudyDate", ""),
                "Modality": tags.get("Modality", "US"),
                "StudyDescription": tags.get("StudyDescription", ""),
                "SeriesDescription": tags.get("SeriesDescription", ""),
            },
        )
        imagen_obj.imagen.save(nombre_archivo, ContentFile(imagen_bytes), save=True)

        logger.info(
            "ImagenEcografica creada: id=%s desde DICOM %s",
            getattr(imagen_obj, 'id', None),
            orthanc_instance_id,
        )

        # ── 4. Encolar análisis CNN ─────────────────────────────────────────
        analizar_imagen_task.delay(
            imagen_id=getattr(imagen_obj, 'id', None),
            modelo="efficientnet_b4",
            user_id=usuario_id,
        )

        # ── 5. Registrar en auditoría ───────────────────────────────────────
        try:
            from auditoria.models import RegistroAuditoria
            RegistroAuditoria.registrar(
                usuario=usuario,
                accion="ANALISIS_CNN",
                modulo="ImagenEcografica",
                registro_id=str(getattr(imagen_obj, 'id', None)),
                detalle=f"DICOM recibido de Orthanc: {orthanc_instance_id}",
            )
        except Exception:
            pass

        return {
            "status": "success",
            "imagen_id": getattr(imagen_obj, 'id', None),
            "orthanc_id": orthanc_instance_id,
        }

    except requests.RequestException as exc:
        logger.error("Error descargando DICOM %s de Orthanc: %s", orthanc_instance_id, exc)
        try:
            self.retry(countdown=30 * (2 ** self.request.retries), exc=exc)
        except self.MaxRetriesExceededError:
            logger.error("Máximo reintentos alcanzado para DICOM %s", orthanc_instance_id)
        return {"status": "error", "message": str(exc)}

    except Exception as exc:
        logger.error("Error procesando DICOM %s: %s", orthanc_instance_id, exc)
        with contextlib.suppress(self.MaxRetriesExceededError):
            self.retry(countdown=60, exc=exc)
        return {"status": "error", "message": str(exc)}
