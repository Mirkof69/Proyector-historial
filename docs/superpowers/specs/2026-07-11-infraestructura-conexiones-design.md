# Infraestructura y Conexiones — Fetal Medical Bolivia

**Fecha:** 2026-07-11
**Sub-proyecto de:** plan general de mejora del sistema (ver diagnóstico completo del 2026-07-11)
**Estado:** aprobado, pendiente de plan de implementación

## Contexto

Un diagnóstico completo del sistema (infraestructura, conexiones entre servicios, UX del
frontend, e integridad de cálculos clínicos) identificó 10 hallazgos críticos, 12
importantes y 7 menores. Dado el volumen, el trabajo se dividió en sub-proyectos
independientes. Este spec cubre el primero: **infraestructura y conexiones entre
servicios**.

Durante el diagnóstico se encontró y corrigió en vivo un bloqueador previo: PostgreSQL
no estaba instalado en la máquina de desarrollo (solo el cliente pgAdmin4 lo estaba).
Se instaló PostgreSQL 18 vía winget, se creó la base `historial` y se corrieron las
migraciones. Ese punto ya está resuelto y no es parte de este plan.

## Alcance

**Incluye:**
- Arreglar el cableado roto entre Django, el microservicio de IA, RabbitMQ y Celery.
- Todo el stack corre nativo en Windows (sin Docker) para desarrollo local.
- Kong se corrige en su configuración pero **no se corre en desarrollo local** (no tiene
  instalación nativa para Windows — solo Docker, confirmado contra la documentación
  oficial de Kong). Su configuración corregida queda lista para cuando el sistema se
  despliegue vía Docker Compose / producción.

**No incluye** (sub-proyectos separados, ya decididos con el usuario):
- Mejorar la precisión del modelo de IA (clases débiles: polihidramnios, cardiopatía
  congénita, biometría sintética, clase `no_ecografia` sin entrenar).
- UX / diseño del frontend (404 roto, ayuda duplicada, toasts de debug, colores
  hardcodeados, accesibilidad).
- Cobertura de tests (13 módulos backend sin ningún test).
- Integridad de cálculos clínicos (MoM con factores placeholder, OCR falso, firma
  digital falsa, README del microservicio desactualizado).

## Componentes a tocar

### 1. Celery
Completar `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` explícitamente en `Backend/.env`
apuntando a Redis local (`redis://127.0.0.1:6379/0`), en vez de depender del default de
`settings.py`. Documentar (sin corregir en este spec, ya que no se corre en Docker
localmente) el gap equivalente en `docker-compose.yml`, donde esas variables faltan en
el servicio `backend` — para que no quede roto cuando se use en producción.

### 2. RabbitMQ nativo en Windows
Instalar RabbitMQ + Erlang/OTP como servicio de Windows (RabbitMQ tiene instalador
oficial para Windows, confirmado contra la documentación oficial).

### 3. Consumer real en el microservicio de IA
Nuevo módulo en `Backend/Microservicio_IA/app/` (el `main.py` original que tenía esta
lógica fue borrado en una limpieza previa y nunca se recreó) que:
- Consuma la cola `dicom.analysis` usando `pika` (ya está en `requirements.txt`).
- Procese la imagen con el modelo ya entrenado (EfficientNet-B4 + Transformer).
- Llame de vuelta al callback `POST /api/ecografias/{id}/ai-result/` que ya existe en
  Django (`ecografias/urls.py`).
- Tenga una dead-letter queue para mensajes que fallan repetidamente, evitando reintentos
  infinitos sobre una imagen corrupta.

### 4. Conectar el publisher real
Hoy `publish_to_rabbitmq()` en `Backend/ecografias/ai_views.py` existe pero ninguna vista
la invoca — es código muerto. Se conecta a la vista real que sube/analiza una ecografía,
para que el mensaje efectivamente se publique cuando corresponde.

### 5. Kong (configuración únicamente, no se corre localmente)
- Unificar `KONG_JWT_SECRET` con el `SECRET_KEY` real de Django (hoy son literales
  distintos en `.env.docker` / `.env.production`).
- Corregir el claim `iss`: Kong exige `key_claim_name: iss` pero SimpleJWT tiene
  `ISSUER: None` (nunca lo emite) — hay que alinear ambos lados.
- Eliminar `Backend/kong.yml` (raíz), marcado como deprecado en el propio archivo y con
  nombres de servicio que no existen en el `docker-compose.yml` actual. El archivo
  vigente es `kong/kong.yml`.

## Flujo de datos resultante

```
Frontend → Django (sube ecografía) → publish_to_rabbitmq()
  → cola dicom.analysis → consumer nuevo (Microservicio_IA)
  → procesa con el modelo ya entrenado → POST callback a Django
  → estado del análisis actualizado en BD
  (notificación WebSocket al frontend queda pendiente del sub-proyecto de UX,
   que es donde se conectará el cliente WS)
```

Este flujo convive con el flujo síncrono que ya funciona hoy para DICOM
(`ia_medica/dicom_consumer.py` vía Celery, disparado por el webhook de Orthanc) —
son dos entradas distintas al mismo servicio de IA; no se reemplazan entre sí.

## Manejo de errores

- Si RabbitMQ no está disponible, `publish_to_rabbitmq()` ya tiene un modo degradado
  documentado (de una sesión de implementación previa) — se mantiene tal cual.
- El consumer nuevo necesita su propia dead-letter queue (ver componente 3).
- Si el callback HTTP a Django falla (Django caído, timeout), el consumer debe reintentar
  con backoff antes de enviar a dead-letter, no descartar el mensaje silenciosamente.

## Verificación

- Script de humo manual: subir una ecografía de prueba vía el frontend o la API,
  confirmar que el mensaje aparece en la cola `dicom.analysis`, que el consumer nuevo lo
  toma, que el callback llega a Django, y que el estado del análisis cambia en la base
  de datos.
- No existe hoy ningún test automatizado de este flujo. El plan de implementación debe
  incluir al menos un test de integración para el consumer nuevo (mockeando RabbitMQ o
  usando una cola de test).
- Verificar con `manage.py check` y una corrida real de Django que las variables de
  Celery quedan tomadas correctamente (no el fallback a `localhost` cuando no
  corresponde).

## Decisiones registradas (para no repreguntar)

- Stack de desarrollo local: **100% nativo en Windows**, no Docker Compose.
- RabbitMQ: se **recrea el consumer real** (no se borra el código muerto del publisher).
- Kong: se **corrige su configuración pero no se corre en local** — Kong no tiene
  instalación nativa para Windows (solo Docker), confirmado contra la documentación
  oficial de Kong (`developer.konghq.com/gateway/install/`).
- Mejorar el modelo de IA queda **fuera de este sub-proyecto**, es su propio sub-proyecto
  futuro.
