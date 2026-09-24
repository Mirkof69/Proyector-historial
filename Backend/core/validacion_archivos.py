"""Validación de archivos subidos por su CONTENIDO, no por su nombre.

Por qué: el tipo lo declaraba el cliente (`tipo_archivo="PDF"`) y solo se miraba
la extensión o el tamaño. Se podía subir una página HTML o un SVG con código
JavaScript llamado «informe.pdf»; al abrirlo desde /media/ se ejecutaba en el
navegador de quien lo viera.

Se comprueban los primeros bytes («números mágicos») de cada formato permitido.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError

#: formato -> (desplazamiento, bytes esperados). DICOM lleva «DICM» en el byte 128.
FIRMAS: dict[str, list[tuple[int, bytes]]] = {
    "PDF": [(0, b"%PDF-")],
    "PNG": [(0, b"\x89PNG\r\n\x1a\n")],
    "JPG": [(0, b"\xff\xd8\xff")],
    "DICOM": [(128, b"DICM")],
    "BMP": [(0, b"BM")],
    "TIFF": [(0, b"II*\x00"), (0, b"MM\x00*")],
    "MP4": [(4, b"ftyp")],
    "AVI": [(8, b"AVI ")],
}

IMAGENES = ("PNG", "JPG", "BMP", "TIFF", "DICOM")
DOCUMENTOS = ("PDF", "PNG", "JPG")


def detectar_formato(archivo) -> str | None:
    """El formato real según sus primeros bytes, o None si no es ninguno conocido."""
    posicion = archivo.tell() if hasattr(archivo, "tell") else 0
    try:
        archivo.seek(0)
        cabecera = archivo.read(136)
    finally:
        archivo.seek(posicion)
    for formato, firmas in FIRMAS.items():
        for desplazamiento, firma in firmas:
            if cabecera[desplazamiento:desplazamiento + len(firma)] == firma:
                return formato
    return None


def validar_archivo(archivo, permitidos=DOCUMENTOS, max_mb: int = 50) -> str:
    """Lanza ValidationError si el archivo no es de un formato permitido o pesa
    demasiado. Devuelve el formato detectado."""
    if archivo is None:
        raise ValidationError("No se recibió ningún archivo.")
    if archivo.size > max_mb * 1024 * 1024:
        raise ValidationError(f"El archivo supera el máximo de {max_mb} MB.")
    formato = detectar_formato(archivo)
    if formato not in permitidos:
        raise ValidationError(
            "El contenido del archivo no corresponde a un formato permitido "
            f"({', '.join(permitidos)}). No basta con cambiar la extensión.")
    return formato
