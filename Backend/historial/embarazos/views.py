from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Embarazo
from .serializers import EmbarazoSerializer

class EmbarazoViewSet(viewsets.ModelViewSet):
    queryset = Embarazo.objects.all()
    serializer_class = EmbarazoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por paciente
        paciente_id = self.request.query_params.get('paciente', None)
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        # Filtrar por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-fecha_registro')
    
    def create(self, request, *args, **kwargs):
        """Crear embarazo con validaciones"""
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "mensaje": "Embarazo registrado exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            return Response(
                {"errores": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        """Actualizar embarazo"""
        try:
            embarazo = self.get_object()
            serializer = self.get_serializer(embarazo, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "mensaje": "Embarazo actualizado exitosamente",
                "data": serializer.data
            })
        except serializers.ValidationError as e:
            return Response(
                {"errores": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al actualizar: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, pk=None):
        """Cambiar estado a finalizado"""
        try:
            embarazo = self.get_object()
            embarazo.estado = 'finalizado'
            embarazo.save()
            return Response(
                {"mensaje": "Embarazo finalizado correctamente"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error al finalizar: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar el estado del embarazo"""
        embarazo = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado not in ['activo', 'finalizado', 'perdida']:
            return Response(
                {"error": "Estado inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        embarazo.estado = nuevo_estado
        embarazo.save()
        
        return Response({
            "mensaje": f"Estado cambiado a {nuevo_estado}",
            "data": self.get_serializer(embarazo).data
        })