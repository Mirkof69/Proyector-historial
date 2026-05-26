"""Dashboard Avanzado - Estadísticas y KPIs Médicos
"""

from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# from pacientes.models import Paciente  # REMOVED
# from embarazos.models import Embarazo  # REMOVED
# from controles.models import ControlPrenatal  # REMOVED
# from partos.models import Parto  # REMOVED


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_kpis(_request):
    """KPIs Médicos Avanzados
    GET /api/dashboard/kpis/
    """
    from controles.models import ControlPrenatal  # Deferred
    from embarazos.models import Embarazo  # Deferred
    from pacientes.models import Paciente  # Deferred
    from partos.models import Parto  # Deferred

    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    hace_7_dias = hoy - timedelta(days=7)

    # Pacientes
    total_pacientes = Paciente.objects.filter(activo=True).count()
    pacientes_nuevos_mes = Paciente.objects.filter(
        fecha_registro__gte=hace_30_dias,
    ).count()
    if pacientes_nuevos_mes == 0:
        pacientes_nuevos_mes = total_pacientes

    # Embarazos
    embarazos_activos = Embarazo.objects.filter(estado="activo").count()
    embarazos_alto_riesgo = Embarazo.objects.filter(
        estado="activo", riesgo_embarazo="alto",
    ).count()
    embarazos_nuevos_mes = Embarazo.objects.filter(
        fecha_registro__gte=hace_30_dias,
    ).count()
    if embarazos_nuevos_mes == 0:
        embarazos_nuevos_mes = Embarazo.objects.count()

    # Controles
    controles_semana = ControlPrenatal.objects.filter(
        fecha_control__gte=hace_7_dias,
    ).count()
    if controles_semana == 0:
        controles_semana = ControlPrenatal.objects.count()
    controles_con_alertas = ControlPrenatal.objects.filter(
        Q(alerta_presion=True) | Q(alerta_peso=True) | Q(alerta_proteinuria=True),
    ).count()

    # Partos
    partos_mes = Parto.objects.filter(fecha_parto__gte=hace_30_dias).count()
    if partos_mes == 0:
        partos_mes = Parto.objects.count()
    partos_cesarea_mes = Parto.objects.filter(
        fecha_parto__gte=hace_30_dias, via_parto="cesarea",
    ).count()
    if partos_cesarea_mes == 0:
        partos_cesarea_mes = Parto.objects.filter(via_parto="cesarea").count()
    tasa_cesarea = (partos_cesarea_mes / partos_mes * 100) if partos_mes > 0 else 0

    # Promedios
    promedio_controles = (
        ControlPrenatal.objects.aggregate(Avg("numero_control"))["numero_control__avg"]
        or 0
    )

    return Response(
        {
            "pacientes": {
                "total": total_pacientes,
                "nuevos_mes": pacientes_nuevos_mes,
            },
            "embarazos": {
                "activos": embarazos_activos,
                "alto_riesgo": embarazos_alto_riesgo,
                "nuevos_mes": embarazos_nuevos_mes,
                "tasa_riesgo": round(
                    (embarazos_alto_riesgo / embarazos_activos * 100)
                    if embarazos_activos > 0
                    else 0,
                    1,
                ),
            },
            "controles": {
                "semana": controles_semana,
                "con_alertas": controles_con_alertas,
                "promedio": round(promedio_controles, 1),
            },
            "partos": {
                "mes": partos_mes,
                "cesarea_mes": partos_cesarea_mes,
                "tasa_cesarea": round(tasa_cesarea, 1),
            },
        },
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_graficas(_request):
    """Datos para gráficas del dashboard
    GET /api/dashboard/graficas/
    """
    from controles.models import ControlPrenatal
    from embarazos.models import Embarazo
    from partos.models import Parto

    hoy = timezone.now().date()

    # Última 12 semanas de controles (si no hay, mostrar totales históricos)
    controles_por_semana = []
    hay_datos = False
    for i in range(12):
        inicio_semana = hoy - timedelta(days=(i + 1) * 7)
        fin_semana = hoy - timedelta(days=i * 7)
        count = ControlPrenatal.objects.filter(
            fecha_control__gte=inicio_semana, fecha_control__lt=fin_semana,
        ).count()
        if count > 0:
            hay_datos = True
        controles_por_semana.insert(0, {"semana": f"Sem {12 - i}", "controles": count})
    if not hay_datos:
        total = ControlPrenatal.objects.count()
        controles_por_semana = [{"semana": "Histórico", "controles": total}]

    # Distribución de riesgos
    riesgos = (
        Embarazo.objects.filter(estado="activo")
        .values("riesgo_embarazo")
        .annotate(count=Count("id"))
    )
    distribucion_riesgos = {r["riesgo_embarazo"]: r["count"] for r in riesgos}

    # Partos por mes (últimos 6 meses, si no hay, mostrar total histórico)
    partos_por_mes = []
    hay_partos = False
    for i in range(6):
        mes_inicio = (hoy.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        mes_fin = (mes_inicio + timedelta(days=32)).replace(day=1)
        count = Parto.objects.filter(
            fecha_parto__gte=mes_inicio, fecha_parto__lt=mes_fin,
        ).count()
        if count > 0:
            hay_partos = True
        partos_por_mes.insert(0, {"mes": mes_inicio.strftime("%b"), "partos": count})
    if not hay_partos:
        total = Parto.objects.count()
        partos_por_mes = [{"mes": "Histórico", "partos": total}]

    return Response(
        {
            "controles_semanales": controles_por_semana,
            "distribucion_riesgos": distribucion_riesgos,
            "partos_mensuales": partos_por_mes,
        },
    )
