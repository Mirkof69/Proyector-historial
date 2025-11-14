"""
URLs para el módulo de calculadoras obstétricas.
Expone todos los endpoints de las 15 calculadoras FMF.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CalculadorasViewSet

# Router para ViewSet de calculadoras
router = DefaultRouter()
router.register(r'', CalculadorasViewSet, basename='calculadoras')

urlpatterns = [
    path('', include(router.urls)),
]

# Endpoints disponibles automáticamente:
# POST /api/calculadoras/preeclampsia/
# POST /api/calculadoras/trisomias/
# POST /api/calculadoras/sga/
# POST /api/calculadoras/diabetes_gestacional/
# POST /api/calculadoras/parto_pretermino/
# POST /api/calculadoras/peso_fetal/
# POST /api/calculadoras/crecimiento_fetal/
# POST /api/calculadoras/translucencia_nucal/
# POST /api/calculadoras/doppler_fetal/
# POST /api/calculadoras/ip_uterinas/
# POST /api/calculadoras/presion_arterial_media/
# POST /api/calculadoras/biomarcadores/
# POST /api/calculadoras/indice_shock/
# POST /api/calculadoras/test_no_estresante/
# GET  /api/calculadoras/lista/