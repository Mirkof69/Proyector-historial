"""Apps module."""
from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    """Auditoriaconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditoria"
    verbose_name = "Auditoría y Trazabilidad"

    def ready(self):
        """Importar signals cuando la app esté lista.

        El import estaba comentado y los receivers quedaban conectados SOLO
        como efecto colateral de que Django importara `auditoria.middleware`
        (que a su vez importa este módulo). Consecuencia: todo lo que no pasa
        por un request HTTP —comandos de management, workers, scripts, tests—
        corría con la auditoría literalmente desconectada, sin ningún error
        visible. Aquí es donde deben registrarse.

        Solo se importa el módulo: no se toca la base de datos, porque en
        `ready()` la BD puede no existir todavía (p. ej. durante `migrate`).
        """
        from . import signals  # noqa: F401
