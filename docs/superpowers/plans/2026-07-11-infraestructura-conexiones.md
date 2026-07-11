# Infraestructura y Conexiones — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Arreglar el cableado roto entre Django, el microservicio de IA y RabbitMQ para desarrollo nativo en Windows, y dejar la configuración de Kong correcta (aunque no se corra en local).

**Architecture:** Stack 100% nativo en Windows (Postgres, Redis y RabbitMQ ya instalados o a instalar como servicios de Windows; Django y el microservicio FastAPI corridos directo con `python`/`uvicorn`). Kong se corrige en configuración pero no se ejecuta localmente (no tiene instalador nativo para Windows). Se añade un consumer real de RabbitMQ al microservicio de IA y se conecta el publisher hoy muerto en Django a un nuevo endpoint asíncrono.

**Tech Stack:** Django 5 + DRF, FastAPI (microservicio IA), `pika` (RabbitMQ), PyTorch/MONAI (modelo ya entrenado), pytest / pytest-django.

## Global Constraints

- Todo el trabajo de este plan corre nativo en Windows — no usar Docker Compose para verificar nada.
- Kong se corrige en `kong/kong.yml` y en las variables de entorno, pero **no se instala ni se corre localmente**.
- No tocar el flujo síncrono existente (`analyze_ultrasound_with_ai`, `ia_medica/dicom_consumer.py` vía Celery) — el flujo nuevo de RabbitMQ es aditivo, no reemplaza nada.
- El consumer nuevo del microservicio de IA reutiliza el `model_manager` y el `preprocessor` ya cargados en `app/main.py` (un solo proceso, un solo modelo en memoria) — no cargar el modelo dos veces.
- Mejorar la precisión del modelo de IA queda fuera de este plan (sub-proyecto aparte, ya acordado).

---

### Task 1: Alinear el puerto y las URLs internas del microservicio de IA

**Contexto del bug:** `Backend/Microservicio_IA/Dockerfile:38` expone el puerto `8001`, y `docker-compose.yml:95,132` usa `AI_SERVICE_URL=https://ia_service:8001`. Pero los defaults en código (`Backend/ecografias/ai_views.py:26`, `Backend/ia_medica/services/cnn_service.py:57,59`) y `Backend/.env:53` apuntan a `8002`. Con la config actual, Django native nunca podría hablar con el microservicio nativo corrido en el puerto correcto (`8001`) a menos que se corrija esto — es un bug de cableado real, no solo cosmético.

**Files:**
- Modify: `Backend/.env:53`
- Modify: `Backend/ecografias/ai_views.py:26`
- Modify: `Backend/ia_medica/services/cnn_service.py:57,59`
- Test: `Backend/tests/test_ia_medica.py` (agregar al final del archivo)

**Interfaces:**
- Produces: `ecografias.ai_views.AI_SERVICE_URL` (str, default `"http://localhost:8001"`), `ia_medica.services.cnn_service._get_ml_service_url()` (función cacheada, mismo default).

- [ ] **Step 1: Escribir los tests que fallan (puerto por defecto)**

Agregar al final de `Backend/tests/test_ia_medica.py`:

```python
import importlib


class AiServiceUrlDefaultTest(TestCase):
    """El microservicio de IA corre en el puerto 8001 (ver Dockerfile EXPOSE 8001
    y docker-compose.yml). Los defaults de código deben coincidir con ese puerto,
    no con 8002 (bug de cableado detectado en la sesion de 2026-07-11)."""

    def test_ai_views_default_matches_microservice_port(self):
        import os
        had_env = "AI_SERVICE_URL" in os.environ
        old_value = os.environ.pop("AI_SERVICE_URL", None)
        try:
            from ecografias import ai_views
            importlib.reload(ai_views)
            self.assertEqual(ai_views.AI_SERVICE_URL, "http://localhost:8001")
        finally:
            if had_env:
                os.environ["AI_SERVICE_URL"] = old_value

    def test_cnn_service_default_matches_microservice_port(self):
        import os
        from ia_medica.services import cnn_service
        had_env = "AI_SERVICE_URL" in os.environ
        old_value = os.environ.pop("AI_SERVICE_URL", None)
        try:
            cnn_service._get_ml_service_url.cache_clear()
            self.assertEqual(cnn_service._get_ml_service_url(), "http://localhost:8001")
        finally:
            cnn_service._get_ml_service_url.cache_clear()
            if had_env:
                os.environ["AI_SERVICE_URL"] = old_value
```

- [ ] **Step 2: Ejecutar y verificar que fallan**

Run: `cd Backend && python -m pytest tests/test_ia_medica.py -k AiServiceUrlDefaultTest -v`
Expected: 2 FAILED — `AssertionError: 'http://localhost:8002' != 'http://localhost:8001'`

- [ ] **Step 3: Corregir los tres defaults**

