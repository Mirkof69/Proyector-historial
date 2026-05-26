"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .ai_views import (
    ai_result_callback,
    ai_service_health,
    analyze_ultrasound_with_ai,
    classify_ultrasound,
    detect_anomalies,
)
from .views import EcografiaViewSet

router = DefaultRouter()
router.register(r"", EcografiaViewSet, basename="ecografia")

urlpatterns = [
    path("", include(router.urls)),
    # Endpoints de IA — análisis síncrono (directo al microservicio)
    path("analyze-with-ai/", analyze_ultrasound_with_ai, name="analyze-with-ai"),
    path("classify/", classify_ultrasound, name="classify-ultrasound"),
    path("detect-anomalies/", detect_anomalies, name="detect-anomalies"),
    path("ai/health/", ai_service_health, name="ai-health"),
    # Callback receptor del Microservicio IA (flujo asíncrono via RabbitMQ)
    # Solo accesible desde red interna Docker — NO expuesto por Kong
    path("<str:ecografia_id>/ai-result/", ai_result_callback, name="ai-result-callback"),
]
