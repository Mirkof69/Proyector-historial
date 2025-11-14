# =============================================================================
# CONFIGURACIÓN DE DJANGO - SETTINGS.PY
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# Backend: Django REST Framework + PostgreSQL + Redis
# Descripción: Archivo de configuración principal de Django con soporte para
#              variables de entorno, seguridad mejorada y configuraciones
#              específicas para desarrollo y producción.
# Autor: Sistema de Gestión Médica
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import os

# =============================================================================
# CONFIGURACIÓN BASE
# =============================================================================
# Directorio base del proyecto
# Path(__file__).resolve() obtiene la ruta absoluta de este archivo
# parent.parent sube dos niveles desde settings.py hasta el directorio raíz
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SEGURIDAD
# =============================================================================
# Clave secreta de Django - NUNCA hardcodear en producción
# Se obtiene del archivo .env mediante python-decouple
# Para generar una nueva clave secreta usar:
# python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY = config('SECRET_KEY', default='django-insecure-CHANGE-THIS-IN-PRODUCTION')

# Modo de depuración - SIEMPRE False en producción
# En desarrollo debe estar en True para ver errores detallados
# En producción debe estar en False por seguridad
DEBUG = config('DEBUG', default=True, cast=bool)

# Hosts permitidos para servir la aplicación
# En producción debe incluir el dominio real
# Ejemplo: ['midominio.com', 'www.midominio.com', '192.168.1.100']
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# =============================================================================
# APLICACIONES INSTALADAS
# =============================================================================
# Lista de todas las aplicaciones de Django habilitadas en este proyecto
# Orden de carga importante:
# 1. Apps de Django (admin, auth, etc.)
# 2. Apps de terceros (rest_framework, corsheaders, etc.)
# 3. Apps propias del proyecto (pacientes, usuarios, etc.)
INSTALLED_APPS = [
    # -------------------------------------------------------------------------
    # APLICACIONES DE DJANGO
    # -------------------------------------------------------------------------
    'django.contrib.admin',           # Panel de administración de Django
    'django.contrib.auth',            # Sistema de autenticación
    'django.contrib.contenttypes',    # Framework de tipos de contenido
    'django.contrib.sessions',        # Framework de sesiones
    'django.contrib.messages',        # Framework de mensajes
    'django.contrib.staticfiles',     # Manejo de archivos estáticos

    # -------------------------------------------------------------------------
    # APLICACIONES DE TERCEROS
    # -------------------------------------------------------------------------
    'rest_framework',                 # Django REST Framework para APIs
    'corsheaders',                    # Manejo de CORS para peticiones cross-origin
    'django_filters',                 # Filtrado avanzado para querysets
    'drf_spectacular',                # Documentación automática OpenAPI/Swagger

    # -------------------------------------------------------------------------
    # APLICACIONES DEL PROYECTO - MÓDULOS PRINCIPALES
    # -------------------------------------------------------------------------
    'usuarios',                       # Gestión de usuarios del sistema (médicos, enfermeros, admin, etc.)
    'pacientes',                      # Gestión de pacientes
    'embarazos',                      # Gestión de embarazos
    'controles',                      # Controles prenatales
    'calculadoras',                   # Calculadoras obstétricas (edad gestacional, IMC, riesgos, etc.)

    # -------------------------------------------------------------------------
    # APLICACIONES DEL PROYECTO - MÓDULOS NUEVOS (SE AGREGARÁN)
    # -------------------------------------------------------------------------
    # 'partos',                       # Gestión de partos y recién nacidos
    # 'laboratorio',                  # Exámenes de laboratorio y resultados
    # 'ecografias',                   # Ecografías y biometría fetal
    # 'citas',                        # Sistema de agendamiento de citas
    # 'reportes',                     # Generación de reportes y documentos
]

