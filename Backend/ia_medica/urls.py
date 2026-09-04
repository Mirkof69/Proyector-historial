"""URLs para módulo IA Médica — CNN + Consultas
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .webhook import dicom_webhook

from . import views_laboratorio

app_name = "ia_medica"

router = DefaultRouter()
router.register(
    r"imagenes", views.ImagenEcograficaViewSet, basename="imagen-ecografica",
)
router.register(r"modelos-cnn", views.ModeloCNNConfigViewSet, basename="modelo-cnn")
router.register(r"consultas", views.ConsultaIAViewSet, basename="consulta-ia")

urlpatterns = [
    # Interpretacion de laboratorio con los rangos propios del embarazo. El
    # servicio (ia_medica/services/ml_laboratorio_service.py) tenia 481
    # lineas que ningun modulo importaba.
    path(
        "laboratorio/analizar/",
        views_laboratorio.analizar_laboratorio,
        name="analizar-laboratorio",
    ),
    # ViewSets CNN + Consultas IA
    path("", include(router.urls)),
    # Consulta IA NLP — gateway al microservicio (mantener compatibilidad)
    path("consultas/consultar/", views.consultar_ia, name="consultar_ia"),
    # Webhook Orthanc — recibe eventos DICOM y encola análisis CNN
    path("dicom/webhook/", dicom_webhook, name="dicom_webhook"),
]
