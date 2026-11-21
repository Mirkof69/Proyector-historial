"""Miniaturas de imágenes de ecografía para listados.

Por qué existe este módulo
--------------------------
Una ecografía convertida desde DICOM pesa varios megabytes. Los listados y la
historia clínica las mostraban a resolución completa, así que abrir el
expediente de una paciente con tres ecografías descargaba varios MB.

En la red móvil de una clínica —3G como piso— eso vuelve la pantalla
inutilizable, y encima para nada: en una lista la imagen se ve a unos pocos
cientos de píxeles. La imagen de diagnóstico completa se sirve solo cuando la
médica abre la ecografía concreta.

WebP con calidad 80 porque comprime bastante mejor que JPEG a la misma calidad
percibida, y todos los navegadores que soporta el sistema lo entienden.
"""
from __future__ import annotations

from io import BytesIO

from PIL import Image

ANCHO_POR_DEFECTO = 480
CALIDAD = 80


def generar_miniatura(archivo, ancho_max: int = ANCHO_POR_DEFECTO) -> BytesIO:
    """Devuelve una miniatura WebP de `archivo`, como máximo de `ancho_max` px.

    Mantiene la proporción original. Una imagen que ya sea más pequeña que
    `ancho_max` se deja como está: ampliarla solo añadiría peso sin aportar
    ningún detalle nuevo.
    """
    imagen = Image.open(archivo)

    # Las ecografías en escala de grises pueden venir en modos que WebP no
    # acepta directamente (P, LA, I;16). RGB es el denominador común.
    if imagen.mode not in ("RGB", "RGBA"):
        imagen = imagen.convert("RGB")

    if imagen.width > ancho_max:
        alto = round(imagen.height * ancho_max / imagen.width)
        imagen = imagen.resize((ancho_max, alto), Image.LANCZOS)

    salida = BytesIO()
    imagen.save(salida, format="WEBP", quality=CALIDAD, method=4)
    salida.seek(0)
    return salida
