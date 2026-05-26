"""=============================================================================
MÓDULO: EMBARAZOS - VIEWSET V3.0 FINAL CORREGIDO
=============================================================================
✅ Sin errores de prefetch_related
✅ Optimizado para el modelo real
=============================================================================
"""

from datetime import date, timedelta

from django.core.cache import cache
from django.db.models import Count, Max
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from core.permissions import FetalMedicalPermission
from rest_framework.response import Response

from pacientes.models import Paciente

from .models import Embarazo
from .serializers import (
    EmbarazoCreateUpdateSerializer,
    EmbarazoListSerializer,
    EmbarazoSerializer,
)


class EmbarazoViewSet(viewsets.ModelViewSet):
    """ViewSet for comprehensive Pregnancy management.

    Manages pregnancy registration, risk assessment, trimester tracking,
    and gestational monitoring.

    **Endpoints:**
    - `GET /api/embarazos/` - List all pregnancies (paginated)
    - `POST /api/embarazos/` - Create new pregnancy
    - `GET /api/embarazos/{id}/` - Get pregnancy details
    - `PUT /api/embarazos/{id}/` - Update pregnancy (full)
    - `PATCH /api/embarazos/{id}/` - Update pregnancy (partial)
    - `DELETE /api/embarazos/{id}/` - Delete pregnancy (admin only)
    - `GET /api/embarazos/activos/` - Active pregnancies
    - `GET /api/embarazos/por_paciente/paciente_id=X` - Pregnancies by patient
    - `GET /api/embarazos/estadisticas/` - General statistics
    - `GET /api/embarazos/{id}/controles/` - Prenatal controls for pregnancy
    - `POST /api/embarazos/{id}/reactivar/` - Reactivate pregnancy
    - `GET /api/embarazos/alto_riesgo/` - High-risk pregnancies
    - `GET /api/embarazos/proximos_partos/dias=30` - Upcoming deliveries
    - `GET /api/embarazos/primer_trimestre/` - First trimester pregnancies
    - `GET /api/embarazos/segundo_trimestre/` - Second trimester pregnancies
    - `GET /api/embarazos/tercer_trimestre/` - Third trimester pregnancies
    - `GET /api/embarazos/{id}/resumen_completo/` - Complete pregnancy summary
    - `GET /api/embarazos/multiples/` - Multiple pregnancies (twins, etc.)

    **Authentication:** JWT Bearer token required
    **Permissions:** Authenticated users (admin required for delete)
    """

    # ✅ OPTIMIZACIÓN: Solo select_related (sin prefetch que causa error)
    queryset = (
        Embarazo.objects.select_related("paciente").all().order_by("-fecha_registro")
    )

    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "estado",
        "tipo_embarazo",
        "riesgo_embarazo",
        "paciente",
        "numero_gesta",
    ]

    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "paciente__apellido_materno",
        "paciente__id_clinico",
        "paciente__ci",  # Campo correcto — era cedula_identidad (no existe)
        "notas",
    ]

    ordering_fields = [
        "fecha_registro",
        "fecha_ultima_menstruacion",
        "fecha_probable_parto",
        "numero_gesta",
        "riesgo_embarazo",
    ]

    def get_serializer_class(self):
        """✅ Serializer según acción"""
        if self.action in ["create", "update", "partial_update"]:
            return EmbarazoCreateUpdateSerializer
        if self.action == "list":
            return EmbarazoListSerializer  # ✅ Usar serializer optimizado para listados
        return EmbarazoSerializer  # Para retrieve y acciones personalizadas

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    def get_queryset(self):
        """✅ Filtros avanzados"""
        queryset = super().get_queryset()

        # Filtro por rango de fechas FUM
        fum_desde = self.request.query_params.get("fum_desde", None)
        fum_hasta = self.request.query_params.get("fum_hasta", None)

        if fum_desde:
            try:
                queryset = queryset.filter(fecha_ultima_menstruacion__gte=fum_desde)
            except Exception:
                pass

        if fum_hasta:
            try:
                queryset = queryset.filter(fecha_ultima_menstruacion__lte=fum_hasta)
            except Exception:
                pass

        # Filtro por semanas de gestación
        semanas_min = self.request.query_params.get("semanas_min", None)
        semanas_max = self.request.query_params.get("semanas_max", None)

        if semanas_min or semanas_max:
            today = date.today()

            if semanas_min:
                try:
                    fecha_max_fum = today - timedelta(weeks=int(semanas_min))
                    queryset = queryset.filter(
                        fecha_ultima_menstruacion__lte=fecha_max_fum,
                    )
                except (ValueError, TypeError):
                    pass

            if semanas_max:
                try:
                    fecha_min_fum = today - timedelta(weeks=int(semanas_max))
                    queryset = queryset.filter(
                        fecha_ultima_menstruacion__gte=fecha_min_fum,
                    )
                except (ValueError, TypeError):
                    pass

        # Filtro por trimestre
        trimestre = self.request.query_params.get("trimestre", None)
        if trimestre:
            try:
                trimestre = int(trimestre)
                today = date.today()

                if trimestre == 1:
                    fecha_max = today
                    fecha_min = today - timedelta(weeks=13)
                    queryset = queryset.filter(
                        fecha_ultima_menstruacion__gte=fecha_min,
                        fecha_ultima_menstruacion__lte=fecha_max,
                    )
                elif trimestre == 2:
                    fecha_max = today - timedelta(weeks=14)
                    fecha_min = today - timedelta(weeks=27)
                    queryset = queryset.filter(
                        fecha_ultima_menstruacion__gte=fecha_min,
                        fecha_ultima_menstruacion__lte=fecha_max,
                    )
                elif trimestre == 3:
                    fecha_max = today - timedelta(weeks=28)
                    queryset = queryset.filter(fecha_ultima_menstruacion__lte=fecha_max)
            except (ValueError, TypeError):
                pass

        return queryset

    @extend_schema(
        summary="List all pregnancies",
        description="Retrieve a paginated list of all pregnancies with filtering options.",
        responses={200: EmbarazoListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new pregnancy",
        description="Register a new pregnancy for a patient.",
        request=EmbarazoCreateUpdateSerializer,
        responses={201: EmbarazoSerializer},
    )
    def create(self, request, *args, **kwargs):
        """✅ Crear embarazo"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Recargar con relaciones
        embarazo = Embarazo.objects.select_related("paciente").get(
            id=serializer.instance.id,
        )
        return_serializer = EmbarazoSerializer(embarazo)

        response_data = return_serializer.data
        response_data["mensaje"] = "Embarazo creado correctamente"

        if embarazo.riesgo_embarazo == "alto":
            response_data["advertencia"] = (
                "Embarazo clasificado como ALTO RIESGO. Requiere seguimiento especializado."
            )

        headers = self.get_success_headers(return_serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        summary="Update pregnancy",
        description="Update pregnancy information (full or partial).",
        request=EmbarazoCreateUpdateSerializer,
        responses={200: EmbarazoSerializer},
    )
    def update(self, request, *args, **kwargs):
        """Update"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        embarazo = Embarazo.objects.select_related("paciente").get(id=instance.id)
        return_serializer = EmbarazoSerializer(embarazo)

        response_data = return_serializer.data
        response_data["mensaje"] = "Embarazo actualizado correctamente"

        return Response(response_data)

    @extend_schema(
        summary="Delete pregnancy",
        description="Permanently delete a pregnancy and all related controls/deliveries. Admin only.",
        responses={200: OpenApiResponse(description="Pregnancy deleted successfully")},
    )
    def destroy(self, request, *args, **kwargs):
        """Eliminar embarazo completamente de la base de datos"""
        # ✅ SEGURIDAD: Solo administradores pueden eliminar
        if request.user.rol != "administrador":
            return Response(
                {
                    "error": "Sin permisos para eliminar",
                    "detalle": "Solo los administradores pueden eliminar embarazos del sistema.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        from django.db import connection

        instance = self.get_object()
        embarazo_id = instance.id
        uuid_str = str(instance.uuid)
        paciente_nombre = f"{instance.paciente.id_clinico} - {instance.paciente.nombre} {instance.paciente.apellido_paterno}"
        numero_gesta = instance.numero_gesta

        # Eliminar usando SQL directo para evitar problemas de cascada
        with connection.cursor() as cursor:
            # 1. Eliminar Controles Prenatales del embarazo
            cursor.execute(
                "DELETE FROM controles_prenatales WHERE embarazo_id = %s", [embarazo_id],
            )
            controles_eliminados = cursor.rowcount

            # 2. Eliminar Partos del embarazo (si existen)
            cursor.execute("DELETE FROM partos WHERE embarazo_id = %s", [embarazo_id])
            partos_eliminados = cursor.rowcount

            # 3. Eliminar el Embarazo
            cursor.execute("DELETE FROM embarazos WHERE id = %s", [embarazo_id])

        return Response(
            {
                "message": "Embarazo eliminado completamente",
                "detalles": {
                    "paciente": paciente_nombre,
                    "numero_gesta": numero_gesta,
                    "controles_eliminados": controles_eliminados,
                    "partos_eliminados": partos_eliminados,
                },
                "id": embarazo_id,
                "uuid": uuid_str,
            },
            status=status.HTTP_200_OK,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENDPOINTS PERSONALIZADOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @action(detail=False, methods=["get"])
    def activos(self, _request):
        """✅ Embarazos activos"""
        embarazos = self.queryset.filter(estado="activo")

        page = self.paginate_queryset(embarazos)
        if page is not None:
            serializer = EmbarazoSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EmbarazoSerializer(embarazos, many=True)
        return Response({"total": embarazos.count(), "embarazos": serializer.data})

    @action(detail=False, methods=["get"], url_path="por_paciente")
    def por_paciente(self, request):
        """✅ Embarazos de un paciente"""
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

        embarazos = self.queryset.filter(paciente=paciente).order_by("-fecha_registro")
        serializer = EmbarazoSerializer(embarazos, many=True)

        estadisticas = {
            "total_embarazos": embarazos.count(),
            "embarazos_activos": embarazos.filter(estado="activo").count(),
            "embarazos_finalizados": embarazos.filter(estado="finalizado").count(),
            "embarazos_perdidas": embarazos.filter(estado="perdida").count(),
            "embarazos_alto_riesgo": embarazos.filter(riesgo_embarazo="alto").count(),
            "gesta_maxima": embarazos.aggregate(Max("numero_gesta"))[
                "numero_gesta__max"
            ]
            or 0,
        }

        from pacientes.serializers import PacienteSerializer

        return Response(
            {
                "paciente": PacienteSerializer(paciente).data,
                "embarazos": serializer.data,
                "estadisticas": estadisticas,
            },
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """Estadisticas generales. Cached for 60 seconds."""
        cache_key = f"embarazo_stats:globales:user_{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)

        total = Embarazo.objects.count()
        activos = Embarazo.objects.filter(estado="activo").count()
        finalizados = Embarazo.objects.filter(estado="finalizado").count()
        perdidas = Embarazo.objects.filter(estado="perdida").count()

        por_tipo = (
            Embarazo.objects.filter(estado="activo")
            .values("tipo_embarazo")
            .annotate(total=Count("id"))
        )

        por_riesgo = (
            Embarazo.objects.filter(estado="activo")
            .values("riesgo_embarazo")
            .annotate(total=Count("id"))
        )

        alto_riesgo = Embarazo.objects.filter(
            estado="activo", riesgo_embarazo="alto",
        ).count()

        today = date.today()

        primer_trimestre = Embarazo.objects.filter(
            estado="activo", fecha_ultima_menstruacion__gte=today - timedelta(weeks=13),
        ).count()

        segundo_trimestre = Embarazo.objects.filter(
            estado="activo",
            fecha_ultima_menstruacion__gte=today - timedelta(weeks=27),
            fecha_ultima_menstruacion__lt=today - timedelta(weeks=13),
        ).count()

        tercer_trimestre = Embarazo.objects.filter(
            estado="activo", fecha_ultima_menstruacion__lt=today - timedelta(weeks=27),
        ).count()

        proximos_30_dias = Embarazo.objects.filter(
            estado="activo",
            fecha_probable_parto__gte=today,
            fecha_probable_parto__lte=today + timedelta(days=30),
        ).count()

        result = {
            "resumen_general": {
                "total_embarazos": total,
                "activos": activos,
                "finalizados": finalizados,
                "perdidas": perdidas,
                "alto_riesgo_activos": alto_riesgo,
            },
            "distribucion_tipo": list(por_tipo),
            "distribucion_riesgo": list(por_riesgo),
            "distribucion_trimestre": {
                "primer_trimestre": primer_trimestre,
                "segundo_trimestre": segundo_trimestre,
                "tercer_trimestre": tercer_trimestre,
            },
            "seguimiento": {
                "proximos_partos_30_dias": proximos_30_dias,
            },
        }

        # Cache for 60 seconds
        cache.set(cache_key, result, timeout=60)
        return Response(result)

    @action(detail=True, methods=["get"])
    def controles(self, _request, _pk=None):
        """✅ Controles del embarazo"""
        embarazo = self.get_object()

        # ✅ Usar related_name correcto del modelo: 'controles'
        controles = embarazo.controles.all().order_by("numero_control", "fecha_control")

        from controles.serializers import ControlPrenatalListSerializer

        serializer = ControlPrenatalListSerializer(controles, many=True)

        return Response(
            {
                "embarazo": EmbarazoSerializer(embarazo).data,
                "controles": serializer.data,
                "total": controles.count(),
            },
        )

    @action(detail=True, methods=["post"])
    def reactivar(self, _request, _pk=None):
        """✅ Reactivar embarazo"""
        embarazo = self.get_object()

        if embarazo.estado == "activo":
            return Response(
                {"error": "El embarazo ya está activo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar que no haya otro embarazo activo
        embarazos_activos = Embarazo.objects.filter(
            paciente=embarazo.paciente, estado="activo",
        )

        if embarazos_activos.exists():
            return Response(
                {"error": "Esta paciente ya tiene un embarazo activo registrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        embarazo.estado = "activo"
        embarazo.save()

        return Response(
            {
                "mensaje": "Embarazo reactivado correctamente",
                "embarazo": EmbarazoSerializer(embarazo).data,
            },
        )

    @action(detail=False, methods=["get"])
    def alto_riesgo(self, _request):
        """✅ Embarazos de alto riesgo"""
        embarazos_alto_riesgo = self.queryset.filter(
            estado="activo", riesgo_embarazo="alto",
        ).order_by("-fecha_registro")

        page = self.paginate_queryset(embarazos_alto_riesgo)
        if page is not None:
            serializer = EmbarazoSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EmbarazoSerializer(embarazos_alto_riesgo, many=True)
        return Response(
            {"total": embarazos_alto_riesgo.count(), "embarazos": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def proximos_partos(self, request):
        """✅ Próximos partos"""
        dias = int(request.query_params.get("dias", 30))
        hoy = date.today()
        fecha_limite = hoy + timedelta(days=dias)

        embarazos = self.queryset.filter(
            estado="activo",
            fecha_probable_parto__gte=hoy,
            fecha_probable_parto__lte=fecha_limite,
        ).order_by("fecha_probable_parto")

        serializer = EmbarazoSerializer(embarazos, many=True)

        return Response(
            {
                "total": embarazos.count(),
                "dias_evaluados": dias,
                "fecha_desde": hoy.strftime("%Y-%m-%d"),
                "fecha_hasta": fecha_limite.strftime("%Y-%m-%d"),
                "embarazos": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def primer_trimestre(self, _request):
        """✅ Embarazos en 1er trimestre"""
        hoy = date.today()
        fecha_min = hoy - timedelta(weeks=13)

        embarazos = self.queryset.filter(
            estado="activo", fecha_ultima_menstruacion__gte=fecha_min,
        ).order_by("-fecha_ultima_menstruacion")

        serializer = EmbarazoSerializer(embarazos, many=True)

        return Response(
            {
                "total": embarazos.count(),
                "trimestre": 1,
                "rango_semanas": "0-13 semanas",
                "embarazos": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def segundo_trimestre(self, _request):
        """✅ Embarazos en 2do trimestre"""
        hoy = date.today()
        fecha_max = hoy - timedelta(weeks=14)
        fecha_min = hoy - timedelta(weeks=27)

        embarazos = self.queryset.filter(
            estado="activo",
            fecha_ultima_menstruacion__gte=fecha_min,
            fecha_ultima_menstruacion__lt=fecha_max,
        ).order_by("-fecha_ultima_menstruacion")

        serializer = EmbarazoSerializer(embarazos, many=True)

        return Response(
            {
                "total": embarazos.count(),
                "trimestre": 2,
                "rango_semanas": "14-27 semanas",
                "embarazos": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def tercer_trimestre(self, _request):
        """✅ Embarazos en 3er trimestre"""
        hoy = date.today()
        fecha_max = hoy - timedelta(weeks=28)

        embarazos = self.queryset.filter(
            estado="activo", fecha_ultima_menstruacion__lt=fecha_max,
        ).order_by("fecha_probable_parto")

        serializer = EmbarazoSerializer(embarazos, many=True)

        return Response(
            {
                "total": embarazos.count(),
                "trimestre": 3,
                "rango_semanas": "28+ semanas",
                "embarazos": serializer.data,
            },
        )

    @action(detail=True, methods=["get"])
    def resumen_completo(self, _request, _pk=None):
        """✅ Resumen completo"""
        embarazo = self.get_object()
        embarazo_data = EmbarazoSerializer(embarazo).data

        # Calcular edad gestacional actual
        if embarazo.fecha_ultima_menstruacion:
            dias_diferencia = (date.today() - embarazo.fecha_ultima_menstruacion).days
            semanas = dias_diferencia // 7
            dias = dias_diferencia % 7
            edad_gestacional = {
                "semanas": semanas,
                "dias": dias,
                "texto": f"{semanas} semanas + {dias} días",
            }
        else:
            edad_gestacional = None

        return Response(
            {
                "embarazo": embarazo_data,
                "edad_gestacional_actual": edad_gestacional,
            },
        )

    @action(detail=False, methods=["get"])
    def multiples(self, _request):
        """✅ Embarazos múltiples"""
        embarazos_multiples = self.queryset.filter(
            estado="activo", tipo_embarazo__in=["gemelar", "multiple"],
        ).order_by("-fecha_registro")

        estadisticas = {
            "total": embarazos_multiples.count(),
            "gemelar": embarazos_multiples.filter(tipo_embarazo="gemelar").count(),
            "multiple": embarazos_multiples.filter(tipo_embarazo="multiple").count(),
        }

        serializer = EmbarazoSerializer(embarazos_multiples, many=True)

        return Response({"estadisticas": estadisticas, "embarazos": serializer.data})
