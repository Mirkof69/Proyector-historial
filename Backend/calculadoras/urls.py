"""=============================================================================
URLS - CALCULADORAS MÉDICAS FMF Y LABORATORIO CLÍNICO
=============================================================================
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Calculadoras FMF
router.register(r"", views.CalculadoraRiesgoViewSet, basename="calculadora-riesgo")

# Laboratorio Clínico
router.register(r"hemogramas", views.HemogramaViewSet, basename="hemograma")
router.register(r"bioquimicas", views.BioquimicaViewSet, basename="bioquimica")
router.register(
    r"marcadores-embarazo", views.MarcadorEmbarazoViewSet, basename="marcador-embarazo",
)

# Doppler Materno
if views.DopplerMaterno is not None:
    router.register(
        r"doppler-materno", views.DopplerMaternoViewSet, basename="doppler-materno",
    )

urlpatterns = [
    path("", include(router.urls)),
]
