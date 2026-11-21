"""=============================================================================
ANTECEDENTES - URLS
=============================================================================
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AntecedenteGinecoObstetricoViewSet, AntecedentePatologicoViewSet

router = DefaultRouter()
router.register(
    r"gineco-obstetricos",
    AntecedenteGinecoObstetricoViewSet,
    basename="antecedente-gineco",
)
router.register(
    r"patologicos", AntecedentePatologicoViewSet, basename="antecedente-patologico",
)

urlpatterns = [
    path("", include(router.urls)),
]
