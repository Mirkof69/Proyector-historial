# =============================================================================
# URLs DE LABORATORIO
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: laboratorio
# Descripción: Configuración de rutas para API de laboratorio
# Versión: 1.0.0
# =============================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamenLaboratorioViewSet

# =============================================================================
# CONFIGURACIÓN DEL ROUTER
# =============================================================================

router = DefaultRouter()
router.register(r'laboratorio', ExamenLaboratorioViewSet, basename='laboratorio')

# =============================================================================
# PATRONES DE URL
# =============================================================================

urlpatterns = [
    path('', include(router.urls)),
]

# =============================================================================
# DOCUMENTACIÓN DE ENDPOINTS
# =============================================================================

"""
ENDPOINTS DISPONIBLES:

1. LISTAR EXÁMENES DE LABORATORIO
   GET /api/laboratorio/

   Query parameters:
   - page: Número de página
   - page_size: Tamaño de página (max: 100)
   - search: Búsqueda en nombre paciente, tipo examen, laboratorio
   - ordering: Campo para ordenar
   - embarazo_id: Filtrar por ID de embarazo
   - tipo: Filtrar por tipo (hematologia, quimica, serologia, orina, cultivo, otro)
   - estado: Filtrar por estado (pendiente, completado)
   - fecha_desde: Fecha mínima (YYYY-MM-DD)
   - fecha_hasta: Fecha máxima (YYYY-MM-DD)
   - con_resultados: true/false
   - laboratorio: Nombre del laboratorio

2. CREAR EXAMEN DE LABORATORIO
   POST /api/laboratorio/

   Body (JSON) - Ejemplo de Hemograma:
   {
       "embarazo": 1,
       "fecha_examen": "2024-01-15",
       "tipo_examen": "hematologia",
       "estado": "completado",
       "fecha_resultado": "2024-01-16",
       "laboratorio": "Lab Central",
       "hemoglobina": 11.5,
       "hematocrito": 34.5,
       "leucocitos": 8500,
       "plaquetas": 220000,
       "observaciones": "Hemograma dentro de parámetros normales"
   }

   Body (JSON) - Ejemplo de Química Sanguínea:
   {
       "embarazo": 1,
       "fecha_examen": "2024-01-15",
       "tipo_examen": "quimica",
       "estado": "completado",
       "fecha_resultado": "2024-01-16",
       "glucosa": 85.0,
       "urea": 25.0,
       "creatinina": 0.8,
       "acido_urico": 4.2,
       "tgo": 28,
       "tgp": 32,
       "observaciones": "Función hepática y renal normal"
   }

   Body (JSON) - Ejemplo de Serología:
   {
       "embarazo": 1,
       "fecha_examen": "2024-01-15",
       "tipo_examen": "serologia",
       "estado": "completado",
       "fecha_resultado": "2024-01-16",
       "grupo_sanguineo": "O",
       "factor_rh": "positivo",
       "vdrl": "no_reactivo",
       "vih": "no_reactivo",
       "hepatitis_b": "no_reactivo",
       "toxoplasmosis_igg": "reactivo",
       "toxoplasmosis_igm": "no_reactivo",
       "rubeola_igg": "reactivo",
       "observaciones": "Inmunidad a toxoplasmosis y rubéola"
   }

   Body (JSON) - Ejemplo de Examen de Orina:
   {
       "embarazo": 1,
       "fecha_examen": "2024-01-15",
       "tipo_examen": "orina",
       "estado": "completado",
       "fecha_resultado": "2024-01-15",
       "orina_color": "amarillo",
       "orina_aspecto": "transparente",
       "orina_ph": 6.0,
       "orina_densidad": 1.020,
       "orina_glucosa": "negativo",
       "orina_proteinas": "negativo",
       "orina_leucocitos": 2,
       "orina_hematies": 1,
       "orina_bacterias": "ausente",
       "observaciones": "Examen de orina normal"
   }

3. OBTENER DETALLE DE EXAMEN
   GET /api/laboratorio/{id}/

   Respuesta incluye campos calculados:
   - paciente_nombre
   - estado_hemograma (interpretación)
   - estado_glucosa (interpretación)
   - estado_funcion_renal (interpretación)
   - estado_funcion_hepatica (interpretación)
   - alerta_infeccion_urinaria (detección)
   - archivo_url (PDF de resultados)
   - dias_resultado (tiempo de entrega)

4. ACTUALIZAR EXAMEN (COMPLETO)
   PUT /api/laboratorio/{id}/

5. ACTUALIZAR EXAMEN (PARCIAL)
   PATCH /api/laboratorio/{id}/

   Body (JSON) - Ejemplo:
   {
       "fecha_resultado": "2024-01-17",
       "estado": "completado",
       "observaciones": "Resultados actualizados"
   }

6. ELIMINAR EXAMEN (SOFT DELETE)
   DELETE /api/laboratorio/{id}/

7. EXÁMENES POR EMBARAZO
   GET /api/laboratorio/por-embarazo/{embarazo_id}/

   Retorna todos los exámenes de un embarazo con información del paciente.

   Respuesta:
   {
       "info_embarazo": {
           "embarazo_id": 1,
           "paciente": "María González",
           "fecha_ur": "2023-08-01",
           "total_examenes": 8
       },
       "examenes": [...]
   }

8. FILTRAR POR TIPO
   GET /api/laboratorio/por-tipo/{tipo}/

   Tipos válidos:
   - hematologia
   - quimica
   - serologia
   - orina
   - cultivo
   - otro

9. EXÁMENES PENDIENTES
   GET /api/laboratorio/pendientes/

   Retorna todos los exámenes con estado "pendiente" (sin resultado).

   Respuesta:
   {
       "count": 5,
       "results": [...]
   }

10. EXÁMENES CON ALERTAS
    GET /api/laboratorio/con_alertas/

    Retorna exámenes con resultados anormales que requieren atención:
    - Hemoglobina <10 g/dL (anemia severa)
    - Glucosa >126 mg/dL (diabetes)
    - Plaquetas <100000 (trombocitopenia severa)
    - Serología reactiva (VDRL, VIH, Hepatitis B)
    - Leucocitos en orina >10/campo
    - Proteinuria positiva ++ o +++

    Respuesta:
    {
        "count": 3,
        "mensaje": "Exámenes con resultados que requieren atención médica",
        "results": [...]
    }

11. ESTADÍSTICAS GENERALES
    GET /api/laboratorio/estadisticas/

    Retorna estadísticas agregadas:
    - Total por tipo de examen
    - Promedios de valores (Hb, glucosa, plaquetas, leucocitos)
    - Estados (pendientes vs completados)
    - Serología reactiva
    - Clasificación de anemia

    Respuesta:
    {
        "total_examenes": 150,
        "por_tipo": {
            "hematologia": {"nombre": "Hematología", "cantidad": 45},
            ...
        },
        "estados": {
            "pendientes": 8,
            "completados": 142
        },
        "promedios": {
            "hemoglobina_promedio": 11.8,
            "glucosa_promedio": 88.5,
            ...
        },
        "serologia_reactiva": {
            "vdrl": 1,
            "vih": 0,
            "hepatitis_b": 2
        },
        "anemia": {
            "leve": 12,
            "moderada": 3,
            "severa": 1
        },
        "fecha_consulta": "2024-01-15T10:30:00Z"
    }

12. INTERPRETAR EXAMEN
    GET /api/laboratorio/{id}/interpretar/

    Retorna interpretación detallada de todos los resultados del examen
    con recomendaciones clínicas.

    Respuesta:
    {
        "examen_id": 1,
        "tipo": "Hematología",
        "fecha": "2024-01-15",
        "estado_hemograma": {
            "hemoglobina": "Anemia (10.5 g/dL)",
            "leucocitos": "Normal (8500/mm³)",
            "plaquetas": "Normal (220000/mm³)",
            "alertas": ["Anemia detectada"]
        },
        "estado_glucosa": {
            "valor": 88.0,
            "estado": "Normal",
            "recomendacion": "Glucosa en rango normal para embarazo"
        },
        "estado_funcion_renal": {
            "urea": "Normal (28 mg/dL)",
            "creatinina": "Normal (0.8 mg/dL)",
            "estado": "Función renal normal",
            "alertas": []
        },
        "estado_funcion_hepatica": {
            "tgo": "Normal (28 U/L)",
            "tgp": "Normal (32 U/L)",
            "estado": "Función hepática normal",
            "alertas": []
        },
        "alerta_infeccion_urinaria": {
            "presente": false,
            "criterios": [],
            "recomendacion": null
        },
        "recomendaciones": [
            "Anemia leve - Iniciar suplementación con hierro oral"
        ]
    }

13. COMPARAR EXÁMENES
    GET /api/laboratorio/comparar/{embarazo_id}/

    Compara resultados en el tiempo para visualizar tendencias.

    Respuesta:
    {
        "embarazo_id": 1,
        "paciente": "María González",
        "total_examenes": 8,
        "evolucion_hemoglobina": [
            {"fecha": "2024-01-15", "valor": 11.5, "tipo": "Hematología"},
            {"fecha": "2024-03-20", "valor": 10.8, "tipo": "Hematología"},
            ...
        ],
        "evolucion_glucosa": [
            {"fecha": "2024-01-15", "valor": 85.0, "tipo": "Química Sanguínea"},
            ...
        ],
        "evolucion_plaquetas": [
            {"fecha": "2024-01-15", "valor": 220000, "tipo": "Hematología"},
            ...
        ]
    }

=============================================================================
AUTENTICACIÓN
=============================================================================

Todos los endpoints requieren autenticación mediante token JWT.

Headers requeridos:
Authorization: Bearer {token}

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
"""
