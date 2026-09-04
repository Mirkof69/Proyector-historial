# Fetal Medical Bolivia — Plan de Implementación Completo

> **Para quien ejecute esto:** usar `superpowers:subagent-driven-development` (recomendado) o `superpowers:executing-plans` para implementar tarea por tarea. Los pasos usan casillas (`- [ ]`) para seguimiento.

**Objetivo:** Dejar el sistema listo para un hospital y una clínica gineco-obstétrica reales: que registrar una historia, subir una ecografía y analizarla sea rápido incluso en 3G, que el diseño sea uniforme y no se rompa, y que cada acción quede auditada.

**Arquitectura:** Django multi-tenant (django-tenants) + DRF sobre PostgreSQL 18, microservicio FastAPI de IA con EfficientNet-B4 en GPU, frontend React 18 + Ant Design 5. Los arreglos siguen tres ejes: quitar trabajo innecesario del camino crítico (consultas, payloads), cerrar huecos de trazabilidad, y consolidar el CSS en un único sistema de tokens.

**Stack:** Django 5 · DRF · django-tenants · PostgreSQL 18.4 · FastAPI · PyTorch 2.6 (CUDA 12.4) · React 18 · Ant Design 5 · Tailwind · pytest · Locust

---

## Restricciones globales

Todas las tareas heredan esto. No se negocia por tarea.

- **Cada tarea entrega tests que declaran resultado ESPERADO y lo comparan con el OBTENIDO.** El mensaje del assert dice qué se esperaba y qué salió. Sin esto la tarea no está terminada.
- **TDD estricto:** primero el test que falla, se corre y se verifica que falla, después la implementación mínima, se corre y se verifica que pasa, luego commit.
- **Nunca se corrige la validación para que pase un test.** Si el dato de prueba no valida, se corrige el generador de datos. `create()` no valida; `full_clean()` sí.
- **La suite completa debe quedar en verde al terminar cada tarea:** `cd Backend && python -m pytest -q` → mínimo 435 pasan, 6 skipped.
- **Ruff limpio:** `python -m ruff check Backend/`.
- **Comentarios y docstrings en español**, explicando *por qué* existe el código, no qué hace.
- **Nada de datos de marcador de posición** en documentos clínicos (nombres de clínica, teléfonos, direcciones inventadas).
- **Presupuesto 3G:** ninguna respuesta del camino clínico crítico puede superar **50 KB** salvo que el usuario pida explícitamente la imagen.

---

## Estado de partida (ya hecho y verificado)

No repetir. Referencia para entender el contexto.

| # | Arreglo | Evidencia |
|---|---|---|
| 1 | N+1 del listado de pacientes | 1.601 → 4 consultas; 42.000 → 670 ms con 100 usuarios |
| 2 | `CONN_MAX_AGE=60` + `CONN_HEALTH_CHECKS` | menos agotamiento de conexiones |
| 3 | `core/paginacion.py` — `?page_size=` funciona | verificado en vivo: `page_size=5` → 5 filas |
| 4 | `pytest` arranca solo (scripts renombrados) | 435 tests recolectados sin excluir nada |
| 5 | CI corre aislamiento de tenants | paso bloqueante con `TEST_CON_TENANTS=true` |
| 6 | Límite de login por IP | `core/throttling.py`, 4 tests |
| 7 | Laboratorios duplicados en historia clínica | `construir_historia_clinica()`, 6 tests |
| 8 | Registro de accesos (acción `VER`) | `auditoria/acceso.py`, 12 tests |
| 9 | 500 por `None` en validación de controles | ahora devuelve 400 con el campo que falta |

---

## Nota de alcance

Este documento cubre **seis subsistemas**. Las fases 1 a 4 son un plan ejecutable de corrido. Las fases 5 y 6 son proyectos con entidad propia y **deberían tener su propio spec antes de ejecutarse** — están listadas para que el inventario esté completo, no para implementarse a ciegas desde aquí.

---

## Mapa de archivos

| Archivo | Responsabilidad | Fase |
|---|---|---|
| `Backend/.env` | URL real del microservicio de IA | 1 |
| `Backend/ecografias/ai_views.py` | Leer configuración desde settings; health correcto | 1 |
| `Backend/ecografias/gradcam.py` *(nuevo)* | Guardar el Grad-CAM como archivo y devolver URL | 1 |
| `Backend/tests/test_flujo_ecografia.py` *(nuevo)* | Tests del flujo subir+analizar y del presupuesto 3G | 1 |
| `Backend/settings.py` | Pool de conexiones, logging con timestamp | 2, 3 |
| `docker-compose.yml` | PgBouncer delante de PostgreSQL | 2 |
| `Backend/auditoria/acciones.py` *(nuevo)* | Vocabulario único de acciones + normalización | 3 |
| `Backend/auditoria/signals.py` | Emitir los nombres canónicos | 3 |
| `Backend/usuarios/views.py` | Registrar `LOGOUT` y `CAMBIO_ROL` | 3 |
| `Backend/conftest.py` | Dejar de excluir `AuditoriaMiddleware` | 3 |
| `Backend/frontend/src/styles/tokens.css` *(nuevo)* | Único origen de verdad de los tokens | 4 |
| `Backend/frontend/src/styles/*.css` | Consolidación y borrado de muertos | 4 |

