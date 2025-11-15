# =============================================================================
# URLs DE ECOGRAFÍAS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: ecografias
# Descripción: Configuración de rutas para API de ecografías
# Versión: 1.0.0
# =============================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EcografiaViewSet

# =============================================================================
# CONFIGURACIÓN DEL ROUTER
# =============================================================================

# El DefaultRouter de Django REST Framework genera automáticamente las rutas
# estándar para el ViewSet, incluyendo:
#
# GET    /api/ecografias/              -> list()       (listar todas)
# POST   /api/ecografias/              -> create()     (crear nueva)
# GET    /api/ecografias/{id}/         -> retrieve()   (detalle)
# PUT    /api/ecografias/{id}/         -> update()     (actualizar completo)
# PATCH  /api/ecografias/{id}/         -> partial_update() (actualizar parcial)
# DELETE /api/ecografias/{id}/         -> destroy()    (eliminar)
#
# Además, genera automáticamente las rutas para las acciones personalizadas
# definidas con @action en el ViewSet:
#
# GET /api/ecografias/por-embarazo/{embarazo_id}/
# GET /api/ecografias/estadisticas/
# GET /api/ecografias/por-tipo/{tipo}/
# GET /api/ecografias/ultimas/
# GET /api/ecografias/biometria-evolution/{embarazo_id}/
# POST /api/ecografias/{id}/validar_coherencia/

router = DefaultRouter()
router.register(r'ecografias', EcografiaViewSet, basename='ecografia')

# =============================================================================
# PATRONES DE URL
# =============================================================================

urlpatterns = [
    # Incluir todas las rutas del router
    path('', include(router.urls)),
]

# =============================================================================
# DOCUMENTACIÓN DE ENDPOINTS
# =============================================================================

