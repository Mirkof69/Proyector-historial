"""
===========================================
MÓDULO: URLs DE USUARIOS
===========================================
Descripción:
    Configuración de rutas (endpoints) para el módulo de usuarios.
    Define todas las URLs disponibles para gestión de usuarios y autenticación.

Rutas principales:
    Autenticación:
        POST   /api/usuarios/login/          - Iniciar sesión (JWT)
        POST   /api/usuarios/logout/         - Cerrar sesión
        POST   /api/usuarios/register/       - Registro público

    CRUD de usuarios (ViewSet):
        GET    /api/usuarios/                - Listar usuarios (paginado)
        POST   /api/usuarios/                - Crear usuario
        GET    /api/usuarios/{id}/           - Obtener usuario
        PUT    /api/usuarios/{id}/           - Actualizar usuario completo
        PATCH  /api/usuarios/{id}/           - Actualizar usuario parcial
        DELETE /api/usuarios/{id}/           - Desactivar usuario

    Acciones personalizadas (ViewSet):
        POST   /api/usuarios/{id}/activar/         - Activar usuario
        POST   /api/usuarios/{id}/desactivar/      - Desactivar usuario
        POST   /api/usuarios/{id}/suspender/       - Suspender usuario
        POST   /api/usuarios/{id}/bloquear/        - Bloquear usuario
        POST   /api/usuarios/{id}/desbloquear/     - Desbloquear usuario
        POST   /api/usuarios/{id}/cambiar_password/ - Cambiar contraseña

        GET    /api/usuarios/me/                   - Obtener perfil propio
        PUT    /api/usuarios/me/                   - Actualizar perfil propio
        PATCH  /api/usuarios/me/                   - Actualizar perfil parcial

        GET    /api/usuarios/estadisticas/         - Estadísticas generales
        GET    /api/usuarios/busqueda_avanzada/    - Búsqueda avanzada

Funcionamiento del Router:
    - El Router de DRF genera automáticamente las rutas del ViewSet
    - Las rutas con {id} requieren autenticación por defecto
    - Las acciones @action se registran automáticamente
    - detail=True crea rutas con /{id}/
    - detail=False crea rutas sin /{id}/

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    LogoutView,
    RegisterView,
    UsuarioViewSet
)


# ===========================================
# CONFIGURACIÓN DEL ROUTER
# ===========================================
"""
ROUTER: Configuración automática de rutas para ViewSets

Funcionamiento:
    1. Se crea un DefaultRouter que maneja automáticamente las rutas RESTful
    2. Se registra el UsuarioViewSet con el basename 'usuarios'
    3. El router genera automáticamente estas rutas:

       - GET    /usuarios/                -> list()
       - POST   /usuarios/                -> create()
       - GET    /usuarios/{id}/           -> retrieve()
       - PUT    /usuarios/{id}/           -> update()
       - PATCH  /usuarios/{id}/           -> partial_update()
       - DELETE /usuarios/{id}/           -> destroy()

    4. También registra las acciones @action del ViewSet:

       - POST   /usuarios/{id}/activar/           -> activar()
       - POST   /usuarios/{id}/desactivar/        -> desactivar()
       - POST   /usuarios/{id}/suspender/         -> suspender()
       - POST   /usuarios/{id}/bloquear/          -> bloquear()
       - POST   /usuarios/{id}/desbloquear/       -> desbloquear()
       - POST   /usuarios/{id}/cambiar_password/  -> cambiar_password()
       - GET    /usuarios/me/                     -> me()
       - PUT    /usuarios/me/                     -> me()
       - PATCH  /usuarios/me/                     -> me()
       - GET    /usuarios/estadisticas/           -> estadisticas()
       - GET    /usuarios/busqueda_avanzada/      -> busqueda_avanzada()

Parámetros:
    - basename='usuarios': Prefijo para los nombres de las rutas
    - trailing_slash=True: Agrega / al final de las URLs (por defecto)
"""

# Crear instancia del router
# Funcionamiento: DefaultRouter proporciona navegación automática en la API
router = DefaultRouter()

# Registrar el ViewSet de usuarios
# Funcionamiento:
#   1. Toma todas las acciones del UsuarioViewSet
#   2. Genera URLs automáticamente para cada acción
#   3. Mapea los métodos HTTP a las acciones del ViewSet
#   4. Configura los permisos según lo definido en el ViewSet
router.register(
    r'',  # Prefijo vacío porque ya está en 'api/usuarios/'
    UsuarioViewSet,
    basename='usuarios'
)


# ===========================================
# RUTAS PERSONALIZADAS (fuera del ViewSet)
# ===========================================
"""
RUTAS ADICIONALES: Endpoints que no pertenecen al ViewSet

