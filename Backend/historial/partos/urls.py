# =============================================================================
# URLs DE PARTOS
# =============================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartoViewSet

router = DefaultRouter()
router.register(r'partos', PartoViewSet, basename='parto')

urlpatterns = [
    path('', include(router.urls)),
]

"""
ENDPOINTS DISPONIBLES:

1. LISTAR PARTOS
   GET /api/partos/
   Query params: page, page_size, search, ordering, embarazo_id, paciente_id, tipo, 
                 fecha_desde, fecha_hasta, con_complicaciones

2. CREAR PARTO
   POST /api/partos/
   Body: embarazo, paciente, fecha_hora_parto, tipo_parto, etc.

3. OBTENER DETALLE
   GET /api/partos/{id}/

4. ACTUALIZAR PARTO
   PUT /api/partos/{id}/
   PATCH /api/partos/{id}/

5. ELIMINAR PARTO
   DELETE /api/partos/{id}/

6. PARTOS POR PACIENTE
   GET /api/partos/por-paciente/{paciente_id}/

7. ESTADÍSTICAS
   GET /api/partos/estadisticas/

8. PARTOS CON COMPLICACIONES
   GET /api/partos/con_complicaciones/
"""
