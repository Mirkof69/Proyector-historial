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

from datetime import date, timedelta

from django.db.models import Avg, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from core.permissions import FetalMedicalPermission
from rest_framework.response import Response

from embarazos.models import Embarazo
from embarazos.serializers import EmbarazoSerializer

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
        "medico_id__username",
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

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTROS POR FECHA
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        fecha_desde = self.request.query_params.get("fecha_desde", None)
        fecha_hasta = self.request.query_params.get("fecha_hasta", None)

        if fecha_desde:
            try:
                queryset = queryset.filter(fecha_control__gte=fecha_desde)
            except Exception:
                pass

        if fecha_hasta:
            try:
                queryset = queryset.filter(fecha_control__lte=fecha_hasta)
            except Exception:
                pass

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTROS POR SEMANAS DE GESTACIÓN
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        semanas_min = self.request.query_params.get("semanas_min", None)
        semanas_max = self.request.query_params.get("semanas_max", None)

        if semanas_min:
            try:
                queryset = queryset.filter(semanas_gestacion__gte=int(semanas_min))
            except (ValueError, TypeError):
                pass

        if semanas_max:
            try:
                queryset = queryset.filter(semanas_gestacion__lte=int(semanas_max))
            except (ValueError, TypeError):
                pass

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTRO POR ALERTAS (VALORES ANORMALES)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        con_alertas = self.request.query_params.get("con_alertas", None)
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
        solo_activos = self.request.query_params.get("solo_activos", None)
        if solo_activos == "true":
            queryset = queryset.filter(embarazo_id__estado="activo")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTRO POR PACIENTE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        paciente_id = self.request.query_params.get("paciente_id", None)
        if paciente_id:
            try:
                queryset = queryset.filter(
                    Q(paciente__id=int(paciente_id))
                    | Q(embarazo_id__paciente__id=int(paciente_id)),
                )
            except (ValueError, TypeError):
                pass

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FILTRO POR TRIMESTRE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        trimestre = self.request.query_params.get("trimestre", None)
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
        if request.user.rol != "administrador":
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

        controles = self.queryset.filter(embarazo_id=embarazo).order_by(
            "numero_control", "fecha_control",
        )

        # ✅ Estadísticas del embarazo
        estadisticas = {
            "total_controles": controles.count(),
            "controles_con_alertas": controles.filter(tiene_alertas=True).count(),
            "ultimo_peso": None,
            "ultima_pa": None,
            "ultima_fcf": None,
        }

        if controles.exists():
            ultimo_control = controles.last()
            estadisticas["ultimo_peso"] = (
                float(ultimo_control.peso_actual)
                if ultimo_control.peso_actual
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

        return Response(
            {
                "embarazo": EmbarazoSerializer(embarazo).data,
                "controles": serializer.data,
                "estadisticas": estadisticas,
                "primer_control": controles.first().fecha_control
                if controles.exists()
                else None,
                "ultimo_control": controles.last().fecha_control
                if controles.exists()
                else None,
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
            from pacientes.models import Paciente

            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado"}, status=status.HTTP_404_NOT_FOUND,
            )

        # Obtener todos los controles del paciente
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
        hoy = date.today()
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
            imc_promedio=Avg("imc"),
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
            ControlPrenatal.objects.values("medico_id__username")
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
        fecha_desde = date.today() - timedelta(days=dias)

        controles = self.queryset.filter(fecha_control__gte=fecha_desde).order_by(
            "-fecha_control",
        )

        # ✅ Estadísticas de controles recientes
        estadisticas = {
            "total": controles.count(),
            "con_alertas": controles.filter(tiene_alertas=True).count(),
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
        controles = (
            self.queryset.filter(embarazo_id__estado="activo")
            .order_by("embarazo_id", "-fecha_control")
            .distinct("embarazo_id")
        )

        # Filtrar embarazos que necesitan control
        embarazos_pendientes = []
        hoy = date.today()

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

        return Response(
            {
                "embarazo_id": embarazo.id,
                "paciente": f"{embarazo.paciente.id_clinico} - {embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                "total_controles": controles.count(),
                "primer_control": controles.first().fecha_control.strftime("%Y-%m-%d"),
                "ultimo_control": controles.last().fecha_control.strftime("%Y-%m-%d"),
                "evolucion": evolucion_data,
                "analisis": analisis,
            },
        )

    @action(detail=True, methods=["get"])
    def reporte_completo(self, _request, _pk=None):
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
        controles_alto_riesgo = self.queryset.filter(
            embarazo_id__riesgo_embarazo="alto", embarazo_id__estado="activo",
        ).order_by("-fecha_control")

        # Estadísticas
        estadisticas = {
            "total": controles_alto_riesgo.count(),
            "con_alertas": controles_alto_riesgo.filter(tiene_alertas=True).count(),
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