---

# FASE 1 — El flujo de la ecografía

La razón de que sea la primera: es el camino que el usuario nombró dos veces, hoy **está caído desde Django**, y su respuesta pesa 252 KB en una red donde el presupuesto es 50.

## Tarea 1: El microservicio de IA es inalcanzable desde Django

**Contexto medido:** `POST /api/ecografias/analyze-with-ai/` devuelve **HTTP 503 "No se pudo conectar al microservicio de IA"**. Tres causas encadenadas:

1. `Backend/.env:53` dice `AI_SERVICE_URL=http://localhost:8002`. En 8002 **no escucha nada**; el microservicio está en 8001.
2. `ecografias/ai_views.py:28` lee `os.environ.get("AI_SERVICE_URL")` **directamente**, saltándose `settings`. `ia_medica/services/cnn_service.py` sí usa `settings`. Dos mecanismos distintos para la misma configuración.
3. `ai_views.py:366` consulta `{AI_SERVICE_URL}/api/health`, que devuelve **404**. La ruta real es `/health` (verificado: `/health` → 200, `/api/health` → 404).

**Files:**
- Modify: `Backend/.env:53`
- Modify: `Backend/ecografias/ai_views.py:28`, `Backend/ecografias/ai_views.py:366`
- Test: `Backend/tests/test_flujo_ecografia.py` *(crear)*

**Interfaces:**
- Consumes: `settings.AI_SERVICE_URL` (ya declarado en `settings.py:50` con default `http://localhost:8001`)
- Produces: `ecografias.ai_views.obtener_url_ia() -> str`

- [ ] **Paso 1: Escribir el test que falla**

```python
# Backend/tests/test_flujo_ecografia.py
"""Tests del flujo clínico: subir una ecografía y analizarla con IA.

Es el camino más usado en consulta y el que más pesa en una red móvil.
Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

from django.test import TestCase, override_settings

from ecografias.ai_views import obtener_url_ia


class ConfiguracionDelMicroservicioTest(TestCase):
    """La URL del microservicio debe salir de settings, no de os.environ.

    Leer `os.environ` directamente hacía que `.env` pudiera apuntar a un
    puerto donde no escucha nada (8002) sin que ningún test lo notara: el
    análisis de ecografías devolvía 503 y el sistema parecía sano.
    """

    @override_settings(AI_SERVICE_URL="http://ia-de-prueba:9999")
    def test_la_url_sale_de_settings(self):
        """ESPERADO: 'http://ia-de-prueba:9999' — el valor de settings."""
        assert obtener_url_ia() == "http://ia-de-prueba:9999"

    @override_settings(AI_SERVICE_URL="http://ia:8001/")
    def test_se_quita_la_barra_final(self):
        """ESPERADO: sin barra final, para no construir '//api/analyze'."""
        assert obtener_url_ia() == "http://ia:8001"
```

- [ ] **Paso 2: Correr el test y verificar que falla**

Run: `cd Backend && python -m pytest tests/test_flujo_ecografia.py -v --no-cov`
Expected: FAIL con `ImportError: cannot import name 'obtener_url_ia'`

- [ ] **Paso 3: Implementar**