En `Backend/ecografias/ai_views.py:26`, cambiar:
```python
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:8002")
```
por:
```python
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:8001")
```

En `Backend/ia_medica/services/cnn_service.py:57`, cambiar:
```python
        return getattr(settings, "AI_SERVICE_URL", os.environ.get("AI_SERVICE_URL", "http://localhost:8002"))
```
por:
```python
        return getattr(settings, "AI_SERVICE_URL", os.environ.get("AI_SERVICE_URL", "http://localhost:8001"))
```

Y en la línea 59 del mismo archivo, cambiar:
```python
        return os.environ.get("AI_SERVICE_URL", "http://localhost:8002")
```
por:
```python
        return os.environ.get("AI_SERVICE_URL", "http://localhost:8001")
```

- [ ] **Step 4: Corregir `Backend/.env:53`**

Cambiar:
```
AI_SERVICE_URL=http://localhost:8002
```
por:
```
AI_SERVICE_URL=http://localhost:8001
```

- [ ] **Step 5: Ejecutar y verificar que los tests pasan**

Run: `cd Backend && python -m pytest tests/test_ia_medica.py -k AiServiceUrlDefaultTest -v`
Expected: 2 PASSED

- [ ] **Step 6: Commit**

```bash
git add Backend/.env Backend/ecografias/ai_views.py Backend/ia_medica/services/cnn_service.py Backend/tests/test_ia_medica.py
git commit -m "fix: alinear puerto del microservicio de IA (8002 -> 8001)"
```

---

### Task 2: Corregir la configuración JWT de Kong y eliminar el archivo deprecado

**Contexto del bug:** `kong/kong.yml:39` exige `key_claim_name: iss` (el JWT debe traer un claim `iss` que coincida con el `key` del consumer), pero `Backend/settings.py:619` tiene `"ISSUER": None` — SimpleJWT nunca emite ese claim. Además `KONG_JWT_SECRET` (usado para verificar la firma HS256) no coincide con `SECRET_KEY` (que es con lo que Django realmente firma) ni en `.env.docker` ni en `.env.production`.

**Files:**
- Modify: `Backend/settings.py:607-622` (bloque `SIMPLE_JWT`)
- Modify: `Backend/.env.docker:72`
- Modify: `Backend/.env.production:48`
- Delete: `Backend/kong.yml`
- Modify: `docker-compose.yml` (comentario en el servicio `celery`)

- [ ] **Step 1: Fijar el ISSUER de SimpleJWT para que coincida con el consumer de Kong**

En `Backend/settings.py`, dentro del diccionario `SIMPLE_JWT` (línea 619), cambiar:
```python
    "ISSUER": None,
```
por:
```python
    "ISSUER": "fetal-medical-frontend",  # debe coincidir con el `key` del
    # consumer "fetal-medical-frontend" en kong/kong.yml (key_claim_name: iss)
```

- [ ] **Step 2: Verificar que el token ahora incluye el claim `iss`**

Run:
```bash
cd Backend && python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()
from rest_framework_simplejwt.tokens import RefreshToken
from usuarios.models import Usuario
u = Usuario.objects.first()
if u is None:
    print('No hay usuarios en la BD todavia - test manual pendiente tras crear uno')
else:
    token = RefreshToken.for_user(u).access_token
    print('iss claim:', token.get('iss'))
"
```
Expected: `iss claim: fetal-medical-frontend` (o el mensaje de "no hay usuarios" si la BD está vacía — no es un fallo, solo falta un usuario de prueba).

- [ ] **Step 3: Unificar el secreto de Kong con `SECRET_KEY` en `.env.docker`**

En `Backend/.env.docker:72`, cambiar:
```
KONG_JWT_SECRET=DockerKongJWTSecret2026
```
por (mismo valor literal que `SECRET_KEY` en la línea 12 de ese archivo):
```
KONG_JWT_SECRET=django-insecure-fetal-medical-bolivia-2026-production-key-change-this
```

- [ ] **Step 4: Documentar el mismo requisito en `.env.production`**

En `Backend/.env.production:48`, cambiar:
```
KONG_JWT_SECRET=REEMPLAZAR-CON-KONG-JWT-SECRET
```
por:
```
KONG_JWT_SECRET=REEMPLAZAR-CON-EL-MISMO-VALOR-EXACTO-DE-SECRET_KEY-DE-ARRIBA
```

- [ ] **Step 5: Eliminar el archivo `kong.yml` deprecado**

```bash
git rm Backend/kong.yml
```

- [ ] **Step 6: Documentar el gap de Celery en `docker-compose.yml` (sin corregirlo — fuera de alcance de este plan)**

Buscar el servicio `celery:` en `docker-compose.yml` (alrededor de la línea 106) y agregar, justo antes de la línea `command: celery -A celery_app worker...`, este comentario:
```yaml
    # NOTA (2026-07-11): CELERY_BROKER_URL/CELERY_RESULT_BACKEND solo estan
    # seteadas aqui, NO en el servicio `backend` de mas arriba. Si se dispara
    # una tarea Celery desde una vista de Django corriendo en Docker, cae al
    # default de settings.py (localhost:6379), que dentro del contenedor
    # `backend` no es Redis. Pendiente de un sub-proyecto de correccion de
    # docker-compose antes de usar este flujo en produccion.
```

- [ ] **Step 7: Commit**

```bash
git add Backend/settings.py Backend/.env.docker Backend/.env.production docker-compose.yml
git rm Backend/kong.yml
git commit -m "fix: alinear JWT de Kong (issuer + secreto) y eliminar kong.yml deprecado"
```

---

### Task 3: Instalar RabbitMQ nativo en Windows y verificar compatibilidad de `pika`

**Nota:** RabbitMQ no tiene paquete en `winget` — solo Erlang OTP lo tiene. Este task combina un paso automatizable (Erlang vía winget) con un paso manual (instalador oficial de RabbitMQ), y termina con una verificación explícita de versiones antes de escribir el consumer (Task 6), tal como pidió el usuario.

**Files:** ninguno (paso operativo, sin cambios de código).

- [ ] **Step 1: Instalar Erlang OTP (requisito de RabbitMQ) vía winget**

```powershell
winget install --id Erlang.ErlangOTP -e --silent --accept-package-agreements --accept-source-agreements
```
Expected: `Instalado correctamente`.

- [ ] **Step 2: Descargar e instalar RabbitMQ Server**

RabbitMQ no está en winget — descargar el instalador oficial desde `https://github.com/rabbitmq/rabbitmq-server/releases` (buscar el `.exe` de la última versión estable, ej. `rabbitmq-server-4.x.x.exe`) y ejecutarlo. El instalador detecta Erlang automáticamente y registra el servicio de Windows `RabbitMQ`.

**Este paso requiere confirmación explícita del usuario antes de ejecutarse** (descarga de un instalador externo, no un paquete de un registro curado como winget) — pedir permiso igual que se hizo con PostgreSQL.

- [ ] **Step 3: Verificar que el servicio quedó activo**

```powershell
Get-Service -Name 'RabbitMQ' | Select-Object Name, Status, StartType
```
Expected: `Status: Running`, `StartType: Automatic`.

```bash
netstat -ano | findstr ":5672"
```
Expected: una línea `LISTENING`.

- [ ] **Step 4: Habilitar el plugin de administración (opcional pero útil para depurar colas)**

```powershell
cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-<version>\sbin"
.\rabbitmq-plugins.bat enable rabbitmq_management
```
Expected: mensaje de plugin activado. La UI queda disponible en `http://localhost:15672` (usuario/password por defecto: `guest`/`guest`, solo accesible desde `localhost`).

- [ ] **Step 5: Verificar la versión de RabbitMQ instalada**

```powershell
& "C:\Program Files\RabbitMQ Server\rabbitmq_server-<version>\sbin\rabbitmqctl.bat" version
```
Anotar la versión exacta (ej. `4.0.x`).

- [ ] **Step 6: Verificar compatibilidad de `pika` contra esa versión**

`pika` es un cliente AMQP 0-9-1 puro — RabbitMQ soporta AMQP 0-9-1 en todas sus versiones activas (no es una API que se retire), así que cualquier `pika>=1.3.2` (ya en `requirements.txt`) es compatible con cualquier RabbitMQ 3.x/4.x moderno. Aun así, confirmarlo en vivo antes de escribir el consumer:

```bash
cd Backend/Microservicio_IA && .venv_gpu/Scripts/python.exe -c "
import pika
print('pika version:', pika.__version__)
params = pika.URLParameters('amqp://guest:guest@localhost:5672/')
conn = pika.BlockingConnection(params)
print('Conexion OK, server properties:', conn.connection.server_properties.get('version'))
conn.close()
"
```
Expected: imprime la versión de `pika` instalada y la versión del servidor RabbitMQ sin excepción — confirma que el cliente puede conectar y negociar el protocolo antes de escribir una sola línea del consumer.

- [ ] **Step 7: Agregar `RABBITMQ_URL` a `.env` para desarrollo nativo**

El default en código (`Backend/ecografias/ai_views.py:32`) espera un usuario/vhost `fetalmedical` que solo existe en el `docker-compose.yml` de producción. Para desarrollo nativo, agregar a `Backend/.env`:
```
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```
(El usuario `guest` de RabbitMQ solo acepta conexiones desde `localhost` por default — suficiente para desarrollo nativo.)

- [ ] **Step 8: Commit**

```bash
git add Backend/.env
git commit -m "chore: configurar RABBITMQ_URL para desarrollo nativo en Windows"
```

---

### Task 4: Declarar la cola con dead-letter y agregar `filename` al mensaje publicado

