"""Views module."""
import contextlib
from datetime import datetime, timedelta

from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.filtros import BusquedaClinicaFilter
from core.permissions import FetalMedicalPermission
from core.exportacion import ExportarExcelMixin

from .models import Cita, Disponibilidad, HistorialCita
from .vencimiento import cerrar_citas_vencidas_hoy
from .serializers import (
    CitaCreateUpdateSerializer,
    CitaDetailSerializer,
    CitaListSerializer,
    DisponibilidadSerializer,
)


def bloques_del_dia(medico_id, fecha):
    """Bloques de atención del médico ese día y sus horas, ordenadas.

    Un médico puede atender mañana y tarde (dos Disponibilidad el mismo día).
    Con .first() solo contaba el primer bloque: los turnos de la tarde no se
    ofrecían en «Nueva cita» y sus citas no salían en la agenda diaria.
    Devuelve (bloques activos, bloques vigentes en esa fecha, horas vigentes).
    """
    bloques = list(Disponibilidad.objects.filter(
        medico_id=medico_id, dia_semana=fecha.weekday(), activo=True,
    ))
    vigentes = [
        b for b in bloques
        if not (b.fecha_inicio_vigencia and fecha < b.fecha_inicio_vigencia)
        and not (b.fecha_fin_vigencia and fecha > b.fecha_fin_vigencia)
    ]
    horas = sorted({hora for b in vigentes for hora in b.horas_disponibles})
    return bloques, vigentes, horas


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

        bloques, vigentes, horas_del_dia = bloques_del_dia(medico_id, fecha)

        if not vigentes:
            respuesta = {
                "fecha": fecha,
                "dia_semana": fecha.strftime("%A"),
                "tiene_disponibilidad": False,
                "horarios": [],
            }
            if bloques:
                respuesta["mensaje"] = "Fecha fuera de vigencia"
            return Response(respuesta)

        # Obtener citas ya agendadas para ese día
        # También las que están en espera o en consulta: la paciente ya ocupa el turno.
        citas_agendadas = Cita.objects.filter(
            medico_id=medico_id, fecha_cita=fecha, estado__in=Cita.OCUPAN_TURNO,
        ).values_list(
            "hora_cita", "id", "paciente__nombre", "paciente__apellido_paterno",
        )

        # Crear diccionario de citas
        citas_dict = {
            hora: {"cita_id": cita_id, "paciente_nombre": f"{nombre} {apellido}"}
            for hora, cita_id, nombre, apellido in citas_agendadas
        }

        # Generar horarios disponibles. Hoy, las horas ya pasadas no se ofrecen:
        # se elegían y el guardado respondía «No se pueden agendar citas en el pasado».
        ahora = timezone.localtime()
        horarios = []
        for hora in horas_del_dia:
            if fecha == ahora.date() and hora <= ahora.time() and hora not in citas_dict:
                horarios.append({"hora": hora, "disponible": False, "cita_id": None,
                                 "paciente_nombre": None, "motivo": "Hora pasada"})
            elif hora in citas_dict:
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


class OrdenFechaHora(filters.OrderingFilter):
    """Al ordenar por fecha, desempata por hora en el MISMO sentido.

    La tabla de citas ordena por «Fecha y Hora» en una sola columna. Con
    `?ordering=fecha_cita` a secas, las citas de un mismo día salían en orden
    arbitrario (y cambiaban de página entre peticiones), porque
    OrderingFilter reemplaza el orden por defecto del queryset.
    """

    def get_ordering(self, request, queryset, view):
        orden = super().get_ordering(request, queryset, view)
        if not orden or any(c.lstrip("-") == "hora_cita" for c in orden):
            return orden
        resultado = []
        for campo in orden:
            resultado.append(campo)
            if campo.lstrip("-") == "fecha_cita":
                resultado.append("-hora_cita" if campo.startswith("-") else "hora_cita")
        return resultado


_MENSAJES_FUERA_DE_DIA = {
    "confirmar": "La cita del {fecha} ya pasó: no se puede confirmar.",
    "completar": "La cita es del {fecha}: todavía no llegó su día, no se puede completar.",
    "no-asistio": "La cita es del {fecha}: todavía no llegó su día, no se puede marcar «No asistió».",
    "marcar-presente": "La llegada se registra solo el día de la cita ({fecha}).",
    "pasar-consulta": "La paciente pasa a consulta solo el día de la cita ({fecha}).",
}


