"""
===========================================
MÓDULO: URLs DE EMBARAZOS
===========================================
Descripción:
    Configuración de rutas (endpoints) para el módulo de embarazos.
    Define todas las URLs disponibles para gestión de embarazos.

Rutas principales:
    CRUD básico:
        GET    /api/embarazos/                - Listar embarazos (paginado)
        POST   /api/embarazos/                - Crear embarazo
        GET    /api/embarazos/{id}/           - Obtener embarazo específico
        PUT    /api/embarazos/{id}/           - Actualizar embarazo completo
        PATCH  /api/embarazos/{id}/           - Actualizar embarazo parcial
        DELETE /api/embarazos/{id}/           - Finalizar embarazo

    Gestión de estado:
        POST   /api/embarazos/{id}/cambiar_estado/     - Cambiar estado
        POST   /api/embarazos/{id}/finalizar/          - Finalizar embarazo
        POST   /api/embarazos/{id}/marcar_perdida/     - Marcar como pérdida
        POST   /api/embarazos/{id}/reactivar/          - Reactivar embarazo

    Información y cálculos:
        GET    /api/embarazos/{id}/historial_completo/     - Historial completo
        GET    /api/embarazos/{id}/calculos_obstetricos/   - Cálculos obstétricos
        GET    /api/embarazos/{id}/proximos_controles/     - Próximos controles
        GET    /api/embarazos/{id}/curva_crecimiento/      - Curva de crecimiento
        GET    /api/embarazos/{id}/riesgos/                - Evaluación de riesgos

    Consultas especializadas:
        GET    /api/embarazos/estadisticas/           - Estadísticas generales
        GET    /api/embarazos/busqueda_avanzada/      - Búsqueda avanzada
        GET    /api/embarazos/por_paciente/{id}/      - Por paciente
        GET    /api/embarazos/activos/                - Solo activos
        GET    /api/embarazos/alto_riesgo/            - Alto riesgo
        GET    /api/embarazos/proximos_partos/        - Partos próximos

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
from .views import EmbarazoViewSet


# ===========================================
# CONFIGURACIÓN DEL ROUTER
# ===========================================
"""
ROUTER: Configuración automática de rutas para ViewSets

Funcionamiento:
    1. Se crea un DefaultRouter que maneja automáticamente las rutas RESTful
    2. Se registra el EmbarazoViewSet con el basename 'embarazos'
    3. El router genera automáticamente estas rutas:

       CRUD Básico:
       - GET    /                -> list()
       - POST   /                -> create()
       - GET    /{id}/           -> retrieve()
       - PUT    /{id}/           -> update()
       - PATCH  /{id}/           -> partial_update()
       - DELETE /{id}/           -> destroy()

    4. También registra las acciones @action del ViewSet:

       Gestión de Estado:
       - POST   /{id}/cambiar_estado/     -> cambiar_estado()
       - POST   /{id}/finalizar/          -> finalizar()
       - POST   /{id}/marcar_perdida/     -> marcar_perdida()
       - POST   /{id}/reactivar/          -> reactivar()

       Información y Cálculos:
       - GET    /{id}/historial_completo/     -> historial_completo()
       - GET    /{id}/calculos_obstetricos/   -> calculos_obstetricos()
       - GET    /{id}/proximos_controles/     -> proximos_controles()
       - GET    /{id}/curva_crecimiento/      -> curva_crecimiento()
       - GET    /{id}/riesgos/                -> riesgos()

       Consultas Especializadas:
       - GET    /estadisticas/           -> estadisticas()
       - GET    /busqueda_avanzada/      -> busqueda_avanzada()
       - GET    /por_paciente/{id}/      -> por_paciente()
       - GET    /activos/                -> activos()
       - GET    /alto_riesgo/            -> alto_riesgo()
       - GET    /proximos_partos/        -> proximos_partos()

