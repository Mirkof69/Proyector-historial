"""Ecografía ginecológica con IA (puente al microservicio).

POST /api/ia/ginecologia/<tarea>/   (multipart: file, tamano_pixel_mm opcional, paciente_id opcional)

    ovario      contorno de la lesión, tipo probable (8 clases) y alarma de malignidad
    mioma       ubicación del mioma uterino
    ovario-pco  ovario normal / folículo dominante / poliquístico

Cada respuesta trae las métricas medidas de las redes; la imagen con la lesión
dibujada vuelve como archivo (no en base64). Cada análisis queda auditado.
"""
from __future__ import annotations

import logging

import requests
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import EsSoloMedico, FetalMedicalPermission

logger = logging.getLogger(__name__)

TAREAS = {"ovario": "Lesión ovárica", "mioma": "Mioma uterino", "ovario-pco": "Ovario poliquístico"}


def _resumen(tarea: str, datos: dict) -> str:
    if tarea == "ovario":
        mal = datos.get("malignidad") or {}
        return (f"tipo probable {datos.get('tipo_probable')}; P(malignidad) {mal.get('probabilidad')}"
                f"{' — ALARMA' if mal.get('alarma') else ''}")
    if tarea == "mioma":
        return "mioma ubicado" if datos.get("mioma_ubicado") else "sin mioma ubicado"
    return f"categoría probable {datos.get('categoria_probable')}"


@extend_schema(summary="Ecografía ginecológica: lesión ovárica, mioma u ovario poliquístico",
               request={"multipart/form-data": OpenApiTypes.OBJECT}, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([FetalMedicalPermission, EsSoloMedico])
def analisis_ginecologico(request, tarea: str):
    from ecografias.ai_views import obtener_url_ia, preparar_respuesta_ia

    if tarea not in TAREAS:
        return Response({"error": f"Análisis desconocido. Use uno de: {', '.join(TAREAS)}."},
                        status=status.HTTP_404_NOT_FOUND)
    archivo = request.FILES.get("file")
    if not archivo:
        return Response({"error": "Adjunte la imagen de la ecografía en el campo «file»."},
                        status=status.HTTP_400_BAD_REQUEST)
    formulario = {}
    if request.data.get("tamano_pixel_mm"):
        formulario["tamano_pixel_mm"] = request.data["tamano_pixel_mm"]
    try:
        r = requests.post(f"{obtener_url_ia()}/api/ginecologia/{tarea}", data=formulario,
                          files={"file": (archivo.name, archivo.read(), archivo.content_type)}, timeout=60)
    except requests.RequestException:
        return Response({"error": "El servicio de IA no responde. Compruebe que está en marcha (puerto 8001)."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if r.status_code != 200:
        es_json = r.headers.get("content-type", "").startswith("application/json")
        detalle = r.json().get("detail") if es_json else r.text
        return Response({"error": detalle or "No se pudo analizar la imagen."}, status=r.status_code)
    datos = r.json()
    try:
        from auditoria.models import RegistroAuditoria

        paciente = request.data.get("paciente_id")
        RegistroAuditoria.registrar(
            usuario=request.user, accion="ANALISIS_CNN", modulo="Ecografía ginecológica",
            detalle=f"{TAREAS[tarea]}{f' (paciente {paciente})' if paciente else ''}: {_resumen(tarea, datos)}",
            request=request)
    except Exception:
        logger.warning("No se pudo auditar el análisis ginecológico", exc_info=True)
    return Response(preparar_respuesta_ia(datos))
