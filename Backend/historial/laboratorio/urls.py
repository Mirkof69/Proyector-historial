from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoExamenViewSet,
    ValorReferenciaViewSet,
    ExamenLaboratorioViewSet,
    ResultadoLaboratorioViewSet,
)

router = DefaultRouter()
router.register(r'tipos-examenes', TipoExamenViewSet, basename='tipo-examen')
router.register(r'valores-referencia', ValorReferenciaViewSet, basename='valor-referencia')
router.register(r'examenes', ExamenLaboratorioViewSet, basename='examen-laboratorio')
router.register(r'resultados', ResultadoLaboratorioViewSet, basename='resultado-laboratorio')

urlpatterns = [
    path('', include(router.urls)),
]