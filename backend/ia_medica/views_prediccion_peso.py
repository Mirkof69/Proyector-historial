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

from drf_spectacular.types import OpenApiTypes
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

    from .models import PrediccionPesoNacimiento

    # Se guarda para medirla contra el peso real cuando nazca el bebé (signals.py).
    PrediccionPesoNacimiento.objects.create(
        ecografia=eco, embarazo=eco.embarazo, semanas_objetivo=datos["semanas_objetivo"],
        peso_previsto_g=resultado["peso_previsto_g"], clase_prevista=str(resultado.get("clase") or "")[:30],
        peso_hadlock_proyectado_g=resultado.get("peso_hadlock_proyectado_g"),
        modelo_version=str(resultado["modelo"].get("version") or ""),
        entrenado_con_datos_sinteticos=resultado["modelo"]["entrenado_con_datos_sinteticos"],
        creado_por=request.user)

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


@extend_schema(summary="Cuánto acierta el modelo de peso con los nacimientos reales", responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([EsSoloMedico])
def desempeno_prediccion_peso(request):
    """Error del modelo y de Hadlock sobre las predicciones ya cerradas con el
    peso real del recién nacido. Sin predicciones cerradas, lo dice (n = 0)."""
    from django.db.models import Avg, Count, F, Func

    from .models import PrediccionPesoNacimiento

    class Abs(Func):
        function = "ABS"

    cerradas = PrediccionPesoNacimiento.objects.filter(peso_real_g__isnull=False)
    agregado = cerradas.aggregate(
        n=Count("id"), mae_modelo=Avg(Abs(F("error_modelo_g"))),
        mae_hadlock=Avg(Abs(F("error_hadlock_g"))))
    return Response({
        "predicciones_totales": PrediccionPesoNacimiento.objects.count(),
        "cerradas_con_nacimiento": agregado["n"],
        "error_medio_modelo_g": round(agregado["mae_modelo"]) if agregado["mae_modelo"] is not None else None,
        "error_medio_hadlock_g": round(agregado["mae_hadlock"]) if agregado["mae_hadlock"] is not None else None,
        "ultimas": list(cerradas.order_by("-fecha_cierre").values(
            "id", "ecografia_id", "semanas_objetivo", "peso_previsto_g", "peso_hadlock_proyectado_g",
            "peso_real_g", "error_modelo_g", "error_hadlock_g", "fecha_cierre")[:20]),
    })
