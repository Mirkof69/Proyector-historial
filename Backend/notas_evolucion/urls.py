"""=============================================================================
URLS - NOTAS DE EVOLUCIÓN
=============================================================================
Configuración de rutas para el módulo de notas médicas de evolución
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotaEvolucionViewSet

# Crear el router
router = DefaultRouter()

# Registrar el ViewSet
router.register(r"", NotaEvolucionViewSet, basename="nota-evolucion")

# URLs disponibles:
# GET    /api/notas-evolucion/                          - Listar todas las notas
# POST   /api/notas-evolucion/                          - Crear nueva nota
# GET    /api/notas-evolucion/{id}/                     - Detalle de una nota
# PUT    /api/notas-evolucion/{id}/                     - Actualizar nota completa
# PATCH  /api/notas-evolucion/{id}/                     - Actualizar nota parcial
# DELETE /api/notas-evolucion/{id}/                     - Eliminar nota
# GET    /api/notas-evolucion/por-paciente/{id}/        - Notas de un paciente
# GET    /api/notas-evolucion/por-embarazo/{id}/        - Notas de un embarazo
# GET    /api/notas-evolucion/mis-notas/                - Notas del médico autenticado
# POST   /api/notas-evolucion/{id}/revisar/             - Marcar nota como revisada
# GET    /api/notas-evolucion/estadisticas/             - Estadísticas de notas

app_name = "notas_evolucion"

urlpatterns = [
    path("", include(router.urls)),
]
