from rest_framework import viewsets, status, serializers  # ← AGREGAR serializers aquí
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import IntegrityError
from .models import Paciente
from .serializers import PacienteSerializer

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.filter(activo=True)
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cedula = self.request.query_params.get('cedula', None)
        if cedula:
            queryset = queryset.filter(cedula_identidad=cedula)
        return queryset
    
    def create(self, request, *args, **kwargs):
        id_clinico = request.data.get('id_clinico', '').strip()
        
        if not id_clinico:
            ultimo_paciente = Paciente.objects.all().order_by('id').last()
            if ultimo_paciente and ultimo_paciente.id_clinico:
                try:
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
                    "mensaje": "Paciente registrado exitosamente",
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
        except IntegrityError as e:
            return Response(
                {"error": "Error de integridad: Verifique que no existan datos duplicados."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        try:
            paciente = self.get_object()
            serializer = self.get_serializer(paciente, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "mensaje": "Paciente actualizado exitosamente",
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
        try:
            paciente = self.get_object()
            paciente.delete()
            return Response(
                {"mensaje": "Paciente eliminado permanentemente"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error al eliminar: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )