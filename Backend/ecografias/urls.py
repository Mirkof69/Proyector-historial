"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .ai_views import (
    ai_result_callback,
    ai_service_health,
    analyze_ultrasound_with_ai,
    classify_ultrasound,
    crear_ecografia_desde_ia,
    detect_anomalies,
)
from .views import EcografiaViewSet

router = DefaultRouter()
router.register(r"", EcografiaViewSet, basename="ecografia")

urlpatterns = [
    # Endpoints de IA — deben ir ANTES del router para evitar que DefaultRouter
    # capture "analyze-with-ai", "classify", "detect-anomalies", "ai/health"
    # como si fueran un {pk} del detail view (lo que causaria 405 en POST).
    path("analyze-with-ai/", analyze_ultrasound_with_ai, name="analyze-with-ai"),
    path("crear-desde-ia/", crear_ecografia_desde_ia, name="crear-desde-ia"),
    path("classify/", classify_ultrasound, name="classify-ultrasound"),
    path("detect-anomalies/", detect_anomalies, name="detect-anomalies"),
    path("ai/health/", ai_service_health, name="ai-health"),
    # Callback receptor del Microservicio IA (flujo asíncrono via RabbitMQ)
    # Solo accesible desde red interna Docker — NO expuesto por Kong
    path("<str:ecografia_id>/ai-result/", ai_result_callback, name="ai-result-callback"),
    # Router — debe ir DESPUES de los paths fijos para evitar colisión de rutas
    path("", include(router.urls)),
]
