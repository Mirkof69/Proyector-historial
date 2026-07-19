"""Views module."""
import contextlib
from datetime import datetime, timedelta

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.filtros import BusquedaClinicaFilter
from core.permissions import FetalMedicalPermission

from .models import Cita, Disponibilidad, HistorialCita
from .serializers import (
    CitaCreateUpdateSerializer,
    CitaDetailSerializer,
    CitaListSerializer,
    DisponibilidadSerializer,
)


class DisponibilidadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de Disponibilidades

    Endpoints:
        pass
    - GET /api/citas/disponibilidades/ - Listar todas
    - POST /api/citas/disponibilidades/ - Crear disponibilidad
    - GET /api/citas/disponibilidades/{id}/ - Ver detalle
    - PUT/PATCH /api/citas/disponibilidades/{id}/ - Actualizar
    - DELETE /api/citas/disponibilidades/{id}/ - Eliminar
    - GET /api/citas/disponibilidades/por-medico/medico_id=X
    - GET /api/citas/disponibilidades/activas/
    """

    queryset = (
        Disponibilidad.objects.select_related("medico")
        .all()
        .order_by("dia_semana", "hora_inicio")
    )
    serializer_class = DisponibilidadSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["medico", "dia_semana", "activo"]
    search_fields = ["medico__nombre", "medico__apellido_paterno"]
    ordering_fields = ["dia_semana", "hora_inicio"]

    @action(detail=False, methods=["get"], url_path="por-medico")
    def por_medico(self, request):
        """Obtener disponibilidades de un médico específico

        Parámetros query:
            pass
        - medico_id: ID del médico (requerido)
        - solo_activas: true/false (opcional)
        """
        medico_id = request.query_params.get("medico_id", None)
        solo_activas = request.query_params.get("solo_activas", "true") == "true"

        if not medico_id:
            return Response(
                {"error": "Debe proporcionar medico_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assert self.queryset is not None
        disponibilidades = self.queryset.filter(medico_id=medico_id)

        if solo_activas:
            disponibilidades = disponibilidades.filter(activo=True)

        serializer = self.get_serializer(disponibilidades, many=True)

        return Response(
            {"total": disponibilidades.count(), "disponibilidades": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def activas(self, _request):
        """Listar solo disponibilidades activas"""
        assert self.queryset is not None
        disponibilidades = self.queryset.filter(activo=True)

        page = self.paginate_queryset(disponibilidades)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(disponibilidades, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="horarios-disponibles")
    def horarios_disponibles(self, request):
        """Obtener horarios disponibles para un médico en una fecha específica

        Parámetros query:
            pass
        - medico_id: ID del médico (requerido)
        - fecha: fecha en formato YYYY-MM-DD (requerido)
        """
        medico_id = request.query_params.get("medico_id", None)
        fecha_str = request.query_params.get("fecha", None)

        if not medico_id or not fecha_str:
            return Response(
                {"error": "Debe proporcionar medico_id y fecha"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # No permitir fechas pasadas
        if fecha < timezone.localdate():
            return Response(
                {"error": "No se pueden consultar fechas pasadas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dia_semana = fecha.weekday()

        # Buscar disponibilidad del médico para ese día
        disponibilidad = Disponibilidad.objects.filter(
            medico_id=medico_id, dia_semana=dia_semana, activo=True,
        ).first()

        if not disponibilidad:
            return Response(
                {
                    "fecha": fecha,
                    "dia_semana": fecha.strftime("%A"),
                    "tiene_disponibilidad": False,
                    "horarios": [],
                },
            )

        # Verificar vigencia
        if (
            disponibilidad.fecha_inicio_vigencia
            and fecha < disponibilidad.fecha_inicio_vigencia
        ):
            return Response(
                {
                    "fecha": fecha,
                    "dia_semana": fecha.strftime("%A"),
                    "tiene_disponibilidad": False,
                    "mensaje": "Fecha fuera de vigencia",
                    "horarios": [],
                },
            )

        if (
            disponibilidad.fecha_fin_vigencia
            and fecha > disponibilidad.fecha_fin_vigencia
        ):
            return Response(
                {
                    "fecha": fecha,
                    "dia_semana": fecha.strftime("%A"),
                    "tiene_disponibilidad": False,
                    "mensaje": "Fecha fuera de vigencia",
                    "horarios": [],
                },
            )

        # Obtener citas ya agendadas para ese día
        citas_agendadas = Cita.objects.filter(
            medico_id=medico_id, fecha_cita=fecha, estado__in=["agendada", "confirmada"],
        ).values_list(
            "hora_cita", "id", "paciente__nombre", "paciente__apellido_paterno",
        )

        # Crear diccionario de citas
        citas_dict = {
            hora: {"cita_id": cita_id, "paciente_nombre": f"{nombre} {apellido}"}
            for hora, cita_id, nombre, apellido in citas_agendadas
        }

        # Generar horarios disponibles
        horarios = []
        for hora in disponibilidad.horas_disponibles:
            if hora in citas_dict:
                horarios.append(
                    {
                        "hora": hora,
                        "disponible": False,
                        "cita_id": citas_dict[hora]["cita_id"],
                        "paciente_nombre": citas_dict[hora]["paciente_nombre"],
                    },
                )
            else:
                horarios.append(
                    {
                        "hora": hora,
                        "disponible": True,
                        "cita_id": None,
                        "paciente_nombre": None,
                    },
                )

        return Response(
            {
                "fecha": fecha,
                "dia_semana": fecha.strftime("%A"),
                "tiene_disponibilidad": True,
                "horarios": horarios,
                "total_horarios": len(horarios),
                "disponibles": len([h for h in horarios if h["disponible"]]),
                "ocupados": len([h for h in horarios if not h["disponible"]]),
            },
        )


class CitaViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gestión de Citas

    Endpoints:
        pass
    - GET /api/citas/citas/ - Listar todas
    - POST /api/citas/citas/ - Crear cita
    - GET /api/citas/citas/{id}/ - Ver detalle
    - PUT/PATCH /api/citas/citas/{id}/ - Actualizar
    - DELETE /api/citas/citas/{id}/ - Eliminar
    - GET /api/citas/citas/por-paciente/paciente_id=X
    - GET /api/citas/citas/por-medico/medico_id=X
    - GET /api/citas/citas/pendientes/
    - GET /api/citas/citas/hoy/
    - GET /api/citas/citas/proximas/dias=7
    - GET /api/citas/citas/agenda-medico/medico_id=X&fecha=YYYY-MM-DD
    - GET /api/citas/citas/estadisticas/
    - POST /api/citas/citas/{id}/confirmar/
    - POST /api/citas/citas/{id}/cancelar/
    - POST /api/citas/citas/{id}/completar/
    - POST /api/citas/citas/{id}/no-asistio/
    """

    queryset = (
        Cita.objects.select_related(
            "paciente", "medico", "confirmada_por", "creado_por",
        )
        .prefetch_related("historial")
        .all()
        .order_by("-fecha_cita", "-hora_cita")
    )

    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        BusquedaClinicaFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["paciente", "medico", "estado", "tipo_cita", "fecha_cita"]
    # Búsqueda por paciente vía BusquedaClinicaFilter: los datos
    # identificatorios de Paciente están cifrados y el SearchFilter de DRF
    # (icontains en SQL) no encontraba NUNCA nada. Ver core/filtros.py.
    busqueda_ruta_paciente = "paciente"
    busqueda_campos_claros = [
        "medico__nombre",
        "medico__apellido_paterno",
    ]
    ordering_fields = ["fecha_cita", "hora_cita", "estado"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return CitaListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return CitaCreateUpdateSerializer
        return CitaDetailSerializer

    def perform_create(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar created_by al crear"""
        serializer.save(creado_por=self.request.user, created_by=self.request.user)

    def perform_update(self, serializer):
        """✅ TRAZABILIDAD: Auto-asignar modificado_por y updated_by al actualizar"""
        serializer.save(modificado_por=self.request.user, updated_by=self.request.user)

    def get_queryset(self):
        """Get queryset"""
        queryset = super().get_queryset()

        # Filtrar por rango de fechas
        fecha_desde = self.request.query_params.get("fecha_desde", None)
        fecha_hasta = self.request.query_params.get("fecha_hasta", None)

        if fecha_desde:
            with contextlib.suppress(Exception):
                queryset = queryset.filter(fecha_cita__gte=fecha_desde)

        if fecha_hasta:
            with contextlib.suppress(Exception):
                queryset = queryset.filter(fecha_cita__lte=fecha_hasta)

        # Restricción por Rol: Médicos solo ven sus propias citas y agendas
        if getattr(self.request.user, 'is_authenticated', False) and not (
            getattr(self.request.user, 'is_superuser', False) or getattr(self.request.user, 'rol', '') == "administrador"
        ):
            # Si es médico, solo ve lo suyo
            if getattr(self.request.user, 'rol', '') == "medico":
                queryset = queryset.filter(medico=self.request.user)
            # Enfermeros ven todo (para poder agendar/gestionar para cualquier médico)
            # o si se requiere restricción, agregar aquí.

        return queryset

    def create(self, request, *args, **kwargs):
        """Crear nueva cita"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Retornar con serializer detallado
        assert serializer.instance is not None
        cita = Cita.objects.select_related("paciente", "medico", "creado_por").get(
            id=serializer.instance.id,
        )

        return_serializer = CitaDetailSerializer(cita)

        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data, status=status.HTTP_201_CREATED, headers=headers,
        )

    @action(detail=False, methods=["get"], url_path="por-paciente")
    def por_paciente(self, request):
        """Obtener todas las citas de un paciente

        Parámetros query:
            pass
        - paciente_id: ID del paciente (requerido)
        """
        paciente_id = request.query_params.get("paciente_id", None)

        if not paciente_id:
            return Response(
                {"error": "Debe proporcionar paciente_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assert self.queryset is not None
        citas = self.queryset.filter(paciente_id=paciente_id).order_by(
            "-fecha_cita", "-hora_cita",
        )

        page = self.paginate_queryset(citas)
        if page is not None:
            serializer = CitaDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CitaDetailSerializer(citas, many=True)
        return Response({"total": citas.count(), "citas": serializer.data})

    @action(detail=False, methods=["get"], url_path="por-medico")
    def por_medico(self, request):
        """Obtener todas las citas de un médico

        Parámetros query:
            pass
        - medico_id: ID del médico (requerido)
        - fecha: filtrar por fecha específica (opcional)
        """
        medico_id = request.query_params.get("medico_id", None)
        fecha_str = request.query_params.get("fecha", None)

        if not medico_id:
            return Response(
                {"error": "Debe proporcionar medico_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assert self.queryset is not None
        citas = self.queryset.filter(medico_id=medico_id)

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                citas = citas.filter(fecha_cita=fecha)
            except ValueError:
                pass

        citas = citas.order_by("-fecha_cita", "-hora_cita")

        page = self.paginate_queryset(citas)
        if page is not None:
            serializer = CitaListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CitaListSerializer(citas, many=True)
        return Response({"total": citas.count(), "citas": serializer.data})

    @action(detail=False, methods=["get"])
    def pendientes(self, _request):
        """Listar citas pendientes (agendadas o confirmadas)"""
        assert self.queryset is not None
        citas = self.queryset.filter(estado__in=["agendada", "confirmada"]).order_by(
            "fecha_cita", "hora_cita",
        )

        page = self.paginate_queryset(citas)
        if page is not None:
            serializer = CitaListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CitaListSerializer(citas, many=True)
        return Response({"total": citas.count(), "citas": serializer.data})

    @action(detail=False, methods=["get"])
    def hoy(self, _request):
        """Citas de hoy"""
        assert self.queryset is not None
        hoy = timezone.localdate()
        citas = self.queryset.filter(fecha_cita=hoy).order_by("hora_cita")

        serializer = CitaListSerializer(citas, many=True)
        return Response(
            {"fecha": hoy, "total": citas.count(), "citas": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def proximas(self, request):
        """Citas próximas

        Parámetros query:
            pass
        - dias: número de días hacia adelante (default: 7)
        """
        dias = int(request.query_params.get("dias", 7))
        hoy = timezone.localdate()
        fecha_limite = hoy + timedelta(days=dias)

        assert self.queryset is not None
        citas = self.queryset.filter(
            fecha_cita__gte=hoy,
            fecha_cita__lte=fecha_limite,
            estado__in=["agendada", "confirmada"],
        ).order_by("fecha_cita", "hora_cita")

        page = self.paginate_queryset(citas)
        if page is not None:
            serializer = CitaListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CitaListSerializer(citas, many=True)
        return Response(
            {
                "desde": hoy,
                "hasta": fecha_limite,
                "total": citas.count(),
                "citas": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="agenda-medico")
    def agenda_medico(self, request):
        """Ver agenda completa de un médico para una fecha

        Parámetros query:
            pass
        - medico_id: ID del médico (requerido)
        - fecha: fecha en formato YYYY-MM-DD (requerido)
        """
        medico_id = request.query_params.get("medico_id", None)
        fecha_str = request.query_params.get("fecha", None)

        if not medico_id or not fecha_str:
            return Response(
                {"error": "Debe proporcionar medico_id y fecha"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dia_semana = fecha.weekday()

        # Buscar disponibilidad
        disponibilidad = Disponibilidad.objects.filter(
            medico_id=medico_id, dia_semana=dia_semana, activo=True,
        ).first()

        if not disponibilidad:
            return Response(
                {
                    "fecha": fecha,
                    "dia_semana": fecha.strftime("%A"),
                    "tiene_disponibilidad": False,
                    "horarios": [],
                    "total_citas": 0,
                    "total_disponibles": 0,
                },
            )

        # Obtener citas del día
        citas = Cita.objects.filter(
            medico_id=medico_id, fecha_cita=fecha,
        ).select_related("paciente")

        # Crear diccionario de citas por hora
        citas_dict = {
            cita.hora_cita: {
                "cita_id": getattr(cita, 'id', None),
                "paciente_nombre": cita.paciente.nombre_completo,
                "estado": cita.estado,
                "tipo_cita": getattr(cita, 'get_tipo_cita_display')(),
                "motivo": cita.motivo,
            }
            for cita in citas
        }

        # Generar agenda completa
        horarios = []
        for hora in disponibilidad.horas_disponibles:
            if hora in citas_dict:
                horarios.append({"hora": hora, "disponible": False, **citas_dict[hora]})
            else:
                horarios.append(
                    {
                        "hora": hora,
                        "disponible": True,
                        "cita_id": None,
                        "paciente_nombre": None,
                    },
                )

        return Response(
            {
                "fecha": fecha,
                "dia_semana": fecha.strftime("%A"),
                "tiene_disponibilidad": True,
                "horarios": horarios,
                "total_citas": len([h for h in horarios if not h["disponible"]]),
                "total_disponibles": len([h for h in horarios if h["disponible"]]),
            },
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, _request):
        """Estadísticas generales de citas"""
        total = Cita.objects.count()

        # Por estado
        por_estado = {}
        for estado_codigo, estado_nombre in Cita.ESTADO_CHOICES:
            count = Cita.objects.filter(estado=estado_codigo).count()
            por_estado[estado_nombre] = count

        # Por tipo
        por_tipo = {}
        for tipo_codigo, tipo_nombre in Cita.TIPO_CITA_CHOICES:
            count = Cita.objects.filter(tipo_cita=tipo_codigo).count()
            por_tipo[tipo_nombre] = count

        # Estadísticas temporales
        hoy = timezone.localdate()
        esta_semana = Cita.objects.filter(
            fecha_cita__gte=hoy, fecha_cita__lte=hoy + timedelta(days=7),
        ).count()

        este_mes = Cita.objects.filter(
            fecha_cita__year=hoy.year, fecha_cita__month=hoy.month,
        ).count()

        # Tasa de asistencia
        total_completadas = Cita.objects.filter(estado="completada").count()
        total_no_asistio = Cita.objects.filter(estado="no_asistio").count()
        total_finalizadas = total_completadas + total_no_asistio

        if total_finalizadas > 0:
            tasa_asistencia = round((total_completadas / total_finalizadas) * 100, 2)
        else:
            tasa_asistencia = 0

        return Response(
            {
                "total_citas": total,
                "citas_esta_semana": esta_semana,
                "citas_este_mes": este_mes,
                "por_estado": por_estado,
                "por_tipo": por_tipo,
                "tasa_asistencia": tasa_asistencia,
                "total_completadas": total_completadas,
                "total_no_asistio": total_no_asistio,
            },
        )

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """Confirmar una cita"""
        cita = self.get_object()

        if cita.estado not in ["agendada"]:
            return Response(
                {
                    "error": f"No se puede confirmar una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cita.confirmar(usuario=request.user)

        serializer = CitaDetailSerializer(cita)
        return Response(
            {"mensaje": "Cita confirmada exitosamente", "cita": serializer.data},
        )

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """Cancelar una cita"""
        cita = self.get_object()
        motivo = request.data.get("motivo", "")

        if cita.estado in ["completada", "cancelada"]:
            return Response(
                {
                    "error": f"No se puede cancelar una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        estado_anterior = cita.estado
        cita.cancelar()

        # Registrar en historial
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior=estado_anterior,
            estado_nuevo="cancelada",
            motivo_cambio=motivo or "Cita cancelada",
            usuario=request.user,
        )

        serializer = CitaDetailSerializer(cita)
        return Response(
            {"mensaje": "Cita cancelada exitosamente", "cita": serializer.data},
        )

    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        """Marcar cita como completada"""
        cita = self.get_object()

        if cita.estado not in ["agendada", "confirmada"]:
            return Response(
                {
                    "error": f"No se puede completar una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        estado_anterior = cita.estado
        cita.completar()

        # Registrar en historial
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior=estado_anterior,
            estado_nuevo="completada",
            motivo_cambio="Cita completada",
            usuario=request.user,
        )

        serializer = CitaDetailSerializer(cita)
        return Response(
            {"mensaje": "Cita completada exitosamente", "cita": serializer.data},
        )

    @action(detail=True, methods=["post"], url_path="no-asistio")
    def no_asistio(self, request, pk=None):
        """Marcar que el paciente no asistió"""
        cita = self.get_object()

        if cita.estado not in ["agendada", "confirmada"]:
            return Response(
                {
                    "error": f"No se puede marcar como no asistió una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        estado_anterior = cita.estado
        cita.marcar_no_asistio()

        # Registrar en historial
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior=estado_anterior,
            estado_nuevo="no_asistio",
            motivo_cambio="Paciente no asistió",
            usuario=request.user,
        )

        serializer = CitaDetailSerializer(cita)
        return Response({"mensaje": "Marcado como no asistió", "cita": serializer.data})

    @action(detail=True, methods=["post"], url_path="marcar-presente")
    def marcar_presente(self, request, pk=None):
        """Registra llegada del paciente → estado en_espera"""
        cita = self.get_object()
        if cita.estado not in ["agendada", "confirmada"]:
            return Response(
                {
                    "error": f"No se puede marcar como presente una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        estado_anterior = cita.estado
        cita.estado = "en_espera"
        cita.save(update_fields=["estado"])
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior=estado_anterior,
            estado_nuevo="en_espera",
            motivo_cambio="Paciente presente en sala de espera",
            usuario=request.user,
        )
        return Response(
            {
                "mensaje": "Paciente marcado como presente",
                "cita": CitaDetailSerializer(cita).data,
            },
        )

    @action(detail=True, methods=["post"], url_path="pasar-consulta")
    def pasar_consulta(self, request, pk=None):
        """Pasa el paciente al consultorio → estado en_consulta"""
        cita = self.get_object()
        if cita.estado not in ["en_espera", "agendada", "confirmada"]:
            return Response(
                {
                    "error": f"No se puede pasar a consulta una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        estado_anterior = cita.estado
        cita.estado = "en_consulta"
        cita.save(update_fields=["estado"])
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior=estado_anterior,
            estado_nuevo="en_consulta",
            motivo_cambio="Paciente en consulta",
            usuario=request.user,
        )
        return Response(
            {
                "mensaje": "Paciente pasado a consulta",
                "cita": CitaDetailSerializer(cita).data,
            },
        )

    @action(detail=True, methods=["post"], url_path="enviar-recordatorio")
    def enviar_recordatorio(self, _request, pk=None):
        """Marca el recordatorio como enviado"""
        cita = self.get_object()
        if cita.estado in ["completada", "cancelada", "no_asistio"]:
            return Response(
                {
                    "error": f"No se puede enviar recordatorio para cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.utils import timezone as tz

        cita.recordatorio_enviado = True
        cita.fecha_recordatorio = tz.now()
        cita.save(update_fields=["recordatorio_enviado", "fecha_recordatorio"])
        return Response(
            {
                "success": True,
                "message": f"Recordatorio registrado para cita #{cita.id}",
                "cita": CitaDetailSerializer(cita).data,
            },
        )

    @action(detail=True, methods=["post"])
    def reprogramar(self, request, pk=None):
        """Cambia la fecha y hora de una cita → vuelve a estado agendada"""
        cita = self.get_object()
        if cita.estado in ["completada", "cancelada", "no_asistio"]:
            return Response(
                {
                    "error": f"No se puede reprogramar una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        nueva_fecha = request.data.get("fecha_cita")
        nueva_hora = request.data.get("hora_cita")
        if not nueva_fecha or not nueva_hora:
            return Response(
                {"error": "Debe proporcionar fecha_cita y hora_cita"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        estado_anterior = cita.estado
        motivo = f"Reprogramada de {cita.fecha_cita} {cita.hora_cita} a {nueva_fecha} {nueva_hora}"
        cita.fecha_cita = nueva_fecha
        cita.hora_cita = nueva_hora
        cita.estado = "agendada"
        cita.save(update_fields=["fecha_cita", "hora_cita", "estado"])
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior=estado_anterior,
            estado_nuevo="agendada",
            motivo_cambio=motivo,
            usuario=request.user,
        )
        return Response(
            {
                "mensaje": "Cita reprogramada exitosamente",
                "cita": CitaDetailSerializer(cita).data,
            },
        )
