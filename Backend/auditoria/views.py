"""=============================================================================
VIEWS: API DE AUDITORÍA
=============================================================================
ViewSets y endpoints para consultar registros de auditoría en tiempo real.
=============================================================================
"""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import PuedeVerAuditoria

from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaListSerializer, RegistroAuditoriaSerializer


class RegistroAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet SOLO LECTURA para consultar registros de auditoría.
    Los registros se crean automáticamente mediante signals o el método registrar().
    Acceso restringido: solo médicos y administradores.
    """

    queryset = RegistroAuditoria.objects.select_related("usuario").all()
    permission_classes = [PuedeVerAuditoria]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["modulo", "accion", "usuario", "registro_id"]
    search_fields = ["modulo", "usuario__email", "usuario__nombre", "usuario_nombre"]
    ordering = ["-fecha"]
    ordering_fields = ["fecha", "modulo", "accion"]

    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == "list":
            return RegistroAuditoriaListSerializer
        return RegistroAuditoriaSerializer

    def get_queryset(self):
        """Filtrado avanzado por parámetros query"""
        queryset = super().get_queryset()

        # Filtrar por rango de fechas
        fecha_inicio = self.request.query_params.get("fecha_inicio")
        fecha_fin = self.request.query_params.get("fecha_fin")

        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)

        # Filtrar por usuario_id
        usuario_id = self.request.query_params.get("usuario_id")
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        return queryset

    @action(detail=False, methods=["get"], url_path="estadisticas-modulos")
    def estadisticas_modulos(self, _request):
        """Retorna estadísticas agrupadas por módulo.

        GET /api/auditoria/estadisticas-modulos/
        """
        stats = (
            RegistroAuditoria.objects.values("modulo")
            .annotate(
                total=Count("id"),
                creates=Count("id", filter=Q(accion="crear")),
                updates=Count("id", filter=Q(accion="actualizar")),
                deletes=Count("id", filter=Q(accion="eliminar")),
            )
            .order_by("-total")
        )

        return Response(stats)

    @action(detail=False, methods=["get"], url_path="estadisticas-generales")
    def estadisticas_generales(self, _request):
        """Retorna estadísticas generales del sistema.

        GET /api/auditoria/estadisticas-generales/
        """
        total_registros = RegistroAuditoria.objects.count()

        # Últimas 24 horas
        hace_24h = timezone.now() - timedelta(hours=24)
        ultimas_24h = RegistroAuditoria.objects.filter(fecha__gte=hace_24h).count()

        # Usuarios activos (que han hecho cambios)
        usuarios_activos = (
            RegistroAuditoria.objects.values("usuario").distinct().count()
        )

        # Módulos activos (con registros)
        modulos_activos = RegistroAuditoria.objects.values("modulo").distinct().count()

        return Response(
            {
                "total_registros": total_registros,
                "ultimas_24h": ultimas_24h,
                "usuarios_activos": usuarios_activos,
                "modulos_activos": modulos_activos,
            },
        )

    @action(detail=False, methods=["get"], url_path=r"modulo/(?P<modulo>[^/.]+)")
    def por_modulo(self, _request, modulo=None):
        """Retorna registros de un módulo específico.

        GET /api/auditoria/modulo/{modulo}/
        """
        queryset = self.get_queryset().filter(modulo=modulo)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"usuario/(?P<usuario_id>[^/.]+)")
    def por_usuario(self, _request, usuario_id=None):
        """Retorna registros de un usuario específico.

        GET /api/auditoria/usuario/{usuario_id}/
        """
        queryset = self.get_queryset().filter(usuario_id=usuario_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<modulo>[^/.]+)/(?P<registro_id>[^/.]+)/historial",
    )
    def historial_registro(self, _request, modulo=None, registro_id=None):
        """Retorna el historial completo de cambios de un registro específico.

        GET /api/auditoria/{modulo}/{registro_id}/historial/
        """
        queryset = (
            self.get_queryset()
            .filter(modulo=modulo, registro_id=registro_id)
            .order_by("fecha")
        )

        serializer = RegistroAuditoriaSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<modulo>[^/.]+)/(?P<registro_id>[^/.]+)/timeline",
    )
    def timeline_registro(self, _request, modulo=None, registro_id=None):
        """Retorna una línea de tiempo de cambios para un registro.

        GET /api/auditoria/{modulo}/{registro_id}/timeline/
        """
        queryset = (
            self.get_queryset()
            .filter(modulo=modulo, registro_id=registro_id)
            .order_by("-fecha")
        )

        serializer = RegistroAuditoriaSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<modulo>[^/.]+)/(?P<registro_id>[^/.]+)/trazabilidad",
    )
    def trazabilidad_display(self, _request, modulo=None, registro_id=None):
        """Retorna información de created_by y updated_by para un registro.

        GET /api/auditoria/{modulo}/{registro_id}/trazabilidad/
        """
        # Buscar el primer registro (creación)
        creacion = (
            self.get_queryset()
            .filter(modulo=modulo, registro_id=registro_id, accion="crear")
            .first()
        )

        # Buscar el último registro (última actualización)
        actualizacion = (
            self.get_queryset()
            .filter(modulo=modulo, registro_id=registro_id, accion="actualizar")
            .order_by("-fecha")
            .first()
        )

        created_by = None
        if creacion and creacion.usuario:
            created_by = {
                "id": creacion.usuario.id,
                "email": creacion.usuario.email,  # Usuario usa email como USERNAME_FIELD
                "nombre_completo": creacion.usuario_nombre_completo,
                "fecha": creacion.fecha.isoformat(),
            }

        updated_by = None
        if actualizacion and actualizacion.usuario:
            updated_by = {
                "id": actualizacion.usuario.id,
                "email": actualizacion.usuario.email,  # Usuario usa email como USERNAME_FIELD
                "nombre_completo": actualizacion.usuario_nombre_completo,
                "fecha": actualizacion.fecha.isoformat(),
            }

        return Response({"created_by": created_by, "updated_by": updated_by})

    @extend_schema(
        parameters=[
            OpenApiParameter("audit_id1", type=int, location=OpenApiParameter.PATH),
            OpenApiParameter("audit_id2", type=int, location=OpenApiParameter.PATH),
        ]
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"comparar/(?P<audit_id1>[^/.]+)/(?P<audit_id2>[^/.]+)",
    )
    @extend_schema(
        parameters=[
            OpenApiParameter("audit_id1", type=int, location=OpenApiParameter.PATH),
            OpenApiParameter("audit_id2", type=int, location=OpenApiParameter.PATH),
        ]
    )
    def comparar_versiones(self, _request, audit_id1=None, audit_id2=None):
        """Compara dos versiones de un registro (dos entradas de auditoría).

        GET /api/auditoria/comparar/{audit_id1}/{audit_id2}/
        """
        try:
            registro1 = RegistroAuditoria.objects.get(pk=audit_id1)
            registro2 = RegistroAuditoria.objects.get(pk=audit_id2)

            # Determinar cuál es el más antiguo
            if registro1.fecha > registro2.fecha:
                registro1, registro2 = registro2, registro1

            cambios = []
            diferencias = []

            if registro1.datos_nuevos and registro2.datos_nuevos:
                for key in registro2.datos_nuevos:
                    valor_anterior = registro1.datos_nuevos.get(key)
                    valor_nuevo = registro2.datos_nuevos.get(key)

                    if valor_anterior != valor_nuevo:
                        cambios.append(
                            {
                                "campo": key,
                                "valor_anterior": valor_anterior,
                                "valor_nuevo": valor_nuevo,
                            },
                        )
                        diferencias.append(f"{key}: {valor_anterior} → {valor_nuevo}")

            return Response({"cambios": cambios, "diferencias": diferencias})

        except RegistroAuditoria.DoesNotExist:
            return Response(
                {"error": "Uno o ambos registros no existen"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["get"], url_path="cambios-detallados")
    def cambios_detallados(self, _request, _pk=None):
        """Retorna los cambios de un registro de auditoría en formato detallado
        para visualización con DiffViewer.

        GET /api/auditoria/{id}/cambios-detallados/
        """
        registro = self.get_object()

        if registro.accion == "crear":
            # Para creaciones, mostrar solo datos nuevos
            cambios = []
            if registro.datos_nuevos:
                for campo, valor in registro.datos_nuevos.items():
                    cambios.append(
                        {
                            "campo": campo,
                            "tipo": "creado",
                            "valor_anterior": None,
                            "valor_nuevo": valor,
                            "cambio_tipo": "add",
                        },
                    )

            return Response(
                {"accion": "crear", "cambios": cambios, "total_cambios": len(cambios)},
            )

        if registro.accion == "eliminar":
            # Para eliminaciones, mostrar solo datos anteriores
            cambios = []
            if registro.datos_anteriores:
                for campo, valor in registro.datos_anteriores.items():
                    cambios.append(
                        {
                            "campo": campo,
                            "tipo": "eliminado",
                            "valor_anterior": valor,
                            "valor_nuevo": None,
                            "cambio_tipo": "remove",
                        },
                    )

            return Response(
                {
                    "accion": "eliminar",
                    "cambios": cambios,
                    "total_cambios": len(cambios),
                },
            )

        if registro.accion == "actualizar":
            # Para actualizaciones, comparar antes y después
            cambios = []

            if registro.datos_anteriores and registro.datos_nuevos:
                # Todos los campos que existen en datos nuevos
                todos_campos = set(registro.datos_anteriores.keys()) | set(
                    registro.datos_nuevos.keys(),
                )

                for campo in sorted(todos_campos):
                    valor_anterior = registro.datos_anteriores.get(campo)
                    valor_nuevo = registro.datos_nuevos.get(campo)

                    if valor_anterior != valor_nuevo:
                        cambios.append(
                            {
                                "campo": campo,
                                "tipo": "modificado",
                                "valor_anterior": valor_anterior,
                                "valor_nuevo": valor_nuevo,
                                "cambio_tipo": "modify",
                            },
                        )

            return Response(
                {
                    "accion": "actualizar",
                    "cambios": cambios,
                    "total_cambios": len(cambios),
                },
            )

        return Response({"accion": registro.accion, "cambios": [], "total_cambios": 0})
