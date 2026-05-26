"""Request Monitoring Middleware

Tracks request/response times, logs errors with context,
and monitors API endpoint usage for production observability.
"""

import logging
import time
import uuid

logger = logging.getLogger("monitoring")
request_logger = logging.getLogger("monitoring.requests")


class RequestMonitoringMiddleware:
    """Middleware that monitors all HTTP requests:
        pass
    - Tracks request/response times
    - Logs errors with full context
    - Tracks API endpoint usage
    - Adds unique request ID for tracing
    """

    def __init__(self, get_response):
        """Init"""
        self.get_response = get_response
        # Track start time for uptime calculation
        import django

        self.server_start_time = (
            django.START_TIME if hasattr(django, "START_TIME") else time.time()
        )

    def __call__(self, request):
        """Call"""
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.META["HTTP_X_REQUEST_ID"] = request_id

        # Skip monitoring static/media files and health checks
        path = request.path
        if self._should_skip(path):
            return self.get_response(request)

        # Capture request start time
        start_time = time.time()

        # Log incoming request
        request_logger.info(
            "%s %s",
            request.method,
            path,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
                "remote_addr": self._get_client_ip(request),
                "query_params": request.GET.dict() if request.GET else None,
            },
        )

        # Process request
        try:
            response = self.get_response(request)
        except Exception as e:
            # Log unhandled exceptions with full context
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Unhandled exception: %s",
                e,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
                    "remote_addr": self._get_client_ip(request),
                },
                exc_info=True,
            )
            raise

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Add response headers for debugging
        response["X-Request-ID"] = request_id
        response["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log response
        if response.status_code >= 500:
            logger.error(
                "Server error %s on %s %s",
                response.status_code,
                request.method,
                path,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
                    "remote_addr": self._get_client_ip(request),
                },
            )
        elif response.status_code >= 400:
            logger.warning(
                "Client error %s on %s %s",
                response.status_code,
                request.method,
                path,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
                    "remote_addr": self._get_client_ip(request),
                },
            )
        else:
            logger.info(
                "%s %s -> %s",
                request.method,
                path,
                response.status_code,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
                    "remote_addr": self._get_client_ip(request),
                },
            )

        # Log slow requests (>1000ms)
        if duration_ms > 1000:
            logger.warning(
                "Slow request: %s %s took %sms",
                request.method,
                path,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "slow_request": True,
                },
            )

        return response

    def _should_skip(self, path):
        """Skip monitoring for certain paths."""
        skip_prefixes = [
            "/static/",
            "/media/",
            "/favicon.ico",
            "/robots.txt",
        ]
        return any(path.startswith(prefix) for prefix in skip_prefixes)

    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",", 1)[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip
