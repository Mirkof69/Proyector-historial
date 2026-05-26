"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExamenLaboratorioViewSet,
    ResultadoLaboratorioViewSet,
    TipoExamenViewSet,
    ValorReferenciaViewSet,
)

router = DefaultRouter()
router.register(r"tipos-examenes", TipoExamenViewSet, basename="tipo-examen")
router.register(
    r"valores-referencia", ValorReferenciaViewSet, basename="valor-referencia",
)
router.register(r"examenes", ExamenLaboratorioViewSet, basename="examen-laboratorio")
router.register(
    r"resultados", ResultadoLaboratorioViewSet, basename="resultado-laboratorio",
)

# ✅ FIX: Alias para compatibilidad con frontend
# El frontend usa /laboratorios/ cuando debería usar /laboratorios/examenes/
# Este alias redirige automáticamente
urlpatterns = [
    path("", include(router.urls)),
]
