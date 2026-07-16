"""Settings module."""
import contextlib
import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import environ

# ========== INICIALIZACIÓN DE VARIABLES DE ENTORNO ==========
BASE_DIR = Path(__file__).resolve().parent

# Leer archivo .env (si existe)
env_file = os.path.join(BASE_DIR, ".env")

env = environ.Env(
    DEBUG=(bool, True),  # True por defecto para desarrollo
    SECRET_KEY=(str, ""),  # ¡CRÍTICO: debe definirse en .env o Vault! Ver CLAUDE.md
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1", "clinica-demo.localhost", "clinica-demo.127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(
        list,
        [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://clinica-demo.localhost:3000",
            "http://clinica-demo.127.0.0.1:3000",
        ],
    ),
    CSRF_COOKIE_SECURE=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    SECURE_SSL_REDIRECT=(bool, False),
    SECURE_HSTS_SECONDS=(int, 0),
    SECURE_HSTS_INCLUDE_SUBDOMAINS=(bool, False),
    SECURE_HSTS_PRELOAD=(bool, False),
    DB_NAME=(str, "Historial"),
    DB_USER=(str, ""),  # ¡CRÍTICO: debe definirse en .env o Vault!
    DB_PASSWORD=(str, ""),  # ¡CRÍTICO: debe definirse en .env o Vault!
    DB_HOST=(str, "localhost"),
    DB_PORT=(str, "5432"),
    # Redis Cache
    REDIS_URL=(str, "redis://localhost:6379/1"),
    # Monitoring & Logging
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, "development"),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.2),
    LOG_LEVEL=(str, "INFO"),
    AI_SERVICE_URL=(str, "http://localhost:8001"),
    ENCRYPTION_KEY=(str, ""),
    ORTHANC_URL=(str, "http://localhost:8042"),
    ORTHANC_USERNAME=(str, "fetalmedical"),
    ORTHANC_PASSWORD=(str, ""),
    OHIF_VIEWER_URL=(str, "http://localhost:3000/viewer"),
)

# Leer archivo .env si existe
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# ========== INTEGRACIÓN HASHICORP VAULT ==========
# Lee secretos desde Vault y sobrescribe variables de entorno si están disponibles
VAULT_ADDR = os.environ.get("VAULT_ADDR")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN")
if VAULT_ADDR and VAULT_TOKEN:
    try:
        import hvac

        client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
        if client.is_authenticated():
            vault_secrets = client.secrets.kv.v2.read_secret_version(
                path="fetalmedical/backend",
            )
            if (
                vault_secrets
                and "data" in vault_secrets
                and "data" in vault_secrets["data"]
            ):
                data = vault_secrets["data"]["data"]
                # Actualizar env() temporalmente con los secretos de Vault
                for key, value in data.items():
                    os.environ[key] = str(value)
            print("HashiCorp Vault: Secretos cargados exitosamente.")
    except Exception as e:
        print(f"HashiCorp Vault: Fallo al cargar secretos ({e}). Usando .env fallback.")

# ========== CONFIGURACIONES DE SEGURIDAD ==========
# DEBUG debe definirse ANTES del bloque Sentry (que lo referencia)
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("SECRET_KEY must be set in .env or environment")
ENCRYPTION_KEY = env("ENCRYPTION_KEY")
# "fernet" (default, AES-128-CBC+HMAC, formato legado) o "aes256gcm" (AES-256
# real). Cambiar a "aes256gcm" hace que las ESCRITURAS nuevas usen AES-256;
# las lecturas siguen soportando ambos formatos indefinidamente (ver
# pacientes/fields.py EncryptedFieldMixin), asi que la migracion es gradual,
# no un corte de un solo dia.
ENCRYPTION_CIPHER_MODE = os.environ.get("ENCRYPTION_CIPHER_MODE", "fernet")

