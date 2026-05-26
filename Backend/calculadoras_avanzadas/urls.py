"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Crear router para las APIs REST
router = DefaultRouter()
router.register(r"score-bishop", views.ScoreBishopViewSet, basename="score-bishop")
router.register(
    r"riesgo-preeclampsia",
    views.RiesgoPreeclampsiaViewSet,
    basename="riesgo-preeclampsia",
)
router.register(
    r"crecimiento-fetal", views.CrecimientoFetalViewSet, basename="crecimiento-fetal",
)
router.register(
    r"riesgo-cromosomico", views.RiesgoCromosomicoViewSet, basename="riesgo-cromosomico",
)
router.register(
    r"dosis-medicamentos", views.DosisMedicamentosViewSet, basename="dosis-medicamentos",
)
router.register(
    r"hemorragia-obstetrica",
    views.HemorragiaObstetricaViewSet,
    basename="hemorragia-obstetrica",
)
router.register(
    r"sufrimiento-fetal", views.SufrimientoFetalViewSet, basename="sufrimiento-fetal",
)

urlpatterns = [
    # APIs REST principales
    path("", include(router.urls)),
    # URLs adicionales para funcionalidades específicas de Score Bishop
    path(
        "score-bishop/estadisticas/",
        views.ScoreBishopViewSet.as_view({"get": "estadisticas"}),
        name="score-bishop-estadisticas",
    ),
    path(
        "score-bishop/calcular/",
        views.ScoreBishopViewSet.as_view({"post": "calcular_score"}),
        name="score-bishop-calcular",
    ),
    path(
        "score-bishop/por-paciente/",
        views.ScoreBishopViewSet.as_view({"get": "por_paciente"}),
        name="score-bishop-por-paciente",
    ),
    # URLs adicionales para Riesgo de Preeclampsia
    path(
        "riesgo-preeclampsia/estadisticas/",
        views.RiesgoPreeclampsiaViewSet.as_view({"get": "estadisticas"}),
        name="riesgo-preeclampsia-estadisticas",
    ),
    path(
        "riesgo-preeclampsia/alto-riesgo/",
        views.RiesgoPreeclampsiaViewSet.as_view({"get": "alto_riesgo"}),
        name="riesgo-preeclampsia-alto-riesgo",
    ),
    # URLs adicionales para Crecimiento Fetal
    path(
        "crecimiento-fetal/estadisticas/",
        views.CrecimientoFetalViewSet.as_view({"get": "estadisticas"}),
        name="crecimiento-fetal-estadisticas",
    ),
    path(
        "crecimiento-fetal/<int:pk>/seguimiento/",
        views.CrecimientoFetalViewSet.as_view({"get": "seguimiento_crecimiento"}),
        name="crecimiento-fetal-seguimiento",
    ),
    # URLs adicionales para Riesgo Cromosómico
    path(
        "riesgo-cromosomico/estadisticas/",
        views.RiesgoCromosomicoViewSet.as_view({"get": "estadisticas"}),
        name="riesgo-cromosomico-estadisticas",
    ),
    # URLs adicionales para Dosis de Medicamentos
    path(
        "dosis-medicamentos/por-medicamento/",
        views.DosisMedicamentosViewSet.as_view({"get": "por_medicamento"}),
        name="dosis-medicamentos-por-medicamento",
    ),
    path(
        "dosis-medicamentos/calcular/",
        views.DosisMedicamentosViewSet.as_view({"post": "calcular_dosis"}),
        name="dosis-medicamentos-calcular",
    ),
    # URLs adicionales para Hemorragia Obstétrica
    path(
        "hemorragia-obstetrica/estadisticas/",
        views.HemorragiaObstetricaViewSet.as_view({"get": "estadisticas"}),
        name="hemorragia-obstetrica-estadisticas",
    ),
    path(
        "hemorragia-obstetrica/casos-severos/",
        views.HemorragiaObstetricaViewSet.as_view({"get": "casos_severos"}),
        name="hemorragia-obstetrica-casos-severos",
    ),
    # URLs adicionales para Sufrimiento Fetal
    path(
        "sufrimiento-fetal/estadisticas/",
        views.SufrimientoFetalViewSet.as_view({"get": "estadisticas"}),
        name="sufrimiento-fetal-estadisticas",
    ),
    path(
        "sufrimiento-fetal/alertas/",
        views.SufrimientoFetalViewSet.as_view({"get": "alertas_activas"}),
        name="sufrimiento-fetal-alertas",
    ),
    path(
        "sufrimiento-fetal/por-tipo/",
        views.SufrimientoFetalViewSet.as_view({"get": "por_tipo_monitoreo"}),
        name="sufrimiento-fetal-por-tipo",
    ),
    # URLs para reportes específicos
    path(
        "reportes/score-bishop/<int:bishop_id>/",
        views.ScoreBishopViewSet.as_view({"get": "retrieve"}),
        name="reporte-score-bishop",
    ),
    path(
        "reportes/riesgo-preeclampsia/<int:riesgo_id>/",
        views.RiesgoPreeclampsiaViewSet.as_view({"get": "retrieve"}),
        name="reporte-riesgo-preeclampsia",
    ),
    path(
        "reportes/crecimiento-fetal/<int:crecimiento_id>/",
        views.CrecimientoFetalViewSet.as_view({"get": "retrieve"}),
        name="reporte-crecimiento-fetal",
    ),
    # URLs para búsquedas avanzadas
    path(
        "buscar/calculadoras-por-paciente/",
        views.ScoreBishopViewSet.as_view({"get": "list"}),
        name="buscar-calculadoras-paciente",
    ),
    path(
        "buscar/alertas-activas/",
        views.SufrimientoFetalViewSet.as_view({"get": "alertas_activas"}),
        name="buscar-alertas-activas",
    ),
]

# Configuración del app_name para namespacing
# app_name = 'calculadoras_avanzadas'  # Comentado temporalmente para diagnosticar
