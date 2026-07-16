"""Django management command for cache operations.

Usage:
    python manage.py cache_flush [--pattern PATTERN] [--all] [--stats]
    python manage.py cache_flush --pattern "patient_*"
    python manage.py cache_flush --all
    python manage.py cache_flush --stats
"""

from django.conf import settings
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Command"""
    help = "Manage Django cache (flush, stats, health check)"

    def __init__(self, *args, **kwargs):
        """Initialize command with cache attributes."""
        super().__init__(*args, **kwargs)
        self.cache_alias = "default"
        self.cache_backend = None

    def add_arguments(self, parser):
        """Add arguments"""
        parser.add_argument(
            "--pattern",
            type=str,
            help="Delete keys matching pattern (supports wildcards)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Flush all caches completely",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Show cache statistics",
        )
        parser.add_argument(
            "--health",
            action="store_true",
            help="Run cache health check",
        )
        parser.add_argument(
            "--cache",
            type=str,
            default="default",
            help="Cache alias to operate on (default: default)",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            help="Application key prefix to target",
        )

    def handle(self, *args, **options):
        """Handle"""
        self.cache_alias = options["cache"]

        try:
            self.cache_backend = caches[self.cache_alias]
        except Exception as e:
            raise CommandError(f"Cache '{self.cache_alias}' not configured: {e}") from e

        if options["stats"]:
            self.show_stats()
        elif options["health"]:
            self.health_check()
        elif options["all"]:
            self.flush_all()
        elif options["pattern"]:
            self.flush_pattern(options["pattern"])
        else:
            self.show_stats()

    def show_stats(self):
        """Display cache statistics."""
        assert self.cache_backend is not None
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Cache Statistics"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        backend = self.cache_backend.__class__.__name__
        self.stdout.write(f"Backend: {backend}")
        self.stdout.write(f"Cache Alias: {self.cache_alias}")

        # Get key prefix from settings
        cache_config = settings.CACHES.get(self.cache_alias, {})
        key_prefix = cache_config.get("KEY_PREFIX", "N/A")
        self.stdout.write(f"Key Prefix: {key_prefix}")

        # Test health
        test_key = "_mgmt_health_check"
        self.cache_backend.set(test_key, "ok", timeout=10)
        result = self.cache_backend.get(test_key)
        self.cache_backend.delete(test_key)

        status = "HEALTHY" if result == "ok" else "UNHEALTHY"
        self.stdout.write(
            f"Status: {self.style.SUCCESS(status) if result == 'ok' else self.style.ERROR(status)}",
        )

    def health_check(self):
        """Run cache health check."""
        assert self.cache_backend is not None
        self.stdout.write("Running cache health check...")

        try:
            # Test write
            test_key = "_mgmt_health_test"
            self.cache_backend.set(test_key, "healthy", timeout=30)

            # Test read
            result = self.cache_backend.get(test_key)

            # Test delete
            self.cache_backend.delete(test_key)

            if result == "healthy":
                self.stdout.write(self.style.SUCCESS("Cache health check PASSED"))
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Cache health check FAILED: Expected "healthy", got "{result}"',
                    ),
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cache health check FAILED: {e!s}"))

    def flush_all(self):
        """Flush all caches."""
        assert self.cache_backend is not None
        self.stdout.write(self.style.WARNING("WARNING: This will flush ALL caches!"))
        self.stdout.write("Are you sure you want to continue")

        # Use cache clear if available
        try:
            # Try to use cache.clear() which is safer
            self.cache_backend.clear()
            self.stdout.write(self.style.SUCCESS("All caches flushed successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to flush cache: {e}"))

    def flush_pattern(self, pattern):
        """Flush keys matching a pattern."""
        assert self.cache_backend is not None
        self.stdout.write(f"Flushing keys matching: {pattern}")

        try:
            # Use delete_pattern if available (Redis cache supports this)
            delete_pattern = getattr(self.cache_backend, "delete_pattern", None)
            if delete_pattern is not None:
                delete_pattern(pattern)
                self.stdout.write(
                    self.style.SUCCESS(f"Pattern '{pattern}' flushed successfully"),
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Cache backend does not support pattern deletion. "
                        "Use Redis cache backend for pattern-based flushing.",
                    ),
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to flush pattern: {e}"))