# =============================================================================
# MIDDLEWARE
# =============================================================================
# Stack de middleware que procesa cada request/response
# ORDEN IMPORTANTE - No cambiar sin entender las implicaciones
# El orden afecta cómo se procesan las peticiones HTTP
MIDDLEWARE = [
    # -------------------------------------------------------------------------
    # CORS - Debe estar PRIMERO para procesar headers de CORS
    # -------------------------------------------------------------------------
    'corsheaders.middleware.CorsMiddleware',

    # -------------------------------------------------------------------------
    # SEGURIDAD
    # -------------------------------------------------------------------------
    'django.middleware.security.SecurityMiddleware',    # Seguridad general (HTTPS, headers, etc.)

    # -------------------------------------------------------------------------
    # SESIONES Y AUTENTICACIÓN
    # -------------------------------------------------------------------------
    'django.contrib.sessions.middleware.SessionMiddleware',  # Manejo de sesiones

    # -------------------------------------------------------------------------
    # PROCESAMIENTO DE REQUEST
    # -------------------------------------------------------------------------
    'django.middleware.common.CommonMiddleware',        # Procesamiento común (URLs, etc.)
    'django.middleware.csrf.CsrfViewMiddleware',        # Protección CSRF

    # -------------------------------------------------------------------------
    # AUTENTICACIÓN Y MENSAJES
    # -------------------------------------------------------------------------
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Autenticación de usuarios
    'django.contrib.messages.middleware.MessageMiddleware',     # Sistema de mensajes

    # -------------------------------------------------------------------------
    # PROTECCIÓN CONTRA CLICKJACKING
    # -------------------------------------------------------------------------
    'django.middleware.clickjacking.XFrameOptionsMiddleware',   # Protección X-Frame-Options
]

# =============================================================================
# CONFIGURACIÓN DE URLS Y WSGI
# =============================================================================
ROOT_URLCONF = 'historial.urls'
WSGI_APPLICATION = 'historial.wsgi.application'

# =============================================================================
# CONFIGURACIÓN DE PLANTILLAS
# =============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =============================================================================
# Base de datos PostgreSQL
# Todas las credenciales se obtienen de variables de entorno por seguridad
# NUNCA hardcodear credenciales en el código
DATABASES = {
    'default': {
        # Motor de base de datos - PostgreSQL
        'ENGINE': 'django.db.backends.postgresql',

        # Nombre de la base de datos
        'NAME': config('DB_NAME', default='Historial'),

        # Usuario de PostgreSQL
        'USER': config('DB_USER', default='postgres'),

        # Contraseña de PostgreSQL - CRÍTICO: obtener de .env
        'PASSWORD': config('DB_PASSWORD', default=''),

        # Host del servidor PostgreSQL
        'HOST': config('DB_HOST', default='localhost'),

        # Puerto de PostgreSQL (5432 por defecto, pero puede variar)
        'PORT': config('DB_PORT', default='5433'),

        # Opciones adicionales de conexión
        'OPTIONS': {
            # Nivel de aislamiento de transacciones
            'isolation_level': None,
        },

        # Pool de conexiones
        'CONN_MAX_AGE': 600,  # Mantener conexiones abiertas por 10 minutos

        # Configuración de timeout
        'CONN_HEALTH_CHECKS': True,  # Django 4.1+ - verificar salud de conexiones
    }
}

# =============================================================================
# CONFIGURACIÓN DE REDIS - CACHE Y SESIONES
# =============================================================================
# Redis se usa para:
# 1. Cache de datos frecuentemente accedidos
# 2. Almacenamiento de sesiones de usuario
# 3. Cola de tareas con Celery (opcional)

# Configuración del sistema de cache con Redis
CACHES = {
    'default': {
        # Backend de Django-Redis para cache
        'BACKEND': 'django_redis.cache.RedisCache',

        # URL de conexión a Redis - obtener de variable de entorno
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),

        # Opciones de configuración de Redis
        'OPTIONS': {
            # Cliente de Django-Redis
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',

            # Timeout de conexión (en segundos)
            'SOCKET_CONNECT_TIMEOUT': 5,

            # Timeout de operación (en segundos)
            'SOCKET_TIMEOUT': 5,

            # Pool de conexiones
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },

            # Serialización de datos (pickle es más rápido que JSON)
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },

        # Timeout por defecto del cache (en segundos) - 5 minutos
        'TIMEOUT': 300,

        # Prefijo de claves en Redis para evitar colisiones
        'KEY_PREFIX': 'historial',

        # Versión del cache (incrementar para invalidar todo el cache)
        'VERSION': 1,
    }
}

# -------------------------------------------------------------------------
# CONFIGURACIÓN DE SESIONES CON REDIS
# -------------------------------------------------------------------------
# Usar Redis para almacenar sesiones en lugar de base de datos
# Ventajas: Más rápido y escalable
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Tiempo de vida de la sesión (en segundos) - 24 horas
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=86400, cast=int)

# Guardar sesión en cada request (False para mejor rendimiento)
SESSION_SAVE_EVERY_REQUEST = False

# Nombre de la cookie de sesión
SESSION_COOKIE_NAME = 'historial_sessionid'

# Cookie de sesión solo por HTTP (no accesible por JavaScript)
SESSION_COOKIE_HTTPONLY = True

# Cookie de sesión segura (solo HTTPS) - True en producción
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)

# Política de SameSite para cookies
SESSION_COOKIE_SAMESITE = 'Lax'

