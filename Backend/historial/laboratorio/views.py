from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta, date

from .models import TipoExamen, ExamenLaboratorio, ValorReferencia, ResultadoLaboratorio
from .serializers import (
    TipoExamenSerializer,
    ValorReferenciaSerializer,
    ExamenLaboratorioListSerializer,
    ExamenLaboratorioDetailSerializer,
    ExamenLaboratorioCreateUpdateSerializer,
    ResultadoLaboratorioSerializer,
    ResultadoLaboratorioCreateUpdateSerializer,
)


class TipoExamenViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Tipos de Exámenes
    
    Endpoints disponibles:
    - GET /api/laboratorio/tipos-examenes/ - Listar tipos
    - POST /api/laboratorio/tipos-examenes/ - Crear tipo
    - GET /api/laboratorio/tipos-examenes/{id}/ - Ver detalle
    - PUT/PATCH /api/laboratorio/tipos-examenes/{id}/ - Actualizar
    - DELETE /api/laboratorio/tipos-examenes/{id}/ - Eliminar
    - GET /api/laboratorio/tipos-examenes/por-categoria/ - Agrupar por categoría
    - GET /api/laboratorio/tipos-examenes/estadisticas/ - Estadísticas
    """
    
    queryset = TipoExamen.objects.all().order_by('categoria', 'nombre')
    serializer_class = TipoExamenSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'activo']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering_fields = ['nombre', 'categoria', 'precio', 'tiempo_resultado']
    
    def get_queryset(self):
        """Filtrar queryset según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar solo activos si se especifica
        solo_activos = self.request.query_params.get('solo_activos', None)
        if solo_activos == 'true':
            queryset = queryset.filter(activo=True)
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='por-categoria')
    def por_categoria(self, request):
        """
        Agrupar tipos de exámenes por categoría
        
        Retorna un diccionario con las categorías como llaves
        y los exámenes activos como valores
        
        Ejemplo de respuesta:
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
                categoria=categoria_codigo,
                activo=True
            ).order_by('nombre')
            
            # Serializar y agregar al diccionario
            categorias[categoria_nombre] = TipoExamenSerializer(examenes, many=True).data
        
        return Response(categorias)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Estadísticas generales de tipos de exámenes
        
        Retorna:
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
        precio_promedio = TipoExamen.objects.aggregate(
            promedio=Avg('precio')
        )['promedio']
        
        return Response({
            'total': total,
            'activos': activos,
            'inactivos': inactivos,
            'por_categoria': por_categoria,
            'precio_promedio': round(float(precio_promedio or 0), 2),
        })
    
    @action(detail=False, methods=['get'])
    def mas_solicitados(self, request):
        """
        Obtener los tipos de exámenes más solicitados
        
        Parámetros query:
        - limite: número de resultados (default: 10)
        """
        limite = int(request.query_params.get('limite', 10))
        
        # Anotar con count de exámenes y ordenar
        tipos_mas_solicitados = TipoExamen.objects.annotate(
            total_examenes=Count('examenes')
        ).filter(
            total_examenes__gt=0
        ).order_by('-total_examenes')[:limite]
        
        resultados = []
        for tipo in tipos_mas_solicitados:
            resultados.append({
                'id': tipo.id,
                'nombre': tipo.nombre,
                'codigo': tipo.codigo,
                'categoria': tipo.get_categoria_display(),
                'total_examenes': tipo.total_examenes,
                'precio': str(tipo.precio),
            })
        
        return Response({
            'total_resultados': len(resultados),
            'examenes_mas_solicitados': resultados
        })


class ValorReferenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Valores de Referencia
    
    Endpoints:
    - GET /api/laboratorio/valores-referencia/ - Listar todos
    - POST /api/laboratorio/valores-referencia/ - Crear valor
    - GET /api/laboratorio/valores-referencia/{id}/ - Ver detalle
    - PUT/PATCH /api/laboratorio/valores-referencia/{id}/ - Actualizar
    - DELETE /api/laboratorio/valores-referencia/{id}/ - Eliminar
    - GET /api/laboratorio/valores-referencia/por-examen/?tipo_examen_id=X
    """
    
    queryset = ValorReferencia.objects.select_related('tipo_examen').all()
    serializer_class = ValorReferenciaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_examen', 'unidad']
    search_fields = ['parametro', 'tipo_examen__nombre']
    ordering_fields = ['parametro', 'tipo_examen__nombre']
    
    @action(detail=False, methods=['get'], url_path='por-examen')
    def por_examen(self, request):
        """
        Obtener valores de referencia de un tipo de examen específico
        
        Parámetros query requeridos:
        - tipo_examen_id: ID del tipo de examen
        
        Ejemplo: /api/laboratorio/valores-referencia/por-examen/?tipo_examen_id=1
        """
        tipo_examen_id = request.query_params.get('tipo_examen_id', None)
        
        # Validar que se proporcione el ID
        if not tipo_examen_id:
            return Response(
                {
                    'error': 'Parámetro requerido faltante',
                    'detalle': 'Debe proporcionar tipo_examen_id en los parámetros de consulta'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el tipo de examen exista
        try:
            tipo_examen = TipoExamen.objects.get(id=tipo_examen_id)
        except TipoExamen.DoesNotExist:
            return Response(
                {
                    'error': 'Tipo de examen no encontrado',
                    'detalle': f'No existe un tipo de examen con ID {tipo_examen_id}'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener valores de referencia
        valores = self.queryset.filter(tipo_examen_id=tipo_examen_id).order_by('parametro')
        serializer = self.get_serializer(valores, many=True)
        
        return Response({
            'tipo_examen': {
                'id': tipo_examen.id,
                'nombre': tipo_examen.nombre,
                'codigo': tipo_examen.codigo,
                'categoria': tipo_examen.get_categoria_display(),
            },
            'total_parametros': valores.count(),
            'valores_referencia': serializer.data
        })


class ExamenLaboratorioViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Exámenes de Laboratorio
    
    Endpoints disponibles:
    - GET /api/laboratorio/examenes/ - Listar todos
    - POST /api/laboratorio/examenes/ - Crear examen
    - GET /api/laboratorio/examenes/{id}/ - Ver detalle completo
    - PUT/PATCH /api/laboratorio/examenes/{id}/ - Actualizar
    - DELETE /api/laboratorio/examenes/{id}/ - Eliminar
    - GET /api/laboratorio/examenes/por-paciente/?paciente_id=X
    - GET /api/laboratorio/examenes/pendientes/
    - GET /api/laboratorio/examenes/vencidos/
    - GET /api/laboratorio/examenes/estadisticas/
    - GET /api/laboratorio/examenes/criticos/
    - GET /api/laboratorio/examenes/recientes/?dias=7
    """
    
    queryset = ExamenLaboratorio.objects.select_related(
        'paciente',
        'control_prenatal',
        'control_prenatal__embarazo_id',
        'tipo_examen',
        'medico_solicitante'
    ).prefetch_related(
        'resultados',
        'resultados__valor_referencia'
    ).all().order_by('-fecha_solicitud')
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['paciente', 'tipo_examen', 'estado', 'prioridad', 'control_prenatal']
    search_fields = [
        'paciente__nombre',
        'paciente__apellido_paterno',
        'paciente__id_clinico',
        'tipo_examen__nombre',
        'tipo_examen__codigo'
    ]
    ordering_fields = ['fecha_solicitud', 'fecha_resultado', 'estado', 'prioridad']
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción"""
        if self.action == 'list':
            return ExamenLaboratorioListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ExamenLaboratorioCreateUpdateSerializer
        return ExamenLaboratorioDetailSerializer
    
    def get_queryset(self):
        """Filtrar queryset según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar por rango de fechas de solicitud
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if fecha_desde:
            try:
                queryset = queryset.filter(fecha_solicitud__gte=fecha_desde)
            except Exception:
                pass
        
        if fecha_hasta:
            try:
                queryset = queryset.filter(fecha_solicitud__lte=fecha_hasta)
            except Exception:
                pass
        
        # Filtrar por categoría de examen
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(tipo_examen__categoria=categoria)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo examen de laboratorio"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retornar con serializer detallado
        examen = ExamenLaboratorio.objects.select_related(
            'paciente',
            'control_prenatal',
            'tipo_examen',
            'medico_solicitante'
        ).get(id=serializer.instance.id)
        
        return_serializer = ExamenLaboratorioDetailSerializer(examen)
        
        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=False, methods=['get'], url_path='por-paciente')
    def por_paciente(self, request):
        """
        Obtener todos los exámenes de un paciente específico
        
        Parámetros query requeridos:
        - paciente_id: ID del paciente
        
        Ejemplo: /api/laboratorio/examenes/por-paciente/?paciente_id=1
        """
        paciente_id = request.query_params.get('paciente_id', None)
        
        if not paciente_id:
            return Response(
                {
                    'error': 'Parámetro requerido faltante',
                    'detalle': 'Debe proporcionar paciente_id'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtrar exámenes del paciente
        examenes = self.queryset.filter(paciente_id=paciente_id).order_by('-fecha_solicitud')
        
        # Paginación
        page = self.paginate_queryset(examenes)
        if page is not None:
            serializer = ExamenLaboratorioDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ExamenLaboratorioDetailSerializer(examenes, many=True)
        
        return Response({
            'total_examenes': examenes.count(),
            'examenes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Listar exámenes pendientes (solicitados o en proceso)
        
        Retorna todos los exámenes que aún no han sido completados
        """
        examenes = self.queryset.filter(
            estado__in=['solicitado', 'en_proceso']
        ).order_by('fecha_solicitud')
        
        # Paginación
        page = self.paginate_queryset(examenes)
        if page is not None:
            serializer = ExamenLaboratorioListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ExamenLaboratorioListSerializer(examenes, many=True)
        
        return Response({
            'total_pendientes': examenes.count(),
            'examenes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def vencidos(self, request):
        """
        Listar exámenes que excedieron el tiempo esperado de resultados
        
        Retorna exámenes pendientes cuyo tiempo desde la solicitud
        excede el tiempo_resultado definido en el tipo de examen
        """
        examenes_pendientes = self.queryset.filter(
            estado__in=['solicitado', 'en_proceso']
        )
        
        # Filtrar los que están vencidos
        vencidos = [e for e in examenes_pendientes if e.esta_vencido]
        
        serializer = ExamenLaboratorioListSerializer(vencidos, many=True)
        
        return Response({
            'total_vencidos': len(vencidos),
            'examenes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def criticos(self, request):
        """
        Listar exámenes con resultados críticos
        
        Retorna exámenes que tienen al menos un resultado crítico
        """
        from django.db.models import Exists, OuterRef
        
        # Subconsulta para verificar resultados críticos
        tiene_criticos = ResultadoLaboratorio.objects.filter(
            examen=OuterRef('pk'),
            es_critico=True
        )
        
        examenes_criticos = self.queryset.annotate(
            tiene_resultado_critico=Exists(tiene_criticos)
        ).filter(tiene_resultado_critico=True).order_by('-fecha_resultado')
        
        # Paginación
        page = self.paginate_queryset(examenes_criticos)
        if page is not None:
            serializer = ExamenLaboratorioDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ExamenLaboratorioDetailSerializer(examenes_criticos, many=True)
        
        return Response({
            'total_criticos': examenes_criticos.count(),
            'examenes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        """
        Listar exámenes recientes
        
        Parámetros query opcionales:
        - dias: número de días hacia atrás (default: 7)
        
        Ejemplo: /api/laboratorio/examenes/recientes/?dias=30
        """
        dias = int(request.query_params.get('dias', 7))
        fecha_desde = date.today() - timedelta(days=dias)
        
        examenes = self.queryset.filter(
            fecha_solicitud__gte=fecha_desde
        ).order_by('-fecha_solicitud')
        
        # Paginación
        page = self.paginate_queryset(examenes)
        if page is not None:
            serializer = ExamenLaboratorioListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ExamenLaboratorioListSerializer(examenes, many=True)
        
        return Response({
            'dias': dias,
            'fecha_desde': fecha_desde,
            'total_examenes': examenes.count(),
            'examenes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Estadísticas generales de exámenes de laboratorio
        
        Retorna:
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
        hace_una_semana = date.today() - timedelta(days=7)
        examenes_semana = ExamenLaboratorio.objects.filter(
            fecha_solicitud__gte=hace_una_semana
        ).count()
        
        # Último mes
        hace_un_mes = date.today() - timedelta(days=30)
        examenes_mes = ExamenLaboratorio.objects.filter(
            fecha_solicitud__gte=hace_un_mes
        ).count()
        
        # Exámenes con resultados anormales
        from django.db.models import Exists, OuterRef
        
        tiene_anormales = ResultadoLaboratorio.objects.filter(
            examen=OuterRef('pk'),
            es_normal=False
        )
        
        con_anormales = ExamenLaboratorio.objects.annotate(
            tiene_anormal=Exists(tiene_anormales)
        ).filter(tiene_anormal=True).count()
        
        # Exámenes con resultados críticos
        tiene_criticos = ResultadoLaboratorio.objects.filter(
            examen=OuterRef('pk'),
            es_critico=True
        )
        
        con_criticos = ExamenLaboratorio.objects.annotate(
            tiene_critico=Exists(tiene_criticos)
        ).filter(tiene_critico=True).count()
        
        return Response({
            'total_examenes': total,
            'examenes_ultima_semana': examenes_semana,
            'examenes_ultimo_mes': examenes_mes,
            'por_estado': por_estado,
            'por_prioridad': por_prioridad,
            'con_resultados_anormales': con_anormales,
            'con_resultados_criticos': con_criticos,
        })
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambiar el estado de un examen
        
        Body requerido:
        {
            "estado": "completado|en_proceso|cancelado"
        }
        """
        examen = self.get_object()
        nuevo_estado = request.data.get('estado', None)
        
        if not nuevo_estado:
            return Response(
                {'error': 'Debe proporcionar el nuevo estado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar estado
        estados_validos = [e[0] for e in ExamenLaboratorio.ESTADO_CHOICES]
        if nuevo_estado not in estados_validos:
            return Response(
                {
                    'error': 'Estado no válido',
                    'estados_validos': estados_validos
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar estado
        examen.estado = nuevo_estado
        
        # Si se marca como completado, registrar fecha de resultado
        if nuevo_estado == 'completado' and not examen.fecha_resultado:
            from django.utils import timezone
            examen.fecha_resultado = timezone.now()
        
        examen.save()
        
        serializer = ExamenLaboratorioDetailSerializer(examen)
        return Response({
            'mensaje': f'Estado cambiado a {examen.get_estado_display()}',
            'examen': serializer.data
        })


class ResultadoLaboratorioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Resultados de Laboratorio
    
    Endpoints:
    - GET /api/laboratorio/resultados/ - Listar todos
    - POST /api/laboratorio/resultados/ - Crear resultado
    - GET /api/laboratorio/resultados/{id}/ - Ver detalle
    - PUT/PATCH /api/laboratorio/resultados/{id}/ - Actualizar
    - DELETE /api/laboratorio/resultados/{id}/ - Eliminar
    - GET /api/laboratorio/resultados/por-examen/?examen_id=X
    - GET /api/laboratorio/resultados/anormales/
    - GET /api/laboratorio/resultados/criticos/
    """
    
    queryset = ResultadoLaboratorio.objects.select_related(
        'examen',
        'examen__paciente',
        'examen__tipo_examen',
        'valor_referencia',
        'valor_referencia__tipo_examen'
    ).all().order_by('-fecha_registro')
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['examen', 'es_normal', 'es_critico']
    search_fields = ['valor_referencia__parametro', 'examen__paciente__nombre']
    ordering_fields = ['fecha_registro', 'es_normal', 'es_critico']
    
    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción"""
        if self.action in ['create', 'update', 'partial_update']:
            return ResultadoLaboratorioCreateUpdateSerializer
        return ResultadoLaboratorioSerializer
    
    @action(detail=False, methods=['get'], url_path='por-examen')
    def por_examen(self, request):
        """
        Obtener resultados de un examen específico
        
        Parámetros query requeridos:
        - examen_id: ID del examen
        
        Ejemplo: /api/laboratorio/resultados/por-examen/?examen_id=1
        """
        examen_id = request.query_params.get('examen_id', None)
        
        if not examen_id:
            return Response(
                {
                    'error': 'Parámetro requerido faltante',
                    'detalle': 'Debe proporcionar examen_id'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el examen exista
        try:
            examen = ExamenLaboratorio.objects.select_related(
                'paciente',
                'tipo_examen'
            ).get(id=examen_id)
        except ExamenLaboratorio.DoesNotExist:
            return Response(
                {
                    'error': 'Examen no encontrado',
                    'detalle': f'No existe un examen con ID {examen_id}'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener resultados
        resultados = self.queryset.filter(examen_id=examen_id).order_by('valor_referencia__parametro')
        serializer = self.get_serializer(resultados, many=True)
        
        # Resumen
        total = resultados.count()
        normales = resultados.filter(es_normal=True).count()
        anormales = resultados.filter(es_normal=False).count()
        criticos = resultados.filter(es_critico=True).count()
        
        return Response({
            'examen': {
                'id': examen.id,
                'paciente': examen.paciente.nombre_completo,
                'tipo_examen': examen.tipo_examen.nombre,
                'fecha_solicitud': examen.fecha_solicitud,
                'estado': examen.get_estado_display(),
            },
            'resumen': {
                'total_parametros': total,
                'normales': normales,
                'anormales': anormales,
                'criticos': criticos,
            },
            'resultados': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def anormales(self, request):
        """
        Listar resultados anormales
        
        Retorna todos los resultados que están fuera del rango normal
        """
        resultados = self.queryset.filter(es_normal=False).order_by('-fecha_registro')
        
        # Paginación
        page = self.paginate_queryset(resultados)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(resultados, many=True)
        
        return Response({
            'total_anormales': resultados.count(),
            'resultados': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def criticos(self, request):
        """
        Listar resultados críticos
        
        Retorna todos los resultados que están en rango crítico
        """
        resultados = self.queryset.filter(es_critico=True).order_by('-fecha_registro')
        
        # Paginación
        page = self.paginate_queryset(resultados)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(resultados, many=True)
        
        return Response({
            'total_criticos': resultados.count(),
            'resultados': serializer.data
        })