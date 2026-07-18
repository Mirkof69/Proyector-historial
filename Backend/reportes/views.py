"""Views module."""
import logging
import os
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count
from django.http import FileResponse, Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import FetalMedicalPermission

logger = logging.getLogger(__name__)

from embarazos.models import Embarazo
from pacientes.models import Paciente

from .models import (
    AlertaMedica,
    AuditoriaReporte,
    DashboardKPI,
    ReporteGenerado,
    TipoReporte,
)
from .serializers import (
    AlertaMedicaResumenSerializer,
    AlertaMedicaSerializer,
    AuditoriaReporteSerializer,
    DashboardKPIResumenSerializer,
    DashboardKPISerializer,
    ReporteGeneradoCreateSerializer,
    ReporteGeneradoResumenSerializer,
    ReporteGeneradoSerializer,
    TipoReporteResumenSerializer,
    TipoReporteSerializer,
)

# ============================================================================
# VIEWSET: TIPOS DE REPORTE
# ============================================================================


class TipoReporteViewSet(viewsets.ModelViewSet):
    """Gestión de tipos de reporte configurables.
    """

    queryset = TipoReporte.objects.all()
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "categoria",
        "frecuencia",
        "automatico",
        "confidencial",
        "activo",
    ]
    search_fields = ["nombre", "codigo", "descripcion"]
    ordering_fields = ["categoria", "nombre", "frecuencia", "fecha_creacion"]
    ordering = ["categoria", "nombre"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return TipoReporteResumenSerializer
        return TipoReporteSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def activos(self, _request):
        """Lista solo los tipos de reporte activos.
        """
        queryset = self.get_queryset().filter(activo=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TipoReporteResumenSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TipoReporteResumenSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def campos(self, _request, pk=None):
        """Devuelve los campos/filtros requeridos y formatos disponibles para un tipo de reporte.
        """
        tipo = self.get_object()
        data = {
            "id": tipo.id,
            "nombre": tipo.nombre,
            "codigo": tipo.codigo,
            "campos_requeridos": tipo.get_campos_requeridos(),
            "formatos_disponibles": tipo.get_formatos_disponibles(),
            "roles_autorizados": tipo.get_roles_autorizados(),
        }
        return Response(data)


# ============================================================================
# VIEWSET: REPORTES GENERADOS
# ============================================================================


class ReporteGeneradoViewSet(viewsets.ModelViewSet):
    """Gestión de instancias de reportes generados.
    Permite crear solicitudes de reporte, ver detalle y consultar estadísticas.
    """

    queryset = ReporteGenerado.objects.select_related("tipo_reporte").all()
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "tipo_reporte",
        "estado",
        "formato",
        "fecha_solicitud",
        "fecha_completado",
        "usuario_solicitante",
    ]
    search_fields = [
        "tipo_reporte__nombre",
        "tipo_reporte__codigo",
        "ruta_archivo",
        "mensaje_error",
    ]
    ordering_fields = [
        "fecha_solicitud",
        "fecha_completado",
        "estado",
        "total_registros",
    ]
    ordering = ["-fecha_solicitud"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return ReporteGeneradoResumenSerializer
        if self.action in ["create", "solicitar"]:
            return ReporteGeneradoCreateSerializer
        return ReporteGeneradoSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Asignar usuario solicitante y created_by al crear"""
        usuario_id = (
            getattr(self.request.user, 'id', None) if getattr(self.request.user, 'is_authenticated', False) else None
        )
        serializer.save(usuario_solicitante=usuario_id, created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["post"])
    def solicitar(self, request):
        """Endpoint específico para solicitar un reporte.

        - Usa ReporteGeneradoCreateSerializer para validar los parámetros.
        - Crea un ReporteGenerado en estado 'pendiente'.
        """
        serializer = ReporteGeneradoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario_id = request.user.id if request.user.is_authenticated else None
        reporte = serializer.save(
            usuario_solicitante=usuario_id,
            estado="pendiente",
        )
        # Devolver detalle completo
        detalle = ReporteGeneradoSerializer(reporte)
        return Response(detalle.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def preview(self, request):
        """Vista previa real de un reporte antes de generarlo.

        No genera el archivo final: cuenta cuántos registros reales
        existen para el tipo de reporte y rango de fechas solicitados,
        usando el modelo más representativo de la categoría del
        TipoReporte (Paciente para reportes de pacientes, Embarazo
        para reportes clínicos/estadísticos, etc.).
        """
        tipo_reporte_id = request.data.get("tipo_reporte")
        if not tipo_reporte_id:
            return Response(
                {"tipo_reporte": "Debe indicar el tipo de reporte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            tipo_reporte = TipoReporte.objects.get(pk=tipo_reporte_id)
        except (TipoReporte.DoesNotExist, ValueError, TypeError):
            return Response(
                {"tipo_reporte": "Tipo de reporte no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        fecha_inicio = request.data.get("fecha_inicio")
        fecha_fin = request.data.get("fecha_fin")
        formato = request.data.get("formato", "pdf")

        # Modelo más representativo según la categoría del reporte,
        # usado solo para estimar cuántos registros reales entrarían.
        modelo_por_categoria = {
            "paciente": (Paciente, "fecha_registro"),
            "clinico": (Embarazo, "fecha_registro"),
            "estadistico": (Embarazo, "fecha_registro"),
        }
        modelo, campo_fecha = modelo_por_categoria.get(
            tipo_reporte.categoria, (Paciente, "fecha_registro"),
        )

        qs = modelo.objects.all()
        if fecha_inicio:
            qs = qs.filter(**{f"{campo_fecha}__date__gte": fecha_inicio})
        if fecha_fin:
            qs = qs.filter(**{f"{campo_fecha}__date__lte": fecha_fin})
        total_registros = qs.count()

        preview_data = {
            "tipo_nombre": tipo_reporte.nombre,
            "formato": formato,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "total_registros": total_registros,
            "tamanio_estimado_kb": max(total_registros * (50 if formato == "pdf" else 10), 10),
        }

        return Response(preview_data)

    @action(detail=True, methods=["post"])
    def marcar_procesando(self, _request, pk=None):
        """Cambia el estado del reporte a 'procesando'.
        """
        reporte = self.get_object()
        if reporte.estado not in ["pendiente", "error"]:
            return Response(
                {
                    "error": f"No se puede marcar como procesando un reporte en estado {getattr(reporte, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        reporte.estado = "procesando"
        reporte.fecha_procesamiento = timezone.now()
        reporte.save()
        return Response(ReporteGeneradoSerializer(reporte).data)

    @action(detail=True, methods=["post"])
    def marcar_completado(self, request, pk=None):
        """Marca un reporte como completado y permite registrar info del archivo.
        """
        reporte = self.get_object()
        if reporte.estado not in ["pendiente", "procesando", "error"]:
            return Response(
                {
                    "error": f"No se puede completar un reporte en estado {getattr(reporte, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data or {}
        reporte.estado = "completado"
        reporte.fecha_completado = timezone.now()
        reporte.ruta_archivo = data.get("ruta_archivo", reporte.ruta_archivo)
        reporte.tamano_archivo = data.get("tamano_archivo", reporte.tamano_archivo)
        reporte.hash_archivo = data.get("hash_archivo", reporte.hash_archivo)
        reporte.total_registros = data.get("total_registros", reporte.total_registros)
        # tiempo_procesamiento opcional
        reporte.tiempo_procesamiento = data.get(
            "tiempo_procesamiento", reporte.tiempo_procesamiento,
        )
        reporte.datos_resumen = data.get("datos_resumen", reporte.datos_resumen)
        reporte.save()

        return Response(ReporteGeneradoSerializer(reporte).data)

    @action(detail=True, methods=["get"])
    def descargar(self, _request, pk=None):
        """Descarga el archivo real de un reporte ya completado.
        """
        reporte = self.get_object()
        if reporte.estado != "completado":
            return Response(
                {
                    "error": f"El reporte está en estado '{getattr(reporte, 'get_estado_display')()}', "
                    "todavía no tiene un archivo disponible para descargar.",
                },
                status=status.HTTP_409_CONFLICT,
            )
        if not reporte.ruta_archivo or not os.path.exists(reporte.ruta_archivo):
            raise Http404("El archivo del reporte no se encuentra en el servidor.")

        reporte.accesos_descarga = (reporte.accesos_descarga or 0) + 1
        reporte.save(update_fields=["accesos_descarga"])

        return FileResponse(
            open(reporte.ruta_archivo, "rb"),
            as_attachment=True,
            filename=os.path.basename(reporte.ruta_archivo),
        )

    @action(detail=True, methods=["post"])
    def marcar_error(self, request, pk=None):
        """Marca un reporte como error, registrando mensaje de error opcional.
        """
        reporte = self.get_object()
        mensaje_error = request.data.get("mensaje_error", "")
        reporte.estado = "error"
        reporte.mensaje_error = mensaje_error
        reporte.fecha_completado = timezone.now()
        reporte.save()
        return Response(ReporteGeneradoSerializer(reporte).data)

    @action(detail=True, methods=["post"])
    def incrementar_descarga(self, _request, pk=None):
        """Incrementa el contador de descargas del reporte.
        Útil para ser llamado cuando el usuario descarga el archivo.
        """
        reporte = self.get_object()
        reporte.accesos_descarga = (reporte.accesos_descarga or 0) + 1
        reporte.save()
        return Response({"accesos_descarga": reporte.accesos_descarga})

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """Devuelve estadisticas globales de reportes generados.
        Cached for 60 seconds to reduce database load.
        """
        cache_key = f"report_stats:globales:user_{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)

        qs = self.get_queryset()
        total = qs.count()
        por_estado = qs.values("estado").annotate(count=Count("id"))
        por_formato = qs.values("formato").annotate(count=Count("id"))
        hoy = timezone.now().date()

        today_reports = qs.filter(fecha_solicitud__date=hoy).count()
        ultima_semana = qs.filter(fecha_solicitud__gte=hoy - timedelta(days=7)).count()

        result = {
            "total_reportes": total,
            "reportes_hoy": today_reports,
            "reportes_ultima_semana": ultima_semana,
            "por_estado": por_estado,
            "por_formato": por_formato,
        }

        # Cache for 60 seconds
        cache.set(cache_key, result, timeout=60)
        return Response(result)


# ============================================================================
# VIEWSET: DASHBOARD KPI
# ============================================================================


class DashboardKAPIViewSet(viewsets.ModelViewSet):
    """Gestión de indicadores KPI del dashboard.
    """

    queryset = DashboardKPI.objects.all()
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "categoria",
        "tipo",
        "activo",
    ]
    search_fields = ["nombre", "codigo", "descripcion"]
    ordering_fields = ["categoria", "orden_dashboard", "nombre"]
    ordering = ["categoria", "orden_dashboard"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return DashboardKPIResumenSerializer
        return DashboardKPISerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def activos(self, _request):
        """Lista KPIs activos (para el dashboard principal).
        """
        qs = self.get_queryset().filter(activo=True)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = DashboardKPIResumenSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = DashboardKPIResumenSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def actualizar_valor(self, request, pk=None):
        """Permite actualizar manualmente valor_actual / valor_anterior / metas.
        Ideal para pruebas o KPIs calculados externamente.
        """
        kpi = self.get_object()
        data = request.data or {}

        # Guardar valor_anterior antes de sobrescribir
        if "valor_actual" in data:
            kpi.valor_anterior = kpi.valor_actual
            kpi.valor_actual = data["valor_actual"]

        if "meta_minima" in data:
            kpi.meta_minima = data["meta_minima"]

        if "meta_optima" in data:
            kpi.meta_optima = data["meta_optima"]

        kpi.ultima_actualizacion = timezone.now()
        kpi.save()

        return Response(DashboardKPISerializer(kpi).data)


# ============================================================================
# VIEWSET: ALERTAS MÉDICAS
# ============================================================================


class AlertaMedicaViewSet(viewsets.ModelViewSet):
    """Gestión de alertas médicas generadas por el sistema.
    """

    queryset = AlertaMedica.objects.all()
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "tipo",
        "prioridad",
        "estado",
        "modulo_origen",
        "paciente_id",
        "embarazo_id",
        "medico_responsable_id",
    ]
    search_fields = [
        "titulo",
        "descripcion",
        "accion_recomendada",
        "protocolo_seguimiento",
    ]
    ordering_fields = [
        "fecha_creacion",
        "prioridad",
    ]
    ordering = ["-fecha_creacion"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return AlertaMedicaResumenSerializer
        return AlertaMedicaSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def activas(self, _request):
        """Lista alertas activas.
        """
        qs = self.get_queryset().filter(estado="activa")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = AlertaMedicaResumenSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = AlertaMedicaResumenSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """Estadisticas generales de alertas medicas.
        Cached for 60 seconds to reduce database load.
        """
        cache_key = f"alert_stats:globales:user_{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)

        qs = self.get_queryset()
        total = qs.count()
        por_tipo = qs.values("tipo").annotate(count=Count("id"))
        por_prioridad = qs.values("prioridad").annotate(count=Count("id"))
        por_estado = qs.values("estado").annotate(count=Count("id"))

        activas = qs.filter(estado="activa").count()
        criticas = qs.filter(
            prioridad__in=["critica", "emergencia"], estado="activa",
        ).count()

        result = {
            "total_alertas": total,
            "alertas_activas": activas,
            "alertas_criticas_activas": criticas,
            "por_tipo": por_tipo,
            "por_prioridad": por_prioridad,
            "por_estado": por_estado,
        }

        # Cache for 60 seconds
        cache.set(cache_key, result, timeout=60)
        return Response(result)

    @action(detail=True, methods=["post"])
    def marcar_revisada(self, request, pk=None):
        """Marca una alerta como revisada.
        """
        alerta = self.get_object()
        if alerta.estado not in ["activa"]:
            return Response(
                {
                    "error": f"No se puede marcar como revisada una alerta en estado {getattr(alerta, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        alerta.estado = "revisada"
        alerta.fecha_revision = timezone.now()
        alerta.usuario_revision_id = request.user.id
        alerta.comentario_revision = request.data.get(
            "comentario", alerta.comentario_revision,
        )
        alerta.save()
        return Response(AlertaMedicaSerializer(alerta).data)

    @action(detail=True, methods=["post"])
    def marcar_resuelta(self, request, pk=None):
        """Marca una alerta como resuelta.
        """
        alerta = self.get_object()
        if alerta.estado not in ["activa", "revisada", "escalada"]:
            return Response(
                {
                    "error": f"No se puede marcar como resuelta una alerta en estado {getattr(alerta, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        alerta.estado = "resuelta"
        alerta.fecha_resolucion = timezone.now()
        alerta.usuario_resolucion_id = request.user.id
        alerta.comentario_resolucion = request.data.get(
            "comentario", alerta.comentario_resolucion,
        )
        alerta.save()
        return Response(AlertaMedicaSerializer(alerta).data)

    @action(detail=True, methods=["post"])
    def descartar(self, request, pk=None):
        """Descarta una alerta (no aplica).
        """
        alerta = self.get_object()
        alerta.estado = "descartada"
        alerta.fecha_resolucion = timezone.now()
        alerta.usuario_resolucion_id = request.user.id
        alerta.comentario_resolucion = request.data.get(
            "comentario", alerta.comentario_resolucion or "Descartada",
        )
        alerta.save()
        return Response(AlertaMedicaSerializer(alerta).data)

    @action(detail=True, methods=["post"])
    def escalar(self, _request, pk=None):
        """Escala una alerta (por ejemplo, a un nivel superior).
        """
        alerta = self.get_object()
        if alerta.estado not in ["activa", "revisada"]:
            return Response(
                {
                    "error": f"No se puede escalar una alerta en estado {getattr(alerta, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        alerta.estado = "escalada"
        alerta.save()
        return Response(AlertaMedicaSerializer(alerta).data)


# ============================================================================
# VIEWSET: AUDITORÍA DE REPORTES
# ============================================================================


class AuditoriaReporteViewSet(viewsets.ReadOnlyModelViewSet):
    """Visualización de registros de auditoría de reportes.
    Solo lectura.
    """

    queryset = AuditoriaReporte.objects.select_related(
        "reporte_generado", "reporte_generado__tipo_reporte",
    ).all()
    serializer_class = AuditoriaReporteSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "reporte_generado",
        "usuario_id",
        "accion",
        "fecha_accion",
    ]
    search_fields = [
        "reporte_generado__tipo_reporte__nombre",
        "direccion_ip",
        "user_agent",
    ]
    ordering_fields = ["fecha_accion", "usuario_id", "accion"]
    ordering = ["-fecha_accion"]


# ============================================================================
# API VIEWS SIMPLES PARA ESTADÍSTICAS
# ============================================================================

import contextlib

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# from embarazos.models import Embarazo  # CIRCULAR_IMPORT_FIX
# from pacientes.models import Paciente  # CIRCULAR_IMPORT_FIX
# from controles.models import ControlPrenatal  # REMOVED
# from partos.models import Parto  # REMOVED


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """Endpoint para obtener estadisticas del dashboard con campos requeridos por el frontend.
    Cached for 60 seconds to reduce database load.
    """
    cache_key = f"dashboard_stats:main:user_{request.user.id}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return Response(cached_result)

    from citas.models import Cita
    from controles.models import ControlPrenatal
    from embarazos.models import Embarazo
    from pacientes.models import Paciente
    from partos.models import Parto

    try:
        hoy = timezone.now().date()
        mes_actual = timezone.now().month
        anio_actual = timezone.now().year

        stats = {
            # Mismo criterio que reportes/stats_views.py: el total es el
            # total; "activos" usa la bandera canónica `activo`.
            "total_pacientes": Paciente.objects.count(),
            "pacientes_activos": Paciente.objects.filter(activo=True).count(),
            "pacientes_inactivos": Paciente.objects.filter(activo=False).count(),
            "pacientes_nuevos_mes": Paciente.objects.filter(
                fecha_registro__month=mes_actual, fecha_registro__year=anio_actual,
            ).count(),
            "embarazos_activos": Embarazo.objects.filter(estado="activo").count(),
            "embarazos_riesgo_alto": Embarazo.objects.filter(
                estado="activo", riesgo_embarazo__in=["alto", "muy_alto"],
            ).count(),
            "controles_hoy": ControlPrenatal.objects.filter(fecha_control=hoy).count(),
            "controles_mes": ControlPrenatal.objects.filter(
                fecha_control__month=mes_actual, fecha_control__year=anio_actual,
            ).count(),
            "partos_mes": Parto.objects.filter(
                fecha_parto__month=mes_actual, fecha_parto__year=anio_actual,
            ).count(),
            "citas_hoy_count": Cita.objects.filter(fecha_cita=hoy).count(),
            "alertas_pendientes": 0,
            "cesareas_porcentaje": 0.0,
        }

        # Calcular alertas si existe el modelo
        with contextlib.suppress(Exception):
            stats["alertas_pendientes"] = AlertaMedica.objects.filter(
                estado="activa",
            ).count()

        # Calcular porcentaje de cesareas
        total_partos_mes = stats["partos_mes"]
        if total_partos_mes > 0:
            cesareas = Parto.objects.filter(
                fecha_parto__month=mes_actual,
                fecha_parto__year=anio_actual,
                tipo_parto__icontains="cesarea",
            ).count()
            stats["cesareas_porcentaje"] = round((cesareas / total_partos_mes) * 100, 1)

        # Cache for 60 seconds
        cache.set(cache_key, stats, timeout=60)
        return Response(stats)
    except Exception as e:
        logger.exception("Error en dashboard stats")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def general_stats_view(request):
    """Endpoint para obtener estadisticas generales.
    Cached for 60 seconds to reduce database load.
    """
    from controles.models import ControlPrenatal
    from embarazos.models import Embarazo
    from pacientes.models import Paciente
    from partos.models import Parto

    cache_key = f"general_stats:user_{request.user.id}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return Response(cached_result)

    try:
        stats = {
            "total_pacientes": Paciente.objects.count(),
            "total_embarazos": Embarazo.objects.count(),
            "total_controles": ControlPrenatal.objects.count(),
            "total_partos": Parto.objects.count(),
        }
        # Cache for 60 seconds
        cache.set(cache_key, stats, timeout=60)
        return Response(stats)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
