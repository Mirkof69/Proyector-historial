"""Views module."""
import contextlib
from datetime import timedelta

from django.db.models import Avg, Count, Exists, OuterRef
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.filtros import BusquedaClinicaFilter
from core.permissions import EsMedicoOEnfermeraOLaboratorista, FetalMedicalPermission

from .models import ExamenLaboratorio, ResultadoLaboratorio, TipoExamen, ValorReferencia
from .serializers import (
    ExamenLaboratorioCreateUpdateSerializer,
    ExamenLaboratorioDetailSerializer,
    ExamenLaboratorioListSerializer,
    ResultadoLaboratorioCreateUpdateSerializer,
    ResultadoLaboratorioSerializer,
    TipoExamenSerializer,
    ValorReferenciaSerializer,
)


class TipoExamenViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de Tipos de Exámenes

    Endpoints disponibles:
        pass
    - GET /api/laboratorio/tipos-examenes/ - Listar tipos
    - POST /api/laboratorio/tipos-examenes/ - Crear tipo
    - GET /api/laboratorio/tipos-examenes/{id}/ - Ver detalle
    - PUT/PATCH /api/laboratorio/tipos-examenes/{id}/ - Actualizar
    - DELETE /api/laboratorio/tipos-examenes/{id}/ - Eliminar
    - GET /api/laboratorio/tipos-examenes/por-categoria/ - Agrupar por categoría
    - GET /api/laboratorio/tipos-examenes/estadisticas/ - Estadísticas
    """

    queryset = TipoExamen.objects.all().order_by("categoria", "nombre")
    serializer_class = TipoExamenSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["categoria", "activo"]
    search_fields = ["nombre", "codigo", "descripcion"]
    ordering_fields = ["nombre", "categoria", "precio", "tiempo_resultado"]

    def perform_create(self, serializer):
        """Asignar created_by para trazabilidad"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Asignar updated_by para trazabilidad"""
        serializer.save(updated_by=self.request.user)

    def get_queryset(self):
        """Filtrar queryset según parámetros"""
        queryset = super().get_queryset()

        # Filtrar solo activos si se especifica
        solo_activos = self.request.query_params.get("solo_activos", None)
        if solo_activos == "true":
            queryset = queryset.filter(activo=True)

        return queryset

    @action(detail=False, methods=["get"], url_path="por-categoria")
    def por_categoria(self, _request):
        """Agrupar tipos de exámenes por categoría

        Retorna un diccionario con las categorías como llaves
        y los exámenes activos como valores

        Ejemplo de respuesta:
            pass
        {
            "Hematología": [...],
            "Bioquímica": [...],
            "Serología": [...]
        }
        """
        categorias = {}

        # Iterar sobre todas las categorías disponibles
        for categoria_codigo, categoria_nombre in TipoExamen.CATEGORIA_CHOICES:
            # Obtener solo exámenes activos de cada categoría
            examenes = TipoExamen.objects.filter(
                categoria=categoria_codigo, activo=True,
            ).order_by("nombre")

            # Serializar y agregar al diccionario
            categorias[categoria_nombre] = TipoExamenSerializer(
                examenes, many=True,
            ).data

        return Response(categorias)

    @action(detail=False, methods=["get"])
    def estadisticas(self, _request):
        """Estadísticas generales de tipos de exámenes

        Retorna:
            pass
        - Total de tipos de exámenes
        - Cantidad de activos e inactivos
        - Distribución por categoría
        """
        # Contar totales
        total = TipoExamen.objects.count()
        activos = TipoExamen.objects.filter(activo=True).count()
        inactivos = total - activos

        # Contar por categoría
        por_categoria = {}
        for codigo, nombre in TipoExamen.CATEGORIA_CHOICES:
            count = TipoExamen.objects.filter(categoria=codigo).count()
            if count > 0:  # Solo incluir categorías con exámenes
                por_categoria[nombre] = count

        # Precio promedio
        precio_promedio = TipoExamen.objects.aggregate(promedio=Avg("precio"))[
            "promedio"
        ]

        return Response(
            {
                "total": total,
                "activos": activos,
                "inactivos": inactivos,
                "por_categoria": por_categoria,
                "precio_promedio": round(float(precio_promedio or 0), 2),
            },
        )

    @action(detail=False, methods=["get"])
    def mas_solicitados(self, request):
        """Obtener los tipos de exámenes más solicitados

        Parámetros query:
            pass
        - limite: número de resultados (default: 10)
        """
        limite = int(request.query_params.get("limite", 10))

        # Anotar con count de exámenes y ordenar
        tipos_mas_solicitados = (
            TipoExamen.objects.annotate(total_examenes=Count("examenes"))
            .filter(total_examenes__gt=0)
            .order_by("-total_examenes")[:limite]
        )

        resultados = []
        for tipo in tipos_mas_solicitados:
            resultados.append(
                {
                    "id": getattr(tipo, 'id', None),
                    "nombre": tipo.nombre,
                    "codigo": tipo.codigo,
                    "categoria": getattr(tipo, 'get_categoria_display')(),
                    "total_examenes": getattr(tipo, 'total_examenes', 0),
                    "precio": str(tipo.precio),
                },
            )

        return Response(
            {
                "total_resultados": len(resultados),
                "examenes_mas_solicitados": resultados,
            },
        )


class ValorReferenciaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de Valores de Referencia

    Endpoints:
        pass
    - GET /api/laboratorio/valores-referencia/ - Listar todos
    - POST /api/laboratorio/valores-referencia/ - Crear valor
    - GET /api/laboratorio/valores-referencia/{id}/ - Ver detalle
    - PUT/PATCH /api/laboratorio/valores-referencia/{id}/ - Actualizar
    - DELETE /api/laboratorio/valores-referencia/{id}/ - Eliminar
    - GET /api/laboratorio/valores-referencia/por-examen/tipo_examen_id=X
    """

    queryset = ValorReferencia.objects.select_related("tipo_examen").all()
    serializer_class = ValorReferenciaSerializer
    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["tipo_examen", "unidad"]
    search_fields = ["parametro", "tipo_examen__nombre"]
    ordering_fields = ["parametro", "tipo_examen__nombre"]

    def perform_create(self, serializer):
        """Asignar created_by para trazabilidad"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Asignar updated_by para trazabilidad"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="por-examen")
    def por_examen(self, request):
        """Obtener valores de referencia de un tipo de examen específico

        Parámetros query requeridos:
            pass
        - tipo_examen_id: ID del tipo de examen

        Ejemplo: /api/laboratorio/valores-referencia/por-examen/tipo_examen_id=1
        """
        tipo_examen_id = request.query_params.get("tipo_examen_id", None)

        # Validar que se proporcione el ID
        if not tipo_examen_id:
            return Response(
                {
                    "error": "Parámetro requerido faltante",
                    "detalle": "Debe proporcionar tipo_examen_id en los parámetros de consulta",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar que el tipo de examen exista
        try:
            tipo_examen = TipoExamen.objects.get(id=tipo_examen_id)
        except TipoExamen.DoesNotExist:
            return Response(
                {
                    "error": "Tipo de examen no encontrado",
                    "detalle": f"No existe un tipo de examen con ID {tipo_examen_id}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Obtener valores de referencia
        assert self.queryset is not None
        valores = self.queryset.filter(tipo_examen_id=tipo_examen_id).order_by(
            "parametro",
        )
        serializer = self.get_serializer(valores, many=True)

        return Response(
            {
                "tipo_examen": {
                    "id": getattr(tipo_examen, 'id', None),
                    "nombre": tipo_examen.nombre,
                    "codigo": tipo_examen.codigo,
                    "categoria": getattr(tipo_examen, 'get_categoria_display')(),
                },
                "total_parametros": valores.count(),
                "valores_referencia": serializer.data,
            },
        )


class ExamenLaboratorioViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gestión de Exámenes de Laboratorio

    Endpoints disponibles:
        pass
    - GET /api/laboratorio/examenes/ - Listar todos
    - POST /api/laboratorio/examenes/ - Crear examen
    - GET /api/laboratorio/examenes/{id}/ - Ver detalle completo
    - PUT/PATCH /api/laboratorio/examenes/{id}/ - Actualizar
    - DELETE /api/laboratorio/examenes/{id}/ - Eliminar
    - GET /api/laboratorio/examenes/por-paciente/paciente_id=X
    - GET /api/laboratorio/examenes/pendientes/
    - GET /api/laboratorio/examenes/vencidos/
    - GET /api/laboratorio/examenes/estadisticas/
    - GET /api/laboratorio/examenes/criticos/
    - GET /api/laboratorio/examenes/recientes/dias=7
    """

    queryset = (
        ExamenLaboratorio.objects.select_related(
            "paciente",
            "control_prenatal",
            "control_prenatal__embarazo",
            "tipo_examen",
            "medico_solicitante",
        )
        .prefetch_related("resultados", "resultados__valor_referencia")
        .all()
        .order_by("-fecha_solicitud")
    )

    permission_classes = [IsAuthenticated, EsMedicoOEnfermeraOLaboratorista]
    filter_backends = [
        DjangoFilterBackend,
        BusquedaClinicaFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "paciente",
        "tipo_examen",
        "estado",
        "prioridad",
        "control_prenatal",
    ]
    # Búsqueda por paciente vía BusquedaClinicaFilter: los datos
    # identificatorios de Paciente están cifrados y el SearchFilter de DRF
    # (icontains en SQL) no encontraba NUNCA nada. Ver core/filtros.py.
    busqueda_ruta_paciente = "paciente"
    busqueda_campos_claros = [
        "tipo_examen__nombre",
        "tipo_examen__codigo",
    ]
    ordering_fields = ["fecha_solicitud", "fecha_resultado", "estado", "prioridad"]

    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción"""
        if self.action == "list":
            return ExamenLaboratorioListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ExamenLaboratorioCreateUpdateSerializer
        return ExamenLaboratorioDetailSerializer

    def get_queryset(self):
        """Filtrar queryset según parámetros"""
        queryset = super().get_queryset()

        # Filtrar por rango de fechas de solicitud
        fecha_desde = self.request.query_params.get("fecha_desde", None)
        fecha_hasta = self.request.query_params.get("fecha_hasta", None)

        if fecha_desde:
            with contextlib.suppress(Exception):
                queryset = queryset.filter(fecha_solicitud__gte=fecha_desde)

        if fecha_hasta:
            with contextlib.suppress(Exception):
                queryset = queryset.filter(fecha_solicitud__lte=fecha_hasta)

        # Filtrar por categoría de examen
        categoria = self.request.query_params.get("categoria", None)
        if categoria:
            queryset = queryset.filter(tipo_examen__categoria=categoria)

        return queryset

    def perform_create(self, serializer):
        """Asignar created_by para trazabilidad"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Asignar updated_by para trazabilidad"""
        serializer.save(updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """Crear nuevo examen de laboratorio"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Retornar con serializer detallado
        assert serializer.instance is not None
        examen = ExamenLaboratorio.objects.select_related(
            "paciente", "control_prenatal", "tipo_examen", "medico_solicitante",
        ).get(id=serializer.instance.id)

        return_serializer = ExamenLaboratorioDetailSerializer(examen)

        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data, status=status.HTTP_201_CREATED, headers=headers,
        )

    @action(detail=False, methods=["get"], url_path="por-paciente")
    def por_paciente(self, request):
        """Obtener todos los exámenes de un paciente específico

        Parámetros query requeridos:
            pass
        - paciente_id: ID del paciente

        Ejemplo: /api/laboratorio/examenes/por-paciente/paciente_id=1
        """
        paciente_id = request.query_params.get("paciente_id", None)

        if not paciente_id:
            return Response(
                {
                    "error": "Parámetro requerido faltante",
                    "detalle": "Debe proporcionar paciente_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filtrar exámenes del paciente
        assert self.queryset is not None
        examenes = self.queryset.filter(paciente_id=paciente_id).order_by(
            "-fecha_solicitud",
        )

        # Paginación
        page = self.paginate_queryset(examenes)
        if page is not None:
            serializer = ExamenLaboratorioDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ExamenLaboratorioDetailSerializer(examenes, many=True)

        return Response(
            {"total_examenes": examenes.count(), "examenes": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def pendientes(self, _request):
        """Listar exámenes pendientes (solicitados o en proceso)

        Retorna todos los exámenes que aún no han sido completados
        """
        assert self.queryset is not None
        examenes = self.queryset.filter(
            estado__in=["solicitado", "en_proceso"],
        ).order_by("fecha_solicitud")

        # Paginación
        page = self.paginate_queryset(examenes)
        if page is not None:
            serializer = ExamenLaboratorioListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ExamenLaboratorioListSerializer(examenes, many=True)

        return Response(
            {"total_pendientes": examenes.count(), "examenes": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def vencidos(self, _request):
        """Listar exámenes que excedieron el tiempo esperado de resultados

        Retorna exámenes pendientes cuyo tiempo desde la solicitud
        excede el tiempo_resultado definido en el tipo de examen
        """
        assert self.queryset is not None
        examenes_pendientes = self.queryset.filter(
            estado__in=["solicitado", "en_proceso"],
        )

        # Filtrar los que están vencidos
        vencidos = [e for e in examenes_pendientes if e.esta_vencido]

        serializer = ExamenLaboratorioListSerializer(vencidos, many=True)

        return Response({"total_vencidos": len(vencidos), "examenes": serializer.data})

    @action(detail=False, methods=["get"])
    def criticos(self, _request):
        """Listar exámenes con resultados críticos

        Retorna exámenes que tienen al menos un resultado crítico
        """
        # Subconsulta para verificar resultados críticos
        tiene_criticos = ResultadoLaboratorio.objects.filter(
            examen=OuterRef("pk"), es_critico=True,
        )

        assert self.queryset is not None
        examenes_criticos = (
            self.queryset.annotate(tiene_resultado_critico=Exists(tiene_criticos))
            .filter(tiene_resultado_critico=True)
            .order_by("-fecha_resultado")
        )

        # Paginación
        page = self.paginate_queryset(examenes_criticos)
        if page is not None:
            serializer = ExamenLaboratorioDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ExamenLaboratorioDetailSerializer(examenes_criticos, many=True)

        return Response(
            {"total_criticos": examenes_criticos.count(), "examenes": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def recientes(self, request):
        """Listar exámenes recientes

        Parámetros query opcionales:
            pass
        - dias: número de días hacia atrás (default: 7)

        Ejemplo: /api/laboratorio/examenes/recientes/dias=30
        """
        dias = int(request.query_params.get("dias", 7))
        fecha_desde = timezone.localdate() - timedelta(days=dias)

        assert self.queryset is not None
        examenes = self.queryset.filter(fecha_solicitud__gte=fecha_desde).order_by(
            "-fecha_solicitud",
        )

        # Paginación
        page = self.paginate_queryset(examenes)
        if page is not None:
            serializer = ExamenLaboratorioListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ExamenLaboratorioListSerializer(examenes, many=True)

        return Response(
            {
                "dias": dias,
                "fecha_desde": fecha_desde,
                "total_examenes": examenes.count(),
                "examenes": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, _request):
        """Estadísticas generales de exámenes de laboratorio

        Retorna:
            pass
        - Total de exámenes
        - Distribución por estado
        - Exámenes de la última semana
        - Exámenes con resultados anormales
        - Exámenes críticos
        """
        total = ExamenLaboratorio.objects.count()

        # Contar por estado
        por_estado = {}
        for estado_codigo, estado_nombre in ExamenLaboratorio.ESTADO_CHOICES:
            count = ExamenLaboratorio.objects.filter(estado=estado_codigo).count()
            por_estado[estado_nombre] = count

        # Contar por prioridad
        por_prioridad = {}
        for prioridad_codigo, prioridad_nombre in ExamenLaboratorio.PRIORIDAD_CHOICES:
            count = ExamenLaboratorio.objects.filter(prioridad=prioridad_codigo).count()
            por_prioridad[prioridad_nombre] = count

        # Última semana
        hace_una_semana = timezone.localdate() - timedelta(days=7)
        examenes_semana = ExamenLaboratorio.objects.filter(
            fecha_solicitud__gte=hace_una_semana,
        ).count()

        # Último mes
        hace_un_mes = timezone.localdate() - timedelta(days=30)
        examenes_mes = ExamenLaboratorio.objects.filter(
            fecha_solicitud__gte=hace_un_mes,
        ).count()

        # Exámenes con resultados anormales

        tiene_anormales = ResultadoLaboratorio.objects.filter(
            examen=OuterRef("pk"), es_normal=False,
        )

        con_anormales = (
            ExamenLaboratorio.objects.annotate(tiene_anormal=Exists(tiene_anormales))
            .filter(tiene_anormal=True)
            .count()
        )

        # Exámenes con resultados críticos
        tiene_criticos = ResultadoLaboratorio.objects.filter(
            examen=OuterRef("pk"), es_critico=True,
        )

        con_criticos = (
            ExamenLaboratorio.objects.annotate(tiene_critico=Exists(tiene_criticos))
            .filter(tiene_critico=True)
            .count()
        )

        return Response(
            {
                "total_examenes": total,
                "examenes_ultima_semana": examenes_semana,
                "examenes_ultimo_mes": examenes_mes,
                "por_estado": por_estado,
                "por_prioridad": por_prioridad,
                "con_resultados_anormales": con_anormales,
                "con_resultados_criticos": con_criticos,
            },
        )

    @action(detail=True, methods=["post"])
    def cambiar_estado(self, request, pk=None):
        """Cambiar el estado de un examen

        Body requerido:
            pass
        {
            "estado": "completado|en_proceso|cancelado"
        }
        """
        examen = self.get_object()
        nuevo_estado = request.data.get("estado", None)

        if not nuevo_estado:
            return Response(
                {"error": "Debe proporcionar el nuevo estado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar estado
        estados_validos = [e[0] for e in ExamenLaboratorio.ESTADO_CHOICES]
        if nuevo_estado not in estados_validos:
            return Response(
                {"error": "Estado no válido", "estados_validos": estados_validos},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Actualizar estado
        examen.estado = nuevo_estado

        # Si se marca como completado, registrar fecha de resultado
        if nuevo_estado == "completado" and not examen.fecha_resultado:
            examen.fecha_resultado = timezone.now()

        examen.save()

        serializer = ExamenLaboratorioDetailSerializer(examen)
        return Response(
            {
                "mensaje": f"Estado cambiado a {getattr(examen, 'get_estado_display')()}",
                "examen": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="valores-referencia-por-tipo")
    def valores_referencia_por_tipo(self, request):
        """Obtener valores de referencia para un tipo de examen

        Parámetros query requeridos:
            pass
        - tipo_examen_id: ID del tipo de examen

        Ejemplo: /api/laboratorio/examenes/valores-referencia-por-tipo/tipo_examen_id=1

        Retorna los parámetros que se deben medir para un tipo de examen específico,
        junto con sus respectivos rangos de referencia.
        """
        tipo_examen_id = request.query_params.get("tipo_examen_id", None)

        if not tipo_examen_id:
            return Response(
                {
                    "error": "Parámetro requerido faltante",
                    "detalle": "Debe proporcionar tipo_examen_id en los parámetros de consulta",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar que el tipo de examen exista
        try:
            tipo_examen = TipoExamen.objects.get(id=tipo_examen_id)
        except TipoExamen.DoesNotExist:
            return Response(
                {
                    "error": "Tipo de examen no encontrado",
                    "detalle": f"No existe un tipo de examen con ID {tipo_examen_id}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Obtener valores de referencia
        valores = ValorReferencia.objects.filter(
            tipo_examen_id=tipo_examen_id,
        ).order_by("parametro")

        serializer = ValorReferenciaSerializer(valores, many=True)

        return Response(
            {
                "tipo_examen": {
                    "id": getattr(tipo_examen, 'id', None),
                    "nombre": tipo_examen.nombre,
                    "codigo": tipo_examen.codigo,
                    "categoria": getattr(tipo_examen, 'get_categoria_display')(),
                },
                "total_parametros": valores.count(),
                "valores_referencia": serializer.data,
            },
        )

    @action(detail=True, methods=["get"], url_path="estadisticas-paciente")
    def estadisticas_paciente(self, request, pk=None):
        """Obtener histórico de resultados de un paciente para análisis estadístico

        Obtiene los últimos exámenes del mismo tipo que el examen actual,
        para mostrar gráficos de evolución temporal.

        Parámetros query opcionales:
            pass
        - limite: cantidad máxima de exámenes históricos (default: 10)

        Ejemplo: /api/laboratorio/examenes/1/estadisticas-paciente/limite=5
        """
        examen_actual = self.get_object()
        limite = int(request.query_params.get("limite", 10))

        # Buscar exámenes anteriores del mismo tipo y paciente
        examenes_historicos = (
            ExamenLaboratorio.objects.filter(
                paciente=examen_actual.paciente,
                tipo_examen=examen_actual.tipo_examen,
                estado="completado",
                fecha_resultado__isnull=False,
            )
            .exclude(
                id=examen_actual.id,  # Excluir el examen actual
            )
            .select_related("tipo_examen", "paciente")
            .prefetch_related("resultados", "resultados__valor_referencia")
            .order_by("-fecha_resultado")[:limite]
        )

        # Serializar examenes históricos
        examenes_data = []
        for examen in examenes_historicos:
            # Obtener resultados del examen
            _resultados_mgr = getattr(examen, 'resultados', ResultadoLaboratorio.objects.none())
            resultados_data = []
            for resultado in _resultados_mgr.all():
                resultados_data.append(
                    {
                        "parametro": resultado.valor_referencia.parametro
                        if resultado.valor_referencia
                        else "N/A",
                        "valor_numerico": float(resultado.valor_numerico)
                        if resultado.valor_numerico
                        else None,
                        "valor_texto": resultado.valor_texto,
                        "unidad": resultado.valor_referencia.unidad
                        if resultado.valor_referencia
                        else None,
                        "es_normal": resultado.es_normal,
                        "es_critico": resultado.es_critico,
                    },
                )

            _resultados = getattr(examen, 'resultados', ResultadoLaboratorio.objects.none())
            examenes_data.append(
                {
                    "id": getattr(examen, 'id', None),
                    "fecha_resultado": examen.fecha_resultado,
                    "fecha_solicitud": examen.fecha_solicitud,
                    "resultados": resultados_data,
                    "resumen": {
                        "total_parametros": _resultados.count(),
                        "normales": _resultados.filter(es_normal=True).count(),
                        "anormales": _resultados.filter(es_normal=False).count(),
                        "criticos": _resultados.filter(es_critico=True).count(),
                    },
                },
            )

        return Response(
            {
                "examen_actual": {
                    "id": getattr(examen_actual, 'id', None),
                    "paciente": {
                        "id": examen_actual.paciente.id,
                        "nombre_completo": examen_actual.paciente.nombre_completo,
                        "id_clinico": examen_actual.paciente.id_clinico,
                    },
                    "tipo_examen": {
                        "id": examen_actual.tipo_examen.id,
                        "nombre": examen_actual.tipo_examen.nombre,
                        "codigo": examen_actual.tipo_examen.codigo,
                    },
                },
                "total_historicos": len(examenes_data),
                "examenes_historicos": examenes_data,
            },
        )

    @action(detail=True, methods=["post"], url_path="crear-resultado-multiple")
    def crear_resultado_multiple(self, request, pk=None):
        """Crear múltiples resultados de laboratorio en una sola petición

        Body requerido:
            pass
        {
            "resultados": [
                {
                    "valor_referencia": 1,
                    "valor_numerico": 95.5,
                    "valor_texto": null,
                    "unidad": "mg/dL",
                    "observaciones": ""
                },
                {
                    "valor_referencia": 2,
                    "valor_numerico": null,
                    "valor_texto": "Negativo",
                    "unidad": "cualitativo",
                    "observaciones": ""
                }
            ],
            "completar_examen": true  // Si true, marca el examen como completado
        }

        Retorna:
            pass
        - Lista de resultados creados
        - Resumen actualizado del examen
        """
        examen = self.get_object()
        resultados_data = request.data.get("resultados", [])
        completar_examen = request.data.get("completar_examen", False)

        if not resultados_data:
            return Response(
                {
                    "error": "Datos faltantes",
                    "detalle": 'Debe proporcionar al menos un resultado en el array "resultados"',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear resultados
        resultados_creados = []
        errores = []

        for idx, resultado_data in enumerate(resultados_data):
            try:
                # Validar valor_referencia existe
                valor_ref_id = resultado_data.get("valor_referencia")
                if not valor_ref_id:
                    errores.append(
                        {"indice": idx, "error": "Falta el ID de valor_referencia"},
                    )
                    continue

                try:
                    valor_referencia = ValorReferencia.objects.get(id=valor_ref_id)
                except ValorReferencia.DoesNotExist:
                    errores.append(
                        {
                            "indice": idx,
                            "error": f"ValorReferencia con ID {valor_ref_id} no encontrado",
                        },
                    )
                    continue

                # Crear resultado
                resultado = ResultadoLaboratorio.objects.create(
                    examen=examen,
                    valor_referencia=valor_referencia,
                    valor_numerico=resultado_data.get("valor_numerico"),
                    valor_texto=resultado_data.get("valor_texto"),
                    unidad=resultado_data.get("unidad", valor_referencia.unidad),
                    observaciones=resultado_data.get("observaciones", ""),
                    created_by=request.user,
                    updated_by=request.user,
                )

                resultados_creados.append(resultado)

            except Exception as e:
                errores.append({"indice": idx, "error": str(e)})

        # Si se solicita completar el examen y no hay errores
        if completar_examen and len(errores) == 0:

            examen.estado = "completado"
            if not examen.fecha_resultado:
                examen.fecha_resultado = timezone.now()
            examen.updated_by = request.user
            examen.save()

        # Serializar resultados creados
        serializer = ResultadoLaboratorioSerializer(resultados_creados, many=True)

        # Calcular resumen actualizado
        todos_resultados = examen.resultados.all()
        resumen = {
            "total_parametros": todos_resultados.count(),
            "normales": todos_resultados.filter(es_normal=True).count(),
            "anormales": todos_resultados.filter(es_normal=False).count(),
            "criticos": todos_resultados.filter(es_critico=True).count(),
            "porcentaje_normalidad": round(
                (
                    todos_resultados.filter(es_normal=True).count()
                    / todos_resultados.count()
                    * 100
                )
                if todos_resultados.count() > 0
                else 0,
                2,
            ),
        }

        return Response(
            {
                "mensaje": f"{len(resultados_creados)} resultados creados exitosamente",
                "resultados_creados": len(resultados_creados),
                "errores": errores,
                "examen_completado": completar_examen and len(errores) == 0,
                "resultados": serializer.data,
                "resumen": resumen,
                "estado_examen": getattr(examen, 'get_estado_display')(),
            },
            status=status.HTTP_201_CREATED,
        )


class ResultadoLaboratorioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de Resultados de Laboratorio

    Endpoints:
        pass
    - GET /api/laboratorio/resultados/ - Listar todos
    - POST /api/laboratorio/resultados/ - Crear resultado
    - GET /api/laboratorio/resultados/{id}/ - Ver detalle
    - PUT/PATCH /api/laboratorio/resultados/{id}/ - Actualizar
    - DELETE /api/laboratorio/resultados/{id}/ - Eliminar
    - GET /api/laboratorio/resultados/por-examen/examen_id=X
    - GET /api/laboratorio/resultados/anormales/
    - GET /api/laboratorio/resultados/criticos/
    """

    queryset = (
        ResultadoLaboratorio.objects.select_related(
            "examen",
            "examen__paciente",
            "examen__tipo_examen",
            "valor_referencia",
            "valor_referencia__tipo_examen",
        )
        .all()
        .order_by("-fecha_registro")
    )

    permission_classes = [FetalMedicalPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["examen", "es_normal", "es_critico"]
    search_fields = ["valor_referencia__parametro", "examen__paciente__nombre"]
    ordering_fields = ["fecha_registro", "es_normal", "es_critico"]

    def perform_create(self, serializer):
        """Asignar created_by para trazabilidad"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Asignar updated_by para trazabilidad"""
        serializer.save(updated_by=self.request.user)

    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción"""
        if self.action in ["create", "update", "partial_update"]:
            return ResultadoLaboratorioCreateUpdateSerializer
        return ResultadoLaboratorioSerializer

    @action(detail=False, methods=["get"], url_path="por-examen")
    def por_examen(self, request):
        """Obtener resultados de un examen específico

        Parámetros query requeridos:
            pass
        - examen_id: ID del examen

        Ejemplo: /api/laboratorio/resultados/por-examen/examen_id=1
        """
        examen_id = request.query_params.get("examen_id", None)

        if not examen_id:
            return Response(
                {
                    "error": "Parámetro requerido faltante",
                    "detalle": "Debe proporcionar examen_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar que el examen exista
        try:
            examen = ExamenLaboratorio.objects.select_related(
                "paciente", "tipo_examen",
            ).get(id=examen_id)
        except ExamenLaboratorio.DoesNotExist:
            return Response(
                {
                    "error": "Examen no encontrado",
                    "detalle": f"No existe un examen con ID {examen_id}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Obtener resultados
        assert self.queryset is not None
        resultados = self.queryset.filter(examen_id=examen_id).order_by(
            "valor_referencia__parametro",
        )
        serializer = self.get_serializer(resultados, many=True)

        # Resumen
        total = resultados.count()
        normales = resultados.filter(es_normal=True).count()
        anormales = resultados.filter(es_normal=False).count()
        criticos = resultados.filter(es_critico=True).count()

        return Response(
            {
            "examen": {
                "id": getattr(examen, 'id', None),
                    "paciente": examen.paciente.nombre_completo,
                    "tipo_examen": examen.tipo_examen.nombre,
                    "fecha_solicitud": examen.fecha_solicitud,
                    "estado": getattr(examen, 'get_estado_display')(),
                },
                "resumen": {
                    "total_parametros": total,
                    "normales": normales,
                    "anormales": anormales,
                    "criticos": criticos,
                },
                "resultados": serializer.data,
            },
        )

    @action(detail=False, methods=["get"])
    def anormales(self, _request):
        """Listar resultados anormales

        Retorna todos los resultados que están fuera del rango normal
        """
        assert self.queryset is not None
        resultados = self.queryset.filter(es_normal=False).order_by("-fecha_registro")

        # Paginación
        page = self.paginate_queryset(resultados)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(resultados, many=True)

        return Response(
            {"total_anormales": resultados.count(), "resultados": serializer.data},
        )

    @action(detail=False, methods=["get"])
    def criticos(self, _request):
        """Listar resultados críticos

        Retorna todos los resultados que están en rango crítico
        """
        assert self.queryset is not None
        resultados = self.queryset.filter(es_critico=True).order_by("-fecha_registro")

        # Paginación
        page = self.paginate_queryset(resultados)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(resultados, many=True)

        return Response(
            {"total_criticos": resultados.count(), "resultados": serializer.data},
        )
