"""Persistencia del mapa de calor (Grad-CAM) del análisis de ecografías.

Por qué existe este módulo
--------------------------
El microservicio devuelve el Grad-CAM como `gradcam_base64`, y la API lo
reenviaba incrustado en el JSON. Medido sobre una ecografía real: la respuesta
pesaba 252 KB, de los cuales 249 KB (el 98%) eran ese base64; todos los datos
clínicos juntos —patologías, biometría, recomendaciones— suman menos de 2 KB.

En la red 3G de una clínica eso son unos 5 segundos por ecografía, y base64
además infla el binario un 33% frente al PNG. Guardando la imagen y devolviendo
su URL, el navegador la pide aparte: se cachea, se sirve comprimida y no
retrasa el resultado que la médica necesita leer.
"""
from __future__ import annotations

import base64
import binascii
import logging
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

CARPETA = "gradcams"


def guardar_gradcam(datos_base64: str, prefijo: str = "eco") -> str:
    """Guarda el Grad-CAM y devuelve su URL relativa.

    Devuelve cadena vacía si no hay datos o si el base64 no es válido: el mapa
    de calor es ayuda visual, y perderlo nunca puede impedir que se entregue el
    resultado clínico del análisis.
    """
    if not datos_base64:
        return ""

    try:
        crudo = base64.b64decode(datos_base64, validate=True)
    except (binascii.Error, ValueError) as e:
        logger.warning("Grad-CAM con base64 inválido (%s); se omite la imagen.", e)
        return ""

    if not crudo:
        return ""

    try:
        nombre = default_storage.save(
            f"{CARPETA}/{prefijo}-{uuid.uuid4().hex}.png", ContentFile(crudo),
        )
    except Exception as e:  # disco lleno, permisos, almacenamiento remoto caído
        logger.warning("No se pudo guardar el Grad-CAM (%s); se omite la imagen.", e)
        return ""

    return f"/media/{nombre}"
