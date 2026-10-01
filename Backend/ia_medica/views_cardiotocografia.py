"""Endpoint del clasificador de cardiotocografía (modelo supervisado).

GET  /api/ia/cardiotocografia/   variables que pide el modelo en uso y su fiabilidad
POST /api/ia/cardiotocografia/   {linea_base, aceleraciones, ...} → normal / sospechosa / patológica

Si no hay modelo o faltan datos, responde 409 con el motivo y ninguna clase.
Cada clasificación queda auditada.
"""
from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import EsSoloMedico

logger = logging.getLogger(__name__)


@extend_schema(summary="Clasificar una cardiotocografía (normal, sospechosa, patológica)")
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

    try:
        from auditoria.models import RegistroAuditoria

        paciente = request.data.get("paciente_id")
        RegistroAuditoria.registrar(
            usuario=request.user, accion="CONSULTA_IA", modulo="Cardiotocografia",
            detalle=(f"CTG{f' paciente {paciente}' if paciente else ''}: {resultado['clase_nombre']} "
                     f"(p={resultado['probabilidades'][resultado['clase']]:.2f}, modelo {resultado['modelo']['version']})"),
            request=request,
        )
    except Exception:
        logger.warning("No se pudo auditar la clasificación de CTG", exc_info=True)
    return Response(resultado)
