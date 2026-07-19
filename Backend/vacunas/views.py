"""=============================================================================
MÓDULO: VACUNAS - VIEWS
=============================================================================
ViewSets para gestión de vacunas en sistema de atención prenatal
- TipoVacunaViewSet: CRUD y filtros para catálogo de vacunas
- RegistroVacunaViewSet: CRUD y acciones personalizadas para registros
=============================================================================
"""

from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets

from core.filtros import BusquedaClinicaFilter
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import RegistroVacuna, TipoVacuna
from .serializers import (
    RegistroVacunaCreateUpdateSerializer,
    RegistroVacunaListSerializer,
    RegistroVacunaSerializer,
    TipoVacunaListSerializer,
    TipoVacunaSerializer,
)

# from pacientes.models import Paciente  # REMOVED
# from embarazos.models import Embarazo  # REMOVED


# =============================================================================
# TIPO VACUNA VIEWSET
# =============================================================================


class TipoVacunaViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gestionar tipos de vacunas

    ENDPOINTS:
        pass
    - list: Lista todos los tipos de vacunas
    - create: Crear nuevo tipo de vacuna
    - retrieve: Obtener detalle de tipo de vacuna
    - update/partial_update: Actualizar tipo de vacuna
    - destroy: Eliminar tipo de vacuna

    ACCIONES PERSONALIZADAS:
        pass
    - activas: Vacunas activas en el catálogo
    - obligatorias_embarazo: Vacunas obligatorias durante el embarazo
    - estadisticas: Estadísticas de uso de vacunas
    """

    queryset = TipoVacuna.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos de filtrado
    filterset_fields = {
        "activo": ["exact"],
        "obligatoria_embarazo": ["exact"],
        "dosis_requeridas": ["exact", "gte", "lte"],
    }

    # Campos de búsqueda
    search_fields = [
        "nombre",
        "descripcion",
        "laboratorio",
    ]

    # Campos de ordenamiento
    ordering_fields = [
        "nombre",
        "dosis_requeridas",
        "fecha_creacion",
    ]
    ordering = ["nombre"]

    def get_serializer_class(self):
        """Usa serializer apropiado según la acción"""
        if self.action == "list":
            return TipoVacunaListSerializer
        return TipoVacunaSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def activas(self, _request):
        """Retorna solo las vacunas activas
        GET /api/vacunas/tipos-vacunas/activas/
        """
        assert self.queryset is not None
        vacunas = self.queryset.filter(activo=True)
        serializer = self.get_serializer(vacunas, many=True)
        return Response({"total": vacunas.count(), "vacunas": serializer.data})

    @action(detail=False, methods=["get"])
    def obligatorias_embarazo(self, _request):
        """Retorna vacunas obligatorias durante el embarazo
        GET /api/vacunas/tipos-vacunas/obligatorias_embarazo/
        """
        assert self.queryset is not None
        vacunas = self.queryset.filter(activo=True, obligatoria_embarazo=True)
        serializer = self.get_serializer(vacunas, many=True)
        return Response({"total": vacunas.count(), "vacunas": serializer.data})

    @action(detail=False, methods=["get"])
    def estadisticas(self, _request):
        """Estadísticas generales de tipos de vacunas
        GET /api/vacunas/tipos-vacunas/estadisticas/
        """
        assert self.queryset is not None
        total_vacunas = self.queryset.count()
        activas = self.queryset.filter(activo=True).count()
        obligatorias = self.queryset.filter(obligatoria_embarazo=True).count()

        # Estadísticas de aplicaciones
        vacunas_con_registros = self.queryset.annotate(
            total_aplicaciones=Count("registros"),
        ).order_by("-total_aplicaciones")[:5]

        top_vacunas = [
            {
                "id": v.id,
                "nombre": v.nombre,
                "total_aplicaciones": getattr(v, "total_aplicaciones", 0),
            }
            for v in vacunas_con_registros
        ]

        return Response(
            {
                "resumen": {
                    "total_vacunas": total_vacunas,
                    "activas": activas,
                    "inactivas": total_vacunas - activas,
                    "obligatorias_embarazo": obligatorias,
                },
                "top_5_mas_aplicadas": top_vacunas,
            },
        )

    @action(detail=True, methods=["get"])
    def registros(self, request, pk=None):
        """Retorna todos los registros de aplicación de esta vacuna
        GET /api/vacunas/tipos-vacunas/{id}/registros/
        """
        tipo_vacuna = self.get_object()
        registros = RegistroVacuna.objects.filter(tipo_vacuna=tipo_vacuna)

        # Aplicar filtros opcionales
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")

        if fecha_desde:
            registros = registros.filter(fecha_aplicacion__gte=fecha_desde)
        if fecha_hasta:
            registros = registros.filter(fecha_aplicacion__lte=fecha_hasta)

        serializer = RegistroVacunaListSerializer(registros, many=True)
        return Response(
            {
                "tipo_vacuna": tipo_vacuna.nombre,
                "total_registros": registros.count(),
                "registros": serializer.data,
            },
        )


# =============================================================================
# REGISTRO VACUNA VIEWSET
# =============================================================================


class RegistroVacunaViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gestionar registros de vacunación

    ENDPOINTS:
        pass
    - list: Lista todos los registros de vacunación
    - create: Crear nuevo registro de vacunación
    - retrieve: Obtener detalle de registro
    - update/partial_update: Actualizar registro
    - destroy: Eliminar registro

    ACCIONES PERSONALIZADAS:
        pass
    - por_paciente: Registros de un paciente específico
    - por_embarazo: Registros de un embarazo específico
    - proximas_dosis: Pacientes con próximas dosis pendientes
    - esquemas_incompletos: Pacientes con esquemas incompletos
    - reacciones_adversas: Registros con reacciones adversas
    - estadisticas: Estadísticas de vacunación
    """

    queryset = RegistroVacuna.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, BusquedaClinicaFilter, OrderingFilter]

    # Campos de filtrado
    filterset_fields = {
        "paciente": ["exact"],
        "embarazo": ["exact"],
        "tipo_vacuna": ["exact"],
        "fecha_aplicacion": ["gte", "lte", "date"],
        "numero_dosis": ["exact"],
        "via_administracion": ["exact"],
        "activo": ["exact"],
        "proxima_dosis_fecha": ["gte", "lte", "isnull"],
    }

    # Campos de búsqueda
    # Búsqueda por paciente vía BusquedaClinicaFilter: los datos
    # identificatorios de Paciente están cifrados y el SearchFilter de DRF
    # (icontains en SQL) no encontraba NUNCA nada. Ver core/filtros.py.
    busqueda_ruta_paciente = "paciente"
    busqueda_campos_claros = [
        "tipo_vacuna__nombre",
        "lote",
        "laboratorio",
    ]

    # Campos de ordenamiento
    ordering_fields = [
        "fecha_aplicacion",
        "numero_dosis",
        "proxima_dosis_fecha",
    ]
    ordering = ["-fecha_aplicacion"]

    def get_queryset(self):
        """Optimiza queries con select_related y prefetch_related"""
        queryset = super().get_queryset()
        return queryset.select_related(
            "paciente", "embarazo", "tipo_vacuna", "aplicado_por",
        )

    def get_serializer_class(self):
        """Usa serializer apropiado según la acción"""
        if self.action == "list":
            return RegistroVacunaListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return RegistroVacunaCreateUpdateSerializer
        return RegistroVacunaSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar aplicado_por y created_by al crear"""
        serializer.save(aplicado_por=self.request.user, created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar updated_by al actualizar"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def por_paciente(self, request):
        """Retorna todos los registros de vacunación de un paciente
        GET /api/vacunas/registros/por_paciente/paciente_id={id}
        """
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response(
                {"error": "El parámetro paciente_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from pacientes.models import Paciente  # Deferred

        paciente = get_object_or_404(Paciente, pk=paciente_id)
        assert self.queryset is not None
        registros = self.queryset.filter(paciente=paciente)

        serializer = RegistroVacunaSerializer(registros, many=True)
        return Response(
            {
                "paciente": {
                    "id": getattr(paciente, 'id', None),
                    "nombre_completo": paciente.nombre_completo,
                    "id_clinico": paciente.id_clinico,
                },
                "total_registros": registros.count(),
                "registros": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def por_embarazo(self, request):
        """Retorna todos los registros de vacunación de un embarazo
        GET /api/vacunas/registros/por_embarazo/embarazo_id={id}
        """
        embarazo_id = request.query_params.get("embarazo_id")
        if not embarazo_id:
            return Response(
                {"error": "El parámetro embarazo_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from embarazos.models import Embarazo  # Deferred

        embarazo = get_object_or_404(Embarazo, pk=embarazo_id)
        assert self.queryset is not None
        registros = self.queryset.filter(embarazo=embarazo)

        serializer = RegistroVacunaSerializer(registros, many=True)
        return Response(
            {
                "embarazo": {
                    "id": embarazo.id,
                    "numero_gesta": embarazo.numero_gesta,
                    "paciente": embarazo.paciente.nombre_completo,
                },
                "total_registros": registros.count(),
                "registros": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def proximas_dosis(self, request):
        """Retorna registros con próximas dosis programadas
        GET /api/vacunas/registros/proximas_dosis/dias={dias}
        """
        dias = int(request.query_params.get("dias", 30))
        fecha_limite = timezone.now().date() + timedelta(days=dias)

        assert self.queryset is not None
        registros = self.queryset.filter(
            proxima_dosis_fecha__isnull=False,
            proxima_dosis_fecha__lte=fecha_limite,
            activo=True,
        ).order_by("proxima_dosis_fecha")

        serializer = RegistroVacunaSerializer(registros, many=True)
        return Response(
            {
                "dias_adelante": dias,
                "fecha_limite": fecha_limite.isoformat(),
                "total_proximas_dosis": registros.count(),
                "registros": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def esquemas_incompletos(self, _request):
        """Retorna pacientes con esquemas de vacunación incompletos
        GET /api/vacunas/registros/esquemas_incompletos/
        """
        # Obtener todos los registros activos
        assert self.queryset is not None
        registros = self.queryset.filter(activo=True)

        # Filtrar solo los que no han completado el esquema
        incompletos = [r for r in registros if not r.esquema_completo]

        serializer = RegistroVacunaSerializer(incompletos, many=True)
        return Response(
            {
                "total_esquemas_incompletos": len(incompletos),
                "registros": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def reacciones_adversas(self, _request):
        """Retorna registros con reacciones adversas reportadas
        GET /api/vacunas/registros/reacciones_adversas/
        """
        assert self.queryset is not None
        registros = self.queryset.filter(reacciones_adversas__isnull=False).exclude(
            reacciones_adversas="",
        )

        serializer = RegistroVacunaSerializer(registros, many=True)
        return Response(
            {"total_con_reacciones": registros.count(), "registros": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, _request):
        """Estadísticas generales de vacunación
        GET /api/vacunas/registros/estadisticas/
        """
        assert self.queryset is not None
        total_registros = self.queryset.count()
        activos = self.queryset.filter(activo=True).count()

        # Esquemas completos vs incompletos
        registros_activos = self.queryset.filter(activo=True)
        completos = sum(1 for r in registros_activos if r.esquema_completo)
        incompletos = activos - completos

        # Por vía de administración
        por_via = (
            self.queryset.values("via_administracion")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # Con reacciones adversas
        con_reacciones = (
            self.queryset.filter(reacciones_adversas__isnull=False)
            .exclude(reacciones_adversas="")
            .count()
        )

        # Próximas dosis en los próximos 30 días
        fecha_limite = timezone.now().date() + timedelta(days=30)
        proximas_30_dias = self.queryset.filter(
            proxima_dosis_fecha__isnull=False,
            proxima_dosis_fecha__lte=fecha_limite,
            activo=True,
        ).count()

        # Vacunas más aplicadas
        vacunas_mas_aplicadas = (
            self.queryset.values("tipo_vacuna__nombre")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        return Response(
            {
                "resumen": {
                    "total_registros": total_registros,
                    "activos": activos,
                    "esquemas_completos": completos,
                    "esquemas_incompletos": incompletos,
                    "con_reacciones_adversas": con_reacciones,
                    "proximas_dosis_30_dias": proximas_30_dias,
                },
                "por_via_administracion": list(por_via),
                "vacunas_mas_aplicadas": list(vacunas_mas_aplicadas),
            },
        )

    @action(detail=True, methods=["post"])
    def marcar_reaccion_adversa(self, request, pk=None):
        """Marca una reacción adversa en un registro
        POST /api/vacunas/registros/{id}/marcar_reaccion_adversa/
        Body: {"reaccion": "descripción de la reacción"}
        """
        registro = self.get_object()
        reaccion = request.data.get("reaccion")

        if not reaccion:
            return Response(
                {"error": "La descripción de la reacción es requerida"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registro.reacciones_adversas = reaccion
        registro.save()

        serializer = RegistroVacunaSerializer(registro)
        return Response(
            {
                "message": "Reacción adversa registrada exitosamente",
                "registro": serializer.data,
            },
        )

    @action(detail=True, methods=["post"])
    def programar_siguiente_dosis(self, request, pk=None):
        """Programa la fecha de siguiente dosis
        POST /api/vacunas/registros/{id}/programar_siguiente_dosis/
        Body: {"fecha": "YYYY-MM-DD"}
        """
        registro = self.get_object()

        if registro.esquema_completo:
            return Response(
                {"error": "El esquema de vacunación ya está completo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fecha = request.data.get("fecha")
        if not fecha:
            # Calcular automáticamente
            fecha_calculada = registro.calcular_proxima_dosis_fecha()
            if not fecha_calculada:
                return Response(
                    {"error": "No se puede calcular la próxima dosis automáticamente"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            fecha = fecha_calculada

        registro.proxima_dosis_fecha = fecha
        registro.save()

        serializer = RegistroVacunaSerializer(registro)
        return Response(
            {
                "message": "Próxima dosis programada exitosamente",
                "registro": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="esquema_vacunacion")
    def esquema_vacunacion(self, request):
        from django.db.models import Count
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response({"error": "Se requiere paciente_id"}, status=status.HTTP_400_BAD_REQUEST)
        registros = self.get_queryset().filter(paciente_id=paciente_id, activo=True)
        serializer = RegistroVacunaSerializer(registros, many=True)
        total_dosis = registros.aggregate(total=Count("id"))["total"]
        completas = sum(1 for r in registros if r.esquema_completo)
        return Response({
            "paciente_id": int(paciente_id),
            "total_dosis_aplicadas": total_dosis,
            "esquema_completo": completas > 0,
            "registros": serializer.data,
        })

    @action(detail=False, methods=["get"], url_path="esquema-completo")
    def esquema_completo(self, request):
        paciente_id = request.query_params.get("paciente_id")
        if not paciente_id:
            return Response({"error": "Se requiere paciente_id"}, status=status.HTTP_400_BAD_REQUEST)
        registros = self.get_queryset().filter(paciente_id=paciente_id, activo=True)
        esquema_completo = all(r.esquema_completo if hasattr(r, "esquema_completo") else True for r in registros)
        serializer = RegistroVacunaSerializer(registros, many=True)
        return Response({
            "paciente_id": int(paciente_id),
            "esquema_completo": esquema_completo,
            "total_vacunas": registros.count(),
            "registros": serializer.data,
        })

    @action(detail=False, methods=["get"])
    def pendientes(self, _request):
        registros = self.get_queryset().filter(
            activo=True,
            proxima_dosis_fecha__isnull=False,
            proxima_dosis_fecha__gte=timezone.localdate(),
        ).order_by("proxima_dosis_fecha")
        serializer = RegistroVacunaListSerializer(registros, many=True) if hasattr(self, 'RegistroVacunaListSerializer') else RegistroVacunaSerializer(registros, many=True)
        return Response({"total": registros.count(), "registros": serializer.data})

    @action(detail=False, methods=["get"])
    def proximas(self, request):
        from datetime import timedelta
        dias = int(request.query_params.get("dias", 30))
        fecha_limite = timezone.localdate() + timedelta(days=dias)
        registros = self.get_queryset().filter(
            activo=True,
            proxima_dosis_fecha__isnull=False,
            proxima_dosis_fecha__lte=fecha_limite,
        ).order_by("proxima_dosis_fecha")
        serializer = RegistroVacunaSerializer(registros, many=True)
        return Response({
            "total": registros.count(),
            "dias": dias,
            "registros": serializer.data,
        })
