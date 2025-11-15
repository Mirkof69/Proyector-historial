# =============================================================================
# VIEWS DE LABORATORIO
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: laboratorio
# Descripción: ViewSets y vistas para gestión de exámenes de laboratorio
# Versión: 1.0.0
# =============================================================================

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import ExamenLaboratorio
from .serializers import (
    ExamenLaboratorioSerializer,
    ExamenLaboratorioListSerializer,
    ExamenLaboratorioCreateSerializer
)
from embarazos.models import Embarazo

# Configuración de logger
logger = logging.getLogger(__name__)


# =============================================================================
# PAGINACIÓN PERSONALIZADA
# =============================================================================

class ExamenLaboratorioPagination(PageNumberPagination):
    """
    Paginación personalizada para listados de exámenes de laboratorio.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Retorna respuesta paginada con metadata."""
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })


# =============================================================================
# VIEWSET PRINCIPAL DE EXÁMENES DE LABORATORIO
# =============================================================================

class ExamenLaboratorioViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de exámenes de laboratorio.

    Operaciones CRUD:
    - list: Listar todos los exámenes (con filtros)
    - create: Crear nuevo examen
    - retrieve: Obtener detalle de un examen
    - update: Actualizar examen completo
    - partial_update: Actualizar campos específicos
    - destroy: Eliminación lógica (soft delete)

    Acciones personalizadas:
    - por_embarazo: Exámenes de un embarazo específico
    - por_tipo: Filtrar por tipo de examen
    - pendientes: Exámenes pendientes de resultado
    - con_alertas: Exámenes con resultados anormales
    - estadisticas: Estadísticas generales
    - interpretar: Interpretación de resultados
    - comparar: Comparar resultados entre fechas
    """

    queryset = ExamenLaboratorio.objects.filter(activo=True)
    permission_classes = [IsAuthenticated]
    pagination_class = ExamenLaboratorioPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = [
        'embarazo__paciente__nombre',
        'embarazo__paciente__apellido',
        'tipo_examen',
        'laboratorio',
        'observaciones'
    ]

    ordering_fields = [
        'fecha_examen',
        'fecha_resultado',
        'tipo_examen',
        'estado',
        'fecha_registro'
    ]

    ordering = ['-fecha_examen']

    def get_serializer_class(self):
        """Retorna la clase de serializer apropiada."""
        if self.action == 'list':
            return ExamenLaboratorioListSerializer
        elif self.action == 'create':
            return ExamenLaboratorioCreateSerializer
        return ExamenLaboratorioSerializer

    def get_queryset(self):
        """
        Retorna queryset filtrado según parámetros de query.

        Parámetros disponibles:
        - embarazo_id: ID del embarazo
        - tipo: Tipo de examen
        - estado: Estado del examen (pendiente/completado)
        - fecha_desde: Fecha mínima
        - fecha_hasta: Fecha máxima
        - con_resultados: Solo exámenes con resultados (true/false)
        - laboratorio: Nombre del laboratorio
        """
        queryset = super().get_queryset()

        # Optimización con select_related
        queryset = queryset.select_related(
            'embarazo',
            'embarazo__paciente'
        )

        # Filtro por embarazo
        embarazo_id = self.request.query_params.get('embarazo_id', None)
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)

        # Filtro por tipo
        tipo = self.request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo_examen=tipo)

        # Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)

        # Filtro por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_examen__gte=fecha_desde)
            except ValueError:
                logger.warning(f"Formato de fecha inválido: {fecha_desde}")

        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_examen__lte=fecha_hasta)
            except ValueError:
                logger.warning(f"Formato de fecha inválido: {fecha_hasta}")

        # Filtro por resultados
        con_resultados = self.request.query_params.get('con_resultados', None)
        if con_resultados is not None:
            if con_resultados.lower() in ['true', '1', 'yes']:
                queryset = queryset.exclude(fecha_resultado__isnull=True)
            else:
                queryset = queryset.filter(fecha_resultado__isnull=True)

        # Filtro por laboratorio
        laboratorio = self.request.query_params.get('laboratorio', None)
        if laboratorio:
            queryset = queryset.filter(laboratorio__icontains=laboratorio)

        return queryset

    def create(self, request, *args, **kwargs):
        """Crea un nuevo examen de laboratorio."""
        try:
            # Validar embarazo
            embarazo_id = request.data.get('embarazo')
            if embarazo_id:
                try:
                    embarazo = Embarazo.objects.get(id=embarazo_id, activo=True)
                except Embarazo.DoesNotExist:
                    return Response(
                        {'error': 'El embarazo especificado no existe o no está activo'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            examen = serializer.save()

            logger.info(
                f"Examen laboratorio creado: ID={examen.id}, "
                f"Tipo={examen.tipo_examen}, "
                f"Usuario={request.user.username}"
            )

            return Response(
                ExamenLaboratorioSerializer(examen).data,
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return Response(
                {'error': 'Error al crear el examen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Actualiza un examen de laboratorio."""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            logger.info(f"Actualizando examen ID={instance.id} por usuario={request.user.username}")

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            examen = serializer.save()

            logger.info(f"Examen ID={instance.id} actualizado exitosamente")

            return Response(ExamenLaboratorioSerializer(examen).data)

        except ValidationError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return Response(
                {'error': 'Error al actualizar el examen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Soft delete de un examen."""
        try:
            instance = self.get_object()

            logger.info(
                f"Eliminando examen ID={instance.id}, "
                f"Usuario={request.user.username}"
            )

            instance.delete()  # Soft delete

            return Response(
                {'message': 'Examen eliminado exitosamente'},
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            logger.error(f"Error al eliminar: {str(e)}")
            return Response(
                {'error': 'Error al eliminar el examen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # =========================================================================
    # ACCIONES PERSONALIZADAS
    # =========================================================================

    @action(detail=False, methods=['get'], url_path='por-embarazo/(?P<embarazo_id>[^/.]+)')
    def por_embarazo(self, request, embarazo_id=None):
        """
        Lista todos los exámenes de un embarazo específico.

        URL: /api/laboratorio/por-embarazo/{embarazo_id}/
        """
        try:
            embarazo = get_object_or_404(Embarazo, id=embarazo_id, activo=True)

            examenes = self.queryset.filter(embarazo=embarazo).order_by('fecha_examen')

            info_embarazo = {
                'embarazo_id': embarazo.id,
                'paciente': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido}",
                'fecha_ur': embarazo.fecha_ur,
                'total_examenes': examenes.count(),
            }

            serializer = ExamenLaboratorioSerializer(examenes, many=True)

            return Response({
                'info_embarazo': info_embarazo,
                'examenes': serializer.data
            })

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                {'error': 'Error al obtener exámenes del embarazo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='por-tipo/(?P<tipo>[^/.]+)')
    def por_tipo(self, request, tipo=None):
        """
        Filtra exámenes por tipo específico.

        URL: /api/laboratorio/por-tipo/{tipo}/
        """
        try:
            tipos_validos = [t[0] for t in ExamenLaboratorio.TIPOS_EXAMEN]
            if tipo not in tipos_validos:
                return Response(
                    {'error': f'Tipo inválido. Tipos válidos: {tipos_validos}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            examenes = self.get_queryset().filter(tipo_examen=tipo)

            page = self.paginate_queryset(examenes)
            if page is not None:
                serializer = ExamenLaboratorioSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = ExamenLaboratorioSerializer(examenes, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                {'error': 'Error al filtrar exámenes'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Retorna exámenes pendientes de resultado.

        URL: /api/laboratorio/pendientes/
        """
        try:
            examenes = self.get_queryset().filter(estado='pendiente')

            page = self.paginate_queryset(examenes)
            if page is not None:
                serializer = ExamenLaboratorioSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = ExamenLaboratorioSerializer(examenes, many=True)
            return Response({
                'count': examenes.count(),
                'results': serializer.data
            })

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                {'error': 'Error al obtener exámenes pendientes'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def con_alertas(self, request):
        """
        Retorna exámenes con resultados anormales que requieren atención.

        URL: /api/laboratorio/con_alertas/

        Criterios de alerta:
        - Hemoglobina <10 g/dL (anemia severa)
        - Glucosa >126 mg/dL (diabetes)
        - Plaquetas <100000 (trombocitopenia severa)
        - Serología reactiva (VDRL, VIH)
        - Leucocitos en orina >10/campo
        - Proteinuria positiva ++ o +++
        """
        try:
            queryset = self.get_queryset()

            # Filtrar exámenes con alertas
            examenes_alerta = queryset.filter(
                Q(hemoglobina__lt=10.0) |  # Anemia severa
                Q(glucosa__gt=126.0) |  # Diabetes
                Q(plaquetas__lt=100000) |  # Trombocitopenia severa
                Q(vdrl='reactivo') |  # Sífilis
                Q(vih='reactivo') |  # VIH
                Q(hepatitis_b='reactivo') |  # Hepatitis B
                Q(orina_leucocitos__gt=10) |  # ITU probable
                Q(orina_proteinas__in=['positivo_2', 'positivo_3'])  # Proteinuria severa
            ).distinct()

            serializer = ExamenLaboratorioSerializer(examenes_alerta, many=True)

            return Response({
                'count': examenes_alerta.count(),
                'mensaje': 'Exámenes con resultados que requieren atención médica',
                'results': serializer.data
            })

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                {'error': 'Error al obtener exámenes con alertas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de exámenes de laboratorio.

        URL: /api/laboratorio/estadisticas/
        """
        try:
            queryset = self.get_queryset()

            # Total por tipo
            por_tipo = {}
            for tipo, nombre in ExamenLaboratorio.TIPOS_EXAMEN:
                count = queryset.filter(tipo_examen=tipo).count()
                por_tipo[tipo] = {'nombre': nombre, 'cantidad': count}

            # Promedios de valores importantes
            promedios = queryset.aggregate(
                hemoglobina_promedio=Avg('hemoglobina'),
                glucosa_promedio=Avg('glucosa'),
                plaquetas_promedio=Avg('plaquetas'),
                leucocitos_promedio=Avg('leucocitos'),
            )

            # Estados
            estados = {
                'pendientes': queryset.filter(estado='pendiente').count(),
                'completados': queryset.filter(estado='completado').count(),
            }

            # Serología reactiva
            serologia_reactiva = {
                'vdrl': queryset.filter(vdrl='reactivo').count(),
                'vih': queryset.filter(vih='reactivo').count(),
                'hepatitis_b': queryset.filter(hepatitis_b='reactivo').count(),
            }

            # Exámenes con anemia
            anemia = {
                'leve': queryset.filter(hemoglobina__gte=10.0, hemoglobina__lt=11.0).count(),
                'moderada': queryset.filter(hemoglobina__gte=7.0, hemoglobina__lt=10.0).count(),
                'severa': queryset.filter(hemoglobina__lt=7.0).count(),
            }

            return Response({
                'total_examenes': queryset.count(),
                'por_tipo': por_tipo,
                'estados': estados,
                'promedios': promedios,
                'serologia_reactiva': serologia_reactiva,
                'anemia': anemia,
                'fecha_consulta': timezone.now()
            })

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                {'error': 'Error al calcular estadísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def interpretar(self, request, pk=None):
        """
        Retorna interpretación detallada de un examen.

        URL: /api/laboratorio/{id}/interpretar/
        """
        try:
            examen = self.get_object()

            # Usar serializer completo que incluye interpretaciones
            serializer = ExamenLaboratorioSerializer(examen, context={'request': request})
            data = serializer.data

            # Resumen de interpretación
            interpretacion = {
                'examen_id': examen.id,
                'tipo': examen.get_tipo_examen_display(),
                'fecha': examen.fecha_examen,
                'estado_hemograma': data.get('estado_hemograma'),
                'estado_glucosa': data.get('estado_glucosa'),
                'estado_funcion_renal': data.get('estado_funcion_renal'),
                'estado_funcion_hepatica': data.get('estado_funcion_hepatica'),
                'alerta_infeccion_urinaria': data.get('alerta_infeccion_urinaria'),
            }

            # Recomendaciones generales
            recomendaciones = []

            # Evaluar hemoglobina
            if examen.hemoglobina:
                hb = float(examen.hemoglobina)
                if hb < 10.0:
                    recomendaciones.append('Anemia severa - Considerar suplementación con hierro IV')
                elif hb < 11.0:
                    recomendaciones.append('Anemia leve - Iniciar suplementación con hierro oral')

            # Evaluar glucosa
            if examen.glucosa:
                glucosa = float(examen.glucosa)
                if glucosa >= 126:
                    recomendaciones.append('Solicitar curva de tolerancia a la glucosa (CTOG)')
                elif glucosa >= 95:
                    recomendaciones.append('Glucosa elevada - Repetir en ayunas')

            # Evaluar serología
            if examen.vdrl == 'reactivo':
                recomendaciones.append('VDRL reactivo - Iniciar tratamiento para sífilis')
            if examen.vih == 'reactivo':
                recomendaciones.append('VIH reactivo - Derivar a infectología')

            # Evaluar infección urinaria
            if examen.orina_leucocitos and examen.orina_leucocitos > 5:
                recomendaciones.append('Solicitar urocultivo - Probable infección urinaria')

            interpretacion['recomendaciones'] = recomendaciones

            return Response(interpretacion)

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                {'error': 'Error al interpretar el examen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='comparar/(?P<embarazo_id>[^/.]+)')
    def comparar(self, request, embarazo_id=None):
        """
        Compara resultados de exámenes en el tiempo para un embarazo.

        URL: /api/laboratorio/comparar/{embarazo_id}/
        """
        try:
            embarazo = get_object_or_404(Embarazo, id=embarazo_id, activo=True)

            examenes = self.queryset.filter(embarazo=embarazo).order_by('fecha_examen')

            # Evolución de hemoglobina
            evolucion_hemoglobina = []
            for ex in examenes.filter(hemoglobina__isnull=False):
                evolucion_hemoglobina.append({
                    'fecha': ex.fecha_examen,
                    'valor': float(ex.hemoglobina),
                    'tipo': ex.get_tipo_examen_display()
                })

            # Evolución de glucosa
            evolucion_glucosa = []
            for ex in examenes.filter(glucosa__isnull=False):
                evolucion_glucosa.append({
                    'fecha': ex.fecha_examen,
                    'valor': float(ex.glucosa),
                    'tipo': ex.get_tipo_examen_display()
                })

            # Evolución de plaquetas
            evolucion_plaquetas = []
            for ex in examenes.filter(plaquetas__isnull=False):
                evolucion_plaquetas.append({
                    'fecha': ex.fecha_examen,
                    'valor': ex.plaquetas,
                    'tipo': ex.get_tipo_examen_display()
                })

            return Response({
                'embarazo_id': embarazo.id,
                'paciente': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido}",
                'total_examenes': examenes.count(),
                'evolucion_hemoglobina': evolucion_hemoglobina,
                'evolucion_glucosa': evolucion_glucosa,
                'evolucion_plaquetas': evolucion_plaquetas,
            })

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                {'error': 'Error al comparar exámenes'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
