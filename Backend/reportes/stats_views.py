"""Vistas simples para estadísticas y reportes
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# CIRCULAR_IMPORT_FIX: Imports comentados - usar lazy imports en funciones
# from embarazos.models import Embarazo
# from pacientes.models import Paciente
# from controles.models import ControlPrenatal
# from citas.models import Cita
# from partos.models import Parto


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(_request):
    """Endpoint para obtener estadísticas del dashboard
    """
    # ✅ LAZY IMPORTS para evitar circular import
    from citas.models import Cita
    from controles.models import ControlPrenatal
    from embarazos.models import Embarazo
    from pacientes.models import Paciente
    from partos.models import Parto

    try:
        now = timezone.now()
        today = now.date()

        stats = {
            "total_pacientes": Paciente.objects.filter(
                estado_paciente="activo",
            ).count(),
            "pacientes_activos": Paciente.objects.filter(
                estado_paciente="activo",
            ).count(),
            "pacientes_nuevos_mes": Paciente.objects.filter(
                fecha_registro__month=now.month, fecha_registro__year=now.year,
            ).count(),
            "embarazos_activos": Embarazo.objects.filter(estado="activo").count(),
            "embarazos_riesgo_alto": Embarazo.objects.filter(
                riesgo_embarazo="alto", estado="activo",
            ).count(),
            "controles_mes": ControlPrenatal.objects.filter(
                fecha_control__month=now.month, fecha_control__year=now.year,
            ).count(),
            "controles_hoy": ControlPrenatal.objects.filter(
                fecha_control=today,
            ).count(),
            "partos_mes": Parto.objects.filter(
                fecha_parto__month=now.month, fecha_parto__year=now.year,
            ).count(),
            "citas_hoy_count": Cita.objects.filter(fecha_cita=today).count(),
            "cesareas_porcentaje": 0.0,
            # Campos adicionales de compatibilidad
            "alertas_pendientes": Embarazo.objects.filter(
                riesgo_embarazo="alto", estado="activo",
            ).count(),
        }

        # Calcular porcentaje de cesáreas
        total_partos_mes = stats["partos_mes"]
        if total_partos_mes > 0:
            cesareas = Parto.objects.filter(
                fecha_parto__month=now.month,
                fecha_parto__year=now.year,
                tipo_parto__icontains="cesarea",
            ).count()
            stats["cesareas_porcentaje"] = round((cesareas / total_partos_mes) * 100, 1)

        return Response(stats)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def general_stats_view(_request):
    """Endpoint para obtener estadísticas generales
    """
    # ✅ LAZY IMPORTS para evitar circular import

    from controles.models import ControlPrenatal
    from embarazos.models import Embarazo
    from pacientes.models import Paciente
    from partos.models import Parto

    try:
        stats = {
            "total_pacientes": Paciente.objects.count(),
            "total_embarazos": Embarazo.objects.count(),
            "total_controles": ControlPrenatal.objects.count(),
            "total_partos": Parto.objects.count(),
        }
        return Response(stats)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
