"""Archivos de /media/ servidos solo con sesión.

Antes: en desarrollo `static()` los servía a cualquiera que tuviera la URL (y
la URL llevaba el nombre de la paciente); en producción (DEBUG=False) no los
servía nadie y las imágenes de ecografía no se veían. Ahora los sirve siempre
esta vista, que exige usuario autenticado, deja fuera a recepción en las
carpetas clínicas y no permite salir de MEDIA_ROOT.
"""
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

#: Carpetas con datos de pacientes: recepción no las ve.
CARPETAS_CLINICAS = ("ecografias", "ia_medica", "gradcams", "laboratorio")


def ruta_media_segura(ruta: str) -> Path | None:
    """La ruta dentro de MEDIA_ROOT, o None si sale de ella o no existe."""
    raiz = Path(settings.MEDIA_ROOT).resolve()
    destino = (raiz / ruta).resolve()
    if not destino.is_relative_to(raiz) or not destino.is_file():
        return None
    return destino


class MediaProtegidaView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Archivo de media protegido por sesión y rol",
                   responses={(200, "application/octet-stream"): OpenApiTypes.BINARY})
    def get(self, request, ruta):
        carpeta = ruta.split("/", 1)[0]
        if carpeta in CARPETAS_CLINICAS and getattr(request.user, "rol", "") == "recepcion":
            return Response({"detail": "Sin permiso para ver archivos clínicos."}, status=403)
        destino = ruta_media_segura(ruta)
        if destino is None:
            raise Http404
        tipo = mimetypes.guess_type(destino.name)[0] or "application/octet-stream"
        respuesta = FileResponse(open(destino, "rb"), content_type=tipo)
        respuesta["X-Content-Type-Options"] = "nosniff"
        respuesta["Cache-Control"] = "private, max-age=3600"
        return respuesta
