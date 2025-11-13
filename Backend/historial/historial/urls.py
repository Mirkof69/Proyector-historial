from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticación JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # APIs del proyecto
    path('api/pacientes/', include('pacientes.urls')),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/embarazos/', include('embarazos.urls')),
    path('api/controles/', include('controles.urls')),
    path('api/ecografias/', include('ecografias.urls')),
    path('api/calculadoras/', include('calculadoras.urls')),
    path('api/laboratorio/', include('laboratorio.urls')),
    path('api/citas/', include('citas.urls')),
    path('api/partos/', include('partos.urls')),
    path('api/calculadoras-avanzadas/', include('calculadoras_avanzadas.urls')),
]

# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)