```python
# Backend/ecografias/ai_views.py — reemplazar la línea 28
def obtener_url_ia() -> str:
    """URL base del microservicio de IA, desde settings.

    Se lee de `settings` y no de `os.environ` para tener UN solo origen de
    verdad: `ia_medica/services/cnn_service.py` ya usaba settings, y tener
    dos mecanismos hizo que `.env` apuntara a un puerto muerto (8002) sin
    que nada lo detectara. La barra final se quita para que las rutas
    queden `http://host:8001/api/analyze` y no `...8001//api/analyze`.
    """
    from django.conf import settings

    return str(getattr(settings, "AI_SERVICE_URL", "http://localhost:8001")).rstrip("/")
```

Sustituir cada uso de la constante `AI_SERVICE_URL` en el módulo por `obtener_url_ia()`.

- [ ] **Paso 4: Corregir la ruta del health**

```python
# Backend/ecografias/ai_views.py:366
# El microservicio expone /health en la raíz, NO /api/health: verificado
# contra el servicio corriendo (/health -> 200, /api/health -> 404).
health_response = requests.get(f"{obtener_url_ia()}/health", timeout=5)
```

- [ ] **Paso 5: Corregir `.env`**

```bash
# Backend/.env línea 53
AI_SERVICE_URL=http://localhost:8001
```

- [ ] **Paso 6: Correr los tests y verificar que pasan**

Run: `cd Backend && python -m pytest tests/test_flujo_ecografia.py -v --no-cov`
Expected: PASS (2 tests)

- [ ] **Paso 7: Verificar en vivo contra los servicios reales**

```bash
# Ventana 1
cd Backend/Microservicio_IA && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# Ventana 2
cd Backend && python -m uvicorn asgi:application --host 127.0.0.1 --port 8000
# Ventana 3
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/ecografias/ai/health/
```

Expected: `200` (antes: 503)

- [ ] **Paso 8: Commit**

```bash
git add Backend/.env Backend/ecografias/ai_views.py Backend/tests/test_flujo_ecografia.py
git commit -m "fix(ia): el analisis de ecografias daba 503 por puerto y ruta de health erroneos"
```

---

## Tarea 2: El Grad-CAM es el 98% de la respuesta

**Contexto medido:** la respuesta de `analyze-with-ai` pesa **252 KB**, de los cuales **249 KB (98%) son `gradcam_base64`**. Los datos clínicos —patologías, biometría, recomendaciones— suman **menos de 2 KB**. En 3G lento (400 kbps) eso son **5 segundos** por ecografía, y base64 infla el binario un 33% sobre el PNG original.

**Decisión:** el Grad-CAM se guarda como archivo y se devuelve su URL. El navegador la pide aparte: se cachea, se comprime como imagen y no bloquea el resultado clínico. La respuesta baja de 252 KB a menos de 3 KB.

**Files:**
- Create: `Backend/ecografias/gradcam.py`
- Modify: `Backend/ecografias/ai_views.py` (la construcción de la respuesta)
- Test: `Backend/tests/test_flujo_ecografia.py`

**Interfaces:**
- Consumes: `obtener_url_ia()` de la Tarea 1
- Produces: `ecografias.gradcam.guardar_gradcam(base64_str, prefijo) -> str` (devuelve la URL relativa del archivo guardado)

- [ ] **Paso 1: Escribir el test que falla**

```python
# añadir a Backend/tests/test_flujo_ecografia.py
import base64

from django.core.files.storage import default_storage

from ecografias.gradcam import guardar_gradcam

# PNG de 1x1 píxel, el más pequeño que existe: sirve para probar el guardado
# sin depender de una imagen real ni de la GPU.
PNG_MINIMO = base64.b64encode(
    base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    ),
).decode()


class GuardarGradcamTest(TestCase):
    """El mapa de calor se guarda como archivo, no viaja en el JSON."""

    def test_devuelve_una_url_no_el_base64(self):
        """ESPERADO: una ruta corta, no 249 KB de base64 incrustado."""
        url = guardar_gradcam(PNG_MINIMO, prefijo="eco-test")

        assert url.startswith("/media/"), f"Esperada una URL /media/..., obtenida {url!r}"
        assert len(url) < 200, f"La URL mide {len(url)} caracteres; debería ser corta."
        assert "base64" not in url

    def test_el_archivo_queda_guardado_y_es_legible(self):
        """ESPERADO: el archivo existe y contiene los bytes del PNG."""
        url = guardar_gradcam(PNG_MINIMO, prefijo="eco-test")
        ruta = url.replace("/media/", "")

        assert default_storage.exists(ruta), "El Grad-CAM no se guardó."
        with default_storage.open(ruta, "rb") as f:
            assert f.read(8) == b"\x89PNG\r\n\x1a\n", "El archivo no es un PNG válido."

    def test_base64_invalido_devuelve_cadena_vacia(self):
        """ESPERADO: '' — un Grad-CAM roto no puede tumbar el análisis clínico.

        El resultado de patologías es lo importante; el mapa de calor es
        ayuda visual. Si falla, se pierde la imagen, no el diagnóstico.
        """
        assert guardar_gradcam("esto-no-es-base64", prefijo="x") == ""
```

- [ ] **Paso 2: Correr y verificar que falla**

Run: `cd Backend && python -m pytest tests/test_flujo_ecografia.py::GuardarGradcamTest -v --no-cov`
Expected: FAIL con `ModuleNotFoundError: No module named 'ecografias.gradcam'`

- [ ] **Paso 3: Implementar**

```python
# Backend/ecografias/gradcam.py
"""Persistencia del mapa de calor (Grad-CAM) del análisis de ecografías.

Por qué existe este módulo
--------------------------
El microservicio devuelve el Grad-CAM como `gradcam_base64`, y la API lo
reenviaba incrustado en el JSON. Medido sobre una ecografía real: la
respuesta pesaba 252 KB, de los cuales 249 KB (98%) eran ese base64; todos
los datos clínicos juntos —patologías, biometría, recomendaciones— suman
menos de 2 KB.

