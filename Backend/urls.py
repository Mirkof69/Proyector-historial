"""Urls module."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# drf-spectacular for API documentation
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# JWT endpoints (SimpleJWT)
from rest_framework_simplejwt.views import TokenObtainPairView

# JWT via cookies httpOnly + CSRF (migración de seguridad)
from usuarios.auth_cookie_views import CookieTokenRefreshView, csrf_bootstrap_view

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check endpoint
    path("api/", include("monitoring.urls")),
    # JWT Authentication (SimpleJWT)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    # Refresh vía cookie httpOnly (acepta también body para clientes API)
    path("api/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    # Bootstrap de la cookie csrftoken para el frontend
    path("api/token/csrf/", csrf_bootstrap_view, name="csrf_bootstrap"),
    # =====================================================
    # API DOCUMENTATION (drf-spectacular)
    # =====================================================
    # OpenAPI 3.0 schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI (interactive API explorer)
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # ReDoc (clean documentation viewer)
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # APIs del proyecto
    path("api/pacientes/", include("pacientes.urls")),
    path("api/usuarios/", include("usuarios.urls")),
    path("api/embarazos/", include("embarazos.urls")),
    path("api/controles/", include("controles.urls")),
    path("api/ecografias/", include("ecografias.urls")),
    path("api/calculadoras/", include("calculadoras.urls")),
    path("api/laboratorios/", include("laboratorio.urls")),
    path("api/citas/", include("citas.urls")),
    path("api/partos/", include("partos.urls")),
    path("api/calculadoras-avanzadas/", include("calculadoras_avanzadas.urls")),
    path("api/reportes/", include("reportes.urls")),
    #  NUEVOS MÓDULOS
    path("api/antecedentes/", include("antecedentes.urls")),
    path("api/triaje/", include("triaje.urls")),
    path("api/consultorios/", include("consultorios.urls")),
    path("api/roles/", include("roles.urls")),
    path("api/evoluciones/", include("evoluciones.urls")),
    path("api/ecografias-archivos/", include("ecografias_archivos.urls")),
    path(
        "api/notas-evolucion/", include("notas_evolucion.urls"),
    ),  # ✅ Notas médicas de evolución
    path("api/vacunas/", include("vacunas.urls")),  # ✅ Control de vacunas
    path(
        "api/auditoria/", include("auditoria.urls"),
    ),  # ✅ Sistema de auditoría en tiempo real
    path("api/ia/", include("ia_medica.urls")),  #  Sistema de IA Médico con ML y NLP
    path("api/soporte/", include("soporte.urls")),  # Tickets de soporte tecnico
    # ✨ Dashboard Avanzado
    path("api/", include("notificaciones.urls")),  # ✅ Sistema de notificaciones
]


# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
