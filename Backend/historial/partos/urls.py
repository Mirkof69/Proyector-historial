from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Crear router para las APIs REST
router = DefaultRouter()
router.register(r'partos', views.PartoViewSet, basename='parto')
router.register(r'recien-nacidos', views.RecienNacidoViewSet, basename='recien-nacido')
router.register(r'partograma', views.PartogramaRegistroViewSet, basename='partograma')

urlpatterns = [
    # APIs REST principales
    path('api/', include(router.urls)),
    
    # URLs adicionales para funcionalidades específicas
    path('api/partos/estadisticas/', views.PartoViewSet.as_view({'get': 'estadisticas'}), name='partos-estadisticas'),
    path('api/partos/hoy/', views.PartoViewSet.as_view({'get': 'partos_hoy'}), name='partos-hoy'),
    path('api/recien-nacidos/estadisticas/', views.RecienNacidoViewSet.as_view({'get': 'estadisticas'}), name='rn-estadisticas'),
    path('api/partograma/alertas/', views.PartogramaRegistroViewSet.as_view({'get': 'alertas_activas'}), name='partograma-alertas'),
    
    # URLs para reportes específicos
    path('reportes/parto/<int:parto_id>/', views.PartoViewSet.as_view({'get': 'resumen_completo'}), name='reporte-parto'),
    path('reportes/recien-nacido/<int:rn_id>/', views.RecienNacidoViewSet.as_view({'get': 'resumen_completo'}), name='reporte-rn'),
    
    # URLs para búsquedas avanzadas
    path('buscar/partos-por-fecha/', views.PartoViewSet.as_view({'get': 'list'}), name='buscar-partos-fecha'),
    path('buscar/rn-por-peso/', views.RecienNacidoViewSet.as_view({'get': 'list'}), name='buscar-rn-peso'),
]

# Configuración del app_name para namespacing
app_name = 'partos'