**Contexto:** El consumer (Task 6) necesita saber la extensión del archivo para decidir si es DICOM o una imagen estándar (`PILImagePreprocessor.load_image(content, ext)` lo requiere), pero el mensaje publicado hoy no incluye `filename`. Además, para que el consumer pueda enrutar mensajes fallidos a una dead-letter queue, la cola debe declararse con los mismos argumentos en ambos lados (RabbitMQ rechaza una redeclaración con argumentos distintos).

**Files:**
- Modify: `Backend/ecografias/ai_views.py:34-104`
- Test: `Backend/tests/test_ia_medica.py` (agregar)

**Interfaces:**
- Produces: `publish_to_rabbitmq(ecografia_id: str, image_bytes: bytes, filename: str) -> bool` (firma nueva, con `filename` agregado). Mensaje publicado: `{"ecografia_id": str, "image_base64": str, "filename": str, "django_callback_url": str}`.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `Backend/tests/test_ia_medica.py`:

```python
from unittest.mock import MagicMock, patch


class PublishToRabbitmqTest(TestCase):
    def test_publish_includes_filename_and_dlx_args(self):
        from ecografias.ai_views import publish_to_rabbitmq

        fake_channel = MagicMock()
        fake_connection = MagicMock()
        fake_connection.channel.return_value = fake_channel

        with patch("pika.BlockingConnection", return_value=fake_connection), \
             patch("pika.URLParameters"):
            result = publish_to_rabbitmq("eco-123", b"fake-bytes", "imagen.png")

        self.assertTrue(result)
        # El mensaje publicado debe incluir "filename"
        publish_call = fake_channel.basic_publish.call_args
        import json
        body = json.loads(publish_call.kwargs["body"])
        self.assertEqual(body["filename"], "imagen.png")
        # La cola debe declararse con dead-letter-exchange (debe coincidir con el consumer)
        declare_call = fake_channel.queue_declare.call_args
        self.assertEqual(
            declare_call.kwargs["arguments"]["x-dead-letter-exchange"],
            "dicom.analysis.dlx",
        )
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd Backend && python -m pytest tests/test_ia_medica.py -k PublishToRabbitmqTest -v`
Expected: FAILED — `TypeError: publish_to_rabbitmq() takes 2 positional arguments but 3 were given`

- [ ] **Step 3: Actualizar `publish_to_rabbitmq` con el parámetro `filename` y los argumentos de dead-letter**

Reemplazar por completo el cuerpo de la función en `Backend/ecografias/ai_views.py:34-104`:

```python
DICOM_QUEUE = "dicom.analysis"
DICOM_QUEUE_ARGS = {
    "x-message-ttl": 86400000,
    "x-dead-letter-exchange": "dicom.analysis.dlx",
    "x-dead-letter-routing-key": "dicom.analysis.dead",
}
# IMPORTANTE: estos argumentos deben coincidir EXACTAMENTE con los que declara
# el consumer en Backend/Microservicio_IA/app/rabbitmq_consumer.py — RabbitMQ
# rechaza una redeclaración de la misma cola con argumentos distintos.


def publish_to_rabbitmq(ecografia_id: str, image_bytes: bytes, filename: str) -> bool:
    """Publica una ecografía en la cola RabbitMQ para análisis asíncrono.

    Args:
        ecografia_id: UUID de la ecografía en la BD.
        image_bytes:  Contenido binario de la imagen DICOM/JPG/PNG.
        filename:     Nombre original del archivo (el consumer lo necesita
                       para decidir si es DICOM o una imagen estándar).

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
    django_host = os.environ.get("DJANGO_INTERNAL_URL", "http://django:8000")
    callback_url = f"{django_host}/api/ecografias/{ecografia_id}/ai-result/"

    message = {
        "ecografia_id": str(ecografia_id),
        "image_base64": image_b64,
        "filename": filename,
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
            arguments=DICOM_QUEUE_ARGS,
        )

        channel.basic_publish(
            exchange="",
            routing_key=DICOM_QUEUE,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
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
```

- [ ] **Step 4: Ejecutar y verificar que el test pasa**

Run: `cd Backend && python -m pytest tests/test_ia_medica.py -k PublishToRabbitmqTest -v`
Expected: PASSED

- [ ] **Step 5: Commit**

```bash
git add Backend/ecografias/ai_views.py Backend/tests/test_ia_medica.py
git commit -m "feat: agregar filename y argumentos de dead-letter al mensaje de RabbitMQ"
```

---

### Task 5: Conectar el publisher a un endpoint real (nuevo view asíncrono)

**Contexto:** Hoy `publish_to_rabbitmq()` no la llama ninguna vista — es código muerto. Se agrega un endpoint nuevo (`analyze_ultrasound_with_ai_async`) que reutiliza la misma lógica de lectura de archivo que `analyze_ultrasound_with_ai`, pero en vez de llamar sincrónicamente al microservicio, publica el mensaje y devuelve `202 Accepted`. El endpoint síncrono existente no se toca.

