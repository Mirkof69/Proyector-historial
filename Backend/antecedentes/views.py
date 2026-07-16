"""=============================================================================
ANTECEDENTES - VIEWS
=============================================================================
ViewSets para antecedentes gineco-obstétricos y patológicos
=============================================================================
"""

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import FetalMedicalPermission

from .models import AntecedenteGinecoObstetrico, AntecedentePatologico
from .serializers import (
    AntecedenteGinecoObstetricoSerializer,
    AntecedentePatologicoSerializer,
)


class AntecedenteGinecoObstetricoViewSet(viewsets.ModelViewSet):
    """ViewSet para antecedentes gineco-obstétricos
    """

    queryset = AntecedenteGinecoObstetrico.objects.all()
    serializer_class = AntecedenteGinecoObstetricoSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "paciente",
        "ciclos_menstruales",
        "gestas",
        "partos",
        "cesareas",
    ]
    search_fields = ["paciente__nombre", "paciente__apellido_paterno", "paciente__ci"]
    ordering_fields = ["fecha_registro", "menarquia_edad", "gestas"]
    ordering = ["-fecha_registro"]

    def get_queryset(self):
        """Optimiza queryset con select_related"""
        return AntecedenteGinecoObstetrico.objects.select_related(
            "paciente", "modificado_por",
        )

    def perform_create(self, serializer):
        """Asigna usuario que modifica al crear"""
        serializer.save(modificado_por=self.request.user)

    def perform_update(self, serializer):
        """Asigna usuario que modifica al actualizar"""
        serializer.save(modificado_por=self.request.user)

    @action(detail=False, methods=["get"])
    def by_paciente(self, request):
        """Obtiene antecedente por paciente_id"""
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response(
                {"error": "Se requiere paciente_id"}, status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            antecedente = self.get_queryset().get(paciente_id=paciente_id)
            serializer = self.get_serializer(antecedente)
            return Response(serializer.data)
        except AntecedenteGinecoObstetrico.DoesNotExist:
            return Response(
                {"error": "No se encontró antecedente para este paciente"},
                status=status.HTTP_404_NOT_FOUND,
            )


class AntecedentePatologicoViewSet(viewsets.ModelViewSet):
    """ViewSet para antecedentes patológicos
    """

    queryset = AntecedentePatologico.objects.all()
    serializer_class = AntecedentePatologicoSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "paciente",
        "tipo",
        "tiene_alergias",
        "diabetes",
        "hipertension",
        "cardiopatias",
        "preeclampsia_previa",
        "eclampsia_previa",
    ]
    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__ci",
        "alergias_medicamentos",
        "otras_enfermedades",
    ]
    ordering_fields = ["fecha_registro", "tipo"]
    ordering = ["-fecha_registro"]

    def get_queryset(self):
        """Optimiza queryset con select_related"""
        return AntecedentePatologico.objects.select_related(
            "paciente", "registrado_por",
        )

    def perform_create(self, serializer):
        """Asigna usuario que registra al crear"""
        serializer.save(registrado_por=self.request.user)

    @action(detail=False, methods=["get"])
    def por_paciente(self, request):
        """Obtiene todos los antecedentes de un paciente"""
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response(
                {"error": "Se requiere paciente_id"}, status=status.HTTP_400_BAD_REQUEST,
            )

        antecedentes = self.get_queryset().filter(paciente_id=paciente_id)
        serializer = self.get_serializer(antecedentes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def con_riesgo(self, _request):
        """Lista antecedentes con factores de riesgo"""
        # Filtra pacientes con factores de riesgo importantes
        antecedentes_riesgo = (
            self.get_queryset()
            .filter(
                Q(diabetes=True)
                | Q(hipertension=True)
                | Q(cardiopatias=True)
                | Q(preeclampsia_previa=True)
                | Q(eclampsia_previa=True),
            )
            .distinct()
        )

        serializer = self.get_serializer(antecedentes_riesgo, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def con_alergias(self, _request):
        """Lista antecedentes con alergias"""
        antecedentes_alergias = self.get_queryset().filter(tiene_alergias=True)
        serializer = self.get_serializer(antecedentes_alergias, many=True)
        return Response(serializer.data)