Estas rutas se definen manualmente porque son vistas independientes
que no siguen el patrón CRUD estándar del ViewSet.

Funcionamiento:
    - path(): Define una ruta individual
    - .as_view(): Convierte la clase APIView en una vista callable
    - name='': Nombre de la ruta para uso con reverse() y url tags
"""

urlpatterns = [
    # ===========================================
    # AUTENTICACIÓN
    # ===========================================

    # Ruta: LOGIN
    # Funcionamiento:
    #   - Recibe email y password
    #   - Valida credenciales
    #   - Retorna tokens JWT (access y refresh)
    # Acceso: Público (AllowAny)
    # Vista: LoginView
    path(
        'login/',
        LoginView.as_view(),
        name='usuarios-login'
    ),

    # Ruta: LOGOUT
    # Funcionamiento:
    #   - Recibe refresh token
    #   - Lo agrega a la blacklist
    #   - Invalida la sesión
    # Acceso: Requiere autenticación
    # Vista: LogoutView
    path(
        'logout/',
        LogoutView.as_view(),
        name='usuarios-logout'
    ),

    # Ruta: REGISTRO PÚBLICO
    # Funcionamiento:
    #   - Permite auto-registro de nuevos usuarios
    #   - Crea usuario con estado 'inactivo'
    #   - Requiere aprobación de administrador
    # Acceso: Público (AllowAny)
    # Vista: RegisterView
    path(
        'register/',
        RegisterView.as_view(),
        name='usuarios-register'
    ),

    # ===========================================
    # RUTAS DEL VIEWSET (auto-generadas)
    # ===========================================

    # Incluir todas las rutas generadas por el router
    # Funcionamiento:
    #   - router.urls contiene todas las rutas del ViewSet
    #   - Se incluyen en urlpatterns usando include()
    #   - Esto agrega las rutas CRUD y las acciones personalizadas
    path(
        '',
        include(router.urls)
    ),
]


"""
RESUMEN DE TODAS LAS RUTAS DISPONIBLES:
=======================================

AUTENTICACIÓN (Público):
    POST   /api/usuarios/login/          -> LoginView.post()
    POST   /api/usuarios/logout/         -> LogoutView.post()
    POST   /api/usuarios/register/       -> RegisterView.post()

CRUD DE USUARIOS (Requiere autenticación):
    GET    /api/usuarios/                -> UsuarioViewSet.list()
    POST   /api/usuarios/                -> UsuarioViewSet.create()
    GET    /api/usuarios/{id}/           -> UsuarioViewSet.retrieve()
    PUT    /api/usuarios/{id}/           -> UsuarioViewSet.update()
    PATCH  /api/usuarios/{id}/           -> UsuarioViewSet.partial_update()
    DELETE /api/usuarios/{id}/           -> UsuarioViewSet.destroy()

GESTIÓN DE ESTADO (Requiere autenticación):
    POST   /api/usuarios/{id}/activar/         -> UsuarioViewSet.activar()
    POST   /api/usuarios/{id}/desactivar/      -> UsuarioViewSet.desactivar()
    POST   /api/usuarios/{id}/suspender/       -> UsuarioViewSet.suspender()
    POST   /api/usuarios/{id}/bloquear/        -> UsuarioViewSet.bloquear()
    POST   /api/usuarios/{id}/desbloquear/     -> UsuarioViewSet.desbloquear()

GESTIÓN DE CONTRASEÑA (Requiere autenticación):
    POST   /api/usuarios/{id}/cambiar_password/ -> UsuarioViewSet.cambiar_password()

PERFIL PROPIO (Requiere autenticación):
    GET    /api/usuarios/me/                   -> UsuarioViewSet.me() [GET]
    PUT    /api/usuarios/me/                   -> UsuarioViewSet.me() [PUT]
    PATCH  /api/usuarios/me/                   -> UsuarioViewSet.me() [PATCH]

CONSULTAS Y ESTADÍSTICAS (Requiere autenticación):
    GET    /api/usuarios/estadisticas/         -> UsuarioViewSet.estadisticas()
    GET    /api/usuarios/busqueda_avanzada/    -> UsuarioViewSet.busqueda_avanzada()

=======================================
Total de endpoints: 20+
Todos documentados y funcionando con la base de datos existente
=======================================
"""
