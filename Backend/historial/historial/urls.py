from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pacientes.urls')),
    path('api/', include('embarazos.urls')),
    path('api/', include('controles.urls')),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/calculadoras/', include('calculadoras.urls')),
    # Nuevos módulos completos
    path('api/', include('ecografias.urls')),
    path('api/', include('laboratorio.urls')),
    path('api/', include('partos.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]