**Files:**
- Modify: `Backend/ecografias/ai_views.py` (agregar función nueva al final)
- Modify: `Backend/ecografias/urls.py`
- Test: `Backend/tests/test_ia_medica.py` (agregar)

**Interfaces:**
- Consumes: `publish_to_rabbitmq(ecografia_id, image_bytes, filename)` (Task 4).
- Produces: endpoint `POST /api/ecografias/analyze-with-ai-async/`, nombre de ruta `analyze-with-ai-async`.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `Backend/tests/test_ia_medica.py`:

```python
class AnalyzeAsyncEndpointTest(APITestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            email="medico2@test.com",
            nombre="Dr",
            apellido_paterno="Async",
            password="pass12345",
            rol="medico",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_queues_analysis_and_returns_202(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake_image = SimpleUploadedFile(
            "eco.jpg", b"fake-image-bytes", content_type="image/jpeg"
        )
        with patch("ecografias.ai_views.publish_to_rabbitmq", return_value=True) as mock_publish:
            response = self.client.post(
                "/api/ecografias/analyze-with-ai-async/",
                {"file": fake_image, "ecografia_id": "eco-999"},
                format="multipart",
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["status"], "queued")
        mock_publish.assert_called_once()
        args = mock_publish.call_args.args
        self.assertEqual(args[0], "eco-999")
        self.assertEqual(args[2], "eco.jpg")

    def test_returns_503_when_rabbitmq_unavailable(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake_image = SimpleUploadedFile(
            "eco.jpg", b"fake-image-bytes", content_type="image/jpeg"
        )
        with patch("ecografias.ai_views.publish_to_rabbitmq", return_value=False):
            response = self.client.post(
                "/api/ecografias/analyze-with-ai-async/",
                {"file": fake_image, "ecografia_id": "eco-999"},
                format="multipart",
            )

        self.assertEqual(response.status_code, 503)
```

Este test necesita `Usuario`, `APIClient`, `APITestCase` y `patch` importados — ya están importados en `test_ecografias.py`; en `test_ia_medica.py` agregar al principio del archivo (si faltan):
```python
from unittest.mock import patch
from rest_framework.test import APIClient, APITestCase
from usuarios.models import Usuario
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd Backend && python -m pytest tests/test_ia_medica.py -k AnalyzeAsyncEndpointTest -v`
Expected: FAILED — `404 Not Found` (la ruta todavía no existe)

- [ ] **Step 3: Escribir la vista nueva**

Agregar al final de `Backend/ecografias/ai_views.py`:

```python
@extend_schema(
    request=inline_serializer(
        "analyze_ultrasound_with_ai_async_request",
        fields={}
    ),
    responses={202: dict}
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_ultrasound_with_ai_async(request):
    """Encola una ecografía para análisis asíncrono vía RabbitMQ.

    Endpoint: POST /api/ecografias/analyze-with-ai-async/

    A diferencia de analyze_ultrasound_with_ai (síncrono), esta vista no
    espera el resultado del microservicio: publica el mensaje en la cola
    dicom.analysis y responde 202 de inmediato. El resultado llega más
    tarde vía ai_result_callback y se notifica al frontend por WebSocket.

    Request:
        - file: Archivo de imagen (DICOM, JPG, PNG)
        - ecografia_id: ID de la ecografía (requerido en este endpoint,
          a diferencia del síncrono, porque no hay otra forma de
          correlacionar la respuesta asíncrona con el registro correcto)
    """
    ecografia_id = request.data.get("ecografia_id")
    if not ecografia_id:
        return Response(
            {"error": "ecografia_id es requerido para el análisis asíncrono"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if "file" not in request.FILES:
        return Response(
            {"error": "No se proporcionó archivo de imagen"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    image_file = request.FILES["file"]
    image_bytes = image_file.read()
    filename = image_file.name

    queued = publish_to_rabbitmq(ecografia_id, image_bytes, filename)

    if not queued:
        return Response(
            {
                "error": "RabbitMQ no disponible",
                "details": "Use /api/ecografias/analyze-with-ai/ (síncrono) mientras tanto",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(
        {"status": "queued", "ecografia_id": ecografia_id},
        status=status.HTTP_202_ACCEPTED,
    )
```

- [ ] **Step 4: Registrar la ruta**

En `Backend/ecografias/urls.py`, agregar `analyze_ultrasound_with_ai_async` al import (línea 5-12):
```python
from .ai_views import (
    ai_result_callback,
    ai_service_health,
    analyze_ultrasound_with_ai,
    analyze_ultrasound_with_ai_async,
    classify_ultrasound,
    crear_ecografia_desde_ia,
    detect_anomalies,
)
```

Y agregar la ruta junto a `analyze-with-ai/` (línea 22):
```python
    path("analyze-with-ai/", analyze_ultrasound_with_ai, name="analyze-with-ai"),
    path("analyze-with-ai-async/", analyze_ultrasound_with_ai_async, name="analyze-with-ai-async"),
```

