"""=============================================================================
MÓDULO: NOTIFICACIONES - VIEWS
=============================================================================
ViewSets y endpoints para el sistema de notificaciones
=============================================================================
"""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from core.permissions import FetalMedicalPermission
from rest_framework.response import Response

from .models import ConfiguracionNotificaciones, HistorialNotificaciones, Notificacion
from .serializers import (
    ConfiguracionNotificacionesSerializer,
    EstadisticasNotificacionesSerializer,
    HistorialNotificacionesSerializer,
    NotificacionCreateSerializer,
    NotificacionListSerializer,
    NotificacionSerializer,
)


class NotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión completa de notificaciones

    Endpoints:
        pass
    - GET /notificaciones/ - Lista notificaciones del usuario
    - GET /notificaciones/{id}/ - Detalle de notificación
    - POST /notificaciones/ - Crear notificación
    - PATCH /notificaciones/{id}/ - Actualizar notificación
    - DELETE /notificaciones/{id}/ - Eliminar notificación
    - POST /notificaciones/marcar_leida/ - Marcar como leída
    - POST /notificaciones/marcar_todas_leidas/ - Marcar todas como leídas
    - POST /notificaciones/archivar/ - Archivar notificación
    - GET /notificaciones/no_leidas/ - Solo no leídas
    - GET /notificaciones/estadisticas/ - Estadísticas
    """

    permission_classes = [FetalMedicalPermission]
    filterset_fields = ["tipo", "prioridad", "leida", "archivada", "entidad_tipo"]
    search_fields = ["titulo", "mensaje"]
    ordering_fields = ["fecha_creacion", "prioridad", "leida"]
    ordering = ["-fecha_creacion"]

    def get_queryset(self):
        """Filtra las notificaciones del usuario autenticado
        """
        usuario = self.request.user

        # Administradores ven todas, usuarios normales solo las suyas
        if usuario.is_staff or usuario.rol == "administrador":
            queryset = Notificacion.objects.all()
        else:
            queryset = Notificacion.objects.filter(usuario=usuario)

        # Filtros adicionales por parámetros de query
        tipo = self.request.query_params.get("tipo", None)
        prioridad = self.request.query_params.get("prioridad", None)
        leida = self.request.query_params.get("leida", None)
        archivada = self.request.query_params.get("archivada", None)

        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        if leida is not None:
            leida_bool = leida.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(leida=leida_bool)
        if archivada is not None:
            archivada_bool = archivada.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(archivada=archivada_bool)

        return queryset.select_related("usuario")

    def get_serializer_class(self):
        """Selecciona el serializer según la acción"""
        if self.action == "list":
            return NotificacionListSerializer
        if self.action == "create":
            return NotificacionCreateSerializer
        return NotificacionSerializer

    @action(detail=False, methods=["GET"])
    def no_leidas(self, _request):
        """GET /notificaciones/no_leidas/

        Obtiene solo las notificaciones no leídas del usuario
        """
        notificaciones = self.get_queryset().filter(leida=False, archivada=False)
        serializer = NotificacionListSerializer(notificaciones, many=True)
        return Response({"count": notificaciones.count(), "results": serializer.data})

    @action(detail=True, methods=["POST"])
    def marcar_leida(self, request, _pk=None):
        """POST /notificaciones/{id}/marcar_leida/

        Marca una notificación como leída
        """
        notificacion = self.get_object()
        notificacion.marcar_como_leida()

        # Registrar en historial
        HistorialNotificaciones.objects.create(
            notificacion=notificacion,
            accion="leida",
            detalles={"usuario": request.user.nombre_completo},
        )

        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    def marcar_todas_leidas(self, _request):
        """POST /notificaciones/marcar_todas_leidas/

        Marca todas las notificaciones del usuario como leídas
        """
        notificaciones = self.get_queryset().filter(leida=False)
        count = notificaciones.count()

        # Marcar como leídas
        notificaciones.update(leida=True, fecha_leida=timezone.now())

        return Response(
            {
                "message": f"Se marcaron {count} notificaciones como leídas",
                "count": count,
            },
        )

    @action(detail=True, methods=["POST"])
    def archivar(self, request, _pk=None):
        """POST /notificaciones/{id}/archivar/

        Archiva una notificación
        """
        notificacion = self.get_object()
        notificacion.archivar()

        # Registrar en historial
        HistorialNotificaciones.objects.create(
            notificacion=notificacion,
            accion="archivada",
            detalles={"usuario": request.user.nombre_completo},
        )

        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)

    @action(detail=False, methods=["DELETE"])
    def limpiar_antiguas(self, _request):
        """DELETE /notificaciones/limpiar_antiguas/

        Elimina notificaciones leídas con más de 30 días
        """
        fecha_limite = timezone.now() - timedelta(days=30)
        notificaciones_antiguas = self.get_queryset().filter(
            leida=True, fecha_creacion__lt=fecha_limite,
        )
        count = notificaciones_antiguas.count()
        notificaciones_antiguas.delete()

        return Response(
            {
                "message": f"Se eliminaron {count} notificaciones antiguas",
                "count": count,
            },
        )

    @action(detail=False, methods=["GET"])
    def estadisticas(self, _request):
        """GET /notificaciones/estadisticas/

        Obtiene estadísticas de notificaciones del usuario
        """
        queryset = self.get_queryset()

        # Contar por estado
        total = queryset.count()
        no_leidas = queryset.filter(leida=False).count()
        leidas = queryset.filter(leida=True).count()
        archivadas = queryset.filter(archivada=True).count()

        # Contar por tipo
        por_tipo = {}
        tipos = queryset.values("tipo").annotate(count=Count("id"))
        for tipo in tipos:
            tipo_nombre = dict(Notificacion._meta.get_field("tipo").choices).get(
                tipo["tipo"],
            )
            por_tipo[tipo_nombre] = tipo["count"]

        # Contar por prioridad
        por_prioridad = {}
        prioridades = queryset.values("prioridad").annotate(count=Count("id"))
        for prioridad in prioridades:
            prioridad_nombre = dict(
                Notificacion._meta.get_field("prioridad").choices,
            ).get(prioridad["prioridad"])
            por_prioridad[prioridad_nombre] = prioridad["count"]

        # Contar recientes (últimas 24 horas)
        hace_24h = timezone.now() - timedelta(hours=24)
        recientes_24h = queryset.filter(fecha_creacion__gte=hace_24h).count()

        datos = {
            "total_notificaciones": total,
            "no_leidas": no_leidas,
            "leidas": leidas,
            "archivadas": archivadas,
            "por_tipo": por_tipo,
            "por_prioridad": por_prioridad,
            "recientes_24h": recientes_24h,
        }

        serializer = EstadisticasNotificacionesSerializer(data=datos)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=False, methods=["GET"])
    def urgentes(self, _request):
        """GET /notificaciones/urgentes/

        Obtiene notificaciones urgentes y críticas no leídas
        """
        notificaciones = self.get_queryset().filter(
            leida=False, prioridad__in=["urgente", "critica"],
        )

        serializer = NotificacionListSerializer(notificaciones, many=True)
        return Response({"count": notificaciones.count(), "results": serializer.data})


class ConfiguracionNotificacionesViewSet(viewsets.ModelViewSet):
    """ViewSet para configuración de notificaciones

    Endpoints:
    - GET /configuracion-notificaciones/ - Obtener configuración
    - PUT /configuracion-notificaciones/{id}/ - Actualizar configuración
    - GET /configuracion-notificaciones/mi_configuracion/ - Config del usuario actual
    """

    queryset = ConfiguracionNotificaciones.objects.all()
    serializer_class = ConfiguracionNotificacionesSerializer
    permission_classes = [FetalMedicalPermission]

    def get_queryset(self):
        """Filtra configuraciones según el usuario"""
        usuario = self.request.user

        if usuario.is_staff or usuario.rol == "administrador":
            return ConfiguracionNotificaciones.objects.all()
        return ConfiguracionNotificaciones.objects.filter(usuario=usuario)

    @action(detail=False, methods=["GET", "PUT", "PATCH"])
    def mi_configuracion(self, request):
        """GET/PUT/PATCH /configuracion-notificaciones/mi_configuracion/

        Obtiene o actualiza la configuración del usuario actual
        """
        usuario = request.user

        # Obtener o crear configuración
        config, _created = ConfiguracionNotificaciones.objects.get_or_create(
            usuario=usuario,
        )

        if request.method == "GET":
            serializer = self.get_serializer(config)
            return Response(serializer.data)

        if request.method in ["PUT", "PATCH"]:
            partial = request.method == "PATCH"
            serializer = self.get_serializer(config, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(
            {"error": "Método no permitido"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class HistorialNotificacionesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para historial de notificaciones (solo lectura)

    Endpoints:
    - GET /historial-notificaciones/ - Lista historial
    - GET /historial-notificaciones/{id}/ - Detalle de historial
    """

    queryset = HistorialNotificaciones.objects.all()
    serializer_class = HistorialNotificacionesSerializer
    permission_classes = [FetalMedicalPermission]
    filterset_fields = ["notificacion", "accion"]
    ordering = ["-fecha"]

    def get_queryset(self):
        """Filtra historial según el usuario"""
        usuario = self.request.user

        if usuario.is_staff or usuario.rol == "administrador":
            return HistorialNotificaciones.objects.all()
        return HistorialNotificaciones.objects.filter(notificacion__usuario=usuario)
