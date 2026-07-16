"""=============================================================================
VIEWS - NOTAS DE EVOLUCIÓN
=============================================================================
ViewSet completo para el sistema de notas médicas de evolución
"""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import FetalMedicalPermission

from .models import NotaEvolucion
from .serializers import (
    NotaEvolucionCreateUpdateSerializer,
    NotaEvolucionListSerializer,
    NotaEvolucionSerializer,
)


class NotaEvolucionViewSet(viewsets.ModelViewSet):
    """ViewSet completo para CRUD de Notas de Evolución

    Incluye:
        pass
    - CRUD completo (list, create, retrieve, update, partial_update, destroy)
    - Filtrado por paciente, embarazo, medico, tipo_consulta
    - Búsqueda por motivo_consulta, diagnosticos
    - Ordenamiento por fecha_consulta
    - Acción personalizada para obtener notas por paciente
    """

    queryset = NotaEvolucion.objects.select_related(
        "paciente", "embarazo", "control_prenatal", "medico", "revisado_por",
    ).all()

    permission_classes = [FetalMedicalPermission]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Campos para filtrado exacto
    filterset_fields = {
        "paciente": ["exact"],
        "paciente__id_clinico": ["exact"],
        "embarazo": ["exact"],
        "medico": ["exact"],
        "tipo_consulta": ["exact"],
        "activo": ["exact"],
        "fecha_consulta": ["gte", "lte", "exact", "date"],
    }

    # Campos para búsqueda de texto
    search_fields = [
        "motivo_consulta",
        "diagnosticos",
        "examen_fisico",
        "plan_tratamiento",
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__ci",
        "paciente__id_clinico",
    ]

    # Campos para ordenamiento
    ordering_fields = [
        "fecha_consulta",
        "fecha_creacion",
        "tipo_consulta",
        "paciente__nombre",
    ]

    ordering = ["-fecha_consulta"]  # Ordenamiento por defecto

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción
        """
        if self.action == "list":
            return NotaEvolucionListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return NotaEvolucionCreateUpdateSerializer
        return NotaEvolucionSerializer

    def get_queryset(self):
        """Personaliza el queryset base
        Permite filtros adicionales por query params
        """
        queryset = super().get_queryset()

        # Filtro adicional: solo activas
        solo_activas = self.request.query_params.get("solo_activas", None)
        if solo_activas and solo_activas.lower() == "true":
            queryset = queryset.filter(activo=True)

        # Filtro adicional: rango de fechas
        fecha_desde = self.request.query_params.get("fecha_desde", None)
        fecha_hasta = self.request.query_params.get("fecha_hasta", None)

        if fecha_desde:
            queryset = queryset.filter(fecha_consulta__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_consulta__lte=fecha_hasta)

        # Filtro adicional: por médico responsable
        medico_id = self.request.query_params.get("medico_id", None)
        if medico_id:
            queryset = queryset.filter(medico_id=medico_id)

        # Filtro adicional: notas sin revisar
        sin_revisar = self.request.query_params.get("sin_revisar", None)
        if sin_revisar and sin_revisar.lower() == "true":
            queryset = queryset.filter(revisado_por__isnull=True)

        return queryset

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @extend_schema(
        summary="Obtener notas por paciente",
        description="Obtiene todas las notas de evolución de un paciente específico por query parameter 'paciente_id'.",
        responses={200: NotaEvolucionListSerializer(many=True)},
    )
    @action(
        detail=False, methods=["get"], url_path="por-paciente",
    )
    def notas_por_paciente(self, request):
        """Endpoint personalizado para obtener todas las notas de un paciente

        GET /api/notas-evolucion/por-paciente/?paciente_id={paciente_id}
        """
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response(
                {"error": "Se requiere paciente_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notas = self.get_queryset().filter(paciente_id=paciente_id)

        # Aplicar paginación
        page = self.paginate_queryset(notas)
        if page is not None:
            serializer = NotaEvolucionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotaEvolucionListSerializer(notas, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Obtener notas por embarazo",
        description="Obtiene todas las notas de evolución de un embarazo específico por query parameter 'embarazo_id'.",
        responses={200: NotaEvolucionListSerializer(many=True)},
    )
    @action(
        detail=False, methods=["get"], url_path="por_embarazo",
    )
    def notas_por_embarazo(self, request):
        """Endpoint personalizado para obtener todas las notas de un embarazo

        GET /api/notas-evolucion/por_embarazo/?embarazo_id={embarazo_id}
        """
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "Se requiere embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notas = self.get_queryset().filter(embarazo_id=embarazo_id)

        # Aplicar paginación
        page = self.paginate_queryset(notas)
        if page is not None:
            serializer = NotaEvolucionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotaEvolucionListSerializer(notas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="mis-notas")
    def mis_notas(self, request):
        """Endpoint para obtener las notas creadas por el médico autenticado

        GET /api/notas-evolucion/mis-notas/
        """
        notas = self.get_queryset().filter(medico=request.user)

        # Aplicar paginación
        page = self.paginate_queryset(notas)
        if page is not None:
            serializer = NotaEvolucionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotaEvolucionListSerializer(notas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="revisar")
    def revisar_nota(self, request, pk=None):
        """Endpoint para marcar una nota como revisada

        POST /api/notas-evolucion/{id}/revisar/

        Body (opcional):
            pass
        {
            "observaciones": "Texto adicional"
        }
        """
        from django.utils import timezone

        nota = self.get_object()

        # Validar que el usuario sea diferente al creador
        if nota.medico == request.user:
            return Response(
                {"detail": "No puedes revisar tus propias notas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Marcar como revisada
        nota.revisado_por = request.user
        nota.fecha_revision = timezone.now()

        # Agregar observaciones si se proporcionan
        observaciones_adicionales = request.data.get("observaciones", "")
        if observaciones_adicionales:
            nota.observaciones = f"{nota.observaciones}\n\n[Revisión por {request.user.nombre_completo}]: {observaciones_adicionales}"

        nota.save()

        serializer = NotaEvolucionSerializer(nota)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="estadisticas")
    def estadisticas(self, _request):
        """Endpoint para obtener estadísticas de las notas de evolución

        GET /api/notas-evolucion/estadisticas/
        """
        from django.db.models import Count

        queryset = self.get_queryset()

        # Contar por tipo de consulta
        por_tipo = (
            queryset.values("tipo_consulta")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # Contar notas sin revisar
        sin_revisar = queryset.filter(revisado_por__isnull=True).count()

        # Contar por médico
        por_medico = (
            queryset.values("medico__id", "medico__nombre", "medico__apellido_paterno")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )  # Top 10 médicos

        estadisticas = {
            "total_notas": queryset.count(),
            "notas_activas": queryset.filter(activo=True).count(),
            "notas_sin_revisar": sin_revisar,
            "por_tipo_consulta": list(por_tipo),
            "top_medicos": list(por_medico),
        }

        return Response(estadisticas)
