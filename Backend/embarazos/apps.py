"""Apps module."""
from django.apps import AppConfig


class EmbarazosConfig(AppConfig):
    """Embarazosconfig"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "embarazos"

    def ready(self):
        """Conecta los signals del módulo.

        Sin este import los receivers de signals.py NO se registran: Django
        solo los conecta cuando el módulo se importa. Estuvieron muertos, y
        por eso los 177 embarazos de alto riesgo de la base no generaron ni
        una alerta. Mismo fallo que tuvo auditoria/apps.py.
        """
        from . import signals  # noqa: F401
