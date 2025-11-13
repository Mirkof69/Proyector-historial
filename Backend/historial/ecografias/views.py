from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Ecografia, BiometriaFetal, AnatomiaFetal, AnexosFetales, ImagenEcografia
from .serializers import (
    EcografiaSerializer, 
    EcografiaListSerializer,
    ImagenEcografiaSerializer
)

class EcografiaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Ecografías con CRUD
    """
    queryset = Ecografia.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EcografiaListSerializer
        return EcografiaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros opcionales
        embarazo_id = self.request.query_params.get('embarazo', None)
        paciente_id = self.request.query_params.get('paciente', None)
        tipo = self.request.query_params.get('tipo', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if embarazo_id:
            queryset = queryset.filter(embarazo_id=embarazo_id)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        if tipo:
            queryset = queryset.filter(tipo_ecografia=tipo)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_ecografia__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_ecografia__lte=fecha_hasta)
        
        return queryset.select_related('embarazo', 'paciente', 'medico').order_by('-fecha_ecografia')
    
    def perform_create(self, serializer):
        # Asignar automáticamente el médico que está logueado
        serializer.save(medico=self.request.user)
    
    @action(detail=True, methods=['post'])
    def subir_imagen(self, request, pk=None):
        """Endpoint para subir imágenes a una ecografía"""
        ecografia = self.get_object()
        archivo = request.FILES.get('archivo')
        
        if not archivo:
            return Response(
                {'error': 'No se proporcionó ningún archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        imagen = ImagenEcografia.objects.create(
            ecografia=ecografia,
            archivo=archivo,
            tipo_imagen=request.data.get('tipo_imagen', ''),
            descripcion=request.data.get('descripcion', '')
        )
        
        serializer = ImagenEcografiaSerializer(imagen)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def imagenes(self, request, pk=None):
        """Obtener todas las imágenes de una ecografía"""
        ecografia = self.get_object()
        imagenes = ecografia.imagenes.all()
        serializer = ImagenEcografiaSerializer(imagenes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def eliminar_imagen(self, request, pk=None):
        """Eliminar una imagen específica"""
        imagen_id = request.data.get('imagen_id')
        
        if not imagen_id:
            return Response(
                {'error': 'Se requiere imagen_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            imagen = ImagenEcografia.objects.get(id=imagen_id, ecografia_id=pk)
            imagen.delete()
            return Response({'mensaje': 'Imagen eliminada correctamente'})
        except ImagenEcografia.DoesNotExist:
            return Response(
                {'error': 'Imagen no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def update(self, request, pk=None):
        """Actualizar ecografía completa"""
        ecografia = self.get_object()
        serializer = self.get_serializer(ecografia, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def destroy(self, request, pk=None):
        """Eliminar ecografía"""
        ecografia = self.get_object()
        ecografia.delete()
        return Response(
            {'mensaje': 'Ecografía eliminada correctamente'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de ecografías"""
        total = Ecografia.objects.count()
        por_tipo = {}
        
        for tipo, nombre in Ecografia.TIPO_CHOICES:
            count = Ecografia.objects.filter(tipo_ecografia=tipo).count()
            por_tipo[nombre] = count
        
        return Response({
            'total_ecografias': total,
            'por_tipo': por_tipo
        })