"""=============================================================================
STATISTICS VIEWS - ENDPOINTS PARA ESTADÍSTICAS
=============================================================================
ViewSets y vistas para obtener estadísticas del sistema
Includes: Statistics, Charts, PDF/Excel Export
=============================================================================
"""

import logging
import traceback
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .excel_generator import excel_generator
from .pdf_generator import pdf_generator
from .pdf_generator_enhanced import pdf_generator_enhanced
from .services.report_service import ReportService as report_service

logger = logging.getLogger(__name__)


@extend_schema(
    request=inline_serializer(
        "dashboard_statistics_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@extend_schema(request=None, responses={200: dict})
@permission_classes([IsAuthenticated])
def dashboard_statistics(request):
    """Obtiene estadísticas generales del dashboard
    Query params:
        pass
    - start_date: Fecha inicio (formato: YYYY-MM-DD)
    - end_date: Fecha fin (formato: YYYY-MM-DD)
    """
    try:
        # Parsear fechas
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        stats = report_service.get_dashboard_stats(start_date, end_date)
        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "embarazos_statistics_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def embarazos_statistics(request):
    """Estadísticas de embarazos"""
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        stats = report_service.get_embarazos_stats(start_date, end_date)
        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "controles_statistics_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def controles_statistics(request):
    """Estadísticas de controles prenatales"""
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        stats = report_service.get_controles_stats(start_date, end_date)
        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "citas_statistics_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def citas_statistics(request):
    """Estadísticas de citas"""
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        stats = report_service.get_citas_stats(start_date, end_date)
        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "partos_statistics_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def partos_statistics(request):
    """Estadísticas de partos"""
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        stats = report_service.get_partos_stats(start_date, end_date)
        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "all_statistics_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def all_statistics(request):
    """Obtiene todas las estadísticas del sistema"""
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        stats = report_service.get_all_statistics(start_date, end_date)
        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:

        error_detail = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }
        logger.exception("Error en statistics")
        return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "download_statistics_pdf_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_statistics_pdf(request):
    """Descarga reporte PDF de estadísticas completas"""
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        # Obtener todas las estadísticas
        stats = report_service.get_all_statistics(start_date, end_date)

        # Generar PDF
        pdf_buffer = pdf_generator.generate_statistics_pdf(stats)

        # Crear respuesta HTTP
        response = HttpResponse(pdf_buffer, content_type="application/pd")
        filename = f"estadisticas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pd"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "download_statistics_pdf_enhanced_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_statistics_pdf_enhanced(request):
    """Descarga reporte PDF mejorado con gráficos embebidos
    Query params:
    - start_date: Fecha inicio (formato: YYYY-MM-DD)
    - end_date: Fecha fin (formato: YYYY-MM-DD)
    """
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        # Obtener todas las estadísticas
        stats = report_service.get_all_statistics(start_date, end_date)

        # Parámetros del reporte
        params = {
            "fecha_inicio": start_date.strftime("%Y-%m-%d") if start_date else "N/A",
            "fecha_fin": end_date.strftime("%Y-%m-%d") if end_date else "N/A",
        }

        # Generar PDF mejorado con gráficos
        pdf_buffer = pdf_generator_enhanced.generate_statistics_pdf(stats, params)

        # Crear respuesta HTTP
        response = HttpResponse(pdf_buffer, content_type="application/pd")
        filename = (
            f"estadisticas_completas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pd"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:

        logger.exception("Error generando PDF mejorado")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "download_statistics_excel_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_statistics_excel(request):
    """Descarga reporte Excel con gráficos y múltiples hojas
    Query params:
    - start_date: Fecha inicio (formato: YYYY-MM-DD)
    - end_date: Fecha fin (formato: YYYY-MM-DD)
    """
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        # Obtener todas las estadísticas
        stats = report_service.get_all_statistics(start_date, end_date)

        # Parámetros del reporte
        params = {
            "fecha_inicio": start_date.strftime("%Y-%m-%d") if start_date else "N/A",
            "fecha_fin": end_date.strftime("%Y-%m-%d") if end_date else "N/A",
        }

        # Generar Excel con gráficos
        excel_buffer = excel_generator.generate_statistics_excel(stats, params)

        # Crear respuesta HTTP
        response = HttpResponse(
            excel_buffer,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = (
            f"estadisticas_completas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:

        logger.exception("Error generando Excel")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "statistics_by_period_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def statistics_by_period(request):
    """Obtiene estadísticas agrupadas por período
    Query params:
    - period_type: 'day', 'week', 'month', 'year'
    - start_date: Fecha inicio (formato: YYYY-MM-DD)
    - end_date: Fecha fin (formato: YYYY-MM-DD)
    - module: 'pacientes', 'embarazos', 'controles', 'partos', 'citas'
    """
    try:
        period_type = request.GET.get("period_type", "day")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        module = request.GET.get("module", "all")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = timezone.make_aware(start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = timezone.make_aware(end_date)

        # Obtener estadísticas según el módulo
        if module == "all":
            stats = report_service.get_all_statistics(start_date, end_date)
        elif module == "embarazos":
            stats = {
                "embarazos": report_service.get_embarazos_stats(start_date, end_date),
            }
        elif module == "controles":
            stats = {
                "controles": report_service.get_controles_stats(start_date, end_date),
            }
        elif module == "partos":
            stats = {"partos": report_service.get_partos_stats(start_date, end_date)}
        elif module == "citas":
            stats = {"citas": report_service.get_citas_stats(start_date, end_date)}
        else:
            stats = report_service.get_dashboard_stats(start_date, end_date)

        # Agregar información del período
        stats["period_info"] = {
            "type": period_type,
            "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
            "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
            "module": module,
        }

        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:

        logger.exception("Error en statistics_by_period")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "composition_chart_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def composition_chart(request):
    """Obtiene datos para gráfico de dona (composición porcentual)
    """
    try:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        data = report_service.get_composition_chart_data(start_date, end_date)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "stacked_bar_chart_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stacked_bar_chart(request):
    """Obtiene datos para gráfico de barras apiladas
    """
    try:
        months = int(request.GET.get("months", 12))
        data = report_service.get_stacked_bar_chart_data(months)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=inline_serializer(
        "distribution_chart_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def distribution_chart(_request):
    """Obtiene datos para gráfico de distribución
    """
    try:
        data = report_service.get_distribution_chart_data()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# WRAPPERS PARA PREVENIR COLISIONES DE OPERATION ID
# =============================================================================

@extend_schema(
    operation_id="reportes_pacientes_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pacientes_statistics_view(request):
    return embarazos_statistics(request._request)


@extend_schema(
    operation_id="reportes_pacientes_embarazadas_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pacientes_embarazadas_statistics_view(request):
    return embarazos_statistics(request._request)


@extend_schema(
    operation_id="reportes_nuevos_pacientes_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def nuevos_pacientes_statistics_view(request):
    return dashboard_statistics(request._request)


@extend_schema(
    operation_id="reportes_embarazos_alto_riesgo_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def embarazos_alto_riesgo_statistics_view(request):
    return embarazos_statistics(request._request)


@extend_schema(
    operation_id="reportes_embarazos_trimestre_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def embarazos_trimestre_statistics_view(request):
    return embarazos_statistics(request._request)


@extend_schema(
    operation_id="reportes_tasa_cesareas_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tasa_cesareas_statistics_view(request):
    return partos_statistics(request._request)


@extend_schema(
    operation_id="reportes_complicaciones_partos_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def complicaciones_partos_statistics_view(request):
    return partos_statistics(request._request)


@extend_schema(
    operation_id="reportes_resultados_neonatales_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resultados_neonatales_statistics_view(request):
    return partos_statistics(request._request)


@extend_schema(
    operation_id="reportes_adherencia_controles_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def adherencia_controles_statistics_view(request):
    return controles_statistics(request._request)


@extend_schema(
    operation_id="reportes_laboratorios_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def laboratorios_statistics_view(request):
    return all_statistics(request._request)


@extend_schema(
    operation_id="reportes_examenes_pendientes_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def examenes_pendientes_statistics_view(request):
    return all_statistics(request._request)


@extend_schema(
    operation_id="reportes_resultados_criticos_stats",
    request=None,
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resultados_criticos_statistics_view(request):
    return all_statistics(request._request)

