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
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]