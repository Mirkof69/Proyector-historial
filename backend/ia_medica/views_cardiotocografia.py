"""Endpoint del clasificador de cardiotocografía (modelo supervisado).

GET  /api/ia/cardiotocografia/   variables que pide el modelo en uso y su fiabilidad
POST /api/ia/cardiotocografia/   {linea_base, aceleraciones, ...} → normal / sospechosa / patológica

GET  /api/ia/cardiotocografias/?paciente_id=  las ya guardadas, paginadas

Si no hay modelo o faltan datos, responde 409 con el motivo y ninguna clase.
Cada clasificación queda auditada; con `paciente_id` queda además en su historial.
"""
from __future__ import annotations

import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.filtros import BusquedaClinicaFilter
from core.permissions import EsSoloMedico, FetalMedicalPermission

from .models import RegistroCardiotocografia
from .serializers import RegistroCardiotocografiaSerializer

logger = logging.getLogger(__name__)


@extend_schema(summary="Clasificar una cardiotocografía (normal, sospechosa, patológica)",
               request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
@permission_classes([EsSoloMedico])
def cardiotocografia(request):
    from ia_medica.ml import cardiotocografia as ctg

    if request.method == "GET":
        try:
            _, ficha = ctg.cargar()
            modelo = {"version": ficha["version"], "algoritmo": ficha["descripcion"], "dataset": ficha["dataset"],
                      "prueba": {k: ficha["prueba"][k] for k in ("exactitud", "exactitud_ic95", "f1_macro",
                                                                 "sensibilidad", "sensibilidad_patologica_ic95")},
                      "registros_prueba": ficha["registros_prueba"], "limites": ficha["limites"]}
        except ctg.CTGNoDisponible as e:
            modelo = {"error": str(e)}
        return Response({"variables": ctg.variables_requeridas(), "modelo": modelo})

    try:
        valores = {k: (float(v) if v not in (None, "") else None) for k, v in request.data.items()
                   if k in {d[0] for d in ctg.VARIABLES.values()}}
    except (TypeError, ValueError):
        return Response({"error": "Todos los valores tienen que ser números."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        resultado = ctg.clasificar(valores)
    except ctg.CTGNoDisponible as e:
        return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

    paciente = request.data.get("paciente_id")
    registro_id = _guardar_en_historial(request, paciente, valores, resultado) if paciente else None
    resultado = {**resultado, "guardado": registro_id is not None, "registro_id": registro_id}
    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(
            usuario=request.user, accion="CONSULTA_IA", modulo="Cardiotocografia",
            detalle=(f"CTG{f' paciente {paciente}' if paciente else ''}: {resultado['clase_nombre']} "
                     f"(p={resultado['probabilidades'][resultado['clase']]:.2f}, modelo {resultado['modelo']['version']})"),
            request=request,
        )
    except Exception:
        logger.warning("No se pudo auditar la clasificación de CTG", exc_info=True)
    return Response(resultado)


def _guardar_en_historial(request, paciente_id, valores: dict, resultado: dict) -> int | None:
    """Deja la clasificación en el historial de la paciente; devuelve el registro.

    Un fallo aquí no quita el resultado al médico: la respuesta dice `guardado: false`.
    """
    from pacientes.models import Paciente

    try:
        paciente = Paciente.objects.filter(pk=paciente_id).first()
        if paciente is None:
            return None
        embarazo = paciente.embarazos.filter(estado="activo").first()
        semana = None
        if embarazo and embarazo.fecha_ultima_menstruacion:
            semana = (timezone.localdate() - embarazo.fecha_ultima_menstruacion).days // 7
            if not 0 < semana <= 42:
                semana = None
        return RegistroCardiotocografia.objects.create(
            paciente=paciente, embarazo=embarazo, semana_gestacional=semana, valores=valores,
            clase=resultado["clase"], probabilidades=resultado["probabilidades"],
            advertencias=resultado["advertencias"], modelo_version=resultado["modelo"]["version"],
            realizado_por=request.user,
        ).id
    except Exception:
        logger.exception("No se pudo guardar la cardiotocografía en el historial")
        return None


class RegistroCardiotocografiaViewSet(viewsets.ReadOnlyModelViewSet):
    """Cardiotocografías guardadas, de la más reciente a la más antigua.

    Filtros: `paciente_id`, `clase`; `search` busca por nombre o CI de la paciente.
    """

    serializer_class = RegistroCardiotocografiaSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [BusquedaClinicaFilter, filters.OrderingFilter]
    busqueda_ruta_paciente = "paciente"
    busqueda_campos_claros = []
    ordering_fields = ["fecha", "clase"]
    ordering = ["-fecha"]

    def get_queryset(self):
        qs = RegistroCardiotocografia.objects.select_related("paciente", "realizado_por")
        paciente_id = self.request.query_params.get("paciente_id")
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)
        clase = self.request.query_params.get("clase")
        if clase:
            qs = qs.filter(clase=clase)
        return qs
