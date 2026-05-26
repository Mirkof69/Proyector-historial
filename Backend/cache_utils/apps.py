"""Cache utilities app configuration for Fetal Medical System.
"""

from django.apps import AppConfig


class CacheUtilsConfig(AppConfig):
    """Cacheutilsconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "cache_utils"
    verbose_name = "Cache Utilities"
