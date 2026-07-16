"""Health check views for monitoring system status.

Provides endpoint /api/health/ that returns:
    pass
- System uptime
- Database connectivity
- Redis cache connectivity
- AI microservice connectivity
- Service versions
"""

import logging
import os
import time

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger("monitoring")

# Application start time for uptime calculation
APP_START_TIME = time.time()


def _get_version():
    """Get application version from settings or default."""
    return getattr(settings, "APP_VERSION", "1.0.0")


def _check_database():
    """Check database connectivity."""
    try:
        db_conn = connections["default"]
        db_conn.ensure_connection()
        return {"status": "healthy", "message": "Database connection successful"}
    except OperationalError as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {e!s}",
        }
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database error: {e!s}"}


def _check_redis():
    """Check Redis cache connectivity."""
    try:
        # Test basic cache operations
        test_key = "_health_check_redis"
        cache.set(test_key, "ok", timeout=10)
        result = cache.get(test_key)
        cache.delete(test_key)

        if result == "ok":
            # Get cache backend info
            backend = cache.__class__.__name__
            is_redis = "Redis" in backend

            if is_redis:
                return {
                    "status": "healthy",
                    "message": "Redis cache connection successful",
                    "backend": backend,
                }
            return {
                "status": "degraded",
                "message": "Using fallback cache (LocMemCache)",
                "backend": backend,
            }
        return {"status": "unhealthy", "message": "Redis cache read/write failed"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Redis cache error: {e!s}"}


def _check_ai_service():
    """Check AI microservice connectivity."""
    ai_url = os.environ.get("AI_SERVICE_URL", "http://localhost:8001")
    try:
        response = requests.get(f"{ai_url}/health", timeout=3)
        if response.status_code == 200:
            return {"status": "healthy", "message": "AI service is reachable"}
        return {
            "status": "degraded",
            "message": f"AI service returned status {response.status_code}",
        }
    except requests.exceptions.ConnectionError:
        return {"status": "unhealthy", "message": "AI service is not reachable"}
    except requests.exceptions.Timeout:
        return {"status": "degraded", "message": "AI service request timed out"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"AI service error: {e!s}"}


def _get_uptime():
    """Get application uptime in human-readable format."""
    uptime_seconds = time.time() - APP_START_TIME
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


@csrf_exempt
@require_http_methods(["GET"])
def health_check(_request):
    """Health check endpoint.

    Returns system status including:
    - Overall health status
    - Database connectivity
    - Redis cache connectivity
    - AI microservice connectivity
    - Application uptime
    - Version information
    """
    # Check all services
    db_status = _check_database()
    redis_status = _check_redis()
    ai_status = _check_ai_service()

    # Determine overall status
    # Redis y AI son opcionales en desarrollo — solo la BD es crítica
    if db_status["status"] == "unhealthy":
        overall_status = "unhealthy"
        status_code = 503
    elif any(s["status"] == "unhealthy" for s in [redis_status, ai_status]):
        overall_status = "degraded"
        status_code = 200
    elif any(s["status"] == "unhealthy" for s in [db_status, redis_status, ai_status]):
        overall_status = "unhealthy"
        status_code = 503
    elif any(s["status"] == "degraded" for s in [db_status, redis_status, ai_status]):
        overall_status = "degraded"
        status_code = 200
    else:
        overall_status = "healthy"
        status_code = 200

    # Log health check
    logger.info(
        "Health check: %s",
        overall_status,
        extra={
            "db_status": db_status["status"],
            "redis_status": redis_status["status"],
            "ai_status": ai_status["status"],
            "overall_status": overall_status,
        },
    )

    response_data = {
        "status": overall_status,
        "version": _get_version(),
        "uptime": _get_uptime(),
        "services": {
            "database": db_status,
            "redis_cache": redis_status,
            "ai_microservice": ai_status,
        },
        "environment": settings.SENTRY_ENVIRONMENT
        if hasattr(settings, "SENTRY_ENVIRONMENT")
        else "development",
        "debug": settings.DEBUG,
    }

    return JsonResponse(response_data, status=status_code)