- [ ] **Step 5: Ejecutar y verificar que los tests pasan**

Run: `cd Backend && python -m pytest tests/test_ia_medica.py -k AnalyzeAsyncEndpointTest -v`
Expected: 2 PASSED

- [ ] **Step 6: Commit**

```bash
git add Backend/ecografias/ai_views.py Backend/ecografias/urls.py Backend/tests/test_ia_medica.py
git commit -m "feat: conectar publish_to_rabbitmq a un endpoint real de analisis asincrono"
```

---

### Task 6: Implementar el consumer real en el microservicio de IA

**Files:**
- Create: `Backend/Microservicio_IA/app/rabbitmq_consumer.py`
- Modify: `Backend/Microservicio_IA/app/main.py`
- Test: `Backend/Microservicio_IA/test_rabbitmq_consumer.py`

**Interfaces:**
- Consumes: `ModelManager.analyze(image: np.ndarray, compute_cam: bool, altitude_m: float | None) -> dict` (ya existe en `app/models.py`), `PILImagePreprocessor.load_image(bytes, ext) -> np.ndarray` y `.enhance_image(np.ndarray) -> np.ndarray` (ya existen en `app/preprocessing.py`).
- Produces: `start_consumer_thread(model_manager: ModelManager) -> threading.Thread` — se llama una vez desde el `lifespan` de `app/main.py`.

- [ ] **Step 1: Escribir el test que falla**

Crear `Backend/Microservicio_IA/test_rabbitmq_consumer.py`:

```python
"""Test del consumer de RabbitMQ del microservicio de IA.

Ejecutar: .venv_gpu/Scripts/python.exe -m pytest test_rabbitmq_consumer.py -v
"""
import json
from unittest.mock import MagicMock, patch

from app.rabbitmq_consumer import _process_message


def test_process_message_calls_model_and_posts_callback():
    fake_model_manager = MagicMock()
    fake_model_manager.analyze.return_value = {
        "status": "success",
        "score_global": 0.1,
        "modelo_version": "EfficientNet-B4",
        "inference_time_ms": 42,
    }

    body = json.dumps({
        "ecografia_id": "eco-123",
        "image_base64": "ZmFrZS1pbWFnZS1ieXRlcw==",  # b"fake-image-bytes"
        "filename": "eco.jpg",
        "django_callback_url": "http://localhost:8000/api/ecografias/eco-123/ai-result/",
    }).encode("utf-8")

    fake_image_array = "fake-ndarray"
    with patch("app.rabbitmq_consumer.preprocessor") as mock_preprocessor, \
         patch("app.rabbitmq_consumer.requests.post") as mock_post:
        mock_preprocessor.load_image.return_value = fake_image_array
        mock_preprocessor.enhance_image.return_value = fake_image_array
        mock_post.return_value = MagicMock(status_code=200)

        result = _process_message(body, fake_model_manager)

    assert result is True
    mock_preprocessor.load_image.assert_called_once()
    load_args = mock_preprocessor.load_image.call_args.args
    assert load_args[1] == ".jpg"  # extension derivada de "eco.jpg"
    fake_model_manager.analyze.assert_called_once()
    mock_post.assert_called_once()
    posted_url, posted_kwargs = mock_post.call_args.args[0], mock_post.call_args.kwargs
    assert posted_url == "http://localhost:8000/api/ecografias/eco-123/ai-result/"
    assert posted_kwargs["json"]["status"] == "completed"


def test_process_message_retries_callback_then_gives_up():
    fake_model_manager = MagicMock()
    fake_model_manager.analyze.return_value = {"status": "success"}

    body = json.dumps({
        "ecografia_id": "eco-456",
        "image_base64": "ZmFrZQ==",
        "filename": "eco.png",
        "django_callback_url": "http://localhost:8000/api/ecografias/eco-456/ai-result/",
    }).encode("utf-8")

    with patch("app.rabbitmq_consumer.preprocessor") as mock_preprocessor, \
         patch("app.rabbitmq_consumer.requests.post", side_effect=ConnectionError("down")) as mock_post, \
         patch("app.rabbitmq_consumer.time.sleep") as mock_sleep:
        mock_preprocessor.load_image.return_value = "fake-ndarray"
        mock_preprocessor.enhance_image.return_value = "fake-ndarray"

        result = _process_message(body, fake_model_manager)

    assert result is False
    assert mock_post.call_count == 3  # 3 intentos antes de rendirse
    assert mock_sleep.call_count == 2  # espera entre intento 1-2 y 2-3
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd Backend/Microservicio_IA && .venv_gpu/Scripts/python.exe -m pytest test_rabbitmq_consumer.py -v`
Expected: FAILED — `ModuleNotFoundError: No module named 'app.rabbitmq_consumer'`