# ========== INTEGRACIÓN ORTHANC (PACS DICOM) ==========
ORTHANC_URL = env("ORTHANC_URL")
ORTHANC_USERNAME = env("ORTHANC_USERNAME")
ORTHANC_PASSWORD = env("ORTHANC_PASSWORD")
OHIF_VIEWER_URL = env("OHIF_VIEWER_URL")
if not ENCRYPTION_KEY and not env("DEBUG"):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "ENCRYPTION_KEY must be set in .env or environment. "
        'Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# ========== SENTRY SDK INTEGRATION ==========
SENTRY_DSN = env("SENTRY_DSN")
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT")
SENTRY_TRACES_SAMPLE_RATE = env("SENTRY_TRACES_SAMPLE_RATE")

if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=cast(str, SENTRY_DSN),
        integrations=[
            DjangoIntegration(transaction_style="url"),
            sentry_logging,
        ],
        environment=cast(str, SENTRY_ENVIRONMENT),
        traces_sample_rate=cast(float, SENTRY_TRACES_SAMPLE_RATE),
        send_default_pii=False,  # SEGURIDAD: nunca enviar PII (datos pacientes) a Sentry — Ley 164 Bolivia
        _experiments={
            "continuous_profiling_auto_start": True,
        },
    )
else:
    with contextlib.suppress(ImportError):
        import sentry_sdk

# ========== VERSION DE LA APLICACIÓN ==========
try:
    from importlib.metadata import version as _importlib_version
    APP_VERSION = _importlib_version("backend")
except (ImportError, Exception):
    APP_VERSION = "3.0.0"

SHARED_APPS = [
    "django_tenants",
    "clientes",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "channels",
    # AUTH_USER_MODEL debe estar en SHARED_APPS para que admin/auth funcionen
    # en el schema public (django-tenants requiere esto)
    "usuarios",
    "roles",
    "auditoria",
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "pacientes",
    "embarazos",
    "controles",
    "calculadoras",
    "ecografias",
    "laboratorio",
    "citas",
    "partos",
    "calculadoras_avanzadas",
    "reportes",
    "antecedentes",
    "triaje",
    "consultorios",
    "evoluciones",
    "ecografias_archivos",
    "notificaciones",
    "notas_evolucion",
    "vacunas",
    "ia_medica",
    "soporte",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL = "clientes.Client"
TENANT_DOMAIN_MODEL = "clientes.Domain"
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # PRIMERO: CORS antes de todo
    "clientes.middleware.FallbackTenantMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "auditoria.middleware.AuditoriaMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "monitoring.middleware.RequestMonitoringMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",  # Agregado para archivos media
            ],
        },
    },
]

WSGI_APPLICATION = "wsgi.application"

# ========== ASGI APPLICATION (Django Channels) ==========
ASGI_APPLICATION = "asgi.application"

# ========== CHANNEL LAYERS (WebSocket Backend) ==========
# InMemoryChannelLayer for development; RedisChannelLayer for production.
_REDIS_URL = env("REDIS_URL", default=cast(Any, ""))

if _REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [_REDIS_URL],
                "capacity": 1500,  # Maximum number of messages to store
                "expiry": 10,  # Message expiry in seconds
            },
        },
    }
else:
    # Development fallback: in-memory channel layer (single-process only)
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "OPTIONS": {
            "client_encoding": "UTF8",
            "connect_timeout": 30,
            "sslmode": env("DB_SSLMODE", default="disable"),
        },
    },
}

if os.environ.get("USE_SQLITE", "").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_dev.sqlite3",
        },
    }

# ========== TESTING CONFIGURATION FOR MULTI-TENANCY FALLBACK ==========
import sys

TESTING = 'test' in sys.argv or any('pytest' in arg for arg in sys.argv)

if TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    DATABASE_ROUTERS: list[str] = []  # type: ignore[no-redef]
    SHARED_APPS = [app for app in SHARED_APPS if app != "django_tenants"]
    TENANT_APPS = [app for app in TENANT_APPS if app != "django_tenants"]
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_tenants"]
    MIDDLEWARE = [mw for mw in MIDDLEWARE if "clientes.middleware" not in mw]


