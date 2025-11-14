from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import Embarazo
from .serializers import (
    EmbarazoSerializer,
    EmbarazoListSerializer,
    EmbarazoCreateUpdateSerializer
)
from pacientes.models import Paciente


class EmbarazoViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Embarazos
    
    Endpoints disponibles:
    - GET /api/embarazos/ - Listar todos los embarazos
    - POST /api/embarazos/ - Crear nuevo embarazo
    - GET /api/embarazos/{id}/ - Obtener detalle de embarazo
    - PUT /api/embarazos/{id}/ - Actualizar embarazo completo
    - PATCH /api/embarazos/{id}/ - Actualizar embarazo parcial
    - DELETE /api/embarazos/{id}/ - Cambiar estado a finalizado
    - GET /api/embarazos/activos/ - Solo embarazos activos
    - GET /api/embarazos/por_paciente/?paciente_id=X - Embarazos de un paciente
    - GET /api/embarazos/estadisticas/ - Estadísticas generales
    """
    
    queryset = Embarazo.objects.select_related('paciente').all().order_by('-fecha_registro')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'tipo_embarazo', 'riesgo_embarazo', 'paciente']
    search_fields = ['paciente__nombre', 'paciente__apellido_paterno', 'paciente__id_clinico', 'medico_responsable']
    ordering_fields = ['fecha_registro', 'fecha_ultima_menstruacion', 'fecha_probable_parto']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return EmbarazoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmbarazoCreateUpdateSerializer
        return EmbarazoSerializer
    
    def get_queryset(self):
        """Filtra el queryset según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar por rango de fechas FUM
        fum_desde = self.request.query_params.get('fum_desde', None)
        fum_hasta = self.request.query_params.get('fum_hasta', None)
        
        if fum_desde:
            queryset = queryset.filter(fecha_ultima_menstruacion__gte=fum_desde)
        if fum_hasta:
            queryset = queryset.filter(fecha_ultima_menstruacion__lte=fum_hasta)
        
        # Filtrar por semanas de gestación
        semanas_min = self.request.query_params.get('semanas_min', None)
        semanas_max = self.request.query_params.get('semanas_max', None)
        
        if semanas_min or semanas_max:
            from datetime import date, timedelta
            today = date.today()
            
            if semanas_min:
                fecha_max_fum = today - timedelta(weeks=int(semanas_min))
                queryset = queryset.filter(fecha_ultima_menstruacion__lte=fecha_max_fum)
            
            if semanas_max:
                fecha_min_fum = today - timedelta(weeks=int(semanas_max))
                queryset = queryset.filter(fecha_ultima_menstruacion__gte=fecha_min_fum)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo embarazo con validaciones"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retornar con serializer completo
        embarazo = Embarazo.objects.get(id=serializer.instance.id)
        return_serializer = EmbarazoSerializer(embarazo)
        
        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def destroy(self, request, *args, **kwargs):
        """Cambiar estado a finalizado en lugar de eliminar"""
        instance = self.get_object()
        instance.estado = 'finalizado'
        instance.save()
        
        return Response(
            {
                'message': 'Embarazo finalizado correctamente',
                'id': instance.id,
                'uuid': str(instance.uuid)
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Listar solo embarazos activos"""
        embarazos = self.queryset.filter(estado='activo')
        
        page = self.paginate_queryset(embarazos)
        if page is not None:
            serializer = EmbarazoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = EmbarazoListSerializer(embarazos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='por_paciente')
    def por_paciente(self, request):
        """Obtener todos los embarazos de un paciente específico"""
        paciente_id = request.query_params.get('paciente_id', None)
        
        if not paciente_id:
            return Response(
                {'error': 'Debe proporcionar el parámetro paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {'error': 'Paciente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        embarazos = self.queryset.filter(paciente=paciente).order_by('-fecha_registro')
        serializer = EmbarazoSerializer(embarazos, many=True)
        
        from pacientes.serializers import PacienteSerializer
        return Response({
            'paciente': PacienteSerializer(paciente).data,
            'embarazos': serializer.data,
            'total': embarazos.count()
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de embarazos"""
        total = Embarazo.objects.count()
        activos = Embarazo.objects.filter(estado='activo').count()
        finalizados = Embarazo.objects.filter(estado='finalizado').count()
        perdidas = Embarazo.objects.filter(estado='perdida').count()
        
        # Por tipo
        por_tipo = Embarazo.objects.filter(estado='activo').values('tipo_embarazo').annotate(
            total=Count('id')
        )
        
        # Por riesgo
        por_riesgo = Embarazo.objects.filter(estado='activo').values('riesgo_embarazo').annotate(
            total=Count('id')
        )
        
        # Alto riesgo activos
        alto_riesgo = Embarazo.objects.filter(
            estado='activo',
            riesgo_embarazo='alto'
        ).count()
        
        return Response({
            'total_embarazos': total,
            'activos': activos,
            'finalizados': finalizados,
            'perdidas': perdidas,
            'por_tipo': list(por_tipo),
            'por_riesgo': list(por_riesgo),
            'alto_riesgo_activos': alto_riesgo,
        })
    
    @action(detail=True, methods=['get'])
    def controles(self, request, pk=None):
        """Obtener todos los controles prenatales de un embarazo"""
        embarazo = self.get_object()
        controles = embarazo.controles_prenatales.all().order_by('-fecha_control')
        
        from controles.serializers import ControlPrenatalSerializer
        serializer = ControlPrenatalSerializer(controles, many=True)
        
        return Response({
            'embarazo': EmbarazoSerializer(embarazo).data,
            'controles': serializer.data,
            'total': controles.count()
        })
    
    @action(detail=True, methods=['post'])
    def reactivar(self, request, pk=None):
        """Reactivar un embarazo finalizado"""
        embarazo = self.get_object()
        
        if embarazo.estado == 'activo':
            return Response(
                {'error': 'El embarazo ya está activo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        embarazo.estado = 'activo'
        embarazo.save()
        
        return Response({
            'message': 'Embarazo reactivado correctamente',
            'embarazo': EmbarazoSerializer(embarazo).data
        })