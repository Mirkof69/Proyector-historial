# -*- coding: utf-8 -*-
"""Helper COMPARTIDO para exportaciones CSV.

Mismo criterio de datos que excel_clinico (idénticos encabezados y filas), pero
en texto plano portable. CSV no admite estilo de celda, así que la "cabecera de
marca" se traduce en: BOM UTF-8 (para que Excel/LibreOffice abran los acentos
bien), una fila de metadatos institucionales al inicio, y los MISMOS nombres de
columna que la versión Excel.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime

from django.http import HttpResponse

NOMBRE_CLINICA = "Fetal Medical Bolivia"


def respuesta_csv(nombre_archivo: str, secciones: list[dict]) -> HttpResponse:
    """Genera un CSV a partir de secciones.

    Cada sección es {"titulo": str, "encabezados": [...], "filas": [[...]]} o
    {"titulo": str, "pares": [(campo, valor)]} para bloques campo→valor.
    """
    buffer = io.StringIO()
    buffer.write("﻿")  # BOM → Excel abre UTF-8 con acentos correctos
    w = csv.writer(buffer)

    # Cabecera institucional (equivalente al encabezado de marca del Excel)
    w.writerow([NOMBRE_CLINICA])
    w.writerow([f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    w.writerow([])

    for sec in secciones:
        if sec.get("titulo"):
            w.writerow([sec["titulo"]])
        if "pares" in sec:
            for campo, valor in sec["pares"]:
                w.writerow([campo, "" if valor in (None, "") else valor])
        else:
            w.writerow(sec.get("encabezados", []))
            for fila in sec.get("filas", []):
                w.writerow(["" if v in (None, "") else v for v in fila])
        w.writerow([])

    fecha = datetime.now().strftime("%Y%m%d")
    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}_{fecha}.csv"'
    return response