# ========== CONFIGURACION DE CACHE ==========
# Redis cache configuration with fallback to LocMemCache for development
_REDIS_CACHE_URL = env("REDIS_URL", default=cast(Any, ""))

if _REDIS_CACHE_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _REDIS_CACHE_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "IGNORE_EXCEPTIONS": True,  # Never fail on cache errors
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 50,
                    "retry_on_timeout": True,
                },
            },
            "KEY_PREFIX": "fetal_medical",
            "TIMEOUT": 300,  # 5 minutes default
            "VERSION": 1,
        },
        # Separate cache for session data
        "sessions": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _REDIS_CACHE_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "fetal_sessions",
            "TIMEOUT": 86400,  # 24 hours
        },
        # Cache for expensive computations/statistics
        "statistics": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _REDIS_CACHE_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "fetal_stats",
            "TIMEOUT": 60,  # 1 minute for frequently changing stats
        },
    }
else:
    # Development fallback: in-memory cache (single-process only)
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "fetal-medical-default",
            "TIMEOUT": 300,
        },
        "sessions": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "fetal-medical-sessions",
        },
        "statistics": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "fetal-medical-stats",
            "TIMEOUT": 60,
        },
    }

# Cache alias for Django's cache framework to use
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = "fetal_medical_middleware"

# ========== CONFIGURACION DE SESIONES ==========
# Use Redis for sessions in production, DB for development
if _REDIS_CACHE_URL:
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "sessions"
else:
    SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# ========== MODELO DE USUARIO PERSONALIZADO ==========
AUTH_USER_MODEL = "usuarios.Usuario"

# ========== BACKENDS DE AUTENTICACIÓN ==========
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# ========== VALIDADORES DE CONTRASEÑA ==========
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========== INTERNACIONALIZACIÓN ==========
LANGUAGE_CODE = "es-bo"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

# ========== ARCHIVOS ESTÁTICOS ==========
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ========== ARCHIVOS MEDIA ==========
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ========== CONFIGURACIÓN PARA IMÁGENES MÉDICAS ==========
# Tamaños máximos de archivos
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Configuración para imágenes de ecografías
ECOGRAFIA_UPLOAD_PATH = "ecografias/%Y/%m/%d/"

# Formatos de imagen permitidos
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".dicom"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Configuración de thumbnails
THUMBNAIL_SIZE = (300, 300)
THUMBNAIL_QUALITY = 85

