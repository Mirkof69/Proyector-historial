from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import Paciente
from .serializers import (
    PacienteSerializer,
    PacienteListSerializer,
    PacienteCreateUpdateSerializer
)
import uuid


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Pacientes
    
    Endpoints disponibles:
    - GET /api/pacientes/ - Listar todos los pacientes
    - POST /api/pacientes/ - Crear nuevo paciente
    - GET /api/pacientes/{id}/ - Obtener detalle de paciente
    - PUT /api/pacientes/{id}/ - Actualizar paciente completo
    - PATCH /api/pacientes/{id}/ - Actualizar paciente parcial
    - DELETE /api/pacientes/{id}/ - Eliminar paciente (soft delete)
    - GET /api/pacientes/buscar/?q=texto - Búsqueda global
    - GET /api/pacientes/estadisticas/ - Estadísticas generales
    """
    
    queryset = Paciente.objects.all().order_by('-fecha_registro')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['genero', 'activo']
    search_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'id_clinico', 'cedula_identidad']
    ordering_fields = ['fecha_registro', 'nombre', 'apellido_paterno']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return PacienteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PacienteCreateUpdateSerializer
        return PacienteSerializer
    
    def get_queryset(self):
        """Filtra el queryset según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar solo activos si se especifica
        solo_activos = self.request.query_params.get('solo_activos', None)
        if solo_activos == 'true':
            queryset = queryset.filter(activo=True)
        
        # Filtrar por rango de edad
        edad_min = self.request.query_params.get('edad_min', None)
        edad_max = self.request.query_params.get('edad_max', None)
        
        if edad_min or edad_max:
            from datetime import date, timedelta
            today = date.today()
            
            if edad_max:
                fecha_min = today - timedelta(days=int(edad_max)*365.25)
                queryset = queryset.filter(fecha_nacimiento__gte=fecha_min)
            
            if edad_min:
                fecha_max = today - timedelta(days=int(edad_min)*365.25)
                queryset = queryset.filter(fecha_nacimiento__lte=fecha_max)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo paciente con ID clínico automático"""
        # Generar ID clínico único
        id_clinico = f"HC-{uuid.uuid4().hex[:8].upper()}"
        
        # Verificar que no exista (muy improbable pero por seguridad)
        while Paciente.objects.filter(id_clinico=id_clinico).exists():
            id_clinico = f"HC-{uuid.uuid4().hex[:8].upper()}"
        
        # Agregar ID clínico a los datos
        data = request.data.copy()
        data['id_clinico'] = id_clinico
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retornar con serializer completo
        paciente = Paciente.objects.get(id=serializer.instance.id)
        return_serializer = PacienteSerializer(paciente)
        
        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete - marcar como inactivo en lugar de eliminar"""
        instance = self.get_object()
        instance.activo = False
        instance.save()
        
        return Response(
            {
                'message': 'Paciente desactivado correctamente',
                'id': instance.id,
                'id_clinico': instance.id_clinico
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        """
        Búsqueda global de pacientes
        Parámetros:
        - q: texto a buscar
        """
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {'error': 'Debe proporcionar un parámetro de búsqueda "q"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Búsqueda en múltiples campos
        pacientes = Paciente.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido_paterno__icontains=query) |
            Q(apellido_materno__icontains=query) |
            Q(id_clinico__icontains=query) |
            Q(cedula_identidad__icontains=query) |
            Q(email__icontains=query)
        ).distinct()[:20]  # Limitar a 20 resultados
        
        serializer = PacienteListSerializer(pacientes, many=True)
        return Response({
            'count': pacientes.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de pacientes"""
        total = Paciente.objects.count()
        activos = Paciente.objects.filter(activo=True).count()
        inactivos = total - activos
        
        # Por género
        por_genero = Paciente.objects.filter(activo=True).values('genero').annotate(
            total=Count('id')
        )
        
        # Con embarazos activos
        con_embarazos = Paciente.objects.filter(
            embarazos__estado='activo',
            activo=True
        ).distinct().count()
        
        return Response({
            'total_pacientes': total,
            'activos': activos,
            'inactivos': inactivos,
            'por_genero': list(por_genero),
            'con_embarazos_activos': con_embarazos,
        })
    
    @action(detail=True, methods=['get'])
    def embarazos(self, request, pk=None):
        """Obtener todos los embarazos de un paciente"""
        paciente = self.get_object()
        embarazos = paciente.embarazos.all().order_by('-fecha_registro')
        
        from embarazos.serializers import EmbarazoSerializer
        serializer = EmbarazoSerializer(embarazos, many=True)
        
        return Response({
            'paciente': PacienteSerializer(paciente).data,
            'embarazos': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """Reactivar un paciente inactivo"""
        paciente = self.get_object()
        paciente.activo = True
        paciente.save()
        
        return Response({
            'message': 'Paciente activado correctamente',
            'paciente': PacienteSerializer(paciente).data
        })