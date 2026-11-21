"""=============================================================================
URLS - CALCULADORAS MÉDICAS FMF Y LABORATORIO CLÍNICO
=============================================================================
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# IMPORTANTE: CalculadoraRiesgoViewSet se registra en la raiz (r""), lo que
# genera una ruta de detalle catch-all "^(?P<pk>[^/.]+)/$" que intercepta
# CUALQUIER ruta de un solo segmento registrada despues (ej. "historial/"
# se interpretaba como pk="historial" de CalculadoraRiesgo, dando 404/405).
# Por eso todo lo demas se registra ANTES que la raiz.

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

# Historial de calculadoras simples (Edad Gestacional, Bishop, IMC, etc.)
router.register(r"historial", views.CalculoHistorialViewSet, basename="calculo-historial")

# Calculadoras FMF (raiz) — debe registrarse AL FINAL (ver nota arriba)
router.register(r"", views.CalculadoraRiesgoViewSet, basename="calculadora-riesgo")

urlpatterns = [
    path("", include(router.urls)),
]
