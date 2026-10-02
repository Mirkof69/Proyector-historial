"""URLs para módulo IA Médica — CNN + Consultas
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .webhook import dicom_webhook

from . import views_cardiotocografia, views_ginecologia, views_laboratorio, views_prediccion_peso

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
    # Modelo supervisado de peso al nacer (ia_medica/ml/servicio_peso.py)
    path("prediccion-peso/", views_prediccion_peso.prediccion_peso, name="prediccion-peso"),
    path("prediccion-peso/desempeno/", views_prediccion_peso.desempeno_prediccion_peso, name="prediccion-peso-desempeno"),
    # Clasificador supervisado de cardiotocografía (ia_medica/ml/cardiotocografia.py)
    path("cardiotocografia/", views_cardiotocografia.cardiotocografia, name="cardiotocografia"),
    # Ecografía ginecológica: lesión ovárica, mioma, ovario poliquístico (microservicio de IA)
    path("ginecologia/<str:tarea>/", views_ginecologia.analisis_ginecologico, name="analisis-ginecologico"),
    # Consulta IA NLP. ANTES del router: si va despues, la ruta de detalle
    # de ConsultaIAViewSet lo captura con pk="consultar" y el POST da 405.
    path("consultas/consultar/", views.consultar_ia, name="consultar_ia"),
    # ViewSets CNN + Consultas IA
    path("", include(router.urls)),
    # Webhook Orthanc — recibe eventos DICOM y encola análisis CNN
    path("dicom/webhook/", dicom_webhook, name="dicom_webhook"),
]