# =============================================================================
# VALIDADORES DE CONTRASEÑA
# =============================================================================
# Validadores para asegurar contraseñas seguras
# Django incluye varios validadores por defecto que se pueden personalizar
AUTH_PASSWORD_VALIDATORS = [
    {
        # Validador que previene contraseñas similares a atributos del usuario
        # Ejemplo: Si el usuario se llama "Juan", no puede usar "juan123" como contraseña
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,  # Máximo 70% de similitud permitida
        }
    },
    {
        # Validador de longitud mínima de contraseña
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Mínimo 8 caracteres (recomendado para sistemas médicos)
        }
    },
    {
        # Validador que previene contraseñas comunes
        # Usa una lista de 20,000 contraseñas comunes
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # Validador que previene contraseñas completamente numéricas
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =============================================================================
# INTERNACIONALIZACIÓN Y LOCALIZACIÓN
# =============================================================================
# Configuración de idioma y zona horaria

# Código de idioma principal - Español de Bolivia
LANGUAGE_CODE = config('LANGUAGE_CODE', default='es-bo')

# Zona horaria - America/La_Paz (Bolivia: UTC-4)
TIME_ZONE = config('TIME_ZONE', default='America/La_Paz')

# Habilitar sistema de internacionalización (i18n)
USE_I18N = True

# Habilitar localización de formatos (L10N)
USE_L10N = True

# Usar zonas horarias en el sistema (recomendado)
# Almacena fechas en UTC en la base de datos y convierte según TIME_ZONE
USE_TZ = True

# Formatos de fecha y hora personalizados para Bolivia
DATE_FORMAT = 'd/m/Y'                    # 25/12/2024
DATETIME_FORMAT = 'd/m/Y H:i:s'          # 25/12/2024 14:30:00
TIME_FORMAT = 'H:i:s'                    # 14:30:00
SHORT_DATE_FORMAT = 'd/m/Y'              # 25/12/2024
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'      # 25/12/2024 14:30

# Primer día de la semana (0=Domingo, 1=Lunes)
FIRST_DAY_OF_WEEK = 1  # Lunes

# =============================================================================
# ARCHIVOS ESTÁTICOS (CSS, JavaScript, Imágenes)
# =============================================================================
# URL para servir archivos estáticos
STATIC_URL = config('STATIC_URL', default='/static/')

# Directorio donde se recopilan todos los archivos estáticos en producción
# Usar: python manage.py collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Directorios adicionales donde buscar archivos estáticos
STATICFILES_DIRS = [
    # os.path.join(BASE_DIR, 'static'),
]

# Finders de archivos estáticos
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# =============================================================================
# ARCHIVOS MEDIA (UPLOADS DE USUARIOS)
# =============================================================================
# URL para servir archivos media (uploads)
MEDIA_URL = config('MEDIA_URL', default='/media/')

# Directorio raíz para archivos media
MEDIA_ROOT = os.path.join(BASE_DIR, config('MEDIA_ROOT', default='media'))

# =============================================================================
# CONFIGURACIÓN GENERAL DE MODELOS
# =============================================================================
# Campo de clave primaria automático por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# CONFIGURACIÓN DE DJANGO REST FRAMEWORK
# =============================================================================
# Configuración global para todas las APIs del sistema
REST_FRAMEWORK = {
    # -------------------------------------------------------------------------
    # AUTENTICACIÓN
    # -------------------------------------------------------------------------
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Autenticación JWT personalizada
        'usuarios.authentication.CustomJWTAuthentication',
        # Autenticación de sesión (útil para browsable API)
        'rest_framework.authentication.SessionAuthentication',
    ],

    # -------------------------------------------------------------------------
    # PERMISOS
    # -------------------------------------------------------------------------
    'DEFAULT_PERMISSION_CLASSES': [
        # Por defecto, todas las vistas requieren autenticación
        'rest_framework.permissions.IsAuthenticated',
    ],

    # -------------------------------------------------------------------------
    # RENDERIZADO
    # -------------------------------------------------------------------------
    'DEFAULT_RENDERER_CLASSES': [
        # JSON - Producción
        'rest_framework.renderers.JSONRenderer',
        # Browsable API - Solo desarrollo (comentar en producción)
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    # -------------------------------------------------------------------------
    # PARSERS (PROCESADORES DE DATOS DE ENTRADA)
    # -------------------------------------------------------------------------
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',        # JSON
        'rest_framework.parsers.FormParser',        # Formularios HTML
        'rest_framework.parsers.MultiPartParser',   # Archivos multipart
    ],

    # -------------------------------------------------------------------------
    # PAGINACIÓN
    # -------------------------------------------------------------------------
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # Número de items por página por defecto

    # -------------------------------------------------------------------------
    # FILTRADO
    # -------------------------------------------------------------------------
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',  # Filtros complejos
        'rest_framework.filters.SearchFilter',                # Búsqueda de texto
        'rest_framework.filters.OrderingFilter',              # Ordenamiento
    ],

    # -------------------------------------------------------------------------
    # THROTTLING (LIMITACIÓN DE TASA)
    # -------------------------------------------------------------------------
    # Prevenir abuso de la API limitando el número de requests
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',   # Usuarios anónimos
        'rest_framework.throttling.UserRateThrottle',   # Usuarios autenticados
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',    # 100 requests por hora para usuarios anónimos
        'user': '1000/hour',   # 1000 requests por hora para usuarios autenticados
    },

    # -------------------------------------------------------------------------
    # MANEJO DE EXCEPCIONES
    # -------------------------------------------------------------------------
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',

    # -------------------------------------------------------------------------
    # FORMATO DE FECHAS Y HORAS
    # -------------------------------------------------------------------------
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',  # 2024-12-25 14:30:00
    'DATE_FORMAT': '%Y-%m-%d',                # 2024-12-25
    'TIME_FORMAT': '%H:%M:%S',                # 14:30:00

    # -------------------------------------------------------------------------
    # VERSIONADO DE API
    # -------------------------------------------------------------------------
    # 'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',

    # -------------------------------------------------------------------------
    # DOCUMENTACIÓN
    # -------------------------------------------------------------------------
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # -------------------------------------------------------------------------
    # OTRAS CONFIGURACIONES
    # -------------------------------------------------------------------------
    # Permitir null en campos no requeridos
    'COERCE_DECIMAL_TO_STRING': False,  # Mantener decimales como números

    # Formato de respuestas de error
    'NON_FIELD_ERRORS_KEY': 'errores',
}

