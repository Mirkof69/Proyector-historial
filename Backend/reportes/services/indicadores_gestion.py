"""Indicadores de gestión obstétrica calculados con los datos reales, con su meta.

La pestaña «Indicadores y metas» leía /reportes/dashboard-kpis/, que devuelve
los KPIs del tablero en otra forma, y mostraba «Sin indicadores». Estos son los
indicadores con los que se mide un servicio de obstetricia; cada uno compara
los últimos 12 meses con los 12 anteriores (tendencia) y con su meta.

Metas de referencia: OMS (cesáreas 10–15 %, ≥ 4 controles prenatales, captación
en el primer trimestre) y valores habituales de calidad perinatal.
"""
from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Max, Min, Q
from django.utils import timezone

# codigo, nombre, categoria, sentido («alto» = más es mejor), óptimo, mínimo aceptable
INDICADORES = [
    ("CPN4", "Partos con 4 o más controles prenatales", "cobertura", "alto", 80, 60),
    ("CAPT", "Captación en el primer trimestre (< 14 semanas)", "cobertura", "alto", 60, 40),
    ("ASIS", "Asistencia a las citas programadas", "cobertura", "alto", 85, 70),
    ("CES", "Tasa de cesáreas", "calidad", "bajo", 15, 25),
    ("BPN", "Recién nacidos con bajo peso (< 2.500 g)", "resultado", "bajo", 10, 15),
    ("PRET", "Partos pretérmino (< 37 semanas)", "resultado", "bajo", 10, 15),
    ("APG", "Apgar a los 5 minutos menor de 7", "resultado", "bajo", 3, 5),
    ("HPP", "Hemorragia posparto", "resultado", "bajo", 5, 10),
    ("ATR", "Embarazos activos con control atrasado (> 4 semanas)", "seguimiento", "bajo", 10, 25),
]
CATEGORIAS = {"cobertura": "Cobertura", "calidad": "Calidad", "resultado": "Resultados perinatales",
              "seguimiento": "Seguimiento"}


def _pct(num: int, den: int) -> float | None:
    return round(num * 100 / den, 1) if den else None


def _semanas(texto: str | None) -> int | None:
    try:
        return int(str(texto or "").split("+")[0])
    except ValueError:
        return None


def _valores(desde, hasta) -> dict[str, tuple[float | None, int, int]]:
    """{codigo: (porcentaje, numerador, denominador)} para partos/citas entre desde y hasta."""
    from citas.models import Cita
    from controles.models import ControlPrenatal
    from embarazos.models import Embarazo
    from partos.models import Parto, RecienNacido

    partos = (Parto.objects.filter(fecha_parto__date__gte=desde, fecha_parto__date__lt=hasta)
              .filter(Q(tipo_aborto__isnull=True) | Q(tipo_aborto="")))
    n_partos = partos.count()
    con_4 = (partos.annotate(n=Count("embarazo__controles", distinct=True)).filter(n__gte=4).count()
             if n_partos else 0)
    cesareas = partos.filter(tipo_parto__startswith="cesarea").count()
    hpp = partos.filter(hemorragia_postparto=True).count()
    pretermino = sum(1 for eg in partos.values_list("edad_gestacional_parto", flat=True)
                     if (s := _semanas(eg)) is not None and s < 37)

    rn = RecienNacido.objects.filter(parto__in=partos)
    n_rn = rn.count()
    bajo_peso = rn.filter(peso_nacimiento__lt=2500).count()
    con_apgar = rn.exclude(apgar_5_minutos__isnull=True)
    apgar_bajo = con_apgar.filter(apgar_5_minutos__lt=7).count()

    # Captación: primer control de los embarazos que empezaron su control en el período.
    primeros = (ControlPrenatal.objects.values("embarazo_id")
                .annotate(primero=Min("fecha_control")).filter(primero__gte=desde, primero__lt=hasta))
    ids = [p["embarazo_id"] for p in primeros]
    precoces = (ControlPrenatal.objects.filter(embarazo_id__in=ids, numero_control=1, semanas_gestacion__lt=14)
                .values("embarazo_id").distinct().count())

    citas = Cita.objects.filter(fecha_cita__gte=desde, fecha_cita__lt=min(hasta, timezone.localdate()))
    cerradas = citas.filter(estado__in=("completada", "no_asistio", "cancelada"))
    n_cerradas = cerradas.count()
    asistio = cerradas.filter(estado="completada").count()

    hoy = timezone.localdate()
    activos = Embarazo.objects.filter(estado="activo", fecha_ultima_menstruacion__lte=hoy - timedelta(weeks=8))
    atrasados = (activos.annotate(ultimo=Max("controles__fecha_control"))
                 .filter(Q(ultimo__isnull=True) | Q(ultimo__lt=hoy - timedelta(weeks=4))).count())
    n_activos = activos.count()

    return {
        "CPN4": (_pct(con_4, n_partos), con_4, n_partos),
        "CAPT": (_pct(precoces, len(ids)), precoces, len(ids)),
        "ASIS": (_pct(asistio, n_cerradas), asistio, n_cerradas),
        "CES": (_pct(cesareas, n_partos), cesareas, n_partos),
        "BPN": (_pct(bajo_peso, n_rn), bajo_peso, n_rn),
        "PRET": (_pct(pretermino, n_partos), pretermino, n_partos),
        "APG": (_pct(apgar_bajo, con_apgar.count()), apgar_bajo, con_apgar.count()),
        "HPP": (_pct(hpp, n_partos), hpp, n_partos),
        "ATR": (_pct(atrasados, n_activos), atrasados, n_activos),
    }


def _estado(valor, sentido, optimo, minimo) -> str:
    if valor is None:
        return "sin_datos"
    if sentido == "alto":
        return "optimo" if valor >= optimo else "en_progreso" if valor >= minimo else "bajo_minimo"
    return "optimo" if valor <= optimo else "en_progreso" if valor <= minimo else "bajo_minimo"


def calcular_indicadores() -> list[dict]:
    hoy = timezone.localdate()
    hace_un_anio = hoy - timedelta(days=365)
    actual = _valores(hace_un_anio, hoy + timedelta(days=1))
    anterior = _valores(hace_un_anio - timedelta(days=365), hace_un_anio)
    colores = {"optimo": "green", "en_progreso": "orange", "bajo_minimo": "red", "sin_datos": "default"}
    filas = []
    for orden, (codigo, nombre, categoria, sentido, optimo, minimo) in enumerate(INDICADORES, 1):
        valor, num, den = actual[codigo]
        previo = anterior[codigo][0]
        if valor is None or previo is None:
            tendencia = "sin_datos"
        else:
            tendencia = "subiendo" if valor > previo + 0.5 else "bajando" if valor < previo - 0.5 else "estable"
        estado = _estado(valor, sentido, optimo, minimo)
        filas.append({
            "id": orden, "codigo": codigo, "nombre": nombre, "categoria": categoria,
            "categoria_display": CATEGORIAS[categoria], "valor_actual": valor, "unidad_medida": "%",
            "numerador": num, "denominador": den, "valor_anterior": previo, "tendencia": tendencia,
            "meta": f"{'≥' if sentido == 'alto' else '≤'} {optimo} %",
            "estado_vs_meta": estado, "color_estado": colores[estado], "orden_dashboard": orden,
        })
    return filas
