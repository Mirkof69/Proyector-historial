"""Views para integración con Microservicio de IA

Incluye:
  - analyze_ultrasound_with_ai:  análisis síncrono (directo al microservicio FastAPI)
  - publish_to_rabbitmq:         publicación asíncrona a la cola dicom.analysis (RabbitMQ)
  - ai_result_callback:          endpoint receptor del callback del microservicio IA
"""

import base64
import json
import logging
import os

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# URL del microservicio de IA
AI_SERVICE_URL = getattr(settings, "AI_SERVICE_URL", "http://localhost:8001")

# URL RabbitMQ (leída de settings o variable de entorno)
RABBITMQ_URL = getattr(
    settings,
    "RABBITMQ_URL",
    os.environ.get("RABBITMQ_URL", "amqp://fetalmedical:RabbitMQ2026#Fetal@localhost:5672/"),
)
DICOM_QUEUE = "dicom.analysis"


def publish_to_rabbitmq(ecografia_id: str, image_bytes: bytes) -> bool:
    """Publica una ecografía en la cola RabbitMQ para análisis asíncrono.

    Args:
        ecografia_id: UUID de la ecografía en la BD.
        image_bytes:  Contenido binario de la imagen DICOM/JPG/PNG.

    Returns:
        True si se publicó correctamente, False en modo degradado (RabbitMQ no disponible).

    El callback Django que recibirá el resultado es:
        POST /api/ecografias/{ecografia_id}/ai-result/
    """
    try:
        import pika
    except ImportError:
        logger.warning(
            "pika no instalado en el entorno Django — "
            "publish_to_rabbitmq no disponible. Usar análisis síncrono."
        )
        return False

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    # Construir URL de callback usando la misma base que AI_SERVICE_URL conoce
    django_host = os.environ.get("DJANGO_INTERNAL_URL", "http://django:8000")
    callback_url = f"{django_host}/api/ecografias/{ecografia_id}/ai-result/"

    message = {
        "ecografia_id": str(ecografia_id),
        "image_base64": image_b64,
        "django_callback_url": callback_url,
    }

    try:
        params = pika.URLParameters(RABBITMQ_URL)
        params.heartbeat = 60
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(
            queue=DICOM_QUEUE,
            durable=True,
            arguments={"x-message-ttl": 86400000},
        )

        channel.basic_publish(
            exchange="",
            routing_key=DICOM_QUEUE,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,  # Mensaje persistente
                content_type="application/json",
            ),
        )
        connection.close()
        logger.info(
            "RabbitMQ: publicado ecografia_id=%s en cola '%s'", ecografia_id, DICOM_QUEUE
        )
        return True

    except Exception as exc:
        logger.warning(
            "RabbitMQ: no disponible al publicar ecografia_id=%s — %s. "
            "Modo degradado: usar análisis síncrono.",
            ecografia_id,
            exc,
        )
        return False


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_ultrasound_with_ai(request):
    """Analiza una ecografía usando el microservicio de IA

    Endpoint: POST /api/ecografias/analyze-with-ai/

    Request:
        - file: Archivo de imagen (DICOM, JPG, PNG)
        - ecografia_id: ID de la ecografía (opcional)

    Returns:
        - Análisis completo de IA
        - Clasificación, segmentación, anomalías
        - Recomendaciones médicas

    """
    try:
        # Validar que se envió un archivo
        if "file" not in request.FILES:
            return Response(
                {"error": "No se proporcionó archivo de imagen"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["file"]

        # Preparar request para el microservicio
        files = {"file": (image_file.name, image_file.read(), image_file.content_type)}

        # Llamar al microservicio de IA
        ai_response = requests.post(
            f"{AI_SERVICE_URL}/api/analyze", files=files, timeout=30,
        )

        if ai_response.status_code == 200:
            ai_results = ai_response.json()

            # Guardar resultados en la imagen ecográfica (si se provee ID)
            ecografia_id = request.data.get("ecografia_id")
            if ecografia_id:
                try:
                    from .models import ImagenEcografia

                    # Buscar la imagen más reciente de esa ecografía
                    imagen = (
                        ImagenEcografia.objects.filter(ecografia_id=ecografia_id)
                        .order_by("-fecha_captura")
                        .first()
                    )
                    if imagen:
                        imagen.analisis_ia = ai_results
                        imagen.save(update_fields=["analisis_ia"])
                except Exception:
                    pass  # No bloquear la respuesta si falla el guardado

            return Response(
                {
                    "status": "success",
                    "ai_analysis": ai_results,
                    "message": "Análisis de IA completado exitosamente",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": "Error en el microservicio de IA",
                "details": ai_response.text,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except requests.exceptions.ConnectionError:
        return Response(
            {
                "error": "No se pudo conectar al microservicio de IA",
                "details": "Verifique que el microservicio esté corriendo en puerto 8001",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except requests.exceptions.Timeout:
        return Response(
            {
                "error": "Timeout al procesar la imagen",
                "details": "El análisis tomó demasiado tiempo",
            },
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )

    except Exception as e:
        return Response(
            {"error": "Error inesperado", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def classify_ultrasound(request):
    """Clasifica el tipo de ecografía usando IA

    Endpoint: POST /api/ecografias/classify/
    """
    try:
        if "file" not in request.FILES:
            return Response(
                {"error": "No se proporcionó archivo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["file"]
        files = {"file": (image_file.name, image_file.read(), image_file.content_type)}

        ai_response = requests.post(
            f"{AI_SERVICE_URL}/api/classify", files=files, timeout=15,
        )

        if ai_response.status_code == 200:
            return Response(ai_response.json(), status=status.HTTP_200_OK)
        return Response(
            {"error": "Error en clasificación"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def detect_anomalies(request):
    """Detecta anomalías fetales usando IA

    Endpoint: POST /api/ecografias/detect-anomalies/
    """
    try:
        if "file" not in request.FILES:
            return Response(
                {"error": "No se proporcionó archivo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["file"]
        files = {"file": (image_file.name, image_file.read(), image_file.content_type)}

        ai_response = requests.post(
            f"{AI_SERVICE_URL}/api/detect-anomalies", files=files, timeout=15,
        )

        if ai_response.status_code == 200:
            return Response(ai_response.json(), status=status.HTTP_200_OK)
        return Response(
            {"error": "Error en detección de anomalías"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_service_health(_request):
    """Verifica el estado del microservicio de IA

    Endpoint: GET /api/ecografias/ai/health/
    """
    try:
        health_response = requests.get(f"{AI_SERVICE_URL}/health", timeout=5)

        if health_response.status_code == 200:
            return Response(
                {"status": "online", "ai_service": health_response.json()},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": "error",
                "message": "Microservicio no responde correctamente",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except requests.exceptions.ConnectionError:
        return Response(
            {"status": "offline", "message": "Microservicio de IA no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])  # Llamado internamente por el microservicio IA (red interna)
def ai_result_callback(request, ecografia_id):
    """Endpoint receptor del callback del Microservicio IA tras análisis asíncrono.

    Endpoint: POST /api/ecografias/{ecografia_id}/ai-result/

    Solo accesible desde la red interna de Docker (no expuesto por Kong al exterior).
    El microservicio IA llama a este endpoint con el resultado del análisis CNN.

    Body:
        status: "completed" | "error"
        ai_analysis: dict con el resultado completo (si status=completed)
        error: str con el mensaje de error (si status=error)
    """
    payload = request.data
    result_status = payload.get("status")

    try:
        from .models import ImagenEcografia

        # Buscar la imagen más reciente de esa ecografía
        imagen = (
            ImagenEcografia.objects.filter(ecografia_id=ecografia_id)
            .order_by("-fecha_captura")
            .first()
        )
        if not imagen:
            logger.warning(
                "ai_result_callback: no se encontró ImagenEcografia para ecografia_id=%s",
                ecografia_id,
            )
            return Response({"error": "Ecografía no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        if result_status == "completed":
            ai_analysis = payload.get("ai_analysis", {})
            imagen.analisis_ia = ai_analysis
            imagen.save(update_fields=["analisis_ia"])

            # Registrar en auditoría
            try:
                from auditoria.models import RegistroAuditoria

                RegistroAuditoria.registrar(
                    usuario=None,
                    accion="ANALISIS_CNN",
                    modulo="Ecografia",
                    registro_id=str(ecografia_id),
                    detalle=(
                        f"Análisis CNN completado — "
                        f"modelo: {ai_analysis.get('model_version', 'N/A')} | "
                        f"tiempo: {ai_analysis.get('inference_time_ms', 'N/A')}ms"
                    ),
                    request=None,
                )
            except Exception as audit_exc:
                logger.warning("ai_result_callback: error registrando auditoría — %s", audit_exc)

            # Notificar al médico vía WebSocket (Redis Pub/Sub) si channels está disponible
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync

                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f"ecografia_{ecografia_id}",
                        {
                            "type": "ai.result",
                            "ecografia_id": str(ecografia_id),
                            "status": "completed",
                            "score_global": ai_analysis.get("score_global"),
                        },
                    )
            except Exception as ws_exc:
                logger.debug("ai_result_callback: WebSocket notify skipped — %s", ws_exc)

            logger.info(
                "ai_result_callback: análisis guardado para ecografia_id=%s", ecografia_id
            )
            return Response({"status": "ok"}, status=status.HTTP_200_OK)

        else:
            # status == "error"
            error_msg = payload.get("error", "Error desconocido")
            logger.error(
                "ai_result_callback: microservicio IA reportó error para ecografia_id=%s — %s",
                ecografia_id,
                error_msg,
            )
            # Guardar el error en analisis_ia para que el médico vea el estado
            imagen.analisis_ia = {"estado": "ERROR", "error": error_msg}
            imagen.save(update_fields=["analisis_ia"])
            return Response({"status": "error_recorded"}, status=status.HTTP_200_OK)

    except Exception as exc:
        logger.error("ai_result_callback: error inesperado — %s", exc)
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