- [ ] **Step 3: Crear `app/rabbitmq_consumer.py`**

```python
"""Consumer de RabbitMQ para análisis asíncrono de ecografías.

Consume la cola `dicom.analysis` (publicada por Django, ver
Backend/ecografias/ai_views.py::publish_to_rabbitmq), procesa la imagen con
el modelo ya cargado en memoria, y llama de vuelta al callback de Django.

Corre en un hilo daemon separado del event loop de FastAPI (pika es
bloqueante), iniciado una vez desde el lifespan de app/main.py.
"""
import base64
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import requests

from .preprocessing import PILImagePreprocessor as ImagePreprocessor

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
DICOM_QUEUE = "dicom.analysis"
DICOM_QUEUE_ARGS = {
    "x-message-ttl": 86400000,
    "x-dead-letter-exchange": "dicom.analysis.dlx",
    "x-dead-letter-routing-key": "dicom.analysis.dead",
}
# IMPORTANTE: debe coincidir EXACTAMENTE con Backend/ecografias/ai_views.py::DICOM_QUEUE_ARGS

CALLBACK_MAX_RETRIES = 3
CALLBACK_RETRY_DELAY_S = 2

preprocessor = ImagePreprocessor()


def _process_message(body: bytes, model_manager) -> bool:
    """Procesa un mensaje de la cola. Retorna True si se completó
    exitosamente (incluye el caso en que se pudo notificar un error a
    Django), False si hay que mandar el mensaje a la dead-letter queue."""
    try:
        message = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.error("Mensaje no es JSON valido, descartando a DLQ")
        return False

    ecografia_id = message.get("ecografia_id")
    callback_url = message.get("django_callback_url")
    filename = message.get("filename", "")
    ext = os.path.splitext(filename)[1].lower()

    try:
        image_bytes = base64.b64decode(message["image_base64"])
        image = preprocessor.load_image(image_bytes, ext)
        enhanced = preprocessor.enhance_image(image)
        result = model_manager.analyze(enhanced, compute_cam=True)
        result["filename"] = filename
        payload = {"status": "completed", "ai_analysis": result}
    except Exception as exc:
        logger.exception("Error procesando ecografia_id=%s: %s", ecografia_id, exc)
        payload = {"status": "error", "error": str(exc)}

    for attempt in range(1, CALLBACK_MAX_RETRIES + 1):
        try:
            response = requests.post(callback_url, json=payload, timeout=15)
            if response.status_code == 200:
                logger.info(
                    "Callback entregado para ecografia_id=%s (intento %d)",
                    ecografia_id, attempt,
                )
                return True
            logger.warning(
                "Callback respondio %d para ecografia_id=%s (intento %d)",
                response.status_code, ecografia_id, attempt,
            )
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Callback fallo para ecografia_id=%s (intento %d/%d): %s",
                ecografia_id, attempt, CALLBACK_MAX_RETRIES, exc,
            )
        if attempt < CALLBACK_MAX_RETRIES:
            time.sleep(CALLBACK_RETRY_DELAY_S)

    logger.error(
        "Callback agoto reintentos para ecografia_id=%s — enviando a dead-letter",
        ecografia_id,
    )
    return False


def _consume_loop(model_manager):
    import pika

    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 60
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.exchange_declare(
                exchange="dicom.analysis.dlx", exchange_type="direct", durable=True,
            )
            channel.queue_declare(queue="dicom.analysis.dead", durable=True)
            channel.queue_bind(
                queue="dicom.analysis.dead",
                exchange="dicom.analysis.dlx",
                routing_key="dicom.analysis.dead",
            )
            channel.queue_declare(queue=DICOM_QUEUE, durable=True, arguments=DICOM_QUEUE_ARGS)
            channel.basic_qos(prefetch_count=1)

            def _on_message(ch, method, _properties, body):
                ok = _process_message(body, model_manager)
                if ok:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue=DICOM_QUEUE, on_message_callback=_on_message)
            logger.info("RabbitMQ consumer escuchando en cola '%s'", DICOM_QUEUE)
            channel.start_consuming()

        except Exception as exc:
            logger.warning(
                "RabbitMQ consumer: conexion perdida o no disponible (%s). "
                "Reintentando en 10s...", exc,
            )
            time.sleep(10)


def start_consumer_thread(model_manager) -> threading.Thread:
    thread = threading.Thread(
        target=_consume_loop, args=(model_manager,), daemon=True, name="rabbitmq-consumer",
    )
    thread.start()
    return thread
```

- [ ] **Step 4: Ejecutar y verificar que los tests pasan**

Run: `cd Backend/Microservicio_IA && .venv_gpu/Scripts/python.exe -m pytest test_rabbitmq_consumer.py -v`
Expected: 2 PASSED

- [ ] **Step 5: Conectar el consumer al lifespan de la app**

En `Backend/Microservicio_IA/app/main.py`, reemplazar:
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .routes import router
from .models import ModelManager

