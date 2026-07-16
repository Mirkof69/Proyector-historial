"""CONSULTORIOS - URLS"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConsultorioViewSet

# Sin prefijo: historial/urls.py ya monta esto bajo "api/consultorios/".
# Con el prefijo duplicado, el frontend (que llama /api/consultorios/) recibía
# el API-root del router en vez del listado, y las acciones daban 404.
router = DefaultRouter()
router.register(r"", ConsultorioViewSet, basename="consultorio")

urlpatterns = [path("", include(router.urls))]
