"""KPIs del tablero calculados con los datos reales.

Antes /reportes/dashboard-kpis/ devolvía la lista de definiciones guardadas
en la tabla DashboardKPI (valores cargados a mano) y las pantallas de
Reportes y KPIs esperaban indicadores calculados: se veían en cero o vacías.
Este módulo produce exactamente la forma DashboardKPIs del frontend
(frontend/src/services/reportesService.ts).
"""
from datetime import timedelta

from django.db.models import Count, Max, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")


def _variacion(actual: int, anterior: int) -> tuple[float, str]:
    if anterior == 0:
        return (100.0 if actual else 0.0), ("up" if actual else "stable")
    cambio = round((actual - anterior) * 100 / anterior, 1)
    return cambio, "up" if cambio > 0 else "down" if cambio < 0 else "stable"


def _altas_por_mes(qs, campo: str, hoy):
    inicio_mes = hoy.replace(day=1)
    inicio_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
    este = qs.filter(**{f"{campo}__date__gte": inicio_mes}).count()
    anterior = qs.filter(**{f"{campo}__date__gte": inicio_anterior, f"{campo}__date__lt": inicio_mes}).count()
    return _variacion(este, anterior)


def calcular_kpis_dashboard() -> dict:
    from citas.models import Cita
    from controles.models import ControlPrenatal
    from embarazos.models import Embarazo
    from laboratorio.models import ExamenLaboratorio
    from pacientes.models import Paciente
    from partos.models import Parto

    hoy = timezone.localdate()

    pacientes = Paciente.objects.filter(activo=True)
    var_pac, tend_pac = _altas_por_mes(Paciente.objects.all(), "fecha_registro", hoy)
    embarazos = Embarazo.objects.filter(estado="activo")
    var_emb, tend_emb = _altas_por_mes(Embarazo.objects.all(), "fecha_registro", hoy)

    citas_hoy = Cita.objects.filter(fecha_cita=hoy).aggregate(
        total=Count("id"),
        completadas=Count("id", filter=Q(estado="completada")),
        pendientes=Count("id", filter=Q(estado__in=("agendada", "confirmada", "en_espera", "en_consulta"))),
        canceladas=Count("id", filter=Q(estado__in=("cancelada", "no_asistio"))),
    )

    def asistencia(desde, hasta):
        c = Cita.objects.filter(fecha_cita__gte=desde, fecha_cita__lt=hasta).aggregate(
            total=Count("id"), faltas=Count("id", filter=Q(estado__in=("cancelada", "no_asistio"))))
        return round((c["total"] - c["faltas"]) * 100 / c["total"], 1) if c["total"] else 0.0

    asistencia_semana = asistencia(hoy - timedelta(days=6), hoy + timedelta(days=1))
    asistencia_previa = asistencia(hoy - timedelta(days=13), hoy - timedelta(days=6))

    # Partos de los últimos 12 meses, por mes
    inicio_anio = (hoy.replace(day=1) - timedelta(days=335)).replace(day=1)
    por_mes = {
        (f["mes"].year, f["mes"].month): f
        for f in Parto.objects.filter(fecha_parto__date__gte=inicio_anio)
        .annotate(mes=TruncMonth("fecha_parto")).values("mes")
        .annotate(total=Count("id"), cesareas=Count("id", filter=Q(tipo_parto__startswith="cesarea")))
    }
    partos_anio = []
    anio, mes = inicio_anio.year, inicio_anio.month
    for _ in range(12):
        f = por_mes.get((anio, mes), {"total": 0, "cesareas": 0})
        partos_anio.append({"mes": f"{MESES[mes - 1]} {anio % 100:02d}", "total": f["total"],
                            "cesareas": f["cesareas"], "vaginales": f["total"] - f["cesareas"]})
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)

    # Controles de las últimas 13 semanas, por semana
    inicio_trim = hoy - timedelta(weeks=12, days=hoy.weekday())
    por_semana = {
        f["semana"].date() if hasattr(f["semana"], "date") else f["semana"]: f["total"]
        for f in ControlPrenatal.objects.filter(fecha_control__gte=inicio_trim)
        .annotate(semana=TruncWeek("fecha_control")).values("semana").annotate(total=Count("id"))
    }
    controles_trim = [
        {"semana": (inicio_trim + timedelta(weeks=i)).strftime("%d/%m"),
         "total": por_semana.get(inicio_trim + timedelta(weeks=i), 0)}
        for i in range(13)
    ]

    # Citas de los últimos 7 días
    citas_semana = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        c = Cita.objects.filter(fecha_cita=dia).aggregate(
            total=Count("id"), completadas=Count("id", filter=Q(estado="completada")),
            canceladas=Count("id", filter=Q(estado__in=("cancelada", "no_asistio"))))
        citas_semana.append({"dia": f"{DIAS[dia.weekday()]} {dia.day}", **c})

    # Embarazos activos sin control en las últimas 4 semanas
    hace_4_semanas = hoy - timedelta(weeks=4)
    atrasados = (
        embarazos.filter(fecha_ultima_menstruacion__lte=hoy - timedelta(weeks=8))
        .annotate(ultimo=Max("controles__fecha_control"))
        .filter(Q(ultimo__isnull=True) | Q(ultimo__lt=hace_4_semanas)).count()
    )

    return {
        "fecha_actualizacion": timezone.now().isoformat(),
        "kpis": {
            "pacientes_activos": {"valor": pacientes.count(), "variacion_mes": var_pac, "tendencia": tend_pac},
            "embarazos_activos": {"valor": embarazos.count(), "variacion_mes": var_emb, "tendencia": tend_emb},
            "citas_dia": {"valor": citas_hoy["total"], "completadas": citas_hoy["completadas"],
                          "pendientes": citas_hoy["pendientes"]},
            # Porcentaje de citas de la semana a las que la paciente asistió.
            "tasa_ocupacion": {"valor": asistencia_semana,
                               "variacion_semana": round(asistencia_semana - asistencia_previa, 1)},
        },
        "tendencias": {
            "partos_ultimo_anio": partos_anio,
            "controles_ultimo_trimestre": controles_trim,
            "citas_ultima_semana": citas_semana,
        },
        "alertas": {
            "embarazos_alto_riesgo": embarazos.filter(riesgo_embarazo="alto").count(),
            "examenes_pendientes": ExamenLaboratorio.objects.filter(estado__in=("solicitado", "en_proceso")).count(),
            "citas_sin_confirmar": Cita.objects.filter(fecha_cita__gte=hoy, estado="agendada").count(),
            "controles_atrasados": atrasados,
        },
    }
