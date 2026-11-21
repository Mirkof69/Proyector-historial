"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, views_fmf

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
    # Modelo bayesiano de la Fetal Medicine Foundation. El servicio
    # (calculadoras/services/calculador_riesgos_fmf.py) llevaba 543 lineas
    # escritas sin que ninguna pantalla pudiera llegar a el.
    path(
        "fmf/preeclampsia/",
        views_fmf.riesgo_preeclampsia_fmf,
        name="fmf-preeclampsia",
    ),
    path(
        "fmf/trisomias/",
        views_fmf.riesgo_trisomias_fmf,
        name="fmf-trisomias",
    ),
    # Aquí había 16 alias a mano de acciones que el router ya expone
    # (score-bishop/estadisticas/, sufrimiento-fetal/alertas_activas/...).
    # Cuatro nunca llegaban a su vista porque la ruta de detalle del router
    # los captaba como pk («calcular», «alertas»), y los de reportes/ pasaban
    # bishop_id a retrieve(), que espera pk: daban 500. Nadie los usaba.
]

app_name = 'calculadoras_avanzadas'
