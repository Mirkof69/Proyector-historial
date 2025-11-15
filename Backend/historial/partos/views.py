"""
===========================================
MÓDULO: VIEWS DE PARTOS
===========================================
CRUD completo + estadísticas para gestión de partos
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg
from .models import Parto, RecienNacido, ComplicacionParto
from .serializers import (
    PartoSerializer, PartoCreateSerializer, PartoDetailSerializer,
    RecienNacidoSerializer, ComplicacionPartoSerializer
)


class PartoViewSet(viewsets.ModelViewSet):
    """ViewSet completo para Partos"""
    queryset = Parto.objects.all()
    serializer_class = PartoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PartoCreateSerializer
        elif self.action == 'retrieve':
            return PartoDetailSerializer
        return PartoSerializer
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de partos"""
        total = Parto.objects.count()
        por_tipo = {}
        for tipo, _ in Parto.TIPOS_PARTO:
            por_tipo[tipo] = Parto.objects.filter(tipo_parto=tipo).count()
        
        return Response({
            'total_partos': total,
            'por_tipo': por_tipo,
        })


class RecienNacidoViewSet(viewsets.ModelViewSet):
    """ViewSet para Recién Nacidos"""
    queryset = RecienNacido.objects.all()
    serializer_class = RecienNacidoSerializer
    permission_classes = [IsAuthenticated]


class ComplicacionPartoViewSet(viewsets.ModelViewSet):
    """ViewSet para Complicaciones"""
    queryset = ComplicacionParto.objects.all()
    serializer_class = ComplicacionPartoSerializer
    permission_classes = [IsAuthenticated]
