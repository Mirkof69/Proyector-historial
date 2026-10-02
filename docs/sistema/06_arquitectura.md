# 06 · Arquitectura

## Vista general (microservicios)

Tres servicios independientes que se comunican por HTTP, más la base de datos.
El frontend nunca habla directamente con el microservicio de IA: todo pasa por
el backend, que aplica permisos, auditoría y traduce los errores.

```mermaid
flowchart LR
    U[👩‍⚕️ Navegador<br/>personal del hospital]

    subgraph FE[Frontend · React 18 + TypeScript + Ant Design]
        SPA[SPA compilada<br/>servir_produccion.py · :3000<br/>gzip + caché por hash]
    end

    subgraph BE[Backend · Django 6 + DRF · API en waitress :8000 · WebSockets en uvicorn :8010]
        API[API REST /api/*<br/>JWT en cookie httpOnly + CSRF]
        WS[WebSocket /ws/*<br/>Django Channels]
        MEDIA[/media/ protegida<br/>solo con sesión y rol/]
        TASKS[Tareas<br/>Celery o en línea]
    end

    subgraph IA[Microservicio de IA · FastAPI + PyTorch · :8001]
        REDES[Redes con ecografías reales<br/>plano · anomalías cerebrales]
        SEG[Segmentación U-Net<br/>cabeza · tórax · abdomen · intraparto]
        CHAT[Asistente obstétrico]
    end

    DB[(PostgreSQL 18<br/>un esquema por clínica)]
    R[(Redis<br/>canal API → WebSockets,<br/>caché, cola)]
    FS[(Archivos<br/>media/ · ml_modelos/<br/>trained_models/)]

    U -->|HTTPS| SPA
    SPA -->|fetch / axios| API
    SPA <-->|notificaciones en vivo| WS
    SPA -->|imágenes con cookie| MEDIA
    API -->|ORM| DB
    API -->|imagen + parámetros| REDES
    API -->|análisis completo| SEG
    API --> CHAT
    API --> FS
    API -->|publica notificaciones| R
    R -->|las entrega| WS
    TASKS -.-> R
    TASKS --> DB
    REDES --> FS
```

## Capas del backend

```mermaid
flowchart TB
    subgraph Presentación
        V[ViewSets DRF y vistas<br/>paginación · filtros · búsqueda cifrada · Excel]
    end
    subgraph Aplicación
        S[Serializers<br/>validación de entrada]
        SV[Servicios<br/>ia_medica/services · reportes/services · importaciones]
        SG[Señales y tareas<br/>notificaciones · auditoría · recordatorios]
    end
    subgraph Dominio
        M[Modelos con reglas clínicas<br/>clean / full_clean · cálculos · alertas]
        C[Cálculo clínico único<br/>peso_fetal · datación · rangos · ILA · preeclampsia]
    end
    subgraph Infraestructura
        DB[(PostgreSQL · django-tenants)]
        CR[Cifrado de campos<br/>EncryptedCharField + hash de búsqueda]
        AU[Auditoría inmutable<br/>trigger en la base]
    end
    V --> S --> M
    V --> SV --> M
    M --> C
    M --> SG
    M --> DB
    M --> CR
    SG --> AU
```

## Multi-clínica (tenants)

Cada clínica es un esquema de PostgreSQL. El dominio con el que se entra
(`localhost`, la IP del servidor o el dominio de la clínica) decide el
esquema. Las tablas de clínicas y dominios están en el esquema `public`.

```mermaid
flowchart LR
    REQ[Petición<br/>Host: clinica.ejemplo.bo] --> MW[Middleware de<br/>django-tenants]
    MW -->|busca el dominio| PUB[(esquema public<br/>clínicas y dominios)]
    MW -->|SET search_path| T1[(clinica_demo)]
    MW -.-> T2[(clinica_b)]
    MW -.-> T3[(clinica_c)]
```

## Módulos del backend (apps de Django)

| Área | Apps |
|---|---|
| Núcleo y seguridad | `core` (permisos, paginación, filtros, exportación, media protegida, validación de archivos), `usuarios`, `roles`, `auditoria`, `clientes` (clínicas) |
| Atención | `pacientes`, `antecedentes`, `citas`, `triaje`, `consultorios` |
| Embarazo | `embarazos`, `controles`, `ecografias`, `ecografias_archivos`, `laboratorio`, `vacunas`, `notas_evolucion`, `evoluciones` (solo lectura, histórico), `partos` |
| Apoyo clínico | `calculadoras`, `calculadoras_avanzadas`, `ia_medica` (puente con la IA y modelo supervisado) |
| Gestión | `reportes`, `notificaciones`, `soporte` |

## Frontend

| Carpeta | Contenido |
|---|---|
| `src/pages/` | Una carpeta por módulo (Pacientes, Embarazos, Controles, Ecografias, Partos, Laboratorio, Vacunas, Triaje, NotasEvolucion, Calculadoras, Reportes, IaMedica, HistoriaClinica…) |
| `src/services/` | Clientes de la API por módulo |
| `src/hooks/useListadoServidor.ts` | Listados paginados en el servidor (búsqueda, filtros, orden) |
| `src/utils/` | Cálculos clínicos compartidos con el backend (peso fetal, diabetes gestacional, ILA, preeclampsia) |
| `src/routes/` | Rutas con permisos y carga diferida por página |

## Tecnologías

| Capa | Tecnología |
|---|---|
| Frontend | React 18, TypeScript, Ant Design 5, Recharts, Day.js |
| Backend | Python 3.12, Django 6, Django REST Framework, django-tenants, Channels, SimpleJWT, drf-spectacular (OpenAPI) |
| IA | FastAPI, PyTorch (CUDA), timm (EfficientNet), scikit-learn (modelo supervisado) |
| Base de datos y mensajería | PostgreSQL 18; Redis (canal de notificaciones entre la API y los WebSockets, caché) |
| Opcionales | Celery, HashiCorp Vault (secretos), nginx (TLS) |
| Pruebas | pytest, Jest, Playwright, ruff, eslint, tsc |
