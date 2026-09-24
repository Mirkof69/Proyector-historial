"""Endpoint del modelo de peso al nacer.

POST /api/ia/prediccion-peso/  {ecografia_id, semanas_objetivo=39}

Devuelve el peso previsto, su clase, el margen de error medido, y Hadlock
proyectado a la misma semana para comparar. Si no se puede predecir, responde
409 con el motivo y ningún número: una estimación inventada es peor que
ninguna. Cada predicción queda auditada, porque orienta decisiones como la vía
del parto.
"""
from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import EsSoloMedico

logger = logging.getLogger(__name__)


class _Entrada(serializers.Serializer):
    ecografia_id = serializers.IntegerField(min_value=1)
    semanas_objetivo = serializers.FloatField(required=False, default=39.0, min_value=24, max_value=42)


@extend_schema(
    summary="Peso al nacer previsto desde una ecografía",
    request=_Entrada,
    responses={200: inline_serializer("PrediccionPesoSalida", fields={})},
)
@api_view(["POST"])
@permission_classes([EsSoloMedico])
def prediccion_peso(request):
    from ecografias.models import Ecografia
    from ia_medica.ml.servicio_peso import PrediccionNoDisponible, predecir_desde_ecografia

    entrada = _Entrada(data=request.data)
    entrada.is_valid(raise_exception=True)
    datos = entrada.validated_data

    try:
        eco = (Ecografia.objects.select_related("biometria", "embarazo", "paciente")
               .get(pk=datos["ecografia_id"]))
    except Ecografia.DoesNotExist:
        return Response({"error": "Ecografía no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    try:
        resultado = predecir_desde_ecografia(eco, datos["semanas_objetivo"])
    except PrediccionNoDisponible as e:
        return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(
            usuario=request.user,
            accion="CONSULTA_IA",
            modulo="PrediccionPeso",
            detalle=(f"Ecografía {eco.pk}: {resultado['peso_previsto_g']} g a las "
                     f"{datos['semanas_objetivo']} semanas (modelo {resultado['modelo']['version']}, "
                     f"Hadlock {resultado['peso_hadlock_proyectado_g']} g)"),
            request=request,
        )
    except Exception:
        logger.warning("No se pudo auditar la predicción de peso", exc_info=True)

    return Response(resultado, status=status.HTTP_200_OK)
