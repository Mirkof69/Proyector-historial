"""Reportes de natalidad y morbilidad, y de uso y resultados de la IA.

GET /api/reportes/natalidad/?desde=AAAA-MM-DD&hasta=AAAA-MM-DD
GET /api/reportes/natalidad/excel/?desde=…&hasta=…
GET /api/reportes/ia/?desde=…&hasta=…

Todo sale de las tablas clínicas (partos, recién nacidos, complicaciones,
análisis de IA, predicciones): si no hay datos en el período, las cifras son
cero y las listas vacías; nunca se completan con valores de ejemplo.
Las fechas se interpretan en la hora local de Bolivia; sin fechas, los
últimos 12 meses.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import FetalMedicalPermission

CESAREAS = ("cesarea_electiva", "cesarea_urgencia", "cesarea_emergencia")
CATEGORIAS_PESO = [("< 1.500 g", 0, 1500), ("1.500–2.499 g", 1500, 2500), ("2.500–4.000 g", 2500, 4001),
                   ("> 4.000 g", 4001, 99999)]


def _rango(request) -> tuple[datetime, datetime, date, date]:
    """(inicio, fin) aware en hora local. ValueError con mensaje si las fechas no sirven."""
    hoy = timezone.localdate()
    try:
        hasta = date.fromisoformat(request.GET["hasta"]) if request.GET.get("hasta") else hoy
        desde = date.fromisoformat(request.GET["desde"]) if request.GET.get("desde") else hasta - timedelta(days=365)
    except ValueError as e:
        raise ValueError("Use fechas AAAA-MM-DD en «desde» y «hasta».") from e
    if desde > hasta:
        raise ValueError("«desde» no puede ser posterior a «hasta».")
    tz = timezone.get_current_timezone()
    return (timezone.make_aware(datetime.combine(desde, time.min), tz),
            timezone.make_aware(datetime.combine(hasta, time.max), tz), desde, hasta)


def _pct(parte: int, total: int) -> float | None:
    return round(100 * parte / total, 1) if total else None


def datos_natalidad(inicio: datetime, fin: datetime) -> dict:
    from partos.models import ComplicacionParto, Parto, RecienNacido

    partos = Parto.objects.filter(fecha_parto__range=(inicio, fin))
    rns = RecienNacido.objects.filter(parto__in=partos)
    total_partos = partos.count()
    total_rn = rns.count()
    cesareas = partos.filter(tipo_parto__in=CESAREAS).count()

    por_mes = {}
    for fila in partos.annotate(mes=TruncMonth("fecha_parto")).values("mes").annotate(n=Count("id")):
        por_mes.setdefault(timezone.localtime(fila["mes"]).strftime("%Y-%m") if timezone.is_aware(fila["mes"])
                           else fila["mes"].strftime("%Y-%m"), {"partos": 0, "cesareas": 0})["partos"] += fila["n"]
    for fila in partos.filter(tipo_parto__in=CESAREAS).annotate(mes=TruncMonth("fecha_parto")).values("mes").annotate(n=Count("id")):
        clave = timezone.localtime(fila["mes"]).strftime("%Y-%m") if timezone.is_aware(fila["mes"]) else fila["mes"].strftime("%Y-%m")
        por_mes.setdefault(clave, {"partos": 0, "cesareas": 0})["cesareas"] += fila["n"]

    pesos = list(rns.values_list("peso_nacimiento", flat=True))
    categorias = [{"categoria": nombre, "total": sum(1 for p in pesos if p is not None and a <= p < b)}
                  for nombre, a, b in CATEGORIAS_PESO]
    bajo_peso = sum(1 for p in pesos if p is not None and p < 2500)
    apgar_bajo = rns.filter(apgar_5_minutos__lt=7).count()

    pretermino = 0
    for eg in partos.values_list("edad_gestacional_parto", flat=True):
        try:
            if eg and int(str(eg).split("+")[0]) < 37:
                pretermino += 1
        except ValueError:
            continue

    complicaciones = Counter(dict(ComplicacionParto.objects.filter(parto__in=partos)
                                  .values_list("tipo_complicacion").annotate(n=Count("id"))))
    etiquetas = dict(ComplicacionParto._meta.get_field("tipo_complicacion").choices)
    estados = Counter(dict(rns.values_list("estado_nacimiento").annotate(n=Count("id"))))
    hpp = partos.filter(hemorragia_postparto=True).count()
    con_complicacion = partos.filter(Q(complicaciones__isnull=False) | ~Q(complicaciones_maternas="") |
                                     Q(hemorragia_postparto=True)).distinct().count()

    return {
        "totales": {"partos": total_partos, "recien_nacidos": total_rn, "cesareas": cesareas,
                    "vaginales": total_partos - cesareas},
        "tasas": {
            "cesarea_pct": _pct(cesareas, total_partos),
            "bajo_peso_pct": _pct(bajo_peso, len(pesos)),
            "pretermino_pct": _pct(pretermino, total_partos),
            "apgar5_menor_7_pct": _pct(apgar_bajo, total_rn),
            "hemorragia_posparto_pct": _pct(hpp, total_partos),
            "partos_con_complicacion_pct": _pct(con_complicacion, total_partos),
        },
        "nacimientos_por_mes": [{"mes": m, **v} for m, v in sorted(por_mes.items())],
        "via_parto": [{"via": dict(Parto.TIPO_PARTO_CHOICES).get(t, t), "total": n}
                      for t, n in partos.values_list("tipo_parto").annotate(n=Count("id")).order_by("-n")],
        "peso_al_nacer": categorias,
        "complicaciones": [{"tipo": etiquetas.get(t, t), "total": n} for t, n in complicaciones.most_common()],
        "estado_al_nacer": [{"estado": dict(RecienNacido.ESTADO_CHOICES).get(e, e), "total": n}
                            for e, n in estados.most_common()],
    }


def datos_ia(inicio: datetime, fin: datetime) -> dict:
    from auditoria.models import RegistroAuditoria
    from ia_medica.models import AnalisisCNN, PrediccionPesoNacimiento
    from ia_medica.services.catalogo_modelos import catalogo

    analisis = AnalisisCNN.objects.filter(fecha_analisis__range=(inicio, fin))
    resultados = dict(AnalisisCNN.RESULTADO_CHOICES)
    planos = Counter()
    for clases in analisis.filter(modelo_usado="redes_medidas").values_list("clases_detectadas", flat=True):
        if clases:
            planos[clases[0]] += 1
    ctg = Counter()
    for detalle in RegistroAuditoria.objects.filter(modulo="Cardiotocografia", fecha__range=(inicio, fin)) \
            .values_list("detalle", flat=True):
        for clase in ("Normal", "Sospechosa", "Patológica"):
            if f": {clase} " in detalle:
                ctg[clase] += 1
    cerradas = PrediccionPesoNacimiento.objects.filter(fecha__range=(inicio, fin), peso_real_g__isnull=False)
    errores = list(cerradas.values_list("error_modelo_g", "error_hadlock_g"))
    return {
        "analisis_imagen": {
            "total": analisis.count(),
            "validados_por_medico": analisis.filter(validado_por_medico=True).count(),
            "por_resultado": [{"resultado": resultados.get(r, r), "total": n}
                              for r, n in analisis.values_list("resultado").annotate(n=Count("id")).order_by("-n")],
            "por_plano": [{"plano": p, "total": n} for p, n in planos.most_common()],
            "tiempo_medio_ms": round(sum(analisis.values_list("tiempo_procesamiento_ms", flat=True)) / analisis.count())
            if analisis.exists() else None,
        },
        "cardiotocografia": [{"clase": c, "total": n} for c, n in ctg.most_common()],
        "prediccion_peso": {
            "predicciones": PrediccionPesoNacimiento.objects.filter(fecha__range=(inicio, fin)).count(),
            "cerradas_con_nacimiento": len(errores),
            "error_medio_modelo_g": round(sum(abs(m) for m, _ in errores) / len(errores)) if errores else None,
            "error_medio_hadlock_g": round(sum(abs(h) for _, h in errores if h is not None) /
                                           max(1, sum(1 for _, h in errores if h is not None))) if errores else None,
        },
        "modelos": catalogo(),
    }


@api_view(["GET"])
@permission_classes([FetalMedicalPermission])
def reporte_natalidad(request):
    try:
        inicio, fin, desde, hasta = _rango(request)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"desde": desde, "hasta": hasta, **datos_natalidad(inicio, fin)})


@api_view(["GET"])
@permission_classes([FetalMedicalPermission])
def reporte_natalidad_excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font

    try:
        inicio, fin, desde, hasta = _rango(request)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    d = datos_natalidad(inicio, fin)
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Resumen"
    hoja.append([f"Natalidad y morbilidad del {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}"])
    hoja["A1"].font = Font(bold=True, size=13)
    etiquetas = {"partos": "Partos", "recien_nacidos": "Recién nacidos", "cesareas": "Cesáreas", "vaginales": "Vaginales",
                 "cesarea_pct": "Tasa de cesárea (%)", "bajo_peso_pct": "Bajo peso al nacer (%)",
                 "pretermino_pct": "Pretérmino < 37 semanas (%)", "apgar5_menor_7_pct": "Apgar 5 min < 7 (%)",
                 "hemorragia_posparto_pct": "Hemorragia posparto (%)",
                 "partos_con_complicacion_pct": "Partos con complicación (%)"}
    for clave, valor in {**d["totales"], **d["tasas"]}.items():
        hoja.append([etiquetas[clave], valor if valor is not None else "—"])
    for titulo, filas, columnas in (("Por mes", d["nacimientos_por_mes"], ("mes", "partos", "cesareas")),
                                    ("Vía de parto", d["via_parto"], ("via", "total")),
                                    ("Peso al nacer", d["peso_al_nacer"], ("categoria", "total")),
                                    ("Complicaciones", d["complicaciones"], ("tipo", "total")),
                                    ("Estado al nacer", d["estado_al_nacer"], ("estado", "total"))):
        h = libro.create_sheet(titulo)
        h.append([c.capitalize() for c in columnas])
        for celda in h[1]:
            celda.font = Font(bold=True)
        for fila in filas:
            h.append([fila[c] for c in columnas])
    from io import BytesIO

    salida = BytesIO()
    libro.save(salida)
    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(usuario=request.user, accion="EXPORTAR", modulo="Reportes",
                                    detalle=f"Excel de natalidad {desde}–{hasta}", request=request)
    except Exception:  # auditar no impide exportar
        pass
    respuesta = HttpResponse(salida.getvalue(),
                             content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    respuesta["Content-Disposition"] = f'attachment; filename="natalidad_{desde}_{hasta}.xlsx"'
    return respuesta


@api_view(["GET"])
@permission_classes([FetalMedicalPermission])
def reporte_ia(request):
    try:
        inicio, fin, desde, hasta = _rango(request)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"desde": desde, "hasta": hasta, **datos_ia(inicio, fin)})