# ========== CAMPO AUTO POR DEFECTO ==========
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========== REST FRAMEWORK CONFIGURATION ==========
REST_FRAMEWORK = {
    # Autenticación: JWT por header (Kong/API externa) con fallback a cookie
    # httpOnly + CSRF para el navegador (migración de seguridad: los tokens
    # ya no viven en localStorage).
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "usuarios.auth_cookies.CookieJWTAuthentication",  # header Bearer o cookie
        "rest_framework.authentication.SessionAuthentication",  # Session para browsable API
    ],
    # Permisos por defecto — RBAC por rol (mínimo privilegio)
    "DEFAULT_PERMISSION_CLASSES": [
        "core.permissions.FetalMedicalPermission",
    ],
    # Renderizadores
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # Interfaz web
    ],
    # Filtros
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Paginación
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 200,
    # Manejo de excepciones
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    # Formatos de fecha/hora
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DATE_FORMAT": "%Y-%m-%d",
    "TIME_FORMAT": "%H:%M:%S",
    # Schema generation for drf-spectacular
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ========== DRF SPECTACULAR - API DOCUMENTATION ==========
SPECTACULAR_SETTINGS = {
    "TITLE": "Fetal Medical System API",
    "DESCRIPTION": """# Fetal Medical System - API Documentation

Comprehensive REST API for fetal medical record management, prenatal care, and obstetric risk assessment.

## System Modules (22 Total)

### Core Patient Management
1. **Pacientes** - Patient registration, clinical history, and advanced search
2. **Usuarios** - User management, authentication, roles, and permissions
3. **Embarazos** - Pregnancy tracking, risk assessment, and gestational monitoring
4. **Controles** - Prenatal checkups, vital signs, and fetal monitoring
5. **Ecografias** - Ultrasound imaging, biometry, and fetal anatomy assessment

### Medical Calculators & Laboratory
6. **Calculadoras** - FMF risk calculators for preeclampsia, trisomies, and gestational diabetes
7. **Calculadoras Avanzadas** - Advanced obstetric calculations and Doppler analysis
8. **Laboratorio** - Clinical laboratory results (hemograms, biochemistry, pregnancy markers)

### Clinical Care Modules
9. **Citas** - Appointment scheduling and management
10. **Partos** - Delivery tracking and birth records
11. **Antecedentes** - Medical history and patient background
12. **Triaje** - Triage assessment and priority classification
13. **Consultorios** - Office/clinic management
14. **Evoluciones** - Clinical evolution tracking
15. **Notas Evolucion** - Medical evolution notes
16. **Vacunas** - Vaccination control and records

### Imaging & Notifications
17. **Ecografias Archivos** - Ultrasound image file management
18. **Notificaciones** - Notification system for alerts and reminders

### Advanced Systems
19. **IA Medica** - AI-powered medical analysis with ML and NLP
20. **Auditoria** - Audit trail and compliance logging
21. **Roles** - Role-based access control management
22. **Reportes** - Reports and statistical analysis
23. **Monitoring** - System health checks and monitoring

## Authentication

All API endpoints require JWT Bearer token authentication.

1. Obtain token: `POST /api/token/` with `{email, password}`
2. Include header: `Authorization: Bearer <access_token>`
3. Refresh token: `POST /api/token/refresh/` with `{refresh_token}`

## Pagination

All list endpoints support pagination with parameters:
    pass
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 200)

## Filtering & Search

Most endpoints support:
    pass
- `search=<term>` - Full-text search across configured fields
- `ordering=<field>` - Sort by field (prefix with `-` for descending)
- `field=value` - Filter by specific field values

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Missing or invalid authentication token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 409 | Conflict - Resource conflict (e.g., duplicate) |
| 500 | Internal Server Error |

## Version

API Version: 1.0.0
""",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_URLCONF": "urls",
    # Authentication schemes
    "SECURITY": [{"jwtAuth": []}],
    # Schema generation
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    # Custom settings
    "SCHEMA_PATH_PREFIX": r"/api/",
    "ENUM_NAME_OVERRIDES": {},
    # Append custom components to the schema
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "jwtAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Bearer token authentication. Obtain token via POST /api/token/ with {email, password}. Refresh token via POST /api/token/refresh/ with {refresh_token}.",
            },
        },
    },
    # License & contact
    "LICENSE": {"name": "Proprietary - Fetal Medical System"},
    "CONTACT": {
        "name": "Fetal Medical System Support",
        "email": "support@fetalmedical.com",
    },
    # Server configuration
    "SERVERS": [
        {"url": os.environ.get("DEV_SERVER_URL", "http://localhost:8000"), "description": "Development server"},
        {"url": os.environ.get("PROD_SERVER_URL", "https://api.fetalmedical.com"), "description": "Production server"},
    ],
    # Warnings and validation
    "DISABLE_ERRORS_AND_WARNINGS": not True,  # Show warnings in development
    "PREPROCESSING_HOOKS": [],
    "POSTPROCESSING_HOOKS": [],
    # Custom extensions for better documentation
    "ENUM_ADD_EXPLICIT_BLANK": False,
    "SCHEMA_COERCE_PATH_PK_SUFFIX": True,
}

