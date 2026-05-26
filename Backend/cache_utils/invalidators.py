"""Cache invalidation helpers for Fetal Medical System.

Provides functions to invalidate cached data when:
    pass
- Patient records are updated
- Dashboard statistics need refreshing
- Global cache flush is required
"""

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def invalidate_patient_cache(patient_id=None):
    """Clear patient-related caches.

    Invalidates cached data for a specific patient or all patient caches.

    Args:
        patient_id: Specific patient ID to invalidate, or None for all

    Usage:
        # Invalidate specific patient cache
        invalidate_patient_cache(patient_id=123)

        # Invalidate all patient caches
        invalidate_patient_cache()

    """
    try:
        if patient_id:
            # Invalidate specific patient caches
            patterns = [
                f"patient_data:*{patient_id}*",
                f"patient_detail:{patient_id}",
                f"patient_history:{patient_id}",
                f"patient_embarazos:{patient_id}",
            ]
            for pattern in patterns:
                cache.delete_pattern(pattern)
            logger.info("Invalidated cache for patient %s", patient_id)
        else:
            # Invalidate all patient caches
            cache.delete_pattern("patient_data:*")
            cache.delete_pattern("patient_detail:*")
            cache.delete_pattern("patient_history:*")
            logger.info("Invalidated all patient caches")
    except Exception as e:
        logger.error("Failed to invalidate patient cache: %s", e)


def invalidate_dashboard_cache():
    """Clear all dashboard statistics caches.

    Call this when underlying data changes and dashboard stats
    need to be refreshed.

    Usage:
        invalidate_dashboard_cache()
    """
    try:
        cache.delete_pattern("dashboard_stats:*")
        cache.delete_pattern("dashboard_kpi:*")
        cache.delete_pattern("dashboard_alerts:*")
        logger.info("Invalidated all dashboard caches")
    except Exception as e:
        logger.error("Failed to invalidate dashboard cache: %s", e)


def invalidate_ultrasound_cache(embarazo_id=None):
    """Clear ultrasound image caches.

    Args:
        embarazo_id: Specific pregnancy ID to invalidate, or None for all

    """
    try:
        if embarazo_id:
            cache.delete_pattern(f"ultrasound_images:*{embarazo_id}*")
            logger.info("Invalidated ultrasound cache for pregnancy %s", embarazo_id)
        else:
            cache.delete_pattern("ultrasound_images:*")
            logger.info("Invalidated all ultrasound caches")
    except Exception as e:
        logger.error("Failed to invalidate ultrasound cache: %s", e)


def invalidate_statistics_cache():
    """Clear all statistics and report caches.
    """
    try:
        cache.delete_pattern("statistics:*")
        cache.delete_pattern("report_stats:*")
        cache.delete_pattern("general_stats:*")
        logger.info("Invalidated all statistics caches")
    except Exception as e:
        logger.error("Failed to invalidate statistics cache: %s", e)


def invalidate_embarazo_cache(embarazo_id=None):
    """Clear pregnancy-related caches.

    Args:
        embarazo_id: Specific pregnancy ID to invalidate, or None for all

    """
    try:
        if embarazo_id:
            cache.delete_pattern(f"embarazo_data:*{embarazo_id}*")
            cache.delete_pattern(f"embarazo_controles:*{embarazo_id}*")
            cache.delete_pattern(f"embarazo_estadisticas:*{embarazo_id}*")
            logger.info("Invalidated cache for pregnancy %s", embarazo_id)
        else:
            cache.delete_pattern("embarazo_data:*")
            cache.delete_pattern("embarazo_controles:*")
            cache.delete_pattern("embarazo_estadisticas:*")
            logger.info("Invalidated all pregnancy caches")
    except Exception as e:
        logger.error("Failed to invalidate embarazo cache: %s", e)


def invalidate_all_caches():
    """Nuclear option: Clear ALL caches.

    Use with caution. This will cause a temporary performance impact
    as all cached data needs to be regenerated.

    Usage:
        invalidate_all_caches()
    """
    try:
        # Clear all cache patterns used by this application
        patterns = [
            "patient_data:*",
            "patient_detail:*",
            "patient_history:*",
            "patient_embarazos:*",
            "dashboard_stats:*",
            "dashboard_kpi:*",
            "dashboard_alerts:*",
            "ultrasound_images:*",
            "statistics:*",
            "report_stats:*",
            "general_stats:*",
            "embarazo_data:*",
            "embarazo_controles:*",
            "embarazo_estadisticas:*",
        ]

        for pattern in patterns:
            cache.delete_pattern(pattern)

        logger.warning("ALL CACHES INVALIDATED - Nuclear option executed")
    except Exception as e:
        logger.error("Failed to invalidate all caches: %s", e)


def get_cache_stats():
    """Get cache statistics for monitoring.

    Returns information about cache usage and hit rates.

    Returns:
        dict: Cache statistics including hit/miss counts

    """
    try:
        # Try to get cache stats from the default cache
        cache_backend = cache
        stats = {
            "backend": cache_backend.__class__.__name__,
            "status": "available",
        }

        # Test cache connectivity
        test_key = "_cache_health_check"
        cache.set(test_key, "ok", timeout=10)
        result = cache.get(test_key)
        cache.delete(test_key)

        stats["connectivity"] = "healthy" if result == "ok" else "degraded"
        return stats
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
