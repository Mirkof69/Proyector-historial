"""Microservicio de IA — Fetal Medical Bolivia
Framework: PyTorch 2.2 + MONAI + EfficientNet-B4
"""

import base64
import json
import logging
import os
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8")

from contextlib import asynccontextmanager

import httpx
from app.config import CORS_ORIGINS
from app.routes import model_manager, preprocessor, router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# ── Configuración RabbitMQ (leída del entorno) ────────────────────────────────
RABBITMQ_URL = os.environ.get(
    "RABBITMQ_URL",
    "amqp://fetalmedical:RabbitMQ2026%23Fetal@localhost:5672/",  # %23 = URL-encode de #
)
DICOM_QUEUE = "dicom.analysis"
RABBITMQ_RETRY_DELAY = 10  # segundos entre reintentos de conexión


# ── Consumer RabbitMQ (thread daemon) ────────────────────────────────────────


def _process_dicom_message(body: bytes) -> None:
    """Procesa un mensaje de la cola dicom.analysis.

    Formato esperado del mensaje:
    {
        "ecografia_id": "uuid-string",
        "image_base64": "base64-encoded-image-bytes",
        "django_callback_url": "http://backend:8000/api/ecografias/{id}/ai-result/"
    }
    """
    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error("RabbitMQ: mensaje con formato inválido — %s", exc)
        return

    ecografia_id = payload.get("ecografia_id")
    image_b64 = payload.get("image_base64")
    callback_url = payload.get("django_callback_url")

    if not all([ecografia_id, image_b64, callback_url]):
        logger.error(
            "RabbitMQ: mensaje incompleto — falta ecografia_id, image_base64 o django_callback_url"
        )
        return

    logger.info("RabbitMQ: procesando ecografia_id=%s", ecografia_id)

    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception as exc:
        logger.error("RabbitMQ: error decodificando image_base64 — %s", exc)
        _post_error_callback(callback_url, ecografia_id, f"Error decodificando imagen: {exc}")
        return

    # Preprocesar imagen
    try:
        ext = ".jpg"  # default; DICOM se detecta por cabecera en preprocessor
        image = preprocessor.load_image(image_bytes, ext)
        enhanced = preprocessor.enhance_image(image)
    except Exception as exc:
        logger.error("RabbitMQ: error preprocesando imagen — %s", exc)
        _post_error_callback(callback_url, ecografia_id, f"Error preprocesando imagen: {exc}")
        return

    # Inferencia CNN
    try:
        result = model_manager.analyze(enhanced, compute_cam=True)
        result["ecografia_id"] = ecografia_id
    except Exception as exc:
        logger.error("RabbitMQ: error en inferencia CNN — %s", exc)
        _post_error_callback(callback_url, ecografia_id, f"Error en inferencia CNN: {exc}")
        return

    # Callback a Django con el resultado
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                callback_url,
                json={"status": "completed", "ai_analysis": result},
                headers={"Content-Type": "application/json"},
            )
        if resp.status_code not in (200, 201, 204):
            logger.warning(
                "RabbitMQ: callback a Django retornó %s para ecografia_id=%s",
                resp.status_code,
                ecografia_id,
            )
        else:
            logger.info(
                "RabbitMQ: resultado enviado a Django para ecografia_id=%s", ecografia_id
            )
    except Exception as exc:
        logger.error("RabbitMQ: error enviando callback a Django — %s", exc)


def _post_error_callback(callback_url: str, ecografia_id: str, error_msg: str) -> None:
    """Notifica a Django que el análisis falló."""
    try:
        with httpx.Client(timeout=10.0) as client:
            client.post(
                callback_url,
                json={"status": "error", "ecografia_id": ecografia_id, "error": error_msg},
                headers={"Content-Type": "application/json"},
            )
    except Exception as exc:
        logger.error("RabbitMQ: no se pudo enviar error_callback — %s", exc)


def _rabbitmq_consumer_loop() -> None:
    """Loop del consumer RabbitMQ. Se ejecuta en thread daemon.

    Conecta con reintentos (modo degradado si RabbitMQ no está disponible).
    El sistema clínico sigue funcionando — las ecografías en cola se procesan
    al restaurarse la conexión.
    """
    try:
        import pika
    except ImportError:
        logger.warning(
            "pika no instalado — consumer RabbitMQ deshabilitado. "
            "Instalar con: pip install pika>=1.3.2"
        )
        return

    while True:
        try:
            logger.info("RabbitMQ: intentando conectar a %s...", RABBITMQ_URL)
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            # Queue durable: sobrevive reinicios de RabbitMQ
            channel.queue_declare(
                queue=DICOM_QUEUE,
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # TTL 24h en ms
                    "x-dead-letter-exchange": "dicom.dlx",  # DLX para mensajes fallidos
                },
            )

            # Dead-letter exchange para mensajes que no se puedan procesar
            channel.exchange_declare(exchange="dicom.dlx", exchange_type="fanout", durable=True)
            channel.queue_declare(queue="dicom.dead_letters", durable=True)
            channel.queue_bind(queue="dicom.dead_letters", exchange="dicom.dlx")

            # Prefetch 1: no recibir más mensajes hasta confirmar el actual
            channel.basic_qos(prefetch_count=1)

            def on_message(ch, method, properties, body):
                try:
                    _process_dicom_message(body)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as exc:
                    logger.error("RabbitMQ: error no recuperable procesando mensaje — %s", exc)
                    # Nack sin requeue → va al DLX
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue=DICOM_QUEUE, on_message_callback=on_message)
            logger.info(
                "RabbitMQ: consumer activo en cola '%s'. Esperando mensajes DICOM...",
                DICOM_QUEUE,
            )
            channel.start_consuming()

        except Exception as exc:
            logger.warning(
                "RabbitMQ: no disponible (%s). Reintentando en %ss — "
                "modo degradado activo (ecografías en cola %s se procesarán al reconectar).",
                exc,
                RABBITMQ_RETRY_DELAY,
                DICOM_QUEUE,
            )
            time.sleep(RABBITMQ_RETRY_DELAY)


def start_rabbitmq_consumer() -> None:
    """Inicia el consumer RabbitMQ en un thread daemon."""
    t = threading.Thread(target=_rabbitmq_consumer_loop, name="rabbitmq-consumer", daemon=True)
    t.start()
    logger.info("RabbitMQ: consumer thread iniciado (daemon=True)")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan"""
    print(" Iniciando Microservicio IA — EfficientNet-B4 (PyTorch + MONAI)...")
    success = model_manager.load_models()
    if success:
        print("Modelo EfficientNet-B4 listo")
    else:
        print("Modelo no disponible — modo fallback activado (sin inferencia real)")

    # Iniciar consumer RabbitMQ en background (modo degradado si no disponible)
    start_rabbitmq_consumer()
    print("RabbitMQ consumer iniciado en background")

    yield
    print(" Deteniendo Microservicio IA...")


app = FastAPI(
    title="Fetal Medical AI API",
    description="""
 **Microservicio de IA** — EfficientNet-B4 (PyTorch 2.2 + MONAI)

## Endpoints CNN

- **POST /api/analyze** — Análisis completo: 15 patologías + biometría + Grad-CAM + SHAP risk scores
- **POST /api/detect-pathologies** — Detección de patologías fetales
- **POST /api/detect-anomalies** — Anomalías fetales con SHAP
- **POST /api/quality-check** — Calidad de imagen médica DICOM/PNG/JPG

## Endpoint Chatbot

- **POST /api/consultar** — Chatbot médico obstétrico (base de conocimiento boliviana)

## Sistema

- **GET /api/health** — Estado del servicio

## ⚠️ Aviso legal
La IA es herramienta de **apoyo diagnóstico**. El médico tiene responsabilidad legal (Ley 3131/2005 Bolivia).
    """,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/health", tags=["Sistema"])
async def health_check():
    """Health check"""
    device_str = str(model_manager.device) if model_manager.device else "N/A"
    try:
        import torch

        pt_version = torch.__version__
    except ImportError:
        pt_version = "no instalado"
    return {
        "status": "healthy",
        "service": "Fetal Medical AI v3.0",
        "framework": "PyTorch + MONAI + EfficientNet-B4",
        "model_loaded": model_manager._loaded,
        "pytorch_version": pt_version,
        "device": device_str,
    }