Parámetros:
    - basename='embarazos': Prefijo para los nombres de las rutas
    - trailing_slash=True: Agrega / al final de las URLs (por defecto)
"""

# Crear instancia del router
# Funcionamiento: DefaultRouter proporciona navegación automática en la API
router = DefaultRouter()

# Registrar el ViewSet de embarazos
# Funcionamiento:
#   1. Toma todas las acciones del EmbarazoViewSet
#   2. Genera URLs automáticamente para cada acción
#   3. Mapea los métodos HTTP a las acciones del ViewSet
#   4. Configura los permisos según lo definido en el ViewSet
router.register(
    r'',  # Prefijo vacío porque ya está en 'api/embarazos/'
    EmbarazoViewSet,
    basename='embarazos'
)


# ===========================================
# URLPATTERNS
# ===========================================
"""
URLPATTERNS: Lista de rutas del módulo

Funcionamiento:
    - Incluye todas las rutas generadas por el router
    - Permite agregar rutas personalizadas si fuera necesario
"""

urlpatterns = [
    # Incluir todas las rutas del router
    # Funcionamiento:
    #   - router.urls contiene todas las rutas del ViewSet
    #   - Se incluyen en urlpatterns usando include()
    #   - Esto agrega las rutas CRUD y las acciones personalizadas
    path('', include(router.urls)),
]


"""
RESUMEN DE TODAS LAS RUTAS DISPONIBLES:
========================================

CRUD BÁSICO (Requiere autenticación):
    GET    /api/embarazos/                -> EmbarazoViewSet.list()
    POST   /api/embarazos/                -> EmbarazoViewSet.create()
    GET    /api/embarazos/{id}/           -> EmbarazoViewSet.retrieve()
    PUT    /api/embarazos/{id}/           -> EmbarazoViewSet.update()
    PATCH  /api/embarazos/{id}/           -> EmbarazoViewSet.partial_update()
    DELETE /api/embarazos/{id}/           -> EmbarazoViewSet.destroy()

GESTIÓN DE ESTADO (Requiere autenticación):
    POST   /api/embarazos/{id}/cambiar_estado/     -> EmbarazoViewSet.cambiar_estado()
    POST   /api/embarazos/{id}/finalizar/          -> EmbarazoViewSet.finalizar()
    POST   /api/embarazos/{id}/marcar_perdida/     -> EmbarazoViewSet.marcar_perdida()
    POST   /api/embarazos/{id}/reactivar/          -> EmbarazoViewSet.reactivar()

INFORMACIÓN Y CÁLCULOS (Requiere autenticación):
    GET    /api/embarazos/{id}/historial_completo/     -> EmbarazoViewSet.historial_completo()
    GET    /api/embarazos/{id}/calculos_obstetricos/   -> EmbarazoViewSet.calculos_obstetricos()
    GET    /api/embarazos/{id}/proximos_controles/     -> EmbarazoViewSet.proximos_controles()
    GET    /api/embarazos/{id}/curva_crecimiento/      -> EmbarazoViewSet.curva_crecimiento()
    GET    /api/embarazos/{id}/riesgos/                -> EmbarazoViewSet.riesgos()

CONSULTAS ESPECIALIZADAS (Requiere autenticación):
    GET    /api/embarazos/estadisticas/           -> EmbarazoViewSet.estadisticas()
    GET    /api/embarazos/busqueda_avanzada/      -> EmbarazoViewSet.busqueda_avanzada()
    GET    /api/embarazos/por_paciente/{id}/      -> EmbarazoViewSet.por_paciente()
    GET    /api/embarazos/activos/                -> EmbarazoViewSet.activos()
    GET    /api/embarazos/alto_riesgo/            -> EmbarazoViewSet.alto_riesgo()
    GET    /api/embarazos/proximos_partos/        -> EmbarazoViewSet.proximos_partos()

========================================
Total de endpoints: 21
Todos documentados y funcionales
========================================
"""