# =============================================================================
# CONFIGURACIÓN DE SIMPLE JWT
# =============================================================================
# Configuración de autenticación con JSON Web Tokens
SIMPLE_JWT = {
    # -------------------------------------------------------------------------
    # TIEMPOS DE VIDA DE TOKENS
    # -------------------------------------------------------------------------
    # Access token - Token de corta duración para autenticación
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)
    ),

    # Refresh token - Token de larga duración para renovar access tokens
    'REFRESH_TOKEN_LIFETIME': timedelta(
        hours=config('JWT_REFRESH_TOKEN_LIFETIME', default=24, cast=int)
    ),

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE ROTACIÓN DE TOKENS
    # -------------------------------------------------------------------------
    # Rotar refresh token en cada refresh (mayor seguridad)
    'ROTATE_REFRESH_TOKENS': True,

    # Blacklist de tokens viejos al rotar
    'BLACKLIST_AFTER_ROTATION': True,

    # -------------------------------------------------------------------------
    # ALGORITMO Y FIRMA
    # -------------------------------------------------------------------------
    'ALGORITHM': 'HS256',  # Algoritmo de firma (HS256 es estándar)
    'SIGNING_KEY': SECRET_KEY,  # Clave de firma (usa SECRET_KEY de Django)

    # -------------------------------------------------------------------------
    # CLAIMS DEL TOKEN
    # -------------------------------------------------------------------------
    'USER_ID_FIELD': 'id',          # Campo del modelo Usuario para ID
    'USER_ID_CLAIM': 'user_id',     # Nombre del claim en el token

    # -------------------------------------------------------------------------
    # HEADERS DEL TOKEN
    # -------------------------------------------------------------------------
    'AUTH_HEADER_TYPES': ('Bearer',),  # Tipo de header: "Bearer <token>"
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',

    # -------------------------------------------------------------------------
    # CLAIMS ADICIONALES PERSONALIZADOS
    # -------------------------------------------------------------------------
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),

    # -------------------------------------------------------------------------
    # AUDIENCIA Y EMISOR (OPCIONAL)
    # -------------------------------------------------------------------------
    # 'AUDIENCE': 'historial-medico',
    # 'ISSUER': 'historial-medico-api',
}

# =============================================================================
# CONFIGURACIÓN DE CORS (CROSS-ORIGIN RESOURCE SHARING)
# =============================================================================
# Permite que el frontend (React) en localhost:3000 acceda a la API

# Orígenes permitidos para hacer peticiones CORS
# En producción, especificar solo los dominios autorizados
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv()
)

# Permitir envío de cookies y credenciales en peticiones CORS
CORS_ALLOW_CREDENTIALS = True

# Headers permitidos en peticiones CORS
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Métodos HTTP permitidos en peticiones CORS
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Tiempo de cache de preflight requests (en segundos)
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 horas

# =============================================================================
# CONFIGURACIÓN DE DOCUMENTACIÓN DE API (DRF-SPECTACULAR)
# =============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'API de Historial Médico Obstétrico',
    'DESCRIPTION': 'API REST para sistema de gestión de historiales médicos obstétricos',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
}

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================
# Sistema de registro de eventos y errores
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # Formatters - Formato de los mensajes de log
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },

    # Handlers - Dónde se escriben los logs
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },

    # Loggers - Configuración de logging por módulo
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD ADICIONAL
# =============================================================================
# Configuraciones de seguridad recomendadas para producción

if not DEBUG:
    # Solo aplicar estas configuraciones en producción

    # Forzar HTTPS
    SECURE_SSL_REDIRECT = True

    # Cookies seguras
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Content Security Policy
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

    # X-Frame-Options
    X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# FIN DE CONFIGURACIÓN
# =============================================================================
