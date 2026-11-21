"""Ángulo de progresión desde una ecografía intraparto (puente al microservicio).

POST /api/partos/angulo-progresion/   (multipart: file)

Reenvía la imagen a /api/segmentacion/intraparto del microservicio de IA y
devuelve la medida con su margen, la interpretación y la imagen con el ángulo
dibujado (como archivo, no en base64). La medida la confirma el médico antes
de guardarla en el tacto del partograma.
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


@extend_schema(summary="Medir el ángulo de progresión en una ecografía transperineal",
               request={"multipart/form-data": OpenApiTypes.OBJECT}, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([FetalMedicalPermission, EsSoloMedico])
def angulo_progresion(request):
    from ecografias.ai_views import obtener_url_ia, preparar_respuesta_ia

    archivo = request.FILES.get("file")
    if not archivo:
        return Response({"error": "Adjunte la imagen de la ecografía intraparto en el campo «file»."},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        r = requests.post(f"{obtener_url_ia()}/api/segmentacion/intraparto",
                          files={"file": (archivo.name, archivo.read(), archivo.content_type)}, timeout=60)
    except requests.RequestException:
        return Response({"error": "El servicio de IA no responde. Compruebe que está en marcha (puerto 8001)."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if r.status_code != 200:
        detalle = r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return Response({"error": detalle or "No se pudo medir el ángulo."}, status=r.status_code)
    try:
        from auditoria.models import RegistroAuditoria

        aop = r.json().get("medidas", {}).get("angulo_progresion_grados")
        RegistroAuditoria.registrar(usuario=request.user, accion="ANALISIS_CNN", modulo="Partograma",
                                    detalle=f"Ángulo de progresión medido por la red: {aop}°", request=request)
    except Exception:
        logger.warning("No se pudo auditar la medida del ángulo de progresión", exc_info=True)
    return Response(preparar_respuesta_ia(r.json()))
