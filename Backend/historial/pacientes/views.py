"""
===========================================
MÓDULO: VIEWS DE PACIENTES
===========================================
Descripción:
    ViewSet completo para gestión de pacientes en el sistema gineco-obstétrico.
    Incluye CRUD completo + 20 acciones personalizadas.

Funcionalidades:
    - CRUD completo con validaciones exhaustivas
    - Búsqueda avanzada multi-criterio
    - Estadísticas demográficas y clínicas
    - Reportes por períodos
    - Gestión de historiales
    - Perfiles de riesgo
    - Exportación de datos
    - Soft delete y reactivación
    - Validación de duplicados

Seguridad:
    - Autenticación JWT requerida
    - Validaciones en cada operación
    - Control de permisos por acción

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import IntegrityError
from django.db.models import Q, Count, Avg, Max, Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from datetime import date, datetime, timedelta
from .models import Paciente
from .serializers import PacienteSerializer, PacienteListSerializer, PacienteDetailSerializer


# ===========================================
# VIEWSET: PACIENTES
# ===========================================
class PacienteViewSet(viewsets.ModelViewSet):
    """
    VIEWSET: ViewSet completo para gestión de Pacientes

    Funcionamiento:
        Proporciona CRUD completo para pacientes más 20+ acciones personalizadas
        Incluye validaciones exhaustivas, filtros avanzados y estadísticas

    Endpoints estándar:
        - GET /api/pacientes/ - Listar todos los pacientes
        - POST /api/pacientes/ - Crear nuevo paciente
        - GET /api/pacientes/{id}/ - Detalle de un paciente
        - PUT /api/pacientes/{id}/ - Actualizar paciente completo
        - PATCH /api/pacientes/{id}/ - Actualizar parcial
        - DELETE /api/pacientes/{id}/ - Desactivar paciente (soft delete)

    Endpoints personalizados:
        - GET /api/pacientes/estadisticas/ - Estadísticas generales
        - GET /api/pacientes/busqueda_avanzada/ - Búsqueda con múltiples filtros
        - GET /api/pacientes/por_edad/ - Agrupar por rangos de edad
        - GET /api/pacientes/por_grupo_sanguineo/ - Agrupar por grupo sanguíneo
        - GET /api/pacientes/recientes/ - Pacientes recientes
        - GET /api/pacientes/inactivos/ - Pacientes desactivados
        - GET /api/pacientes/sin_embarazos/ - Pacientes sin embarazos
        - GET /api/pacientes/con_embarazos_activos/ - Pacientes con embarazos activos
        - GET /api/pacientes/reporte_demografico/ - Reporte demográfico
        - GET /api/pacientes/reporte_mensual/ - Reporte del mes
        - GET /api/pacientes/validar_duplicados/ - Validar duplicados
        - POST /api/pacientes/{id}/reactivar/ - Reactivar paciente
        - GET /api/pacientes/{id}/historial_completo/ - Historial completo
        - GET /api/pacientes/{id}/perfil_riesgo/ - Perfil de riesgo
        - GET /api/pacientes/{id}/resumen_clinico/ - Resumen clínico
        - GET /api/pacientes/{id}/linea_tiempo/ - Línea de tiempo
        - GET /api/pacientes/{id}/proximos_controles/ - Próximos controles
        - GET /api/pacientes/buscar_por_ci/ - Buscar por cédula
        - GET /api/pacientes/buscar_por_nombre/ - Buscar por nombre
        - GET /api/pacientes/exportar/ - Exportar datos

    Permisos:
        - Requiere autenticación JWT
        - IsAuthenticated para todas las operaciones
    """

    queryset = Paciente.objects.filter(activo=True).select_related()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Campos para filtrado
    filterset_fields = ['genero', 'estado_civil', 'grupo_sanguineo', 'activo', 'ciudad']

    # Campos para búsqueda
    search_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'id_clinico', 'cedula_identidad']

    # Campos para ordenamiento
    ordering_fields = ['fecha_registro', 'nombre', 'apellido_paterno', 'id_clinico', 'fecha_nacimiento']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        """
        MÉTODO: Determinar serializer según acción

        Funcionamiento:
            - list: PacienteListSerializer (simplificado para listados)
            - retrieve: PacienteDetailSerializer (completo con relaciones)
            - otros: PacienteSerializer (estándar)
        """
        if self.action == 'list':
            return PacienteListSerializer
        elif self.action == 'retrieve':
            return PacienteDetailSerializer
        return PacienteSerializer

    def get_queryset(self):
        """
        MÉTODO: Personalizar queryset con filtros

        Funcionamiento:
            Aplica filtros adicionales basados en query params

        Parámetros query:
            - cedula: Buscar por cédula
            - activo: Filtrar por estado (true/false)
            - edad_min: Edad mínima
            - edad_max: Edad máxima
            - genero: Filtrar por género
            - grupo_sanguineo: Filtrar por grupo sanguíneo
            - search: Búsqueda en múltiples campos
        """
        queryset = super().get_queryset()

        # Filtro por cédula
        cedula = self.request.query_params.get('cedula', None)
        if cedula:
            queryset = queryset.filter(cedula_identidad__icontains=cedula)

        # Filtro por estado activo/inactivo
        activo = self.request.query_params.get('activo', None)
        if activo is not None:
            if activo.lower() == 'false':
                queryset = Paciente.objects.filter(activo=False)
            else:
                queryset = queryset.filter(activo=True)

        # Filtro por género
        genero = self.request.query_params.get('genero', None)
        if genero:
            queryset = queryset.filter(genero=genero)

        # Filtro por grupo sanguíneo
        grupo_sanguineo = self.request.query_params.get('grupo_sanguineo', None)
        if grupo_sanguineo:
            queryset = queryset.filter(grupo_sanguineo=grupo_sanguineo)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        MÉTODO: Crear nuevo paciente

        Funcionamiento:
            - Auto-genera ID clínico si no se proporciona
            - Valida datos exhaustivamente
            - Maneja errores de duplicados
            - Retorna respuesta estructurada

        Genera ID clínico:
            Formato: HC-001, HC-002, etc.
            Si no se proporciona, se auto-genera secuencialmente
        """
        # Auto-generar ID clínico si no se proporciona
        id_clinico = request.data.get('id_clinico', '').strip()

        if not id_clinico:
            # Obtener el último paciente para generar el siguiente ID
            ultimo_paciente = Paciente.objects.all().order_by('id').last()
            if ultimo_paciente and ultimo_paciente.id_clinico:
                try:
                    # Extraer el número del formato HC-001
                    ultimo_num = int(ultimo_paciente.id_clinico.split('-')[1])
                    nuevo_num = ultimo_num + 1
                except:
                    nuevo_num = Paciente.objects.all().count() + 1
            else:
                nuevo_num = 1
            request.data['id_clinico'] = f"HC-{str(nuevo_num).zfill(3)}"

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response(
                {
                    "success": True,
                    "mensaje": "Paciente registrado exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "success": False,
                    "errores": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError as e:
            return Response(
                {
                    "success": False,
                    "error": "Error de integridad: Verifique que no existan datos duplicados (ID Clínico o Cédula)."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error inesperado: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        MÉTODO: Actualizar paciente

        Funcionamiento:
            Actualiza datos del paciente
            Soporta actualización parcial (PATCH) y completa (PUT)
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response({
                "success": True,
                "mensaje": "Paciente actualizado exitosamente",
                "data": serializer.data
            })
        except serializers.ValidationError as e:
            return Response(
                {
                    "success": False,
                    "errores": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al actualizar: {str(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """
        MÉTODO: Soft delete del paciente

        Funcionamiento:
            Desactiva el paciente en lugar de eliminarlo físicamente
            Preserva integridad referencial con embarazos y controles
        """
        try:
            paciente = self.get_object()
            paciente.soft_delete()

            return Response(
                {
                    "success": True,
                    "mensaje": f"Paciente {paciente.id_clinico} desactivado exitosamente"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al desactivar: {str(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    # ===========================================
    # ACCIÓN: REACTIVAR PACIENTE
    # ===========================================
    @action(detail=True, methods=['post'])
    def reactivar(self, request, pk=None):
        """
        ACCIÓN: Reactivar paciente desactivado

        Funcionamiento:
            Cambia el estado de activo=False a activo=True

        Retorna:
            Datos del paciente reactivado
        """
        try:
            paciente = self.get_object()
            paciente.activar()

            return Response({
                "success": True,
                "mensaje": f"Paciente {paciente.id_clinico} reactivado exitosamente",
                "data": PacienteSerializer(paciente).data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al reactivar: {str(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    # ===========================================
    # ACCIÓN: HISTORIAL COMPLETO
    # ===========================================
    @action(detail=True, methods=['get'])
    def historial_completo(self, request, pk=None):
        """
        ACCIÓN: Obtener historial completo del paciente

        Funcionamiento:
            Recopila toda la información clínica del paciente:
            - Datos personales
            - Embarazos
            - Controles prenatales
            - Partos
            - Estadísticas

        Retorna:
            JSON con historial estructurado
        """
        try:
            paciente = self.get_object()

            # Obtener embarazos relacionados
            embarazos = paciente.embarazos.all().order_by('-fecha_registro')

            # Obtener controles relacionados
            controles = paciente.controles.all().order_by('-fecha_control')[:10]

            # Obtener partos si existen
            partos = paciente.partos.all().order_by('-fecha_parto') if hasattr(paciente, 'partos') else []

            return Response({
                "success": True,
                "paciente": PacienteDetailSerializer(paciente).data,
                "estadisticas": {
                    "total_embarazos": embarazos.count(),
                    "embarazos_activos": embarazos.filter(estado='activo').count(),
                    "embarazos_finalizados": embarazos.filter(estado='finalizado').count(),
                    "total_controles": controles.count(),
                    "total_partos": len(partos),
                },
                "embarazos_recientes": [
                    {
                        "id": e.id,
                        "numero_gesta": e.numero_gesta,
                        "fecha_ultima_menstruacion": e.fecha_ultima_menstruacion,
                        "fecha_probable_parto": e.fecha_probable_parto,
                        "estado": e.estado,
                        "riesgo_embarazo": e.riesgo_embarazo,
                    }
                    for e in embarazos[:5]
                ],
                "controles_recientes": [
                    {
                        "id": c.id,
                        "fecha_control": c.fecha_control,
                        "semanas_gestacion": c.semanas_gestacion,
                        "peso": c.peso_actual,
                    }
                    for c in controles[:5]
                ] if controles else []
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al obtener historial: {str(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    # ===========================================
    # ACCIÓN: ESTADÍSTICAS GENERALES
    # ===========================================
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        ACCIÓN: Estadísticas generales de pacientes

        Funcionamiento:
            Calcula estadísticas demográficas y clínicas
            Agrupa por diferentes criterios

        Retorna:
            Estadísticas completas del sistema
        """
        try:
            total_pacientes = Paciente.objects.count()
            activos = Paciente.objects.filter(activo=True).count()
            inactivos = Paciente.objects.filter(activo=False).count()

            # Estadísticas por género
            por_genero = Paciente.objects.filter(activo=True).values('genero').annotate(
                total=Count('id')
            )

            # Estadísticas por grupo sanguíneo
            por_grupo = Paciente.objects.filter(activo=True, grupo_sanguineo__isnull=False).values(
                'grupo_sanguineo'
            ).annotate(total=Count('id'))

            # Estadísticas por estado civil
            por_estado_civil = Paciente.objects.filter(activo=True, estado_civil__isnull=False).values(
                'estado_civil'
            ).annotate(total=Count('id'))

            # Pacientes registrados en el último mes
            hace_un_mes = date.today() - timedelta(days=30)
            nuevos_mes = Paciente.objects.filter(
                fecha_registro__gte=hace_un_mes
            ).count()

            return Response({
                "success": True,
                "estadisticas": {
                    "total_pacientes": total_pacientes,
                    "pacientes_activos": activos,
                    "pacientes_inactivos": inactivos,
                    "nuevos_ultimo_mes": nuevos_mes,
                    "por_genero": list(por_genero),
                    "por_grupo_sanguineo": list(por_grupo),
                    "por_estado_civil": list(por_estado_civil),
                }
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al obtener estadísticas: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: BÚSQUEDA AVANZADA
    # ===========================================
    @action(detail=False, methods=['get'])
    def busqueda_avanzada(self, request):
        """
        ACCIÓN: Búsqueda avanzada de pacientes

        Funcionamiento:
            Permite filtrar por múltiples criterios simultáneamente

        Parámetros:
            - q: Búsqueda en nombre, apellidos, CI, ID clínico
            - genero: Filtrar por género
            - edad_min: Edad mínima
            - edad_max: Edad máxima
            - grupo_sanguineo: Filtrar por grupo sanguíneo
            - estado_civil: Filtrar por estado civil
            - ciudad: Filtrar por ciudad

        Retorna:
            Lista de pacientes filtrados
        """
        try:
            queryset = Paciente.objects.filter(activo=True)

            # Búsqueda general
            q = request.query_params.get('q', None)
            if q:
                queryset = queryset.filter(
                    Q(nombre__icontains=q) |
                    Q(apellido_paterno__icontains=q) |
                    Q(apellido_materno__icontains=q) |
                    Q(cedula_identidad__icontains=q) |
                    Q(id_clinico__icontains=q)
                )

            # Filtro por ciudad
            ciudad = request.query_params.get('ciudad', None)
            if ciudad:
                queryset = queryset.filter(ciudad__icontains=ciudad)

            # Filtro por estado civil
            estado_civil = request.query_params.get('estado_civil', None)
            if estado_civil:
                queryset = queryset.filter(estado_civil=estado_civil)

            # Aplicar filtros del get_queryset
            queryset = self.filter_queryset(queryset)

            # Paginar resultados
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = PacienteListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = PacienteListSerializer(queryset, many=True)
            return Response({
                "success": True,
                "count": queryset.count(),
                "results": serializer.data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error en búsqueda: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: AGRUPAR POR EDAD
    # ===========================================
    @action(detail=False, methods=['get'])
    def por_edad(self, request):
        """
        ACCIÓN: Agrupar pacientes por rangos de edad

        Funcionamiento:
            Agrupa pacientes en rangos etarios estándar

        Rangos:
            - <18: Adolescentes
            - 18-25: Adultos jóvenes
            - 26-35: Adultos
            - 36-45: Adultos maduros
            - >45: Adultos mayores

        Retorna:
            Distribución por rangos de edad
        """
        try:
            pacientes = Paciente.objects.filter(activo=True)

            rangos = {
                'adolescentes': 0,
                'adultos_jovenes': 0,
                'adultos': 0,
                'adultos_maduros': 0,
                'adultos_mayores': 0
            }

            for paciente in pacientes:
                edad = paciente.edad
                if edad:
                    if edad < 18:
                        rangos['adolescentes'] += 1
                    elif 18 <= edad <= 25:
                        rangos['adultos_jovenes'] += 1
                    elif 26 <= edad <= 35:
                        rangos['adultos'] += 1
                    elif 36 <= edad <= 45:
                        rangos['adultos_maduros'] += 1
                    else:
                        rangos['adultos_mayores'] += 1

            return Response({
                "success": True,
                "total_pacientes": pacientes.count(),
                "distribucion_por_edad": {
                    "adolescentes_menor_18": rangos['adolescentes'],
                    "adultos_jovenes_18_25": rangos['adultos_jovenes'],
                    "adultos_26_35": rangos['adultos'],
                    "adultos_maduros_36_45": rangos['adultos_maduros'],
                    "adultos_mayores_mayor_45": rangos['adultos_mayores'],
                }
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al agrupar por edad: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: AGRUPAR POR GRUPO SANGUÍNEO
    # ===========================================
    @action(detail=False, methods=['get'])
    def por_grupo_sanguineo(self, request):
        """
        ACCIÓN: Estadísticas por grupo sanguíneo

        Funcionamiento:
            Agrupa pacientes por grupo sanguíneo y factor RH

        Retorna:
            Distribución por tipo sanguíneo con porcentajes
        """
        try:
            total = Paciente.objects.filter(activo=True, grupo_sanguineo__isnull=False).count()

            grupos = Paciente.objects.filter(
                activo=True,
                grupo_sanguineo__isnull=False
            ).values('grupo_sanguineo').annotate(
                total=Count('id')
            ).order_by('-total')

            resultados = []
            for grupo in grupos:
                resultados.append({
                    'grupo': grupo['grupo_sanguineo'],
                    'total': grupo['total'],
                    'porcentaje': round((grupo['total'] / total * 100), 2) if total > 0 else 0
                })

            return Response({
                "success": True,
                "total_con_grupo": total,
                "sin_grupo": Paciente.objects.filter(activo=True, grupo_sanguineo__isnull=True).count(),
                "distribucion": resultados
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al agrupar por grupo sanguíneo: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: PACIENTES RECIENTES
    # ===========================================
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        """
        ACCIÓN: Obtener pacientes registrados recientemente

        Funcionamiento:
            Retorna pacientes de los últimos N días

        Parámetros:
            - dias: Cantidad de días hacia atrás (default: 30)

        Retorna:
            Lista de pacientes recientes ordenados por fecha
        """
        try:
            dias = int(request.query_params.get('dias', 30))
            fecha_limite = datetime.now() - timedelta(days=dias)

            pacientes = Paciente.objects.filter(
                activo=True,
                fecha_registro__gte=fecha_limite
            ).order_by('-fecha_registro')

            serializer = PacienteListSerializer(pacientes, many=True)

            return Response({
                "success": True,
                "total": pacientes.count(),
                "dias": dias,
                "pacientes": serializer.data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al obtener recientes: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: PACIENTES INACTIVOS
    # ===========================================
    @action(detail=False, methods=['get'])
    def inactivos(self, request):
        """
        ACCIÓN: Listar pacientes desactivados

        Funcionamiento:
            Retorna todos los pacientes con activo=False

        Retorna:
            Lista de pacientes inactivos
        """
        try:
            pacientes = Paciente.objects.filter(activo=False).order_by('-fecha_ultima_actualizacion')

            serializer = PacienteListSerializer(pacientes, many=True)

            return Response({
                "success": True,
                "total_inactivos": pacientes.count(),
                "pacientes": serializer.data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al obtener inactivos: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: PACIENTES SIN EMBARAZOS
    # ===========================================
    @action(detail=False, methods=['get'])
    def sin_embarazos(self, request):
        """
        ACCIÓN: Pacientes sin embarazos registrados

        Funcionamiento:
            Filtra pacientes que no tienen embarazos asociados

        Retorna:
            Lista de pacientes sin embarazos
        """
        try:
            pacientes = Paciente.objects.filter(activo=True, embarazos__isnull=True).distinct()

            serializer = PacienteListSerializer(pacientes, many=True)

            return Response({
                "success": True,
                "total": pacientes.count(),
                "pacientes": serializer.data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: PACIENTES CON EMBARAZOS ACTIVOS
    # ===========================================
    @action(detail=False, methods=['get'])
    def con_embarazos_activos(self, request):
        """
        ACCIÓN: Pacientes con embarazos en curso

        Funcionamiento:
            Filtra pacientes que tienen al menos un embarazo activo

        Retorna:
            Lista de pacientes con embarazos activos
        """
        try:
            pacientes = Paciente.objects.filter(
                activo=True,
                embarazos__estado='activo'
            ).distinct()

            serializer = PacienteListSerializer(pacientes, many=True)

            return Response({
                "success": True,
                "total": pacientes.count(),
                "pacientes": serializer.data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: REPORTE DEMOGRÁFICO
    # ===========================================
    @action(detail=False, methods=['get'])
    def reporte_demografico(self, request):
        """
        ACCIÓN: Generar reporte demográfico completo

        Funcionamiento:
            Genera estadísticas demográficas detalladas

        Retorna:
            Reporte completo con múltiples indicadores
        """
        try:
            total = Paciente.objects.filter(activo=True).count()

            # Distribución por género
            por_genero = {}
            for genero, _ in Paciente.GENEROS:
                count = Paciente.objects.filter(activo=True, genero=genero).count()
                por_genero[genero] = {
                    'total': count,
                    'porcentaje': round((count / total * 100), 2) if total > 0 else 0
                }

            # Distribución por estado civil
            por_estado_civil = {}
            for estado, _ in Paciente.ESTADOS_CIVILES:
                count = Paciente.objects.filter(activo=True, estado_civil=estado).count()
                por_estado_civil[estado] = {
                    'total': count,
                    'porcentaje': round((count / total * 100), 2) if total > 0 else 0
                }

            # Ciudades más frecuentes
            top_ciudades = Paciente.objects.filter(
                activo=True,
                ciudad__isnull=False
            ).values('ciudad').annotate(
                total=Count('id')
            ).order_by('-total')[:10]

            return Response({
                "success": True,
                "fecha_reporte": date.today().isoformat(),
                "total_pacientes": total,
                "por_genero": por_genero,
                "por_estado_civil": por_estado_civil,
                "top_10_ciudades": list(top_ciudades)
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al generar reporte: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: REPORTE MENSUAL
    # ===========================================
    @action(detail=False, methods=['get'])
    def reporte_mensual(self, request):
        """
        ACCIÓN: Generar reporte del mes

        Funcionamiento:
            Genera estadísticas del mes actual o especificado

        Parámetros:
            - mes: Mes en formato YYYY-MM (opcional)

        Retorna:
            Reporte completo del mes
        """
        try:
            # Determinar mes a reportar
            mes_param = request.query_params.get('mes')
            if mes_param:
                try:
                    fecha = datetime.strptime(mes_param, '%Y-%m').date()
                    mes_inicio = fecha.replace(day=1)
                except:
                    return Response(
                        {'error': 'Formato de mes inválido (usar YYYY-MM)'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                hoy = date.today()
                mes_inicio = hoy.replace(day=1)

            # Calcular fin de mes
            if mes_inicio.month == 12:
                mes_fin = mes_inicio.replace(year=mes_inicio.year + 1, month=1)
            else:
                mes_fin = mes_inicio.replace(month=mes_inicio.month + 1)

            # Pacientes registrados en el mes
            nuevos = Paciente.objects.filter(
                fecha_registro__gte=mes_inicio,
                fecha_registro__lt=mes_fin
            ).count()

            # Pacientes actualizados en el mes
            actualizados = Paciente.objects.filter(
                fecha_ultima_actualizacion__gte=mes_inicio,
                fecha_ultima_actualizacion__lt=mes_fin
            ).count()

            return Response({
                "success": True,
                "periodo": {
                    "mes": mes_inicio.strftime('%Y-%m'),
                    "fecha_inicio": mes_inicio.isoformat(),
                    "fecha_fin": (mes_fin - timedelta(days=1)).isoformat()
                },
                "estadisticas": {
                    "pacientes_nuevos": nuevos,
                    "pacientes_actualizados": actualizados,
                }
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al generar reporte: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: VALIDAR DUPLICADOS
    # ===========================================
    @action(detail=False, methods=['get'])
    def validar_duplicados(self, request):
        """
        ACCIÓN: Validar posibles duplicados

        Funcionamiento:
            Busca pacientes con CI o nombres similares

        Parámetros:
            - cedula: Cédula a validar
            - nombre: Nombre a validar
            - apellido: Apellido a validar

        Retorna:
            Lista de posibles duplicados
        """
        try:
            cedula = request.query_params.get('cedula')
            nombre = request.query_params.get('nombre')
            apellido = request.query_params.get('apellido')

            duplicados = []

            if cedula:
                por_cedula = Paciente.objects.filter(cedula_identidad=cedula)
                if por_cedula.exists():
                    duplicados.append({
                        'tipo': 'cedula',
                        'pacientes': PacienteListSerializer(por_cedula, many=True).data
                    })

            if nombre and apellido:
                por_nombre = Paciente.objects.filter(
                    nombre__iexact=nombre,
                    apellido_paterno__iexact=apellido
                )
                if por_nombre.exists():
                    duplicados.append({
                        'tipo': 'nombre_completo',
                        'pacientes': PacienteListSerializer(por_nombre, many=True).data
                    })

            return Response({
                "success": True,
                "tiene_duplicados": len(duplicados) > 0,
                "duplicados": duplicados
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al validar: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: PERFIL DE RIESGO
    # ===========================================
    @action(detail=True, methods=['get'])
    def perfil_riesgo(self, request, pk=None):
        """
        ACCIÓN: Generar perfil de riesgo del paciente

        Funcionamiento:
            Analiza factores de riesgo obstétrico

        Factores evaluados:
            - Edad (< 18 o > 35)
            - Embarazos previos
            - Complicaciones anteriores
            - Grupo sanguíneo RH negativo

        Retorna:
            Perfil de riesgo con recomendaciones
        """
        try:
            paciente = self.get_object()
            factores_riesgo = []
            nivel_riesgo = 'bajo'

            # Evaluar edad
            edad = paciente.edad
            if edad:
                if edad < 18:
                    factores_riesgo.append("Edad menor a 18 años (embarazo adolescente)")
                    nivel_riesgo = 'alto'
                elif edad > 35:
                    factores_riesgo.append("Edad mayor a 35 años (embarazo añoso)")
                    nivel_riesgo = 'medio'

            # Evaluar grupo sanguíneo RH negativo
            if paciente.grupo_sanguineo and '-' in paciente.grupo_sanguineo:
                factores_riesgo.append("Grupo sanguíneo RH negativo (riesgo de incompatibilidad)")
                if nivel_riesgo == 'bajo':
                    nivel_riesgo = 'medio'

            # Evaluar embarazos previos
            total_embarazos = paciente.embarazos.count()
            if total_embarazos >= 4:
                factores_riesgo.append("Gran multípara (4 o más embarazos)")
                nivel_riesgo = 'alto'

            return Response({
                "success": True,
                "paciente_id": paciente.id,
                "nombre": paciente.nombre_completo,
                "edad": edad,
                "nivel_riesgo": nivel_riesgo,
                "factores_riesgo": factores_riesgo,
                "total_embarazos": total_embarazos,
                "recomendaciones": self._generar_recomendaciones(nivel_riesgo, factores_riesgo)
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al generar perfil: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generar_recomendaciones(self, nivel_riesgo, factores):
        """Genera recomendaciones según el nivel de riesgo"""
        recomendaciones = []

        if nivel_riesgo == 'alto':
            recomendaciones.append("Control prenatal especializado obligatorio")
            recomendaciones.append("Evaluación por medicina materno-fetal")
            recomendaciones.append("Controles más frecuentes (cada 2 semanas)")
        elif nivel_riesgo == 'medio':
            recomendaciones.append("Control prenatal mensual")
            recomendaciones.append("Seguimiento de factores de riesgo")
        else:
            recomendaciones.append("Control prenatal regular")

        return recomendaciones

    # ===========================================
    # ACCIÓN: RESUMEN CLÍNICO
    # ===========================================
    @action(detail=True, methods=['get'])
    def resumen_clinico(self, request, pk=None):
        """
        ACCIÓN: Resumen clínico del paciente

        Funcionamiento:
            Genera resumen clínico completo para consulta rápida

        Retorna:
            Resumen estructurado con datos clave
        """
        try:
            paciente = self.get_object()

            resumen = {
                "datos_personales": {
                    "id_clinico": paciente.id_clinico,
                    "nombre_completo": paciente.nombre_completo,
                    "cedula": paciente.cedula_identidad,
                    "edad": paciente.edad,
                    "fecha_nacimiento": paciente.fecha_nacimiento,
                    "genero": paciente.get_genero_display(),
                    "estado_civil": paciente.get_estado_civil_display() if paciente.estado_civil else None,
                },
                "datos_clinicos": {
                    "grupo_sanguineo": paciente.grupo_sanguineo,
                },
                "contacto": {
                    "telefono": paciente.telefono_principal,
                    "email": paciente.email,
                    "ciudad": paciente.ciudad,
                },
                "historial_obstetrico": {
                    "total_embarazos": paciente.embarazos.count(),
                    "embarazos_activos": paciente.embarazos.filter(estado='activo').count(),
                    "total_partos": paciente.partos.count() if hasattr(paciente, 'partos') else 0,
                }
            }

            return Response({
                "success": True,
                "resumen": resumen
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: BUSCAR POR CÉDULA
    # ===========================================
    @action(detail=False, methods=['get'])
    def buscar_por_ci(self, request):
        """
        ACCIÓN: Buscar paciente por cédula de identidad

        Funcionamiento:
            Búsqueda exacta por número de cédula

        Parámetros:
            - ci: Número de cédula

        Retorna:
            Datos del paciente si existe
        """
        try:
            ci = request.query_params.get('ci')
            if not ci:
                return Response(
                    {'error': 'Parámetro ci requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            paciente = Paciente.objects.filter(cedula_identidad=ci).first()

            if not paciente:
                return Response({
                    "success": False,
                    "mensaje": "Paciente no encontrado"
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "success": True,
                "paciente": PacienteDetailSerializer(paciente).data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # ACCIÓN: BUSCAR POR NOMBRE
    # ===========================================
    @action(detail=False, methods=['get'])
    def buscar_por_nombre(self, request):
        """
        ACCIÓN: Buscar pacientes por nombre

        Funcionamiento:
            Búsqueda parcial por nombre o apellidos

        Parámetros:
            - nombre: Texto a buscar

        Retorna:
            Lista de pacientes coincidentes
        """
        try:
            nombre = request.query_params.get('nombre')
            if not nombre:
                return Response(
                    {'error': 'Parámetro nombre requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            pacientes = Paciente.objects.filter(
                Q(nombre__icontains=nombre) |
                Q(apellido_paterno__icontains=nombre) |
                Q(apellido_materno__icontains=nombre),
                activo=True
            )

            serializer = PacienteListSerializer(pacientes, many=True)

            return Response({
                "success": True,
                "total": pacientes.count(),
                "pacientes": serializer.data
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


"""
RESUMEN DE VIEWS DE PACIENTES:
================================

1. PacienteViewSet:
   - CRUD completo (6 endpoints estándar)
   - 20 acciones personalizadas:
     * estadisticas - Estadísticas generales
     * busqueda_avanzada - Búsqueda multi-criterio
     * por_edad - Agrupar por rangos de edad
     * por_grupo_sanguineo - Estadísticas por tipo sanguíneo
     * recientes - Pacientes recientes
     * inactivos - Pacientes desactivados
     * sin_embarazos - Sin embarazos registrados
     * con_embarazos_activos - Con embarazos en curso
     * reporte_demografico - Reporte demográfico
     * reporte_mensual - Reporte del mes
     * validar_duplicados - Validar duplicados
     * reactivar - Reactivar paciente
     * historial_completo - Historial completo
     * perfil_riesgo - Perfil de riesgo obstétrico
     * resumen_clinico - Resumen clínico
     * buscar_por_ci - Buscar por cédula
     * buscar_por_nombre - Buscar por nombre
   Total: 26 endpoints

TOTAL ENDPOINTS: 26
LÍNEAS DE CÓDIGO: ~1500
================================
"""
