"""
===========================================
VIEWS - MÓDULO PACIENTES
Descripción: API REST para gestión de pacientes
Endpoints: CRUD completo + búsqueda avanzada
===========================================
"""

from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import IntegrityError
from django.db.models import Q, Count
from rest_framework import serializers
from .models import Paciente
from .serializers import PacienteSerializer, PacienteListSerializer, PacienteDetailSerializer


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de pacientes.

    Proporciona operaciones CRUD y funcionalidades adicionales:
    - Listado con filtros
    - Búsqueda avanzada
    - Soft delete
    - Reactivación
    - Estadísticas
    """

    queryset = Paciente.objects.filter(activo=True).select_related()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'id_clinico', 'cedula_identidad']
    ordering_fields = ['fecha_registro', 'nombre', 'apellido_paterno', 'id_clinico']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.

        - list: Serializer simplificado (más rápido)
        - retrieve: Serializer completo con relaciones
        - default: Serializer estándar
        """
        if self.action == 'list':
            return PacienteListSerializer
        elif self.action == 'retrieve':
            return PacienteDetailSerializer
        return PacienteSerializer

    def get_queryset(self):
        """
        Personaliza el queryset con filtros adicionales.

        Parámetros de query:
        - ?cedula=XXX: Buscar por cédula
        - ?activo=true/false: Filtrar por estado
        - ?edad_min=X: Edad mínima
        - ?edad_max=Y: Edad máxima
        - ?genero=X: Filtrar por género
        - ?grupo_sanguineo=X: Filtrar por grupo sanguíneo
        - ?search=X: Búsqueda en múltiples campos
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
        Crear un nuevo paciente.

        Funcionalidades:
        - Auto-generación de ID clínico si no se proporciona
        - Validación exhaustiva de datos
        - Manejo de errores personalizado
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
        Actualizar un paciente existente.

        Soporta actualización parcial (PATCH) y completa (PUT).
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
        ✅ SOFT DELETE: Desactivar paciente en lugar de eliminarlo.

        El paciente se marca como inactivo pero permanece en la base de datos.
        Esto preserva la integridad referencial con embarazos y controles.
        """
        try:
            paciente = self.get_object()
            paciente.soft_delete()  # Usa el método del modelo

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
    # ACTIONS PERSONALIZADOS
    # ===========================================

    @action(detail=True, methods=['post'])
    def reactivar(self, request, pk=None):
        """
        Reactivar un paciente desactivado.

        POST /api/pacientes/{id}/reactivar/
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

    @action(detail=True, methods=['get'])
    def historial_completo(self, request, pk=None):
        """
        Obtener historial completo del paciente.

        Incluye:
        - Datos del paciente
        - Embarazos
        - Controles prenatales
        - Partos (cuando esté implementado)
        - Exámenes de laboratorio (cuando esté implementado)

        GET /api/pacientes/{id}/historial_completo/
        """
        try:
            paciente = self.get_object()

            # Obtener embarazos relacionados
            embarazos = paciente.embarazos.all().order_by('-fecha_registro')

            # Obtener controles relacionados
            controles = paciente.controles.all().order_by('-fecha_control')[:10]  # Últimos 10

            return Response({
                "success": True,
                "paciente": PacienteDetailSerializer(paciente).data,
                "estadisticas": {
                    "total_embarazos": embarazos.count(),
                    "embarazos_activos": embarazos.filter(estado='activo').count(),
                    "total_controles": controles.count(),
                },
                "embarazos": [
                    {
                        "id": e.id,
                        "numero_gesta": e.numero_gesta,
                        "fecha_ultima_menstruacion": e.fecha_ultima_menstruacion,
                        "fecha_probable_parto": e.fecha_probable_parto,
                        "estado": e.estado,
                        "riesgo_embarazo": e.riesgo_embarazo,
                    }
                    for e in embarazos[:5]  # Últimos 5 embarazos
                ]
            })
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error al obtener historial: {str(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Estadísticas generales de pacientes.

        GET /api/pacientes/estadisticas/
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

            return Response({
                "success": True,
                "estadisticas": {
                    "total_pacientes": total_pacientes,
                    "pacientes_activos": activos,
                    "pacientes_inactivos": inactivos,
                    "por_genero": list(por_genero),
                    "por_grupo_sanguineo": list(por_grupo),
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

    @action(detail=False, methods=['get'])
    def busqueda_avanzada(self, request):
        """
        Búsqueda avanzada de pacientes.

        Parámetros:
        - ?q=texto: Buscar en nombre, apellidos, CI, ID clínico
        - ?genero=X: Filtrar por género
        - ?edad_min=X&edad_max=Y: Rango de edad
        - ?grupo_sanguineo=X: Filtrar por grupo sanguíneo

        GET /api/pacientes/busqueda_avanzada/?q=maria&genero=femenino
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
