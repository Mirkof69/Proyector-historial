"""Endpoints de riesgo según la Fetal Medicine Foundation.

Por qué existe este módulo
--------------------------
`calculadoras/services/calculador_riesgos_fmf.py` implementa desde hace tiempo
el modelo bayesiano de la FMF —riesgo de preeclampsia con biomarcadores y
cribado de trisomías 21/18/13—, 543 líneas de lógica clínica correcta.

Y **no lo usaba nadie**: ningún módulo del proyecto lo importaba, así que no
había ninguna pantalla desde la que una médica pudiera llegar a él. Este
módulo es el puente que faltaba.

Los cálculos son puros: no guardan nada. Lo que sí queda es el registro de
auditoría, porque un cálculo de riesgo es una decisión clínica y hay que poder
reconstruir quién lo pidió y con qué datos.
"""
from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from calculadoras.services.calculador_riesgos_fmf import CalculadorRiesgosFMF
from core.permissions import EsMedicoOEnfermera

logger = logging.getLogger(__name__)


def _auditar(request, accion: str, detalle: str) -> None:
    """Deja constancia del cálculo. Nunca interrumpe la respuesta."""
    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(
            usuario=request.user if getattr(request.user, "is_authenticated", False) else None,
            accion=accion,
            modulo="CalculadoraFMF",
            detalle=detalle,
            request=request,
        )
    except Exception:
        logger.warning("No se pudo auditar el cálculo FMF", exc_info=True)


class _PreeclampsiaEntrada(serializers.Serializer):
    """Datos del cribado de preeclampsia del primer trimestre."""

    edad_materna = serializers.IntegerField(min_value=10, max_value=60)
    peso_kg = serializers.FloatField(min_value=30, max_value=250)
    talla_cm = serializers.FloatField(min_value=100, max_value=220)
    semanas = serializers.IntegerField(min_value=4, max_value=42)

    origen_etnico = serializers.CharField(required=False, default="mestizo")
    metodo_concepcion = serializers.CharField(required=False, default="espontaneo")
    fumadora = serializers.BooleanField(required=False, default=False)
    hipertension_cronica = serializers.BooleanField(required=False, default=False)
    diabetes_tipo1 = serializers.BooleanField(required=False, default=False)
    diabetes_tipo2 = serializers.BooleanField(required=False, default=False)
    lupus = serializers.BooleanField(required=False, default=False)
    sindrome_antifosfolipidos = serializers.BooleanField(required=False, default=False)
    historia_preeclampsia = serializers.BooleanField(required=False, default=False)
    intervalo_embarazo_meses = serializers.IntegerField(required=False, allow_null=True)

    # Biomarcadores: opcionales porque no toda clínica los tiene. El modelo
    # da un riesgo solo con la historia clínica y lo refina si llegan.
    pas_mmhg = serializers.FloatField(required=False, allow_null=True)
    pad_mmhg = serializers.FloatField(required=False, allow_null=True)
    utap_ip_promedio = serializers.FloatField(required=False, allow_null=True)
    plgf_pg_ml = serializers.FloatField(required=False, allow_null=True)


class _TrisomiasEntrada(serializers.Serializer):
    """Datos del cribado combinado del primer trimestre."""

    edad_materna = serializers.IntegerField(min_value=10, max_value=60)
    semanas = serializers.IntegerField(min_value=10, max_value=14)
    #: Sin translucencia nucal no hay cribado del primer trimestre: es el
    #: marcador ecográfico sobre el que se construye todo el cálculo.
    translucencia_nucal_mm = serializers.FloatField(min_value=0.1, max_value=20)

    papp_a_mom = serializers.FloatField(required=False, allow_null=True)
    free_bhcg_mom = serializers.FloatField(required=False, allow_null=True)
    hueso_nasal_presente = serializers.BooleanField(required=False, allow_null=True, default=None)
    flujo_ductus_venoso = serializers.CharField(required=False, allow_null=True, default=None)
    regurgitacion_tricuspidea = serializers.BooleanField(required=False, default=False)


@extend_schema(
    summary="Riesgo de preeclampsia (modelo FMF)",
    description=(
        "Calcula el riesgo de preeclampsia según el modelo bayesiano de la Fetal "
        "Medicine Foundation. Los biomarcadores son opcionales: sin ellos se "
        "devuelve el riesgo por historia clínica; con ellos se refina."
    ),
    request=_PreeclampsiaEntrada,
    responses={200: inline_serializer("RiesgoPreeclampsiaFMF", fields={})},
)
@api_view(["POST"])
@permission_classes([EsMedicoOEnfermera])
def riesgo_preeclampsia_fmf(request):
    """Riesgo de preeclampsia con el modelo completo de la FMF."""
    entrada = _PreeclampsiaEntrada(data=request.data)
    if not entrada.is_valid():
        return Response(
            {"error": "Datos incompletos o fuera de rango", "detalle": entrada.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        resultado = CalculadorRiesgosFMF.calcular_riesgo_preeclampsia_completo(
            **entrada.validated_data,
        )
    except Exception as e:
        logger.exception("Fallo el cálculo de riesgo de preeclampsia")
        return Response(
            {"error": "No se pudo calcular el riesgo", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    _auditar(
        request, "CALCULO_RIESGO",
        f"Riesgo de preeclampsia: {resultado.get('clasificacion_riesgo', 'sin clasificar')}",
    )
    return Response(resultado, status=status.HTTP_200_OK)


@extend_schema(
    summary="Riesgo de trisomías 21, 18 y 13 (modelo FMF)",
    description=(
        "Cribado combinado del primer trimestre. La translucencia nucal es "
        "obligatoria; los marcadores bioquímicos y ecográficos adicionales "
        "refinan el resultado."
    ),
    request=_TrisomiasEntrada,
    responses={200: inline_serializer("RiesgoTrisomiasFMF", fields={})},
)
@api_view(["POST"])
@permission_classes([EsMedicoOEnfermera])
def riesgo_trisomias_fmf(request):
    """Riesgo de trisomías con el cribado combinado de la FMF."""
    entrada = _TrisomiasEntrada(data=request.data)
    if not entrada.is_valid():
        return Response(
            {"error": "Datos incompletos o fuera de rango", "detalle": entrada.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        resultado = CalculadorRiesgosFMF.calcular_riesgo_trisomias(
            **entrada.validated_data,
        )
    except Exception as e:
        logger.exception("Fallo el cálculo de riesgo de trisomías")
        return Response(
            {"error": "No se pudo calcular el riesgo", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    _auditar(
        request, "CALCULO_RIESGO",
        f"Cribado de trisomías: T21 {resultado.get('clasificacion_t21', 'sin clasificar')}",
    )
    return Response(resultado, status=status.HTTP_200_OK)
