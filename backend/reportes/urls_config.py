"""=============================================================================
URLS PARA CONFIGURACIÓN DEL SISTEMA
=============================================================================
"""

from django.urls import path

from .views_config import (
    configuracion_general,
    crear_backup,
    descargar_backup,
    eliminar_backup,
    horarios_atencion,
    listar_backups,
)

urlpatterns = [
    # Configuración General
    path("configuracion/general/", configuracion_general, name="config-general"),
    # Horarios de Atención
    path("configuracion/horarios/", horarios_atencion, name="config-horarios"),
    # Backups
    path("configuracion/backups/", listar_backups, name="listar-backups"),
    path("configuracion/backups/create/", crear_backup, name="crear-backup"),
    path(
        "configuracion/backups/<str:filename>/",
        descargar_backup,
        name="descargar-backup",
    ),
    path(
        "configuracion/backups/<str:filename>/delete/",
        eliminar_backup,
        name="eliminar-backup",
    ),
]
