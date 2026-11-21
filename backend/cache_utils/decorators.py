"""Custom cache decorators for Fetal Medical System.

Provides specialized decorators for caching:
    pass
- Patient-related queries
- Dashboard statistics
- Ultrasound image lists
"""

import functools
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def _generate_cache_key(prefix, *args, **kwargs):
    """Generate a consistent cache key from function arguments.

    Handles both positional and keyword arguments, converting
    them to a hashable string format.
    """
    key_parts = [prefix]

    # Add positional args
    for arg in args:
        if hasattr(arg, "id"):
            key_parts.append(str(arg.id))
        else:
            key_parts.append(str(arg))

    # Add keyword args (sorted for consistency)
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        if hasattr(value, "id"):
            key_parts.append(f"{key}={value.id}")
        else:
            key_parts.append(f"{key}={value}")

    return ":".join(key_parts)


def cache_patient_data(timeout=300):
    """Decorator to cache patient-related queries.

    Use on view methods that fetch patient data, clinical history,
    or patient search results.

    Args:
        timeout: Cache timeout in seconds (default: 300 = 5 minutes)

    Usage:
        @cache_patient_data(timeout=600)
        def get_patient_history(request, patient_id):
            ...

    """

    def decorator(view_func):
        """Decorator"""
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            """Wrapped view"""
            cache_key = _generate_cache_key(
                "patient_data",
                request.user.id if hasattr(request, "user") else "anonymous",
                *args,
                **kwargs,
            )

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for patient data: %s", cache_key)
                return cached_result

            # Execute view and cache result
            logger.debug("Cache miss for patient data: %s", cache_key)
            result = view_func(request, *args, **kwargs)

            # Only cache successful responses
            if hasattr(result, "status_code") and result.status_code == 200:
                try:
                    cache.set(cache_key, result, timeout)
                except Exception as e:
                    logger.warning("Failed to cache patient data: %s", e)

            return result

        return _wrapped_view

    return decorator


def cache_dashboard_data(timeout=60):
    """Decorator to cache dashboard statistics.

    Dashboard stats are expensive to compute but change frequently,
    so they use a shorter timeout (default: 60 seconds).

    Args:
        timeout: Cache timeout in seconds (default: 60)

    Usage:
        @cache_dashboard_data(timeout=120)
        def get_dashboard_stats(request):
            ...

    """

    def decorator(view_func):
        """Decorator"""
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            """Wrapped view"""
            cache_key = _generate_cache_key(
                "dashboard_stats",
                request.user.id if hasattr(request, "user") else "anonymous",
                **dict(request.query_params.items()),
            )

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for dashboard: %s", cache_key)
                return cached_result

            # Execute view and cache result
            logger.debug("Cache miss for dashboard: %s", cache_key)
            result = view_func(request, *args, **kwargs)

            # Only cache successful responses
            if hasattr(result, "status_code") and result.status_code == 200:
                try:
                    cache.set(cache_key, result, timeout)
                except Exception as e:
                    logger.warning("Failed to cache dashboard data: %s", e)

            return result

        return _wrapped_view

    return decorator


def cache_ultrasound_images(timeout=900):
    """Decorator to cache ultrasound image lists.

    Ultrasound image lists change infrequently, so they use
    a longer timeout (default: 900 = 15 minutes).

    Args:
        timeout: Cache timeout in seconds (default: 900 = 15 minutes)

    Usage:
        @cache_ultrasound_images(timeout=1800)
        def get_ultrasound_images(request, pk):
            ...

    """

    def decorator(view_func):
        """Decorator"""
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            """Wrapped view"""
            cache_key = _generate_cache_key("ultrasound_images", *args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for ultrasound images: %s", cache_key)
                return cached_result

            # Execute view and cache result
            logger.debug("Cache miss for ultrasound images: %s", cache_key)
            result = view_func(request, *args, **kwargs)

            # Only cache successful responses
            if hasattr(result, "status_code") and result.status_code == 200:
                try:
                    cache.set(cache_key, result, timeout)
                except Exception as e:
                    logger.warning("Failed to cache ultrasound images: %s", e)

            return result

        return _wrapped_view

    return decorator


def cache_query_result(queryset_func, timeout=300, key_prefix="query"):
    """Decorator for caching Django QuerySet results.

    Use this to cache expensive database queries that return QuerySets.

    Args:
        queryset_func: Function that returns the cache key portion
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key

    Usage:
        @cache_query_result(lambda self: f"patient_{self.pk}", timeout=600)
        def get_expensive_data(self):
            return self.related_objects.all()

    """

    def decorator(method):
        """Decorator"""
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            """Wrapper"""
            try:
                key_part = queryset_func(self)
                cache_key = f"{key_prefix}:{key_part}"

                cached = cache.get(cache_key)
                if cached is not None:
                    return cached

                result = method(self, *args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result
            except Exception as e:
                logger.warning("Cache error in %s: %s", method.__name__, e)
                return method(self, *args, **kwargs)

        return wrapper

    return decorator