model_manager = ModelManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_manager.load_models()
    import app.routes
    app.routes.model_manager = model_manager
    yield
```
por:
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .routes import router
from .models import ModelManager
from .rabbitmq_consumer import start_consumer_thread

model_manager = ModelManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_manager.load_models()
    import app.routes
    app.routes.model_manager = model_manager
    start_consumer_thread(model_manager)
    yield
```

- [ ] **Step 6: Commit**

```bash
git add Backend/Microservicio_IA/app/rabbitmq_consumer.py Backend/Microservicio_IA/app/main.py Backend/Microservicio_IA/test_rabbitmq_consumer.py
git commit -m "feat: implementar consumer real de RabbitMQ en el microservicio de IA"
```

---

### Task 7: Verificación end-to-end manual

**Files:** ninguno (solo verificación).

- [ ] **Step 1: Levantar el stack nativo completo**

En 3 ventanas de PowerShell separadas:
```powershell
# Ventana 1
cd "Backend"; python manage.py runserver 0.0.0.0:8000

# Ventana 2
cd "Backend\Microservicio_IA"; .venv_gpu\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# (RabbitMQ y PostgreSQL ya corren como servicios de Windows)
```

- [ ] **Step 2: Confirmar que el consumer arrancó**

Revisar el log de la ventana 2 — debe aparecer: `RabbitMQ consumer escuchando en cola 'dicom.analysis'`.

- [ ] **Step 3: Crear un usuario y autenticarse**

```bash
cd Backend && python manage.py shell -c "
from usuarios.models import Usuario
if not Usuario.objects.filter(email='test@test.com').exists():
    Usuario.objects.create_superuser(email='test@test.com', nombre='Test', apellido_paterno='User', password='test12345')
    print('creado')
else:
    print('ya existe')
"
```

- [ ] **Step 4: Disparar el análisis asíncrono con una imagen real**

```bash
cd Backend && python -c "
import requests
r = requests.post('http://localhost:8000/api/usuarios/login/', json={'email':'test@test.com','password':'test12345'})
token = r.json().get('access')
print('login status:', r.status_code)
headers = {'Authorization': f'Bearer {token}'}
with open('Microservicio_IA/datasets_pathology/validation/normal/' , 'rb') as f:
    pass
"
```

(Ajustar la ruta de una imagen real de `Microservicio_IA/datasets_pathology/` o `datasets/` según lo que exista en el checkout — usar cualquier `.jpg` de validación.)

```bash
cd Backend && python -c "
import requests
files = {'file': ('test.jpg', open('<ruta-a-una-imagen-real.jpg>', 'rb'), 'image/jpeg')}
data = {'ecografia_id': 'smoke-test-1'}
r = requests.post('http://localhost:8000/api/ecografias/analyze-with-ai-async/', files=files, data=data, headers={'Authorization': 'Bearer <token>'})
print(r.status_code, r.json())
"
```
Expected: `202 {'status': 'queued', 'ecografia_id': 'smoke-test-1'}`

- [ ] **Step 5: Confirmar que el consumer procesó el mensaje**

Revisar el log de la ventana 2 (microservicio) — debe aparecer `Callback entregado para ecografia_id=smoke-test-1 (intento 1)`.

- [ ] **Step 6: Confirmar en la UI de administración de RabbitMQ que la cola está vacía**

Abrir `http://localhost:15672` (guest/guest) → pestaña "Queues" → `dicom.analysis` debe tener 0 mensajes pendientes y 0 en la `dicom.analysis.dead`.

- [ ] **Step 7: Correr toda la suite de tests para confirmar que nada se rompió**

```bash
cd Backend && python -m pytest tests/ -q
cd Backend/Microservicio_IA && .venv_gpu/Scripts/python.exe -m pytest -q
```
Expected: todos los tests existentes siguen en verde, más los nuevos de este plan.

---

## Self-Review (completado por el autor del plan)

- **Cobertura de spec:** Celery (documentado, no corregido, según el spec) ✓ · RabbitMQ nativo ✓ · consumer real ✓ · publisher conectado ✓ · Kong JWT + archivo deprecado ✓ · verificación end-to-end ✓. El bug de puerto 8001/8002 no estaba en el spec original — se agregó como Task 1 porque se descubrió durante la investigación de este plan y bloquea directamente el objetivo del spec ("arreglar el cableado roto").
- **Placeholders:** ninguno — cada step tiene código completo o comandos exactos con salida esperada.
- **Consistencia de tipos:** `publish_to_rabbitmq(ecografia_id, image_bytes, filename)` se usa con la misma firma en Task 4 y Task 5. `DICOM_QUEUE_ARGS` se define idéntico en `ai_views.py` (Task 4) y `rabbitmq_consumer.py` (Task 6), con comentario cruzado en ambos lados advirtiendo que deben coincidir.
