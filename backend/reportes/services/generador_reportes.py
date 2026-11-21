"""Genera el archivo de un reporte solicitado desde «Generar reporte PDF».

Antes `solicitar` creaba el ReporteGenerado en estado «pendiente» y nada lo
procesaba: la descarga respondía siempre «todavía no tiene un archivo». Aquí
cada tipo de reporte arma sus datos reales (resumen, tablas y gráficos) y se
escriben en PDF, Excel, CSV o JSON con los formatos institucionales del sistema
(reportes/pdf_clinico.py y excel_clinico.py).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
from collections import Counter
from datetime import date, datetime, timedelta

from django.utils import timezone

MAX_FILAS_PDF = 300
MAX_FILAS_ARCHIVO = 5000


def _fecha(valor) -> str:
    if not valor:
        return ""
    if isinstance(valor, datetime):
        return timezone.localtime(valor).strftime("%d/%m/%Y %H:%M") if timezone.is_aware(valor) else valor.strftime("%d/%m/%Y %H:%M")
    return valor.strftime("%d/%m/%Y")


def _rango(qs, campo: str, desde: date | None, hasta: date | None, es_fecha_hora: bool = True):
    sufijo = "__date" if es_fecha_hora else ""
    if desde:
        qs = qs.filter(**{f"{campo}{sufijo}__gte": desde})
    if hasta:
        qs = qs.filter(**{f"{campo}{sufijo}__lte": hasta})
    return qs


# ── Contenido de cada reporte: {resumen, tablas: [(titulo, encabezados, filas)], graficos} ──

def _pacientes(desde, hasta):
    from django.db.models import Count

    from pacientes.models import Paciente

    qs = _rango(Paciente.objects.annotate(n_emb=Count("embarazos")), "fecha_registro", desde, hasta).order_by("-fecha_registro")
    filas = [[p.id_clinico, p.nombre_completo, p.edad, p.ciudad or "", _fecha(p.fecha_registro), p.n_emb]
             for p in qs[:MAX_FILAS_ARCHIVO]]
    por_ciudad = Counter(f[3] or "Sin dato" for f in filas).most_common(8)
    return {"resumen": [("Pacientes en el período", qs.count())],
            "graficos": [("barras", "Pacientes por ciudad", [c for c, _ in por_ciudad], [n for _, n in por_ciudad])],
            "tablas": [("Pacientes", ["ID clínico", "Nombre", "Edad", "Ciudad", "Registro", "Embarazos"], filas)]}


def _embarazos(desde, hasta):
    from embarazos.models import Embarazo

    qs = _rango(Embarazo.objects.select_related("paciente"), "fecha_registro", desde, hasta).order_by("-fecha_registro")
    riesgo = Counter(qs.values_list("riesgo_embarazo", flat=True))
    filas = [[e.paciente.id_clinico, e.paciente.nombre_completo, _fecha(e.fecha_ultima_menstruacion),
              _fecha(e.fecha_probable_parto), e.get_riesgo_embarazo_display() if e.riesgo_embarazo else "", e.estado]
             for e in qs[:MAX_FILAS_ARCHIVO]]
    return {"resumen": [("Embarazos en el período", qs.count()), ("Activos", qs.filter(estado="activo").count()),
                        ("Alto riesgo", riesgo.get("alto", 0))],
            "graficos": [("torta", "Embarazos por riesgo", [str(k or "sin dato") for k in riesgo], list(riesgo.values()))],
            "tablas": [("Embarazos", ["ID clínico", "Paciente", "FUM", "FPP", "Riesgo", "Estado"], filas)]}


def _controles(desde, hasta):
    from controles.models import ControlPrenatal

    qs = _rango(ControlPrenatal.objects.select_related("paciente"), "fecha_control", desde, hasta, False).order_by("-fecha_control")
    filas = []
    con_alerta = 0
    for c in qs[:MAX_FILAS_ARCHIVO]:
        criticas = [a["mensaje"] for a in c.get_alertas() if a.get("tipo") == "critico"]
        con_alerta += bool(criticas)
        filas.append([_fecha(c.fecha_control), c.paciente.nombre_completo, c.semanas_gestacion,
                      f"{c.presion_arterial_sistolica or ''}/{c.presion_arterial_diastolica or ''}",
                      c.altura_uterina or "", c.frecuencia_cardiaca_fetal or "", "; ".join(criticas)])
    return {"resumen": [("Controles en el período", qs.count()), ("Con alerta crítica (de los listados)", con_alerta)],
            "tablas": [("Controles prenatales", ["Fecha", "Paciente", "Semanas", "PA", "AU (cm)", "FCF", "Alertas"], filas)]}


def _partos(desde, hasta):
    from partos.models import Parto

    qs = _rango(Parto.objects.select_related("paciente").prefetch_related("recien_nacidos"), "fecha_parto", desde, hasta).order_by("-fecha_parto")
    tipos = Counter(p.get_tipo_parto_display() for p in qs)
    filas = []
    for p in qs[:MAX_FILAS_ARCHIVO]:
        rn = p.recien_nacidos.all()
        filas.append([_fecha(p.fecha_parto), p.paciente.nombre_completo, p.get_tipo_parto_display(),
                      p.edad_gestacional_parto or "", ", ".join(f"{r.peso_nacimiento} g" for r in rn),
                      ", ".join(f"{r.apgar_1_minuto}/{r.apgar_5_minutos}" for r in rn)])
    total = sum(tipos.values())
    cesareas = sum(n for t, n in tipos.items() if "esárea" in t or "esarea" in t)
    return {"resumen": [("Partos en el período", total),
                        ("Cesáreas", f"{cesareas} ({round(cesareas * 100 / total, 1) if total else 0} %)")],
            "graficos": [("torta", "Partos por tipo", list(tipos), list(tipos.values()))],
            "tablas": [("Partos y recién nacidos", ["Fecha", "Paciente", "Tipo", "EG", "Peso RN", "Apgar 1/5"], filas)]}


def _citas(desde, hasta):
    from citas.models import Cita

    qs = _rango(Cita.objects.select_related("paciente", "medico"), "fecha_cita", desde, hasta, False).order_by("-fecha_cita", "-hora_cita")
    estados = Counter(qs.values_list("estado", flat=True))
    filas = [[_fecha(c.fecha_cita), c.hora_cita.strftime("%H:%M"), c.paciente.nombre_completo,
              f"{c.medico.nombre} {c.medico.apellido_paterno}", c.get_tipo_cita_display(), c.get_estado_display()]
             for c in qs[:MAX_FILAS_ARCHIVO]]
    return {"resumen": [("Citas en el período", qs.count()), *[(e.replace("_", " ").capitalize(), n) for e, n in estados.items()]],
            "graficos": [("barras", "Citas por estado", [e.replace("_", " ") for e in estados], list(estados.values()))],
            "tablas": [("Agenda", ["Fecha", "Hora", "Paciente", "Médico", "Tipo", "Estado"], filas)]}


def _alertas(desde, hasta):
    from reportes.models import AlertaMedica

    qs = _rango(AlertaMedica.objects.select_related("paciente"), "fecha_creacion", desde, hasta).order_by("-fecha_creacion")
    prioridad = Counter(qs.values_list("prioridad", flat=True))
    filas = [[_fecha(a.fecha_creacion), a.paciente.nombre_completo if a.paciente else "", a.titulo,
              a.get_prioridad_display(), a.get_estado_display(), a.valor_actual]
             for a in qs[:MAX_FILAS_ARCHIVO]]
    return {"resumen": [("Alertas en el período", qs.count()), ("Activas", qs.filter(estado="activa").count())],
            "graficos": [("torta", "Alertas por prioridad", list(prioridad), list(prioridad.values()))],
            "tablas": [("Alertas médicas", ["Fecha", "Paciente", "Alerta", "Prioridad", "Estado", "Valor"], filas)]}


def _laboratorio(desde, hasta):
    from laboratorio.models import ResultadoLaboratorio

    qs = (_rango(ResultadoLaboratorio.objects.select_related("examen__paciente", "valor_referencia"),
                 "examen__fecha_solicitud", desde, hasta).filter(es_normal=False).order_by("-examen__fecha_solicitud"))
    filas = [[_fecha(r.examen.fecha_solicitud), r.examen.paciente.nombre_completo,
              getattr(r.valor_referencia, "parametro", ""), r.valor_numerico if r.valor_numerico is not None else r.valor_texto,
              getattr(r.valor_referencia, "unidad", ""), "Crítico" if r.es_critico else "Anormal"]
             for r in qs[:MAX_FILAS_ARCHIVO]]
    return {"resumen": [("Resultados fuera de rango", qs.count()), ("Críticos", qs.filter(es_critico=True).count())],
            "tablas": [("Laboratorio fuera de rango", ["Fecha", "Paciente", "Parámetro", "Valor", "Unidad", "Nivel"], filas)]}


def _indicadores(_desde, _hasta):
    from reportes.services.indicadores_gestion import calcular_indicadores

    filas = [[i["nombre"], "" if i["valor_actual"] is None else f"{i['valor_actual']} %", f"{i['numerador']}/{i['denominador']}",
              i["meta"], i["estado_vs_meta"].replace("_", " "), i["tendencia"].replace("_", " ")]
             for i in calcular_indicadores()]
    return {"resumen": [("Período", "últimos 12 meses frente a los 12 anteriores")],
            "tablas": [("Indicadores de gestión", ["Indicador", "Valor", "Casos", "Meta", "Estado", "Tendencia"], filas)]}


#: codigo -> (nombre, descripción, categoría, función)
REPORTES = {
    "RPT-PACIENTES": ("Pacientes registradas", "Listado de pacientes con edad, ciudad y número de embarazos.", "paciente", _pacientes),
    "RPT-EMBARAZOS": ("Embarazos y clasificación de riesgo", "Embarazos registrados con FUM, FPP, riesgo y estado.", "clinico", _embarazos),
    "RPT-CONTROLES": ("Controles prenatales", "Controles del período con signos vitales y alertas críticas.", "clinico", _controles),
    "RPT-PARTOS": ("Partos y recién nacidos", "Partos por tipo, edad gestacional, peso y Apgar del recién nacido.", "estadistico", _partos),
    "RPT-CITAS": ("Agenda y asistencia", "Citas del período por médico, tipo y estado.", "institucional", _citas),
    "RPT-ALERTAS": ("Alertas médicas", "Alertas clínicas generadas por controles y laboratorio, con su estado.", "clinico", _alertas),
    "RPT-LAB": ("Laboratorio: valores fuera de rango", "Resultados anormales y críticos del período.", "clinico", _laboratorio),
    "RPT-INDICADORES": ("Indicadores de gestión obstétrica", "Cobertura, calidad y resultados perinatales con su meta.", "institucional", _indicadores),
}


def _escribir(contenido: dict, titulo: str, subtitulo: str, formato: str) -> tuple[bytes, str]:
    if formato in ("pd", "pdf"):
        from reportes.pdf_clinico import PdfClinico

        pdf = PdfClinico(titulo, subtitulo)
        pdf.seccion("Resumen")
        pdf.ficha(contenido["resumen"])
        for tipo, nombre, etiquetas, valores in contenido.get("graficos", []):
            if valores and any(valores):
                (pdf.grafico_torta if tipo == "torta" else pdf.grafico_barras)(nombre, etiquetas, valores)
        for nombre, encabezados, filas in contenido["tablas"]:
            pdf.seccion(nombre)
            if len(filas) > MAX_FILAS_PDF:
                pdf.explicacion(f"Se muestran las {MAX_FILAS_PDF} filas más recientes de {len(filas)}; "
                                "el reporte en Excel o CSV las trae todas.")
            pdf.tabla(encabezados, filas[:MAX_FILAS_PDF])
        return pdf.generar().getvalue(), "pdf"
    if formato == "excel":
        from reportes.excel_clinico import escribir_ficha, escribir_tabla, libro_clinico

        wb, ws = libro_clinico("Resumen")
        escribir_ficha(ws, [("Reporte", titulo), ("Período", subtitulo), *contenido["resumen"]])
        for nombre, encabezados, filas in contenido["tablas"]:
            escribir_tabla(wb.create_sheet(nombre[:31]), encabezados, filas)
        salida = io.BytesIO()
        wb.save(salida)
        return salida.getvalue(), "xlsx"
    if formato == "csv":
        texto = io.StringIO()
        w = csv.writer(texto)
        w.writerow([titulo, subtitulo])
        for nombre, encabezados, filas in contenido["tablas"]:
            w.writerow([])
            w.writerow([nombre])
            w.writerow(encabezados)
            w.writerows(filas)
        return ("﻿" + texto.getvalue()).encode("utf-8"), "csv"
    datos = {"titulo": titulo, "periodo": subtitulo, "resumen": dict(contenido["resumen"]),
             "tablas": [{"nombre": n, "columnas": e, "filas": f} for n, e, f in contenido["tablas"]]}
    return json.dumps(datos, ensure_ascii=False, default=str, indent=1).encode("utf-8"), "json"


def generar(reporte) -> None:
    """Produce el archivo del ReporteGenerado y lo deja «completado» (o «error» con el motivo)."""
    from reportes.views import carpeta_reportes

    inicio = time.monotonic()
    tipo = reporte.tipo_reporte
    _, _, _, funcion = REPORTES.get(tipo.codigo, REPORTES["RPT-PACIENTES"] if tipo.categoria == "paciente" else REPORTES["RPT-EMBARAZOS"])
    try:
        desde, hasta = reporte.fecha_inicio, reporte.fecha_fin
        contenido = funcion(desde, hasta)
        periodo = (f"Del {_fecha(desde)} al {_fecha(hasta)}" if desde and hasta else
                   f"Desde el {_fecha(desde)}" if desde else f"Hasta el {_fecha(hasta)}" if hasta else "Todo el historial")
        datos, extension = _escribir(contenido, tipo.nombre, periodo, reporte.formato)
        carpeta = carpeta_reportes()
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta = carpeta / f"{tipo.codigo.lower()}_{reporte.pk}_{timezone.localtime():%Y%m%d_%H%M%S}.{extension}"
        ruta.write_bytes(datos)
        reporte.estado = "completado"
        reporte.ruta_archivo = str(ruta)
        reporte.tamano_archivo = len(datos)
        reporte.hash_archivo = hashlib.sha256(datos).hexdigest()
        reporte.total_registros = sum(len(f) for _, _, f in contenido["tablas"])
        reporte.datos_resumen = {str(k): str(v) for k, v in contenido["resumen"]}
        reporte.fecha_procesamiento = reporte.fecha_procesamiento or timezone.now()
        reporte.fecha_completado = timezone.now()
        reporte.fecha_expiracion = timezone.now() + timedelta(days=30)
        reporte.mensaje_error = ""
    except Exception as error:  # el motivo queda a la vista en la pantalla de reportes
        reporte.estado = "error"
        reporte.mensaje_error = f"No se pudo generar el reporte: {error}"[:2000]
    reporte.tiempo_procesamiento = round(time.monotonic() - inicio)
    reporte.save()
