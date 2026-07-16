"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Crear router para las APIs REST
router = DefaultRouter()
# ✅ FIX: No usar prefijo 'partos' porque ya está en historial/urls.py
router.register(r"", views.PartoViewSet, basename="parto")
router.register(r"recien-nacidos", views.RecienNacidoViewSet, basename="recien-nacido")
router.register(r"partograma", views.PartogramaRegistroViewSet, basename="partograma")
router.register(
    r"complicaciones", views.ComplicacionPartoViewSet, basename="complicacion-parto",
)
router.register(
    r"apgar-detallado", views.ApgarScoreDetalladoViewSet, basename="apgar-detallado",
)

urlpatterns = [
    # APIs REST principales - ✅ FIX: Incluir directamente sin 'api/' adicional
    path("", include(router.urls)),
    # URLs adicionales para funcionalidades específicas
    path(
        "estadisticas/",
        views.PartoViewSet.as_view({"get": "estadisticas_generales"}),
        name="partos-estadisticas",
    ),
    path(
        "hoy/",
        views.PartoViewSet.as_view({"get": "partos_recientes"}),
        name="partos-hoy",
    ),
    path(
        "recien-nacidos/estadisticas/",
        views.RecienNacidoViewSet.as_view({"get": "estadisticas_generales"}),
        name="rn-estadisticas",
    ),
    path(
        "partograma/alertas/",
        views.PartogramaRegistroViewSet.as_view({"get": "con_alertas"}),
        name="partograma-alertas",
    ),
    # URLs para reportes específicos
    path(
        "reportes/parto/<int:parto_id>/",
        views.PartoViewSet.as_view({"get": "resumen_completo"}),
        name="reporte-parto",
    ),
    path(
        "reportes/recien-nacido/<int:rn_id>/",
        views.RecienNacidoViewSet.as_view({"get": "resumen_completo"}),
        name="reporte-rn",
    ),
    # URLs para búsquedas avanzadas
    path(
        "analizar-paciente/<int:paciente_id>/",
        views.PartoViewSet.as_view({"get": "analizar_paciente"}),
        name="parto-analizar-paciente-path",
    ),
    path(
        "buscar/partos-por-fecha/",
        views.PartoViewSet.as_view({"get": "list"}),
        name="buscar-partos-fecha",
    ),
    path(
        "buscar/rn-por-peso/",
        views.RecienNacidoViewSet.as_view({"get": "list"}),
        name="buscar-rn-peso",
    ),
]

# Configuración del app_name para namespacing
app_name = "partos"
