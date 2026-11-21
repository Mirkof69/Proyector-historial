"""Endpoint de análisis asistido de resultados de laboratorio.

Por qué existe este módulo
--------------------------
`ia_medica/services/ml_laboratorio_service.py` implementa el análisis de
hemograma, glucosa, función hepática y función renal con los rangos propios
del embarazo —que no son los de la población general— y devuelve valores
anormales, patologías sospechadas, alertas y recomendaciones.

Estaban ahí 481 líneas que **ningún módulo importaba**. El laboratorista
cargaba los resultados y el sistema no decía nada sobre ellos.

Este endpoint es puro cálculo: no guarda resultados, los interpreta. Lo que sí
queda es el registro de auditoría, porque una alerta de laboratorio orienta
una decisión clínica.
"""
from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import EsMedicoOEnfermeraOLaboratorista

logger = logging.getLogger(__name__)

#: Panel -> método del servicio que lo interpreta.
PANELES = {
    "hemograma": "analizar_hemograma",
    "glucosa": "analizar_glucosa",
    "funcion_hepatica": "analizar_funcion_hepatica",
    "funcion_renal": "analizar_funcion_renal",
}


@extend_schema(
    summary="Interpretar resultados de laboratorio",
    description=(
        "Recibe uno o varios paneles (hemograma, glucosa, funcion_hepatica, "
        "funcion_renal) y devuelve, por cada uno, los valores fuera de rango "
        "para el embarazo, las patologías sospechadas, las alertas y las "
        "recomendaciones. No guarda nada: interpreta lo que se le envía."
    ),
    request=inline_serializer("AnalisisLaboratorioEntrada", fields={}),
    responses={200: inline_serializer("AnalisisLaboratorioSalida", fields={})},
)
@api_view(["POST"])
@permission_classes([EsMedicoOEnfermeraOLaboratorista])
def analizar_laboratorio(request):
    """Interpreta los paneles de laboratorio que lleguen en el cuerpo."""
    datos = request.data if isinstance(request.data, dict) else {}
    solicitados = {k: v for k, v in datos.items() if k in PANELES and isinstance(v, dict)}

    if not solicitados:
        return Response(
            {
                "error": "No se envió ningún panel de laboratorio.",
                "paneles_disponibles": sorted(PANELES),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    from ia_medica.services.ml_laboratorio_service import MLLaboratorioService

    servicio = MLLaboratorioService()
    salida: dict = {}
    con_alerta = []

    for panel, valores in solicitados.items():
        try:
            salida[panel] = getattr(servicio, PANELES[panel])(valores)
            if salida[panel].get("alertas"):
                con_alerta.append(panel)
        except Exception as e:
            # Un panel que falla no puede impedir que se interpreten los
            # otros: el médico necesita lo que sí se pudo analizar.
            logger.exception("Fallo el análisis del panel %s", panel)
            salida[panel] = {"error": f"No se pudo analizar: {e}"}

    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(
            usuario=request.user if getattr(request.user, "is_authenticated", False) else None,
            accion="CONSULTA_IA",
            modulo="Laboratorio",
            detalle=(
                f"Análisis de {', '.join(sorted(solicitados))}"
                + (f" — alertas en {', '.join(con_alerta)}" if con_alerta else "")
            ),
            request=request,
        )
    except Exception:
        logger.warning("No se pudo auditar el análisis de laboratorio", exc_info=True)

    return Response(salida, status=status.HTTP_200_OK)
