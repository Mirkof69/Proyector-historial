# =============================================================================
# URLS DE USUARIOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: usuarios
# Descripción: Rutas completas para todas las funcionalidades de usuarios,
#              autenticación, perfiles, contraseñas y administración.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 - EXTENDIDO
# Última actualización: 2025-11-14
# =============================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    # Autenticación
    LoginView,
    LogoutView,

    # ViewSet
    UsuarioViewSet,

    # Contraseñas
    cambiar_password,
    solicitar_recuperacion_password,
    recuperar_password,
    restablecer_password_admin,

    # Verificación
    verificar_email,
    reenviar_verificacion_email,

    # Bloqueo/Desbloqueo
    bloquear_usuario,
    desbloquear_usuario,

    # Sesiones
    historial_sesiones,
    historial_sesiones_usuario,

    # Perfil
    perfil,

    # Activación
    activar_usuario,
    desactivar_usuario,

    # Registro
    registro_publico,

    # Búsqueda
    buscar_usuarios,
)

# =============================================================================
# ROUTER PARA VIEWSETS
# =============================================================================
router = DefaultRouter()
router.register(r'', UsuarioViewSet, basename='usuario')

# =============================================================================
# URL PATTERNS
# =============================================================================
urlpatterns = [
    # =========================================================================
    # AUTENTICACIÓN
    # =========================================================================
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('registro/', registro_publico, name='registro'),

    # =========================================================================
    # CONTRASEÑAS
    # =========================================================================
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
    path('solicitar-recuperacion-password/', solicitar_recuperacion_password, name='solicitar_recuperacion'),
    path('recuperar-password/', recuperar_password, name='recuperar_password'),
    path('restablecer-password-admin/', restablecer_password_admin, name='restablecer_password_admin'),

    # =========================================================================
    # VERIFICACIÓN DE EMAIL
    # =========================================================================
    path('verificar-email/', verificar_email, name='verificar_email'),
    path('reenviar-verificacion/', reenviar_verificacion_email, name='reenviar_verificacion'),

    # =========================================================================
    # BLOQUEO Y DESBLOQUEO
    # =========================================================================
    path('bloquear/', bloquear_usuario, name='bloquear_usuario'),
    path('desbloquear/', desbloquear_usuario, name='desbloquear_usuario'),

    # =========================================================================
    # HISTORIAL DE SESIONES
    # =========================================================================
    path('historial-sesiones/', historial_sesiones, name='historial_sesiones'),
    path('<int:usuario_id>/historial-sesiones/', historial_sesiones_usuario, name='historial_sesiones_usuario'),

    # =========================================================================
    # PERFIL
    # =========================================================================
    path('perfil/', perfil, name='perfil'),

    # =========================================================================
    # ACTIVACIÓN/DESACTIVACIÓN
    # =========================================================================
    path('<int:usuario_id>/activar/', activar_usuario, name='activar_usuario'),
    path('<int:usuario_id>/desactivar/', desactivar_usuario, name='desactivar_usuario'),

    # =========================================================================
    # BÚSQUEDA
    # =========================================================================
    path('buscar/', buscar_usuarios, name='buscar_usuarios'),

    # =========================================================================
    # VIEWSET ROUTES
    # =========================================================================
    # Incluye todas las rutas del ViewSet:
    # - GET    /api/usuarios/              - Listar usuarios
    # - POST   /api/usuarios/              - Crear usuario
    # - GET    /api/usuarios/{id}/         - Detalle usuario
    # - PUT    /api/usuarios/{id}/         - Actualizar usuario completo
    # - PATCH  /api/usuarios/{id}/         - Actualizar usuario parcial
    # - DELETE /api/usuarios/{id}/         - Eliminar usuario (soft delete)
    # - GET    /api/usuarios/me/           - Perfil del usuario actual
    # - GET    /api/usuarios/medicos/      - Listar médicos
    # - GET    /api/usuarios/enfermeros/   - Listar enfermeros
    # - GET    /api/usuarios/estadisticas/ - Estadísticas de usuarios
    path('', include(router.urls)),
]

# =============================================================================
# DOCUMENTACIÓN DE ENDPOINTS
# =============================================================================
"""
ENDPOINTS DISPONIBLES:

AUTENTICACIÓN:
--------------
POST   /api/usuarios/login/                       - Iniciar sesión
POST   /api/usuarios/logout/                      - Cerrar sesión
POST   /api/usuarios/token/refresh/               - Refrescar token JWT
POST   /api/usuarios/registro/                    - Registro público (pacientes)

CONTRASEÑAS:
------------
POST   /api/usuarios/cambiar-password/            - Cambiar contraseña
POST   /api/usuarios/solicitar-recuperacion-password/ - Solicitar recuperación
POST   /api/usuarios/recuperar-password/          - Recuperar con token
POST   /api/usuarios/restablecer-password-admin/  - Restablecer (admin)

VERIFICACIÓN:
-------------
POST   /api/usuarios/verificar-email/             - Verificar email con token
POST   /api/usuarios/reenviar-verificacion/       - Reenviar email verificación

GESTIÓN DE USUARIOS (CRUD):
---------------------------
GET    /api/usuarios/                             - Listar usuarios
POST   /api/usuarios/                             - Crear usuario (admin)
GET    /api/usuarios/{id}/                        - Detalle de usuario
PUT    /api/usuarios/{id}/                        - Actualizar completo
PATCH  /api/usuarios/{id}/                        - Actualizar parcial
DELETE /api/usuarios/{id}/                        - Eliminar (soft delete)

PERFIL:
-------
GET    /api/usuarios/perfil/                      - Obtener perfil actual
PUT    /api/usuarios/perfil/                      - Actualizar perfil
PATCH  /api/usuarios/perfil/                      - Actualizar perfil parcial
GET    /api/usuarios/me/                          - Alias de perfil

BLOQUEO/DESBLOQUEO:
-------------------
POST   /api/usuarios/bloquear/                    - Bloquear usuario (admin)
POST   /api/usuarios/desbloquear/                 - Desbloquear usuario (admin)

ACTIVACIÓN/DESACTIVACIÓN:
-------------------------
POST   /api/usuarios/{id}/activar/                - Activar usuario (admin)
POST   /api/usuarios/{id}/desactivar/             - Desactivar usuario (admin)

HISTORIAL:
----------
GET    /api/usuarios/historial-sesiones/         - Historial de sesiones
GET    /api/usuarios/{id}/historial-sesiones/    - Historial de usuario (admin)

LISTADOS ESPECÍFICOS:
---------------------
GET    /api/usuarios/medicos/                     - Listar solo médicos
GET    /api/usuarios/enfermeros/                  - Listar solo enfermeros

ESTADÍSTICAS:
-------------
GET    /api/usuarios/estadisticas/                - Estadísticas generales (admin)

BÚSQUEDA:
---------
GET    /api/usuarios/buscar/?q={query}            - Búsqueda avanzada

FILTROS DISPONIBLES (en listado):
----------------------------------
- rol: Filtrar por rol (medico, enfermero, paciente, etc.)
- estado: Filtrar por estado (activo, inactivo, bloqueado, etc.)
- especialidad: Filtrar por especialidad médica
- activo: Filtrar por activo/inactivo (true/false)
- buscar: Búsqueda de texto libre

Ejemplo:
GET /api/usuarios/?rol=medico&activo=true&especialidad=obstetricia
"""

# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