# ========== CONFIGURACIÓN JWT ==========
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=15,
    ),  # CLAUDE.md security spec: 15 minutos
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    # Kong valida los JWT con KONG_JWT_SECRET; debe ser la misma clave con la
    # que Django firma. Sin Kong (dev local) cae a SECRET_KEY.
    "SIGNING_KEY": env("KONG_JWT_SECRET", default=SECRET_KEY),
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    # Kong usa key_claim_name=iss para mapear el consumer "fetal-medical-frontend".
    "ISSUER": env("JWT_ISSUER", default="fetal-medical-frontend"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# En desarrollo: permitir todos los orígenes para evitar bloqueos CORS
DEBUG_CORS = env.bool("DEBUG", default=True)
if DEBUG_CORS:
    CORS_ALLOW_ALL_ORIGINS = True  # Solo en desarrollo
else:
    CORS_ALLOWED_ORIGINS = env.list(
        "CORS_ALLOWED_ORIGINS",
        default=cast(Any, [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]),
    )

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ========== SEGURIDAD ==========
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=cast(Any, [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://clinica-demo.localhost:3000",
        "http://clinica-demo.127.0.0.1:3000",
    ]),
)

# Configuraciones de seguridad para producción
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("SECURE_HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Configuración de seguridad para proxies inversos (nginx/Kong)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Configuración de cookies de sesión
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # React necesita leer la cookie CSRF via JS
CSRF_COOKIE_SAMESITE = "Lax"

# Suppress security warnings for development (DEBUG=True)
# These are only relevant in production where DEBUG=False
if DEBUG:
    SILENCED_SYSTEM_CHECKS = [
        "security.W004",  # SECURE_HSTS_SECONDS
        "security.W008",  # SECURE_SSL_REDIRECT
        "security.W009",  # SECRET_KEY length
        "security.W012",  # SESSION_COOKIE_SECURE
        "security.W016",  # CSRF_COOKIE_SECURE
        "security.W018",  # DEBUG=True
    ]

# ========== CONFIGURACIÓN DE LOGGING ESTRUCTURADO ==========
LOG_LEVEL = env("LOG_LEVEL")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Formato JSON para logging estructurado
LOG_JSON_FORMATTER = "pythonjsonlogger.jsonlogger.JsonFormatter"

# Check if sentry_sdk is available
SENTRY_AVAILABLE = False
try:
    import sentry_sdk  # type: ignore

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

# Build handlers dict conditionally
_handlers = {
    # Consola para desarrollo
    "console": {
        "level": "DEBUG",
        "filters": ["require_debug_true"],
        "class": "logging.StreamHandler",
        "formatter": "verbose",
    },
    # Archivo principal con rotación
    "file_main": {
        "level": "INFO",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": LOG_DIR / "django.log",
        "maxBytes": 10 * 1024 * 1024,  # 10MB
        "backupCount": 5,
        "formatter": "json",
        "encoding": "utf-8",
    },
    # Archivo de errores con rotación
    "file_errors": {
        "level": "WARNING",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": LOG_DIR / "errors.log",
        "maxBytes": 10 * 1024 * 1024,  # 10MB
        "backupCount": 5,
        "formatter": "json",
        "encoding": "utf-8",
    },
    # Archivo de auditoría con rotación
    "file_audit": {
        "level": "INFO",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": LOG_DIR / "audit.log",
        "maxBytes": 10 * 1024 * 1024,  # 10MB
        "backupCount": 10,
        "formatter": "json",
        "encoding": "utf-8",
    },
    # Archivo de requests con rotación
    "file_requests": {
        "level": "INFO",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": LOG_DIR / "requests.log",
        "maxBytes": 10 * 1024 * 1024,  # 10MB
        "backupCount": 5,
        "formatter": "json",
        "encoding": "utf-8",
    },
    # Null handler para /dev/null
    "null": {
        "class": "logging.NullHandler",
    },
}

# Add Sentry handler only if sentry_sdk is installed
if SENTRY_AVAILABLE:
    _handlers["sentry"] = {
        "level": "ERROR",
        "filters": ["require_debug_false"],
        "class": "sentry_sdk.integrations.logging.EventHandler",
    }


# Helper to conditionally add sentry handler to handler lists
def _with_sentry(*handlers):
    """Add 'sentry' handler to the list if available."""
    result = list(handlers)
    if SENTRY_AVAILABLE:
        result.append("sentry")
    return result


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} | {levelname:<8} | {name} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": LOG_JSON_FORMATTER,
            "format": "%(timestamp)s %(levelname)s %(name)s %(message)s %(filename)s %(lineno)d %(funcName)s",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": _handlers,
    "loggers": {
        # Logger principal de Django
        "django": {
            "handlers": ["console", "file_main", "file_errors"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # Logger de seguridad
        "django.security": {
            "handlers": _with_sentry("console", "file_errors"),
            "level": "WARNING",
            "propagate": False,
        },
        # Logger de requests (usado por el middleware)
        "django.request": {
            "handlers": _with_sentry("console", "file_requests", "file_errors"),
            "level": "INFO",
            "propagate": False,
        },
        # Logger de base de datos
        "django.db.backends": {
            "handlers": ["file_main"],
            "level": "WARNING",
            "propagate": False,
        },
        # Logger de auditoría
        "auditoria": {
            "handlers": _with_sentry("console", "file_audit"),
            "level": "INFO",
            "propagate": False,
        },
        # Logger de monitoreo
        "monitoring": {
            "handlers": _with_sentry("console", "file_requests"),
            "level": "INFO",
            "propagate": False,
        },
        # Logger de IA médica
        "ia_medica": {
            "handlers": _with_sentry("console", "file_main", "file_errors"),
            "level": "INFO",
            "propagate": False,
        },
        # Logger de reportes
        "reportes": {
            "handlers": ["console", "file_main"],
            "level": "INFO",
            "propagate": False,
        },
        # Logger raíz del proyecto
        "": {
            "handlers": _with_sentry("console", "file_main", "file_errors"),
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# ========== CONFIGURACIÓN DE EMAIL ==========
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@fetalmedical.com")

# ========== CONFIGURACIÓN CELERY ==========
# Broker: Redis (no requiere instalación de RabbitMQ)
# Para usar RabbitMQ en producción: CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=cast(Any, "redis://127.0.0.1:6379/0"))

# Resultados de las tareas
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=cast(Any, "redis://127.0.0.1:6379/1"))

# Serialización
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Configuraciones de enrutamiento y tiempos
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = (
    30 * 60
)  # 30 minutos máximo por tarea (ideal para procesamiento DICOM pesado)

# Ejecución síncrona/eager en desarrollo si Celery no está corriendo
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=cast(bool, DEBUG))
CELERY_TASK_EAGER_PROPAGATES = True

# ========== ESCALAMIENTO DE ALERTAS CRÍTICAS ==========
# Cadena de derivación cuando una notificación de prioridad CRÍTICA sigue SIN
# LEERSE. Los tiempos y roles son CONFIGURABLES (no hardcodeados) para que un
# comité médico los ajuste. Solo escala prioridad crítica (el resto no, para no
# generar alert fatigue en los niveles superiores).
#
# NOTA (pendiente de validación con comité médico real): 15/30 min y los roles
# 'jefe_guardia'/'coordinacion_medica' son un DEFAULT razonable, no una decisión
# clínica definitiva. Mientras esos roles no existan en el sistema, el
# escalamiento cae al fallback de administradores activos.
ESCALAMIENTO_NIVEL2_MINUTOS = env.int("ESCALAMIENTO_NIVEL2_MINUTOS", default=15)
ESCALAMIENTO_NIVEL3_MINUTOS = env.int("ESCALAMIENTO_NIVEL3_MINUTOS", default=30)
ESCALAMIENTO_ROL_NIVEL2 = env("ESCALAMIENTO_ROL_NIVEL2", default="jefe_guardia")
ESCALAMIENTO_ROL_NIVEL3 = env("ESCALAMIENTO_ROL_NIVEL3", default="coordinacion_medica")

# Programación periódica del chequeo de escalamiento (Celery beat).
CELERY_BEAT_SCHEDULE = {
    "escalar-notificaciones-criticas": {
        "task": "notificaciones.tasks.escalar_notificaciones_criticas",
        # Cada 5 min: suficiente resolución para umbrales de 15/30 min.
        "schedule": env.int("ESCALAMIENTO_CHECK_SEGUNDOS", default=300),
    },
}
