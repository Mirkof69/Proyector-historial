"""=============================================================================
MÓDULO: CONTROLES PRENATALES - VIEWSET COMPLETO V2.0 CORREGIDO
=============================================================================
✅ CORRECCIONES V2.0:
    pass
- Fix: Usa ControlPrenatalSerializer en list para incluir paciente_nombre ✅
- Fix: Todos los filtros corregidos (negativa en lugar de negativo) ✅
- Fix: Select_related optimizado para evitar N+1 queries ✅
- Fix: Todos los endpoints extendidos con información completa ✅
- Nuevos endpoints para análisis y reportes avanzados ✅
=============================================================================
"""

import contextlib
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import FetalMedicalPermission
from embarazos.models import Embarazo
from embarazos.serializers import EmbarazoSerializer
from pacientes.models import Paciente

from .models import ControlPrenatal
from .serializers import (
    ControlPrenatalCreateUpdateSerializer,
    ControlPrenatalSerializer,
)


class ControlPrenatalViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gestión de Controles Prenatales

    Endpoints disponibles:
        pass
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    CRUD BÁSICO:
        pass
    - GET    /api/controles/              → Listar todos los controles
    - POST   /api/controles/              → Crear nuevo control
    - GET    /api/controles/{id}/         → Obtener detalle de control
    - PUT    /api/controles/{id}/         → Actualizar control completo
    - PATCH  /api/controles/{id}/         → Actualizar control parcial
    - DELETE /api/controles/{id}/         → Eliminar control

    ENDPOINTS AVANZADOS:
        pass
    - GET /api/controles/por_embarazo/embarazo_id=X     → Controles de un embarazo
    - GET /api/controles/por_paciente/paciente_id=X     → Controles de un paciente
    - GET /api/controles/estadisticas/                   → Estadísticas generales
    - GET /api/controles/alertas/                        → Controles con valores anormales
    - GET /api/controles/recientes/dias=7               → Últimos controles
    - GET /api/controles/proximos/dias=30               → Próximos controles
    - GET /api/controles/evolucion/embarazo_id=X        → Evolución de parámetros
    - GET /api/controles/{id}/reporte_completo/          → Reporte detallado
    - GET /api/controles/trimestre/trimestre=1          → Controles por trimestre
    - GET /api/controles/riesgo_alto/                    → Controles de alto riesgo
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """

    # ✅ OPTIMIZACIÓN: Select_related para evitar N+1 queries
    queryset = (
        ControlPrenatal.objects.select_related(
            "embarazo", "embarazo__paciente", "paciente", "medico",
        )
        .prefetch_related("embarazo__controles")
        .all()
        .order_by("-fecha_control", "-numero_control")
    )

    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # ✅ CORRECCIÓN: Campos correctos del modelo
    filterset_fields = [
        "embarazo_id",
        "paciente",
        "semanas_gestacion",
        "edema",
        "proteinuria",
        "numero_control",
        "medico_id",
        "presentacion_fetal",
        "movimientos_fetales",
    ]

    search_fields = [
        "embarazo_id__paciente__nombre",
        "embarazo_id__paciente__apellido_paterno",
        "embarazo_id__paciente__apellido_materno",
        "embarazo_id__paciente__id_clinico",
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
        "paciente__id_clinico",
        "observaciones",
        "medico_id__email",
    ]

    ordering_fields = [
        "fecha_control",
        "semanas_gestacion",
        "peso_actual",
        "numero_control",
        "presion_arterial_sistolica",
        "frecuencia_cardiaca_fetal",
    ]

    def get_serializer_class(self):
        """✅ FIX: Usar ControlPrenatalSerializer SIEMPRE para incluir paciente_nombre"""
        if self.action in ["create", "update", "partial_update"]:
            return ControlPrenatalCreateUpdateSerializer
        # ✅ Para list y retrieve, usar serializer completo
        return ControlPrenatalSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    def get_queryset(self):
        """✅ EXTENDIDO: Filtros avanzados con validaciones"""
        queryset = super().get_queryset()

        # query_params pertenece a rest_framework.request.Request (no HttpRequest)
        params = self.request.query_params  # type: ignore[attr-defined]

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTROS POR FECHA
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        fecha_desde = params.get("fecha_desde", None)
        fecha_hasta = params.get("fecha_hasta", None)

        if fecha_desde:
            with contextlib.suppress(Exception):
                queryset = queryset.filter(fecha_control__gte=fecha_desde)

        if fecha_hasta:
            with contextlib.suppress(Exception):
                queryset = queryset.filter(fecha_control__lte=fecha_hasta)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTROS POR SEMANAS DE GESTACIÓN
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        semanas_min = params.get("semanas_min", None)
        semanas_max = params.get("semanas_max", None)

        if semanas_min:
            with contextlib.suppress(ValueError, TypeError):
                queryset = queryset.filter(semanas_gestacion__gte=int(semanas_min))

        if semanas_max:
            with contextlib.suppress(ValueError, TypeError):
                queryset = queryset.filter(semanas_gestacion__lte=int(semanas_max))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTRO POR ALERTAS (VALORES ANORMALES)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        con_alertas = params.get("con_alertas", None)
        if con_alertas == "true":
            queryset = queryset.filter(
                Q(presion_arterial_sistolica__gte=140)
                | Q(presion_arterial_diastolica__gte=90)
                | Q(frecuencia_cardiaca_fetal__lt=110)
                | Q(frecuencia_cardiaca_fetal__gt=160)
                | Q(edema__in=["severo", "generalizado"])
                | Q(movimientos_fetales__in=["disminuidos", "ausentes"])
                | ~Q(proteinuria="negativa"),  # ✅ CORRECCIÓN
            )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTRO POR ESTADO DEL EMBARAZO
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        solo_activos = params.get("solo_activos", None)
        if solo_activos == "true":
            queryset = queryset.filter(embarazo_id__estado="activo")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTRO POR PACIENTE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        paciente_id = params.get("paciente_id", None)
        if paciente_id:
            with contextlib.suppress(ValueError, TypeError):
                queryset = queryset.filter(
                    Q(paciente__id=int(paciente_id))
                    | Q(embarazo_id__paciente__id=int(paciente_id)),
                )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTRO POR TRIMESTRE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        trimestre = params.get("trimestre", None)
        if trimestre:
            try:
                trimestre = int(trimestre)
                if trimestre == 1:
                    queryset = queryset.filter(semanas_gestacion__lte=13)
                elif trimestre == 2:
                    queryset = queryset.filter(
                        semanas_gestacion__gt=13, semanas_gestacion__lte=27,
                    )
                elif trimestre == 3:
                    queryset = queryset.filter(semanas_gestacion__gt=27)
            except (ValueError, TypeError):
                pass

        return queryset

    def list(self, request, *args, **kwargs):
        """✅ FIX: Override list para usar ControlPrenatalSerializer completo"""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ControlPrenatalSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ControlPrenatalSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """✅ EXTENDIDO: Crear control con validaciones y respuesta completa"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Recargar control con todas las relaciones
        assert serializer.instance is not None
        control = ControlPrenatal.objects.select_related(
            "embarazo", "embarazo__paciente", "paciente", "medico",
        ).get(id=serializer.instance.id)

        return_serializer = ControlPrenatalSerializer(control)

        headers = self.get_success_headers(return_serializer.data)

        # ✅ Respuesta con mensaje de éxito
        response_data = return_serializer.data
        response_data["mensaje"] = "Control prenatal creado correctamente"

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """✅ EXTENDIDO: Actualizar control con respuesta completa"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Recargar con relaciones
        control = ControlPrenatal.objects.select_related(
            "embarazo", "embarazo__paciente", "paciente", "medico",
        ).get(id=instance.id)

        return_serializer = ControlPrenatalSerializer(control)

        response_data = return_serializer.data
        response_data["mensaje"] = "Control actualizado correctamente"

        return Response(response_data)

    def destroy(self, request, *args, **kwargs):
        """✅ Eliminar control prenatal completamente de la base de datos"""
        # ✅ SEGURIDAD: Solo administradores pueden eliminar
        if getattr(request.user, 'rol', '') != "administrador":
            return Response(
                {
                    "error": "Sin permisos para eliminar",
                    "detalle": "Solo los administradores pueden eliminar controles prenatales del sistema.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        from django.db import connection

        instance = self.get_object()
        control_id = instance.id
        embarazo_id = instance.embarazo.id if instance.embarazo else None
        numero_control = instance.numero_control
        fecha_control = instance.fecha_control
        paciente_nombre = None

        if instance.embarazo and instance.embarazo.paciente:
            paciente = instance.embarazo.paciente
            paciente_nombre = (
                f"{paciente.id_clinico} - {paciente.nombre} {paciente.apellido_paterno}"
            )

        # Eliminar usando SQL directo (hard delete)
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM controles_prenatales WHERE id = %s", [control_id],
            )

        return Response(
            {
                "message": "Control prenatal eliminado completamente",
                "detalles": {
                    "paciente": paciente_nombre,
                    "numero_control": numero_control,
                    "fecha_control": str(fecha_control),
                    "embarazo_id": embarazo_id,
                },
                "id": control_id,
            },
            status=status.HTTP_200_OK,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENDPOINTS PERSONALIZADOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @action(detail=False, methods=["get"], url_path="por_embarazo")
    def por_embarazo(self, request):
        """✅ EXTENDIDO: Controles de un embarazo con estadísticas"""
        embarazo_id = request.query_params.get("embarazo_id", None)

        if not embarazo_id:
            return Response(
                {"error": "Debe proporcionar el parámetro embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            embarazo = Embarazo.objects.select_related("paciente").get(id=embarazo_id)
        except Embarazo.DoesNotExist:
            return Response(
                {"error": "Embarazo no encontrado"}, status=status.HTTP_404_NOT_FOUND,
            )

        assert self.queryset is not None
        controles = self.queryset.filter(embarazo_id=embarazo).order_by(
            "numero_control", "fecha_control",
        )

        # ✅ Estadísticas del embarazo
        estadisticas = {
            "total_controles": controles.count(),
            "controles_con_alertas": controles.filter(
                Q(presion_arterial_sistolica__gte=140)
                | Q(presion_arterial_diastolica__gte=90)
                | Q(frecuencia_cardiaca_fetal__lt=110)
                | Q(frecuencia_cardiaca_fetal__gt=160)
                | Q(edema__in=["severo", "generalizado"])
                | Q(movimientos_fetales__in=["disminuidos", "ausentes"])
            ).count(),
            "ultimo_peso": None,
            "ultima_pa": None,
            "ultima_fcf": None,
        }

        if controles.exists():
            ultimo_control = controles.last()
            if ultimo_control is not None:
                estadisticas["ultimo_peso"] = (
                    float(ultimo_control.peso_actual)
                    if ultimo_control.peso_actual is not None
                    else None
                )
                if (
                    ultimo_control.presion_arterial_sistolica
                    and ultimo_control.presion_arterial_diastolica
                ):
                    estadisticas["ultima_pa"] = (
                        f"{ultimo_control.presion_arterial_sistolica}/{ultimo_control.presion_arterial_diastolica}"
                    )
                estadisticas["ultima_fcf"] = ultimo_control.frecuencia_cardiaca_fetal

        serializer = ControlPrenatalSerializer(controles, many=True)

        primer_ctrl = controles.first()
        ultimo_ctrl = controles.last()
        return Response(
            {
                "embarazo": EmbarazoSerializer(embarazo).data,
                "controles": serializer.data,
                "estadisticas": estadisticas,
                "primer_control": primer_ctrl.fecha_control if primer_ctrl is not None else None,
                "ultimo_control": ultimo_ctrl.fecha_control if ultimo_ctrl is not None else None,
            },
        )

    @action(detail=False, methods=["get"], url_path="por_paciente")
    def por_paciente(self, request):
        """✅ NUEVO: Todos los controles de un paciente (todos sus embarazos)"""
        paciente_id = request.query_params.get("paciente_id", None)

        if not paciente_id:
            return Response(
                {"error": "Debe proporcionar el parámetro paciente_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado"}, status=status.HTTP_404_NOT_FOUND,
            )

        # Obtener todos los controles del paciente
        assert self.queryset is not None
        controles = self.queryset.filter(
            Q(paciente=paciente) | Q(embarazo_id__paciente=paciente),
        ).order_by("-fecha_control")

        # Agrupar por embarazo
        embarazos_ids = controles.values_list("embarazo_id", flat=True).distinct()

        serializer = ControlPrenatalSerializer(controles, many=True)

        from pacientes.serializers import PacienteSerializer

        return Response(
            {
                "paciente": PacienteSerializer(paciente).data,
                "total_controles": controles.count(),
                "total_embarazos": len(embarazos_ids),
                "controles": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, _request):
        """✅ EXTENDIDO: Estadísticas completas con más métricas"""
        total = ControlPrenatal.objects.count()

        # Estadísticas temporales
        hoy = timezone.localdate()
        hace_una_semana = hoy - timedelta(days=7)
        hace_un_mes = hoy - timedelta(days=30)
        hace_tres_meses = hoy - timedelta(days=90)

        controles_semana = ControlPrenatal.objects.filter(
            fecha_control__gte=hace_una_semana,
        ).count()
        controles_mes = ControlPrenatal.objects.filter(
            fecha_control__gte=hace_un_mes,
        ).count()
        controles_tres_meses = ControlPrenatal.objects.filter(
            fecha_control__gte=hace_tres_meses,
        ).count()

        # Promedios generales
        promedios = ControlPrenatal.objects.aggregate(
            peso_promedio=Avg("peso_actual"),
            altura_uterina_promedio=Avg("altura_uterina"),
            pa_sistolica_promedio=Avg("presion_arterial_sistolica"),
            pa_diastolica_promedio=Avg("presion_arterial_diastolica"),
            fcf_promedio=Avg("frecuencia_cardiaca_fetal"),
            fcm_promedio=Avg("frecuencia_cardiaca"),
            temperatura_promedio=Avg("temperatura"),
        )

        # ✅ CORRECCIÓN: Alertas médicas
        con_hipertension = ControlPrenatal.objects.filter(
            Q(presion_arterial_sistolica__gte=140)
            | Q(presion_arterial_diastolica__gte=90),
        ).count()

        con_fcf_anormal = ControlPrenatal.objects.filter(
            Q(frecuencia_cardiaca_fetal__lt=110) | Q(frecuencia_cardiaca_fetal__gt=160),
        ).count()

        con_proteinuria = ControlPrenatal.objects.exclude(
            Q(proteinuria="negativa") | Q(proteinuria__isnull=True),
        ).count()

        con_edema_severo = ControlPrenatal.objects.filter(
            edema__in=["generalizado", "severo"],
        ).count()

        con_movimientos_anormales = ControlPrenatal.objects.filter(
            movimientos_fetales__in=["disminuidos", "ausentes"],
        ).count()

        # Distribución por trimestre
        por_trimestre = {
            "primer_trimestre": ControlPrenatal.objects.filter(
                semanas_gestacion__lte=13,
            ).count(),
            "segundo_trimestre": ControlPrenatal.objects.filter(
                semanas_gestacion__gt=13, semanas_gestacion__lte=27,
            ).count(),
            "tercer_trimestre": ControlPrenatal.objects.filter(
                semanas_gestacion__gt=27,
            ).count(),
        }

        # Embarazos únicos con controles
        embarazos_con_controles = (
            ControlPrenatal.objects.values("embarazo_id").distinct().count()
        )

        # ✅ NUEVO: Controles por médico
        controles_por_medico = (
            ControlPrenatal.objects.values("medico_id__email")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )

        return Response(
            {
                "resumen": {
                    "total_controles": total,
                    "embarazos_con_controles": embarazos_con_controles,
                    "controles_ultima_semana": controles_semana,
                    "controles_ultimo_mes": controles_mes,
                    "controles_tres_meses": controles_tres_meses,
                },
                "promedios": promedios,
                "alertas": {
                    "con_hipertension": con_hipertension,
                    "con_fcf_anormal": con_fcf_anormal,
                    "con_proteinuria": con_proteinuria,
                    "con_edema_severo": con_edema_severo,
                    "con_movimientos_anormales": con_movimientos_anormales,
                    "total_con_alertas": (
                        con_hipertension
                        + con_fcf_anormal
                        + con_proteinuria
                        + con_edema_severo
                        + con_movimientos_anormales
                    ),
                },
                "distribucion_trimestres": por_trimestre,
                "controles_por_medico": list(controles_por_medico),
            },
        )

    @action(detail=False, methods=["get"])
    def alertas(self, _request):
        """✅ EXTENDIDO: Controles con alertas médicas agrupadas por tipo"""
        assert self.queryset is not None
        controles_alerta = self.queryset.filter(
            Q(presion_arterial_sistolica__gte=140)
            | Q(presion_arterial_diastolica__gte=90)
            | Q(frecuencia_cardiaca_fetal__lt=110)
            | Q(frecuencia_cardiaca_fetal__gt=160)
            | Q(edema__in=["severo", "generalizado"])
            | Q(movimientos_fetales__in=["disminuidos", "ausentes"])
            | ~Q(proteinuria="negativa"),
        ).order_by("-fecha_control")

        # ✅ Agrupar por tipo de alerta
        alertas_por_tipo = {
            "hipertension": controles_alerta.filter(
                Q(presion_arterial_sistolica__gte=140)
                | Q(presion_arterial_diastolica__gte=90),
            ).count(),
            "fcf_anormal": controles_alerta.filter(
                Q(frecuencia_cardiaca_fetal__lt=110)
                | Q(frecuencia_cardiaca_fetal__gt=160),
            ).count(),
            "proteinuria": controles_alerta.exclude(
                Q(proteinuria="negativa") | Q(proteinuria__isnull=True),
            ).count(),
            "edema_severo": controles_alerta.filter(
                edema__in=["severo", "generalizado"],
            ).count(),
            "movimientos_anormales": controles_alerta.filter(
                movimientos_fetales__in=["disminuidos", "ausentes"],
            ).count(),
        }

        page = self.paginate_queryset(controles_alerta)
        if page is not None:
            serializer = ControlPrenatalSerializer(page, many=True)
            return self.get_paginated_response(
                {
                    "total_alertas": controles_alerta.count(),
                    "alertas_por_tipo": alertas_por_tipo,
                    "results": serializer.data,
                },
            )

        serializer = ControlPrenatalSerializer(controles_alerta, many=True)
        return Response(
            {
                "total_alertas": controles_alerta.count(),
                "alertas_por_tipo": alertas_por_tipo,
                "controles": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def recientes(self, request):
        """✅ EXTENDIDO: Controles recientes con estadísticas"""
        dias = int(request.query_params.get("dias", 7))
        fecha_desde = timezone.localdate() - timedelta(days=dias)

        assert self.queryset is not None
        controles = self.queryset.filter(fecha_control__gte=fecha_desde).order_by(
            "-fecha_control",
        )

        # ✅ Estadísticas de controles recientes
        estadisticas = {
            "total": controles.count(),
            "con_alertas": controles.filter(
                Q(presion_arterial_sistolica__gte=140)
                | Q(presion_arterial_diastolica__gte=90)
                | Q(frecuencia_cardiaca_fetal__lt=110)
                | Q(frecuencia_cardiaca_fetal__gt=160)
                | Q(edema__in=["severo", "generalizado"])
                | Q(movimientos_fetales__in=["disminuidos", "ausentes"])
            ).count(),
            "embarazos_unicos": controles.values("embarazo_id").distinct().count(),
        }

        page = self.paginate_queryset(controles)
        if page is not None:
            serializer = ControlPrenatalSerializer(page, many=True)
            return self.get_paginated_response(
                {"dias": dias, "estadisticas": estadisticas, "results": serializer.data},
            )

        serializer = ControlPrenatalSerializer(controles, many=True)
        return Response(
            {"dias": dias, "estadisticas": estadisticas, "controles": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def proximos(self, request):
        """✅ EXTENDIDO: Embarazos que requieren control próximo"""
        dias = int(request.query_params.get("dias", 30))

        # Obtener último control de cada embarazo activo
        assert self.queryset is not None
        controles = (
            self.queryset.filter(embarazo_id__estado="activo")
            .order_by("embarazo_id", "-fecha_control")
            .distinct("embarazo_id")
        )

        # Filtrar embarazos que necesitan control
        embarazos_pendientes = []
        hoy = timezone.localdate()

        for control in controles:
            dias_desde_ultimo = (hoy - control.fecha_control).days

            # Lógica: controles cada 4 semanas antes de semana 28, luego cada 2 semanas
            if control.semanas_gestacion and control.semanas_gestacion < 28:
                intervalo_recomendado = 28  # 4 semanas
            else:
                intervalo_recomendado = 14  # 2 semanas

            if dias_desde_ultimo >= intervalo_recomendado:
                embarazos_pendientes.append(control)

        serializer = ControlPrenatalSerializer(embarazos_pendientes, many=True)

        return Response(
            {
                "total": len(embarazos_pendientes),
                "mensaje": "Embarazos activos que requieren control prenatal",
                "dias_evaluados": dias,
                "controles": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def evolucion(self, request):
        """✅ EXTENDIDO: Evolución de parámetros con análisis de tendencias"""
        embarazo_id = request.query_params.get("embarazo_id", None)

        if not embarazo_id:
            return Response(
                {"error": "Debe proporcionar el parámetro embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            embarazo = Embarazo.objects.select_related("paciente").get(id=embarazo_id)
        except Embarazo.DoesNotExist:
            return Response(
                {"error": "Embarazo no encontrado"}, status=status.HTTP_404_NOT_FOUND,
            )

        assert self.queryset is not None
        controles = self.queryset.filter(embarazo_id=embarazo).order_by("fecha_control")

        if not controles.exists():
            return Response(
                {
                    "embarazo_id": embarazo.id,
                    "paciente": f"{embarazo.paciente.id_clinico} - {embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                    "total_controles": 0,
                    "mensaje": "No hay controles registrados para este embarazo",
                    "evolucion": {},
                },
            )

        # ✅ Preparar datos para gráficas
        evolucion_data = {
            "fechas": [],
            "semanas": [],
            "peso": [],
            "altura_uterina": [],
            "presion_sistolica": [],
            "presion_diastolica": [],
            "fcf": [],
            "imc": [],
            "temperatura": [],
            "ganancia_peso": [],
        }

        peso_inicial = None

        for idx, control in enumerate(controles):
            evolucion_data["fechas"].append(control.fecha_control.strftime("%Y-%m-%d"))
            evolucion_data["semanas"].append(control.semanas_gestacion)
            evolucion_data["peso"].append(
                float(control.peso_actual) if control.peso_actual else None,
            )
            evolucion_data["altura_uterina"].append(
                float(control.altura_uterina) if control.altura_uterina else None,
            )
            evolucion_data["presion_sistolica"].append(
                control.presion_arterial_sistolica,
            )
            evolucion_data["presion_diastolica"].append(
                control.presion_arterial_diastolica,
            )
            evolucion_data["fcf"].append(control.frecuencia_cardiaca_fetal)
            evolucion_data["imc"].append(float(control.imc) if control.imc else None)
            evolucion_data["temperatura"].append(
                float(control.temperatura) if control.temperatura else None,
            )

            # Calcular ganancia de peso
            if idx == 0 and control.peso_actual:
                peso_inicial = control.peso_actual
                evolucion_data["ganancia_peso"].append(0)
            elif peso_inicial and control.peso_actual:
                ganancia = float(control.peso_actual) - float(peso_inicial)
                evolucion_data["ganancia_peso"].append(round(ganancia, 2))
            else:
                evolucion_data["ganancia_peso"].append(None)

        # ✅ Análisis de tendencias
        analisis = {
            "tendencia_peso": "estable",
            "tendencia_pa": "normal",
            "tendencia_fcf": "normal",
            "alertas_detectadas": [],
        }

        # Analizar tendencia de peso
        pesos_validos = [p for p in evolucion_data["peso"] if p is not None]
        if len(pesos_validos) >= 2:
            if pesos_validos[-1] > pesos_validos[0] * 1.15:
                analisis["tendencia_peso"] = "aumento_significativo"
            elif pesos_validos[-1] < pesos_validos[0] * 0.95:
                analisis["tendencia_peso"] = "disminución"

        primer_ctrl = controles.first()
        ultimo_ctrl = controles.last()
        return Response(
            {
                "embarazo_id": embarazo.id,
                "paciente": f"{embarazo.paciente.id_clinico} - {embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                "total_controles": controles.count(),
                "primer_control": primer_ctrl.fecha_control.strftime("%Y-%m-%d") if primer_ctrl is not None else None,
                "ultimo_control": ultimo_ctrl.fecha_control.strftime("%Y-%m-%d") if ultimo_ctrl is not None else None,
                "evolucion": evolucion_data,
                "analisis": analisis,
            },
        )

    @action(detail=True, methods=["get"])
    def reporte_completo(self, _request, pk=None):
        """✅ EXTENDIDO: Reporte completo con información del embarazo"""
        control = self.get_object()

        # Obtener método del modelo
        reporte = control.generar_reporte_completo()

        # ✅ Agregar información del embarazo
        if control.embarazo_id:

            reporte["embarazo"] = EmbarazoSerializer(control.embarazo_id).data

        return Response(reporte)

    @action(detail=False, methods=["get"])
    def riesgo_alto(self, _request):
        """✅ NUEVO: Controles de embarazos de alto riesgo"""
        assert self.queryset is not None
        controles_alto_riesgo = self.queryset.filter(
            embarazo_id__riesgo_embarazo="alto", embarazo_id__estado="activo",
        ).order_by("-fecha_control")

        # Estadísticas
        estadisticas = {
            "total": controles_alto_riesgo.count(),
            "con_alertas": controles_alto_riesgo.filter(
                Q(presion_arterial_sistolica__gte=140)
                | Q(presion_arterial_diastolica__gte=90)
                | Q(frecuencia_cardiaca_fetal__lt=110)
                | Q(frecuencia_cardiaca_fetal__gt=160)
                | Q(edema__in=["severo", "generalizado"])
                | Q(movimientos_fetales__in=["disminuidos", "ausentes"])
            ).count(),
            "embarazos_unicos": controles_alto_riesgo.values("embarazo_id")
            .distinct()
            .count(),
        }

        page = self.paginate_queryset(controles_alto_riesgo)
        if page is not None:
            serializer = ControlPrenatalSerializer(page, many=True)
            return self.get_paginated_response(
                {"estadisticas": estadisticas, "results": serializer.data},
            )

        serializer = ControlPrenatalSerializer(controles_alto_riesgo, many=True)
        return Response({"estadisticas": estadisticas, "controles": serializer.data})

    @action(detail=False, methods=["get"], url_path="ultimo-control")
    def ultimo_control(self, request):
        """Obtener el último control de un embarazo"""
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "Debe proporcionar el parámetro embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ultimo = ControlPrenatal.objects.filter(embarazo_id=embarazo_id).order_by("-fecha_control").first()
            if not ultimo:
                return Response(
                    {"error": "No hay controles para este embarazo"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = ControlPrenatalSerializer(ultimo)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="con-alertas")
    def con_alertas(self, _request):
        """Alias para alertas — compatibilidad con frontend"""
        return self.alertas(_request)

    @action(detail=False, methods=["post"])
    def programar(self, request):
        """Programar próximo control prenatal automáticamente"""
        embarazo_id = request.data.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "Se requiere embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            from datetime import timedelta
            embarazo = Embarazo.objects.get(id=embarazo_id)
            ultimo = ControlPrenatal.objects.filter(embarazo_id=embarazo).order_by("-fecha_control").first()
            if ultimo:
                dias_desde_ultimo = (timezone.localdate() - ultimo.fecha_control).days
                if dias_desde_ultimo < 14:
                    return Response({
                        "mensaje": "El último control fue hace menos de 14 días",
                        "ultimo_control": str(ultimo.fecha_control),
                        "proximo_sugerido": str(ultimo.fecha_control + timedelta(days=28)),
                    })
            num_control = (ultimo.numero_control + 1) if ultimo else 1
            proxima_fecha = timezone.localdate() + timedelta(days=30)
            return Response({
                "mensaje": "Próximo control programado",
                "numero_control": num_control,
                "fecha_sugerida": str(proxima_fecha),
                "embarazo_id": int(embarazo_id),
            })
        except Embarazo.DoesNotExist:
            return Response({"error": "Embarazo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], url_path="sugerencias-controles")
    def sugerencias_controles(self, request):
        """Sugerir fechas de controles según protocolo"""
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "Se requiere embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            embarazo = Embarazo.objects.get(id=embarazo_id)
            sugerencias = []
            if embarazo.fecha_ultima_menstruacion:
                fum = embarazo.fecha_ultima_menstruacion
                from datetime import timedelta
                hitos = [
                    (12, "Control 1er trimestre (sem 12-14)"),
                    (20, "Ecografía morfológica (sem 20-22)"),
                    (28, "Control 2do trimestre (sem 28)"),
                    (32, "Control 3er trimestre (sem 32)"),
                    (36, "Control semanal (sem 36+)"),
                ]
                for semana, desc in hitos:
                    fecha = fum + timedelta(weeks=semana)
                    sugerencias.append({
                        "semana": semana,
                        "descripcion": desc,
                        "fecha_sugerida": str(fecha),
                    })
            return Response({"embarazo_id": embarazo.id, "sugerencias": sugerencias})
        except Embarazo.DoesNotExist:
            return Response({"error": "Embarazo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"])
    def evaluar(self, request, pk=None):
        """Evaluar un control prenatal con análisis de riesgos"""
        control = self.get_object()
        alertas = []
        if control.tiene_hipertension():
            alertas.append("Hipertensión detectada")
        if control.fcf_es_anormal():
            alertas.append("Frecuencia cardíaca fetal anormal")
        if control.proteinuria and "positiva" in str(control.proteinuria):
            alertas.append("Proteinuria positiva")
        return Response({
            "control_id": control.id,
            "evaluacion": "con_alertas" if alertas else "normal",
            "alertas": alertas,
            "recomendacion": "Revisión médica requerida" if alertas else "Control dentro de parámetros normales",
        })

    @action(detail=True, methods=["get"], url_path="detectar-riesgos")
    def detectar_riesgos(self, _request, pk=None):
        """Detectar factores de riesgo en un control prenatal"""
        control = self.get_object()
        riesgos = []
        if control.presion_arterial_sistolica and control.presion_arterial_sistolica >= 140:
            riesgos.append({"tipo": "hipertension", "nivel": "alto", "valor": control.presion_arterial_sistolica})
        if control.presion_arterial_diastolica and control.presion_arterial_diastolica >= 90:
            riesgos.append({"tipo": "hipertension_diastolica", "nivel": "alto", "valor": control.presion_arterial_diastolica})
        if control.frecuencia_cardiaca_fetal and (control.frecuencia_cardiaca_fetal < 110 or control.frecuencia_cardiaca_fetal > 160):
            riesgos.append({"tipo": "fcf_anormal", "nivel": "alto", "valor": control.frecuencia_cardiaca_fetal})
        if control.proteinuria and "positiva" in str(control.proteinuria):
            riesgos.append({"tipo": "proteinuria", "nivel": "medio", "valor": control.proteinuria})
        if control.edema in ("severo", "generalizado"):
            riesgos.append({"tipo": "edema", "nivel": "medio", "valor": control.edema})
        return Response({
            "control_id": control.id,
            "total_riesgos": len(riesgos),
            "nivel": "alto" if any(r["nivel"] == "alto" for r in riesgos) else "bajo",
            "riesgos": riesgos,
        })

    @action(detail=False, methods=["get"], url_path="curva-crecimiento")
    def curva_crecimiento(self, request):
        """Obtener datos para curva de crecimiento (peso, AU por semanas)"""
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "Se requiere embarazo_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            controles = ControlPrenatal.objects.filter(
                embarazo_id=embarazo_id
            ).order_by("semanas_gestacion").values(
                "semanas_gestacion", "peso_actual", "altura_uterina"
            )
            data = {
                "peso": [{"semana": c["semanas_gestacion"], "valor": float(c["peso_actual"]) if c["peso_actual"] else None} for c in controles],
                "altura_uterina": [{"semana": c["semanas_gestacion"], "valor": float(c["altura_uterina"]) if c["altura_uterina"] else None} for c in controles],
            }
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="exportar-excel")
    def exportar_excel(self, request):
        """Exportar controles a Excel"""
        try:
            from io import BytesIO

            import openpyxl
            from django.http import HttpResponse
            queryset = self.filter_queryset(self.get_queryset())
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Controles"
            ws.append(["ID", "Embarazo", "N° Control", "Fecha", "Semanas", "Peso", "AU", "PA Sist", "PA Diast", "FCF"])
            for c in queryset:
                ws.append([
                    c.id, c.embarazo_id, c.numero_control, str(c.fecha_control),
                    c.semanas_gestacion, float(c.peso_actual) if c.peso_actual else None,
                    float(c.altura_uterina) if c.altura_uterina else None,
                    c.presion_arterial_sistolica, c.presion_arterial_diastolica,
                    c.frecuencia_cardiaca_fetal,
                ])
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = "attachment; filename=controles.xlsx"
            return response
        except ImportError:
            return Response({"error": "openpyxl no instalado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"], url_path="exportar-pdf")
    def exportar_pdf(self, request, pk=None):
        """Exporta control prenatal a PDF
        GET /api/controles/{id}/exportar-pdf/
        """
        control = self.get_object()
        try:
            import pdfkit
            from django.http import HttpResponse
            from django.template.loader import render_to_string
            html = render_to_string("controles/reporte_control_pdf.html", {
                "control": control,
                "paciente": control.paciente,
            })
            pdf = pdfkit.from_string(html, False)
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="control_{control.id}.pdf"'
            return response
        except ImportError:
            serializer = self.get_serializer(control)
            return Response({"mensaje": "PDF no disponible. Instale pdfkit: pip install pdfkit", "control": serializer.data})
        except Exception as e:
            return Response({"error": f"Error generando PDF: {e}"}, status=500)