En la red de una clínica con 3G eso son ~5 segundos por ecografía, y base64
además infla el binario un 33% frente al PNG. Guardando la imagen y
devolviendo su URL, el navegador la pide aparte: se cachea, se sirve
comprimida y no retrasa el resultado que el médico necesita leer.
"""
from __future__ import annotations

import base64
import binascii
import logging
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

CARPETA = "gradcams"


def guardar_gradcam(datos_base64: str, prefijo: str = "eco") -> str:
    """Guarda el Grad-CAM y devuelve su URL relativa.

    Devuelve cadena vacía si el base64 no es válido: el mapa de calor es
    ayuda visual, y perderlo nunca puede impedir que se entregue el
    resultado clínico del análisis.
    """
    if not datos_base64:
        return ""
    try:
        crudo = base64.b64decode(datos_base64, validate=True)
    except (binascii.Error, ValueError) as e:
        logger.warning("Grad-CAM con base64 inválido (%s); se omite la imagen.", e)
        return ""

    nombre = f"{CARPETA}/{prefijo}-{uuid.uuid4().hex}.png"
    default_storage.save(nombre, ContentFile(crudo))
    return f"/media/{nombre}"
```

- [ ] **Paso 4: Correr y verificar que pasa**

Run: `cd Backend && python -m pytest tests/test_flujo_ecografia.py::GuardarGradcamTest -v --no-cov`
Expected: PASS (3 tests)

- [ ] **Paso 5: Conectarlo a la vista**

En `ecografias/ai_views.py`, donde se arma la respuesta con `ai_analysis`, reemplazar el reenvío del base64:

```python
# El Grad-CAM sale del JSON y se sirve como archivo: era el 98% del peso
# de la respuesta (249 KB de 252 KB) y hacía inusable el análisis en 3G.
gradcam = resultado.pop("gradcam_base64", "")
if gradcam:
    from .gradcam import guardar_gradcam

    resultado["gradcam_url"] = guardar_gradcam(gradcam, prefijo="eco")
```

- [ ] **Paso 6: Test del presupuesto de 3G**

```python
# añadir a Backend/tests/test_flujo_ecografia.py
class PresupuestoDeRedTest(TestCase):
    """El JSON del análisis debe caber en una red móvil lenta."""

    def test_la_respuesta_no_lleva_base64_incrustado(self):
        """ESPERADO: 'gradcam_url' presente y 'gradcam_base64' ausente.

        Con el base64 dentro, la respuesta medía 252 KB: unos 5 segundos en
        3G lento (400 kbps) para leer un resultado que ocupa 2 KB.
        """
        from ecografias.ai_views import _preparar_respuesta_ia

        crudo = {"gradcam_base64": PNG_MINIMO, "pathology_detection": {"normal": 0.9}}
        salida = _preparar_respuesta_ia(crudo)

        assert "gradcam_base64" not in salida
        assert salida["gradcam_url"].startswith("/media/")
        assert salida["pathology_detection"] == {"normal": 0.9}
```

Extraer la transformación del Paso 5 a `_preparar_respuesta_ia(resultado: dict) -> dict` para que sea testeable sin HTTP ni GPU.

- [ ] **Paso 7: Correr toda la suite**

Run: `cd Backend && python -m pytest -q --no-cov`
Expected: 440+ pasan, 6 skipped, 0 fallos

- [ ] **Paso 8: Medir el resultado real**

```bash
IMG=Backend/Microservicio_IA/datasets_pathology/train/anencefalia/brain_Copy-of-encephalocele-20a_aug_0_png_jpg.rf.66f6200cdcb485e8d85b0f1453a7b0bf.jpg
curl -s -o /dev/null -w "peso=%{size_download} bytes  tiempo=%{time_total}s\n" \
  -X POST http://127.0.0.1:8000/api/ecografias/analyze-with-ai/ -F "file=@$IMG"
```

Expected: `peso` por debajo de **3.000 bytes** (antes: 258.018). Anotar el número obtenido.

- [ ] **Paso 9: Commit**

```bash
git add Backend/ecografias/gradcam.py Backend/ecografias/ai_views.py Backend/tests/test_flujo_ecografia.py
git commit -m "perf(ia): el gradcam sale del JSON y se sirve como archivo (252 KB -> <3 KB)"
```

---

## Tarea 3: Las imágenes de ecografía se sirven sin límite de tamaño

**Contexto:** una ecografía DICOM convertida puede pesar varios MB. En 3G, abrir una historia clínica con 3 ecografías es inviable si se sirven a resolución completa.

**Files:**
- Create: `Backend/ecografias/miniaturas.py`
- Modify: `Backend/ecografias/models.py` (guardar la miniatura al subir)
- Test: `Backend/tests/test_flujo_ecografia.py`

**Interfaces:**
- Produces: `ecografias.miniaturas.generar_miniatura(archivo, ancho_max=480) -> ContentFile`

- [ ] **Paso 1: Test que falla**

```python
class MiniaturasTest(TestCase):
    """Los listados sirven miniaturas, no la imagen de diagnóstico completa."""

    def test_la_miniatura_respeta_el_ancho_maximo(self):
        """ESPERADO: ancho 480 px, manteniendo la proporción."""
        from io import BytesIO

        from PIL import Image

        from ecografias.miniaturas import generar_miniatura

        original = Image.new("RGB", (1920, 1080), "gray")
        buf = BytesIO()
        original.save(buf, format="PNG")
        buf.seek(0)

        chica = Image.open(generar_miniatura(buf, ancho_max=480))
        assert chica.width == 480, f"Esperado ancho 480, obtenido {chica.width}"
        assert chica.height == 270, f"Esperado alto 270, obtenido {chica.height}"

    def test_una_imagen_ya_pequena_no_se_agranda(self):
        """ESPERADO: se deja como está; ampliar solo añade peso sin detalle."""
        from io import BytesIO

        from PIL import Image

        from ecografias.miniaturas import generar_miniatura

        buf = BytesIO()
        Image.new("RGB", (200, 100), "gray").save(buf, format="PNG")
        buf.seek(0)

        chica = Image.open(generar_miniatura(buf, ancho_max=480))
        assert chica.width == 200
```

- [ ] **Paso 2: Verificar que falla** — Run: `python -m pytest tests/test_flujo_ecografia.py::MiniaturasTest -v --no-cov` → FAIL, módulo inexistente.
- [ ] **Paso 3: Implementar** `generar_miniatura` con Pillow (`Image.thumbnail`, formato WebP calidad 80).
- [ ] **Paso 4: Verificar que pasa** — Expected: PASS (2 tests).
- [ ] **Paso 5: Commit** — `perf(ecografias): miniaturas webp para listados en redes lentas`

---

# FASE 2 — Capacidad para un hospital

## Tarea 4: PostgreSQL se queda sin conexiones

**Contexto medido:** con 100 usuarios quedan **94 errores HTTP 500**, todos con `FATAL: lo siento, ya tenemos demasiados clientes`. La cuenta exacta: 4 workers de uvicorn × 20 hilos del pool de asgiref (en una máquina de 16 núcleos) = **80 conexiones persistentes potenciales**, más Celery y overhead, contra `max_connections = 100`, que es el valor por defecto de PostgreSQL.

Bajar el pool con `ASGI_THREADS=15` reduce los errores pero no los elimina. **El arreglo es de servidor, no de código.**

**Files:**
- Modify: `docker-compose.yml` (servicio `pgbouncer`)
- Create: `Backend/scripts/pgbouncer.ini`
- Modify: `Backend/.env` (apuntar `DB_PORT` a PgBouncer)

- [ ] **Paso 1: Añadir PgBouncer al compose**

```yaml
  pgbouncer:
    image: edoburu/pgbouncer:latest
    environment:
      DB_HOST: db
      DB_PORT: "5432"
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      # transaction: la conexión vuelve al pool al terminar cada transacción.
      # Es el modo correcto para Django, que abre y cierra por petición.
      POOL_MODE: transaction
      MAX_CLIENT_CONN: "500"
      DEFAULT_POOL_SIZE: "25"
    depends_on: [db]
    networks: [fetal-internal]
```

- [ ] **Paso 2: Apuntar Django a PgBouncer** — en `.env`: `DB_HOST=pgbouncer`, `DB_PORT=6432`.

- [ ] **Paso 3: Ajustar `CONN_MAX_AGE`**

```python
# Backend/settings.py — con PgBouncer en modo transaction, mantener
# conexiones vivas del lado de Django es contraproducente: el pooler ya
# hace ese trabajo y las conexiones persistentes de Django solo ocupan
# slots del pool sin usarlos.
"CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=0 if env.bool("USA_PGBOUNCER", default=False) else 60),
```

- [ ] **Paso 4: Prueba de carga de verificación**

```bash
python -m locust -f locustfile.py --headless -u 100 -r 10 -t 3m --host http://127.0.0.1:8000
```

ESPERADO: **0 errores HTTP 500**. OBTENIDO antes del cambio: 94. Anotar el número.

- [ ] **Paso 5: Commit** — `fix(infra): pgbouncer elimina el agotamiento de conexiones con 100 usuarios`

## Tarea 5: Alternativa sin Docker

Si el despliegue no usa Docker, subir `max_connections` a 200 en `postgresql.conf` y reiniciar el servicio. Verificar con `SHOW max_connections;` → ESPERADO `200`. Documentarlo en `README.md`.

---

# FASE 3 — Trazabilidad completa

## Tarea 6: Seis acciones declaradas que nunca se registran

**Contexto medido** sobre 18.834 registros de auditoría reales:

| Acción | Registros | Estado |
|---|---|---|
| `CREAR` + `crear` | 17.267 | **dos nombres para lo mismo** |
| `actualizar` | 884 | el canónico `EDITAR` tiene 0 |
| `LOGIN` | 514 | ok |
| `LOGOUT` | **0** | declarado, nunca emitido |
| `EXPORTAR` | **0** | declarado, nunca emitido |
| `ANALISIS_CNN` | **0** | declarado, nunca emitido |
| `CONSULTA_IA` | **0** | declarado, nunca emitido |
| `DESACTIVAR` | **0** | se registra como `eliminar` |
| `CAMBIO_ROL` | **0** | declarado, nunca emitido |

La duplicación es el problema serio: filtrar la auditoría por `EDITAR` **no devuelve las 884 ediciones** registradas como `actualizar`. Una auditoría que no se puede consultar de forma fiable no cumple su función legal.

**Files:**
- Create: `Backend/auditoria/acciones.py`
- Modify: `Backend/auditoria/signals.py`, `Backend/auditoria/models.py`
- Modify: `Backend/usuarios/views.py` (LOGOUT, CAMBIO_ROL)
- Create: `Backend/auditoria/migrations/00XX_normalizar_acciones.py`
- Test: `Backend/tests/test_auditoria_acciones.py`

**Interfaces:**
- Produces: `auditoria.acciones.canonica(valor: str) -> str`

- [ ] **Paso 1: Test que falla**

```python
# Backend/tests/test_auditoria_acciones.py
"""Un solo vocabulario de acciones en la auditoría.