"""
ENDPOINTS DISPONIBLES:

1. LISTAR ECOGRAFÍAS
   GET /api/ecografias/

   Query parameters opcionales:
   - page: Número de página (default: 1)
   - page_size: Tamaño de página (default: 20, max: 100)
   - search: Búsqueda en nombre paciente, tipo, hallazgos, observaciones
   - ordering: Campo para ordenar (fecha_ecografia, tipo_ecografia, etc.)
   - embarazo_id: Filtrar por ID de embarazo
   - tipo: Filtrar por tipo de ecografía
   - fecha_desde: Fecha mínima (YYYY-MM-DD)
   - fecha_hasta: Fecha máxima (YYYY-MM-DD)
   - semanas_min: Edad gestacional mínima
   - semanas_max: Edad gestacional máxima
   - latido_presente: true/false
   - anatomia_normal: true/false

   Respuesta:
   {
       "links": {
           "next": "http://...",
           "previous": "http://..."
       },
       "count": 100,
       "total_pages": 5,
       "current_page": 1,
       "page_size": 20,
       "results": [...]
   }

2. CREAR ECOGRAFÍA
   POST /api/ecografias/

   Body (JSON):
   {
       "embarazo": 1,
       "fecha_ecografia": "2024-01-15",
       "tipo_ecografia": "segundo_trimestre",
       "edad_gestacional_semanas": 20,
       "edad_gestacional_dias": 3,
       "diametro_biparietal": 48.5,
       "circunferencia_cefalica": 175.0,
       "circunferencia_abdominal": 160.0,
       "longitud_femur": 32.0,
       "peso_fetal_estimado": 350,
       "localizacion_placenta": "anterior",
       "grado_placentario": "I",
       "liquido_amniotico": "normal",
       "indice_liquido_amniotico": 12.5,
       "numero_fetos": 1,
       "latido_cardiaco_presente": true,
       "frecuencia_cardiaca_fetal": 145,
       "movimientos_fetales": true,
       "evaluacion_anatomia": "normal",
       "hallazgos": "Desarrollo fetal acorde a edad gestacional",
       "observaciones": "Ecografía morfológica completa"
   }

3. OBTENER DETALLE DE ECOGRAFÍA
   GET /api/ecografias/{id}/

   Respuesta incluye todos los campos de la ecografía más campos calculados:
   - paciente_nombre
   - edad_gestacional_texto
   - clasificacion_peso_fetal
   - percentil_peso
   - estado_liquido_amniotico
   - imagen_url

4. ACTUALIZAR ECOGRAFÍA (COMPLETO)
   PUT /api/ecografias/{id}/

   Body (JSON): Todos los campos obligatorios

5. ACTUALIZAR ECOGRAFÍA (PARCIAL)
   PATCH /api/ecografias/{id}/

   Body (JSON): Solo los campos a actualizar
   {
       "hallazgos": "Nuevos hallazgos...",
       "observaciones": "Observaciones actualizadas..."
   }

6. ELIMINAR ECOGRAFÍA (SOFT DELETE)
   DELETE /api/ecografias/{id}/

   Respuesta:
   {
       "message": "Ecografía eliminada exitosamente"
   }

7. ECOGRAFÍAS POR EMBARAZO
   GET /api/ecografias/por-embarazo/{embarazo_id}/

   Retorna todas las ecografías de un embarazo específico con información
   adicional del embarazo y la paciente.

   Respuesta:
   {
       "info_embarazo": {
           "embarazo_id": 1,
           "paciente": "María González",
           "fecha_ur": "2023-08-01",
           "total_ecografias": 5
       },
       "ecografias": [...]
   }

8. ESTADÍSTICAS GENERALES
   GET /api/ecografias/estadisticas/

   Retorna estadísticas agregadas:
   - Total de ecografías
   - Distribución por tipo
   - Distribución por trimestre
   - Promedios de biometría
   - Evaluación de anatomía
   - Estado de líquido amniótico

   Respuesta:
   {
       "total_ecografias": 250,
       "por_tipo": {...},
       "por_trimestre": {...},
       "biometria": {...},
       "anatomia": {...},
       "liquido_amniotico": {...},
       "fecha_consulta": "2024-01-15T10:30:00Z"
   }

9. FILTRAR POR TIPO
   GET /api/ecografias/por-tipo/{tipo}/

   Tipos válidos:
   - primer_trimestre
   - segundo_trimestre
   - tercer_trimestre
   - genetica
   - doppler
   - otra

   Retorna lista paginada de ecografías del tipo especificado.

10. ÚLTIMAS ECOGRAFÍAS
    GET /api/ecografias/ultimas/?limit=10

    Query parameters:
    - limit: Cantidad a retornar (default: 10, max: 50)

    Retorna las últimas ecografías ordenadas por fecha descendente.

    Respuesta:
    {
        "count": 10,
        "limit": 10,
        "results": [...]
    }

11. EVOLUCIÓN BIOMÉTRICA
    GET /api/ecografias/biometria-evolution/{embarazo_id}/

    Retorna datos de evolución de biometría fetal para graficar curvas
    de crecimiento. Incluye DBP, CC, CA, LF y peso fetal en cada ecografía.

    Respuesta:
    {
        "embarazo_id": 1,
        "paciente": "María González",
        "total_ecografias": 5,
        "evolution": [
            {
                "fecha": "2023-12-01",
                "semanas": 20,
                "dias": 0,
                "edad_gestacional": "20+0",
                "mediciones": {
                    "dbp": 48.5,
                    "cc": 175.0,
                    "ca": 160.0,
                    "lf": 32.0,
                    "peso_fetal": 350,
                    "ila": 12.5
                },
                "tipo_ecografia": "Segundo Trimestre (18-22 semanas)"
            },
            ...
        ]
    }

12. VALIDAR COHERENCIA
    POST /api/ecografias/{id}/validar_coherencia/

    Valida la coherencia clínica de los datos de una ecografía:
    - Peso fetal acorde a edad gestacional
    - Mediciones biométricas proporcionales
    - ILA dentro de rangos normales
    - Grado placentario acorde a semanas
    - Frecuencia cardíaca fetal en rango normal

    Respuesta:
    {
        "ecografia_id": 1,
        "estado": "warning",  // "ok", "warning", "error"
        "mensaje": "Validación completada",
        "errores": [],
        "advertencias": [
            "Peso fetal (2500g) menor al esperado para 28 semanas..."
        ],
        "total_advertencias": 1,
        "total_errores": 0
    }

=============================================================================
AUTENTICACIÓN
=============================================================================

Todos los endpoints requieren autenticación mediante token JWT.

Headers requeridos:
Authorization: Bearer {token}

=============================================================================
PERMISOS
=============================================================================

- Todos los usuarios autenticados pueden:
  * Listar ecografías (list)
  * Ver detalle de ecografías (retrieve)
  * Ver estadísticas
  * Ver evolución biométrica

- Solo usuarios con permisos de modificación pueden:
  * Crear ecografías (create)
  * Actualizar ecografías (update/partial_update)
  * Eliminar ecografías (destroy)

=============================================================================
CÓDIGOS DE RESPUESTA HTTP
=============================================================================

200 OK              - Operación exitosa (GET, PUT, PATCH)
201 Created         - Recurso creado exitosamente (POST)
204 No Content      - Recurso eliminado exitosamente (DELETE)
400 Bad Request     - Datos inválidos o faltantes
401 Unauthorized    - No autenticado
403 Forbidden       - Sin permisos
404 Not Found       - Recurso no encontrado
500 Internal Error  - Error del servidor

=============================================================================
EJEMPLOS DE USO CON CURL
=============================================================================

# Listar todas las ecografías
curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/api/ecografias/

# Crear nueva ecografía
curl -X POST \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{
         "embarazo": 1,
         "fecha_ecografia": "2024-01-15",
         "tipo_ecografia": "segundo_trimestre",
         ...
     }' \
     http://localhost:8000/api/ecografias/

# Obtener ecografías de un embarazo
curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/api/ecografias/por-embarazo/1/

# Obtener estadísticas
curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/api/ecografias/estadisticas/

# Validar coherencia
curl -X POST \
     -H "Authorization: Bearer {token}" \
     http://localhost:8000/api/ecografias/1/validar_coherencia/

=============================================================================
"""
