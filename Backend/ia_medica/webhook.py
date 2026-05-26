"""
Webhook para eventos DICOM de Orthanc.

Configurar en Orthanc (orthanc.json):
  "WebHooks": [
    {
      "URL": "http://backend:8000/api/ia/dicom/webhook/",
      "Method": "POST",
      "Events": ["StableInstance"]
    }
  ]

Orthanc envía:
  {"Level": "Instance", "ID": "<orthanc-uuid>", "Path": "/instances/<uuid>"}
"""

import hashlib
import hmac
import logging
import os

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .dicom_consumer import procesar_estudio_dicom

logger = logging.getLogger("ia_medica.dicom")

WEBHOOK_SECRET = os.environ.get("ORTHANC_WEBHOOK_SECRET", "")


def _verify_hmac(request) -> bool:
    """Verifica firma HMAC-SHA256 del webhook de Orthanc (opcional)."""
    if not WEBHOOK_SECRET:
        return True  # Sin secreto configurado, se acepta (solo en red interna)
    signature = request.headers.get("X-Orthanc-Signature", "")
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        request.body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@api_view(["POST"])
@permission_classes([AllowAny])
def dicom_webhook(request):
    """Recibe evento de nueva instancia DICOM desde Orthanc y encola análisis CNN."""
    if not _verify_hmac(request):
        logger.warning("Webhook DICOM rechazado: firma HMAC inválida")
        return Response(
            {"error": "Firma inválida"}, status=status.HTTP_401_UNAUTHORIZED,
        )

    data = request.data
    level = data.get("Level", "")
    orthanc_id = data.get("ID", "")

    if not orthanc_id:
        return Response(
            {"error": "ID de instancia Orthanc faltante"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if level not in ("Instance", "Series", "Study", ""):
        logger.info("Evento DICOM ignorado (level=%s)", level)
        return Response({"status": "ignored"})

    logger.info("Webhook DICOM recibido: level=%s id=%s", level, orthanc_id)

    paciente_id = data.get("paciente_id")
    usuario_id = data.get("usuario_id")

    task = procesar_estudio_dicom.delay(
        orthanc_instance_id=orthanc_id,
        paciente_id=int(paciente_id) if paciente_id else None,
        usuario_id=int(usuario_id) if usuario_id else None,
    )

    logger.info("Tarea DICOM encolada: task_id=%s para orthanc_id=%s", task.id, orthanc_id)

    return Response(
        {
            "status": "encolado",
            "task_id": task.id,
            "orthanc_id": orthanc_id,
        },
        status=status.HTTP_202_ACCEPTED,
    )