Existían dos nombres para la misma cosa —`CREAR` y `crear`, `EDITAR` y
`actualizar`— así que filtrar por el canónico perdía registros: había 884
ediciones guardadas como `actualizar` que no aparecían al buscar `EDITAR`.
"""

from django.test import TestCase

from auditoria.acciones import canonica


class AccionCanonicaTest(TestCase):
    def test_las_minusculas_legadas_se_normalizan(self):
        """ESPERADO: el nombre canónico en mayúsculas."""
        assert canonica("crear") == "CREAR"
        assert canonica("actualizar") == "EDITAR"
        assert canonica("eliminar") == "DESACTIVAR"

    def test_las_canonicas_se_dejan_igual(self):
        """ESPERADO: idempotente — normalizar dos veces da lo mismo."""
        assert canonica("CREAR") == "CREAR"
        assert canonica(canonica("crear")) == "CREAR"

    def test_una_accion_desconocida_se_conserva(self):
        """ESPERADO: se devuelve tal cual; perder el dato es peor que un nombre raro."""
        assert canonica("ALGO_NUEVO") == "ALGO_NUEVO"
```

- [ ] **Paso 2: Verificar que falla** — Expected: `ModuleNotFoundError: No module named 'auditoria.acciones'`
- [ ] **Paso 3: Implementar** `canonica()` con el mapa `{"crear": "CREAR", "actualizar": "EDITAR", "eliminar": "DESACTIVAR"}`.
- [ ] **Paso 4: Verificar que pasa** — Expected: PASS (3 tests)
- [ ] **Paso 5: Aplicar `canonica()` en `RegistroAuditoria.registrar()`** para que nada vuelva a entrar con nombre legado.
- [ ] **Paso 6: Migración de datos** que normaliza las 6.153 filas existentes con nombres legados. Debe ser reversible.
- [ ] **Paso 7: Registrar las acciones que faltan** — `LOGOUT` en `logout_view`, `CAMBIO_ROL` al cambiar rol, `EXPORTAR` en cada `exportar-*`, `ANALISIS_CNN` en `analyze-with-ai`, `CONSULTA_IA` en el chatbot. Un test por cada una que verifique que queda la fila.
- [ ] **Paso 8: Correr la suite** — Expected: todo verde.
- [ ] **Paso 9: Commit** — `fix(auditoria): un solo vocabulario de acciones y las 6 que nunca se emitian`

## Tarea 7: Los logs no tienen fecha

**Contexto:** todos los registros de `logs/errors.log` salen con `"timestamp": null`. Durante esta auditoría eso hizo perseguir un bug de exportación de ecografías **que ya estaba arreglado**: la entrada del log era vieja y no había forma de saberlo.

**Files:** `Backend/settings.py` (configuración de `pythonjsonlogger`)

- [ ] **Paso 1: Test que falla** — un test que emite un log y verifica que el JSON resultante tiene `timestamp` no nulo y parseable como ISO 8601.
- [ ] **Paso 2: Verificar que falla.**
- [ ] **Paso 3: Implementar** — el formateador necesita `%(asctime)s` en su formato para poblar el campo; sin él `pythonjsonlogger` deja `timestamp` vacío.
- [ ] **Paso 4: Verificar que pasa.**
- [ ] **Paso 5: Commit** — `fix(logs): los registros salian sin fecha, imposibles de situar en el tiempo`

## Tarea 8: La auditoría no se ejercita en ningún test

**Contexto:** `Backend/conftest.py:42` excluye `auditoria.middleware.AuditoriaMiddleware` de **toda** la suite. Es justamente el componente que, según el reporte de julio, ya se apagó en silencio una vez sin que ningún test lo detectara.

- [ ] **Paso 1:** Añadir un *fixture* `con_auditoria` que reponga el middleware, en vez de excluirlo siempre.
- [ ] **Paso 2:** Migrar `tests/test_auditoria_accesos.py` a usarlo (hoy instancia el middleware a mano como rodeo).
- [ ] **Paso 3:** Test que verifica que crear una paciente por la API deja fila de auditoría **con el middleware puesto**. ESPERADO: 1 fila `CREAR` con usuario no vacío.
- [ ] **Paso 4:** Commit — `test(auditoria): la suite por fin ejercita el middleware de auditoria`

---

# FASE 4 — Diseño uniforme

**Contexto medido:** `src/styles/` tiene **5.245 líneas en 7 archivos** y **389 `!important`**, de los cuales 194 están en `theme-dark-fixes.css` y 195 en `theme-enhancements.css`. Ese patrón —dos archivos llamados "fixes" y "enhancements" concentrando casi todos los `!important`— es una guerra de cascada: cada archivo pisa al anterior a la fuerza en vez de corregir el origen. Es la causa de que tocar una pantalla rompa otra.

**Dato verificado, y corrección de un diagnóstico anterior:** primero conté 34 variables con valores en conflicto, incluido un `--color-primary` naranja peleando con el azul. Al revisar los imports resultó que `variables-clinical-dark.css` (373 líneas, el archivo naranja) **no se importa en ningún lado**. Entre los 6 archivos que sí se cargan quedan **3 conflictos reales**, los tres de tiempos de transición.

**Regla para toda la fase:** una pantalla por commit, con captura antes y después. Nada de reescrituras masivas a ciegas — es la forma más rápida de romper lo que hoy funciona.

## Tarea 9: Borrar el CSS muerto

- [ ] **Paso 1:** Confirmar con `grep -rl "variables-clinical-dark" src/` → ESPERADO: 0 resultados.
- [ ] **Paso 2:** `git rm Backend/frontend/src/styles/variables-clinical-dark.css`
- [ ] **Paso 3:** `npm run build` → ESPERADO: compila; el tamaño del bundle no cambia (era código muerto).
- [ ] **Paso 4:** Commit — `chore(estilos): borra 373 lineas de un tema que no se importaba`

## Tarea 10: Un único origen de verdad para los tokens

- [ ] **Paso 1:** Crear `src/styles/tokens.css` con las 113 variables consolidadas, resolviendo los 3 conflictos de transición a favor de `global-theme.css` (que usa curvas `cubic-bezier`, más precisas que los `0.2s` planos de `variables-claude.css`).
- [ ] **Paso 2:** Test visual: script que compara los valores computados de las 113 variables antes y después. ESPERADO: 110 idénticas, 3 cambiadas a propósito.
- [ ] **Paso 3:** Que `variables-claude.css` y la sección de variables de `global-theme.css` importen de `tokens.css` en vez de redefinir.
- [ ] **Paso 4:** `npm test` → ESPERADO: 20 tests siguen pasando.
- [ ] **Paso 5:** Commit — `refactor(estilos): un solo archivo de tokens, 3 conflictos resueltos`

## Tarea 11: Eliminar los 389 `!important`, pantalla por pantalla

Diez subtareas, una por pantalla, en orden de tamaño:

- [ ] Historia Clínica (`HistoriaClinica.tsx`, 1.298 líneas)
- [ ] Embarazos (988)
- [ ] Calculadoras (782)
- [ ] Calculadoras Avanzadas (766)
- [ ] Pacientes (728)
- [ ] Controles (702)
- [ ] Ecografías · Citas · Laboratorio · Vacunas

Para cada una: captura antes → quitar los `!important` de esa pantalla subiendo la especificidad correcta o corrigiendo el token → captura después → comparar → commit.

ESPERADO al terminar: `grep -c "!important" src/styles/*.css` por debajo de **20** (los legítimos, para pisar estilos inline de Ant Design).

## Tarea 12: Layout dinámico — que la pantalla se adapte

**Contexto medido:** 52 archivos de 534 usan puntos de corte responsive. En una clínica el sistema se abre en el monitor del consultorio, en la tablet de enfermería y en el teléfono de la médica de guardia; hoy no hay garantía de que las tres funcionen.

**Files:**
- Create: `Backend/frontend/src/styles/layout.css`
- Test: `Backend/frontend/src/pages/__tests__/layout.test.tsx`

- [ ] **Paso 1: Test que falla** — renderizar Pacientes a 360 px (teléfono), 768 px (tablet) y 1440 px (escritorio) con `matchMedia` simulado. ESPERADO: en 360 px la tabla no desborda horizontalmente el `body` (`document.body.scrollWidth <= 360`).
- [ ] **Paso 2: Verificar que falla** — anotar en qué anchos desborda.
- [ ] **Paso 3: Implementar** — contenedores de tabla con `overflow-x: auto` propio; rejillas con `grid-template-columns: repeat(auto-fit, minmax(...))` en vez de columnas fijas; unidades relativas.
- [ ] **Paso 4: Verificar que pasa** en los tres anchos.
- [ ] **Paso 5: Commit** — `fix(diseno): las pantallas ya no desbordan en tablet ni telefono`

## Tarea 13: Iconos y animaciones — coherentes y ligeros

**Contexto:** `@ant-design/icons` ya está como dependencia; **no hace falta traer iconos de GitHub**, y hacerlo añadiría peso y mezclaría dos estilos visuales. `framer-motion` (~50 KB) se usa para animación: hay que verificar si compensa en 3G o si las transiciones CSS bastan.

- [ ] **Paso 1:** Inventariar iconos: `grep -rhoE "<[A-Z][A-Za-z]+Outlined|Filled|TwoTone" src/ | sort | uniq -c`. ESPERADO: una lista; detectar dónde se usan dos iconos distintos para la misma acción.
- [ ] **Paso 2:** Unificar en un mapa `src/config/iconos.ts` — una acción, un icono, en todo el sistema.
- [ ] **Paso 3:** Medir `framer-motion`: build con y sin él. ESPERADO: saber cuántos KB cuesta.
- [ ] **Paso 4:** Si las animaciones son transiciones simples (entrada, hover, despliegue), sustituir por CSS con `prefers-reduced-motion` respetado, y quitar la dependencia.
- [ ] **Paso 5:** `npm run build` → ESPERADO: bundle menor. Anotar antes/después.
- [ ] **Paso 6:** Commit — `refactor(diseno): un icono por accion y animaciones en CSS`

## Tarea 14: Accesibilidad — 357 inputs sin etiqueta

**Contexto medido:** 357 elementos de entrada en `src/pages/`, **0 con `aria-label`**. Un lector de pantalla no puede decir qué campo es cuál.

- [ ] **Paso 1:** Regla de ESLint `jsx-a11y/label-has-associated-control` como error.
- [ ] **Paso 2:** `npx eslint src` → ESPERADO: ~357 errores nuevos. Anotar el número.
- [ ] **Paso 3:** Corregir por pantalla, en el mismo orden de pantallas de la Tarea 11.
- [ ] **Paso 4:** ESPERADO al final: 0 errores de esa regla.
- [ ] **Paso 5:** Commit por pantalla.

---

# FASE 5 — 3G (requiere su propio spec)

**Contexto medido:** la carga inicial son **404 KB gzip** (main.js 384 KB + CSS 21 KB) = **8,3 s en 3G lento**, 2,1 s en 3G típico. El code-splitting **ya funciona**: `xlsx`, `jspdf` y `recharts` viajan en chunks aparte. El peso es React + Ant Design + el armazón.

**Verificado, y corrección de otro diagnóstico:** creí que nginx no comprimía los `.js` porque `gzip_types` no incluye `application/javascript`. Desde nginx 1.21.1 los `.js` se sirven como `text/javascript`, que sí está en la lista, y la imagen es `nginx:alpine` (≥1.27). **La compresión funciona.** Añadir el tipo queda como endurecimiento barato por si alguna vez se fija una versión anterior.

Candidatos a evaluar en el spec: importación selectiva de componentes de Ant Design; sustituir `framer-motion` por transiciones CSS; service worker que cachee el armazón; precompresión Brotli en el build.

**Meta:** carga inicial por debajo de **200 KB gzip** (4,1 s en 3G lento).

---

# FASE 6 — Clínico y de integración (requieren su propio spec)

## Alertas clínicas sin destinatario — **es lo más urgente de esta fase**

`logs/errors.log` registra: `Evento clínico '⚠️ Factores de Riesgo Detectados' (alerta_advertencia) sin destinatario: la notificación NO llegará a nadie.` El sistema detecta la condición y la reporta —buen diseño— pero la condición existe: hay alertas de riesgo obstétrico que no llegan a ningún médico. Es lo único del inventario que afecta la seguridad de la paciente.

## Búsqueda difusa de pacientes

Diseño ya acordado: índice fonético irreversible adaptado al castellano-aymara (H↔G↔W, C↔K↔Q, B↔V, S↔C↔Z) + ranking por similitud, dentro de `ids_pacientes_que_coinciden()`. Los 15 viewsets lo heredan sin tocarlos. **Medido: 15 de 15 variantes de transcripción reales fallan hoy**, perdiendo entre 11 y 36 pacientes cada una. Nota técnica: `soundex` **no sirve** — `soundex('Huanca')='H520'` vs `soundex('Guanca')='G520'`.

## HL7 / FHIR

Cero referencias en todo el código. DICOM sí está resuelto (Orthanc, 8 módulos). Sin HL7 v2 o FHIR el sistema no intercambia pacientes, órdenes ni resultados con el HIS del hospital: funciona solo, no se integra.

## Optimización de agenda con la investigación de operaciones

Teoría de colas M/M/c, ruta crítica CPM y funciones objetivo multi-criterio ya están hechas, en notebooks dentro de `zip/material de investigacion/`. Nada de eso corre en el sistema. Conectarlo a la agenda de citas convierte un anexo académico en el motor de una pantalla.

---

## Orden de ejecución y por qué

1. **Fase 1** — el flujo de ecografía está caído (503) y su respuesta es 126× más pesada que su contenido útil.
2. **Fase 2** — sin esto el sistema no sostiene 100 usuarios sin errores 500.
3. **Fase 3** — trazabilidad; requisito legal, y la duplicación de nombres hace la auditoría poco fiable de consultar.
4. **Fase 4** — diseño; grande y mecánico, pero sin riesgo clínico.
5. **Fase 6 (alertas)** — subir de prioridad si se confirma que hay alertas de riesgo sin entregar en producción.
6. **Fases 5 y 6 restantes** — cada una con su propio spec antes de tocar código.
