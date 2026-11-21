"""Nombres de archivo clínico sin datos de la paciente.

Antes cada modelo renombraba el archivo en save() a «Nombre_Apellido_fecha»:
ponía el nombre en la URL, era adivinable y, si el archivo ya estaba escrito
(p. ej. al guardarlo con FieldFile.save), la base quedaba apuntando a un
nombre que no existía en disco. upload_to decide el nombre antes de escribir.
"""
import os
import uuid

from django.utils import timezone


def _ruta(carpeta, nombre_original):
    hoy = timezone.localdate()
    ext = os.path.splitext(nombre_original)[1].lower()
    return f"{carpeta}/{hoy:%Y/%m/%d}/{uuid.uuid4().hex}{ext}"


def ruta_imagen_ecografia(_instancia, nombre_original):
    return _ruta("ecografias", nombre_original)


def ruta_archivo_ecografia(_instancia, nombre_original):
    return _ruta("ecografias/archivos", nombre_original)
