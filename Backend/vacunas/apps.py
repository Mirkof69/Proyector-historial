"""Configuración de la aplicación Vacunas
"""

from django.apps import AppConfig


class VacunasConfig(AppConfig):
    """Configuración de la aplicación Vacunas
    Gestiona vacunas y registros de vacunación para pacientes embarazadas
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "vacunas"
    verbose_name = "Vacunas"

    def ready(self):
        """Configuración al iniciar la aplicación
        """
