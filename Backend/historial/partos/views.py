# =============================================================================
# VIEWS DE PARTOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: partos
# Descripción: ViewSets y vistas para gestión de partos
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
import logging

from .models import Parto
from .serializers import PartoSerializer, PartoListSerializer, PartoCreateSerializer
from embarazos.models import Embarazo
from pacientes.models import Paciente

logger = logging.getLogger(__name__)


class PartoPagination(PageNumberPagination):
    """Paginación para partos."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {'next': self.get_next_link(), 'previous': self.get_previous_link()},
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.page_size,
            'results': data
        })


class PartoViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gestión de partos."""

    queryset = Parto.objects.filter(activo=True)
    permission_classes = [IsAuthenticated]
    pagination_class = PartoPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = [
        'paciente__nombre',
        'paciente__apellido',
        'tipo_parto',
        'medico_atencion',
        'lugar_parto',
        'observaciones'
    ]

    ordering_fields = [
        'fecha_hora_parto',
        'tipo_parto',
        'peso_rn_gramos',
        'fecha_registro'
    ]

    ordering = ['-fecha_hora_parto']

    def get_serializer_class(self):
        if self.action == 'list':
            return PartoListSerializer
        elif self.action == 'create':
            return PartoCreateSerializer
        return PartoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('embarazo', 'paciente', 'medico')

        # Filtros
        embarazo_id = self.request.query_params.get('embarazo_id')
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)

        paciente_id = self.request.query_params.get('paciente_id')
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)

        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_parto=tipo)

        # Filtro por fechas
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
                queryset = queryset.filter(fecha_hora_parto__gte=fecha_desde)
            except ValueError:
                pass

        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                queryset = queryset.filter(fecha_hora_parto__lte=fecha_hasta)
            except ValueError:
                pass

        # Filtro por complicaciones
        con_complicaciones = self.request.query_params.get('con_complicaciones')
        if con_complicaciones == 'true':
            queryset = queryset.filter(
                Q(complicaciones_maternas__isnull=False) |
                Q(complicaciones_neonatales__isnull=False) |
                Q(hemorragia_postparto=True)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            parto = serializer.save()

            logger.info(f"Parto creado: ID={parto.id}, Tipo={parto.tipo_parto}, Usuario={request.user.username}")

            return Response(
                PartoSerializer(parto).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return Response({'error': 'Error al crear el parto'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='por-paciente/(?P<paciente_id>[^/.]+)')
    def por_paciente(self, request, paciente_id=None):
        """Lista partos de una paciente."""
        try:
            paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
            partos = self.queryset.filter(paciente=paciente).order_by('-fecha_hora_parto')

            serializer = PartoSerializer(partos, many=True)
            return Response({
                'paciente': paciente.get_nombre_completo(),
                'total_partos': partos.count(),
                'partos': serializer.data
            })
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response({'error': 'Error al obtener partos'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de partos."""
        try:
            queryset = self.get_queryset()

            # Por tipo
            por_tipo = {}
            for tipo, nombre in Parto.TIPOS_PARTO:
                count = queryset.filter(tipo_parto=tipo).count()
                por_tipo[tipo] = {'nombre': nombre, 'cantidad': count}

            # Promedios
            promedios = queryset.aggregate(
                peso_promedio=Avg('peso_rn_gramos'),
                apgar_promedio=Avg('apgar_5_min'),
                edad_gestacional_promedio=Avg('edad_gestacional_parto_semanas'),
                duracion_promedio=Avg('duracion_trabajo_parto_horas'),
            )

            # Clasificaciones
            prematuros = queryset.filter(edad_gestacional_parto_semanas__lt=37).count()
            bajo_peso = queryset.filter(peso_rn_gramos__lt=2500).count()
            macrosomia = queryset.filter(peso_rn_gramos__gt=4000).count()

            return Response({
                'total_partos': queryset.count(),
                'por_tipo': por_tipo,
                'promedios': promedios,
                'clasificaciones': {
                    'prematuros': prematuros,
                    'bajo_peso': bajo_peso,
                    'macrosomia': macrosomia,
                },
                'fecha_consulta': timezone.now()
            })
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response({'error': 'Error al calcular estadísticas'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def con_complicaciones(self, request):
        """Partos con complicaciones."""
        try:
            partos = self.get_queryset().filter(
                Q(complicaciones_maternas__isnull=False) |
                Q(complicaciones_neonatales__isnull=False) |
                Q(hemorragia_postparto=True) |
                Q(apgar_5_min__lt=7)
            ).distinct()

            serializer = PartoSerializer(partos, many=True)
            return Response({
                'count': partos.count(),
                'mensaje': 'Partos que requieren seguimiento especial',
                'results': serializer.data
            })
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response({'error': 'Error al obtener partos con complicaciones'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