def _fuera_de_dia(cita, accion, desde_hoy=False, hasta_hoy=False):
    """400 si la acción no corresponde a la fecha de la cita; None si sí.

    Antes se podía marcar «No asistió» una cita de la semana próxima o marcar
    presente a una paciente citada para otro día.
    """
    hoy = timezone.localdate()
    if (desde_hoy and cita.fecha_cita < hoy) or (hasta_hoy and cita.fecha_cita > hoy):
        return Response(
            {"error": _MENSAJES_FUERA_DE_DIA[accion].format(fecha=cita.fecha_cita.strftime("%d/%m/%Y"))},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


class CitaViewSet(ExportarExcelMixin, viewsets.ModelViewSet):
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

    excel_nombre = "citas"
    excel_columnas = [
        ("Fecha", "fecha_cita"),
        ("Hora", "hora_cita"),
        ("Paciente", "paciente.nombre_completo"),
        ("ID clínico", "paciente.id_clinico"),
        ("Médico", "medico.nombre_completo"),
        ("Consultorio", "consultorio"),
        ("Tipo", "tipo_cita"),
        ("Estado", "estado"),
        ("Motivo", "motivo"),
    ]


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
        OrdenFechaHora,
    ]
    filterset_fields = ["paciente", "medico", "estado", "tipo_cita", "fecha_cita"]
    # Búsqueda por paciente vía BusquedaClinicaFilter: los datos
    # identificatorios de Paciente están cifrados y el SearchFilter de DRF
    # (icontains en SQL) no encontraba NUNCA nada. Ver core/filtros.py.
    busqueda_ruta_paciente = "paciente"
    # Motivo y observaciones están en claro: la pantalla los buscaba en el
    # navegador y, al paginar en el servidor, la búsqueda tiene que cubrirlos.
    busqueda_campos_claros = [
        "medico__nombre",
        "medico__apellido_paterno",
        "motivo",
        "observaciones",
    ]
    ordering_fields = ["fecha_cita", "hora_cita", "estado"]

    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == "list":
            return CitaListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return CitaCreateUpdateSerializer
        return CitaDetailSerializer

    def initial(self, request, *args, **kwargs):
        """Antes de responder, cierra las citas de días pasados (una vez al día)."""
        super().initial(request, *args, **kwargs)
        cerrar_citas_vencidas_hoy()

    def perform_create(self, serializer):
        """TRAZABILIDAD: quién agendó la cita.

        Cita tiene creado_por/modificado_por; created_by/updated_by son de
        Disponibilidad y pasarlos aquí hacía que toda alta o edición de cita
        respondiera 500 («unexpected keyword arguments: created_by»).
        """
        serializer.save(creado_por=self.request.user)

    def perform_update(self, serializer):
        """TRAZABILIDAD: quién modificó la cita."""
        serializer.save(modificado_por=self.request.user)

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

        # Mañana y tarde: todos los bloques activos del día.
        bloques, _vigentes, _horas = bloques_del_dia(medico_id, fecha)
        horas_del_dia = sorted({hora for b in bloques for hora in b.horas_disponibles})

        if not bloques:
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

        # Las canceladas dejan el turno libre; si una cancelada y una nueva
        # compartían hora, la cancelada podía tapar a la vigente.
        citas = Cita.objects.filter(
            medico_id=medico_id, fecha_cita=fecha,
        ).exclude(estado="cancelada").select_related("paciente")

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
        for hora in horas_del_dia:
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
    def resumen(self, _request):
        """Cifras de la pantalla de citas, con los MISMOS filtros que el listado.

        GET /api/citas/citas/resumen/?search=&estado=&tipo_cita=&fecha_desde=&fecha_hasta=

        Antes la pantalla descargaba TODAS las citas y TODAS las pacientes en
        bucle para contar en el navegador. Respeta la restricción por rol de
        `get_queryset` (un médico solo cuenta sus citas), cosa que el
        `estadisticas` global no hace.
        """
        qs = self.filter_queryset(self.get_queryset()).order_by()
        hoy = timezone.localdate()
        por_estado = dict(qs.values_list("estado").annotate(n=Count("id")))
        return Response({
            "total": sum(por_estado.values()),
            **{codigo: por_estado.get(codigo, 0) for codigo, _ in Cita.ESTADO_CHOICES},
            # Pendientes de atender hoy (las ya cerradas no cuentan).
            "hoy": qs.filter(fecha_cita=hoy,
                             estado__in=["agendada", "confirmada", "en_espera", "en_consulta"]).count(),
            # Fecha pasada y nadie la cerró: la paciente no vino o falta registrarlo.
            "atrasadas": qs.filter(fecha_cita__lt=hoy, estado__in=["agendada", "confirmada"]).count(),
            "pendientes_confirmacion": por_estado.get("agendada", 0),
        })

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
        if error := _fuera_de_dia(cita, "confirmar", desde_hoy=True):
            return error

        if cita.estado not in ["agendada"]:
            return Response(
                {
                    "error": f"No se puede confirmar una cita en estado {getattr(cita, 'get_estado_display')()}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cita.confirmar(usuario=request.user)
        HistorialCita.objects.create(
            cita=cita,
            estado_anterior="agendada",
            estado_nuevo="confirmada",
            motivo_cambio="Cita confirmada",
            usuario=request.user,
        )

        serializer = CitaDetailSerializer(cita)
        return Response(
            {"mensaje": "Cita confirmada exitosamente", "cita": serializer.data},
        )

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """Cancelar una cita"""
        cita = self.get_object()
        motivo = request.data.get("motivo", "")

        # Una cita cerrada (atendida, cancelada o «No asistió») ya no se cancela.
        if cita.estado not in ["agendada", "confirmada", "en_espera"]:
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
        if error := _fuera_de_dia(cita, "completar", hasta_hoy=True):
            return error

        # La paciente en consulta es el caso normal: antes solo se aceptaba
        # agendada/confirmada y la que estaba en consulta no se podía cerrar.
        if cita.estado not in ["agendada", "confirmada", "en_espera", "en_consulta"]:
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
        if error := _fuera_de_dia(cita, "no-asistio", hasta_hoy=True):
            return error

        if cita.estado not in ["agendada", "confirmada", "en_espera"]:
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
        if error := _fuera_de_dia(cita, "marcar-presente", desde_hoy=True, hasta_hoy=True):
            return error
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
        if error := _fuera_de_dia(cita, "pasar-consulta", desde_hoy=True, hasta_hoy=True):
            return error
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
