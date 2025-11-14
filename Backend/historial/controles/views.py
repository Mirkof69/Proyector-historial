from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Max, Min
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta, date
from .models import ControlPrenatal
from .serializers import (
    ControlPrenatalSerializer,
    ControlPrenatalListSerializer,
    ControlPrenatalCreateUpdateSerializer
)
from embarazos.models import Embarazo


class ControlPrenatalViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de Controles Prenatales
    
    Endpoints disponibles:
    - GET /api/controles/ - Listar todos los controles
    - POST /api/controles/ - Crear nuevo control
    - GET /api/controles/{id}/ - Obtener detalle de control
    - PUT /api/controles/{id}/ - Actualizar control completo
    - PATCH /api/controles/{id}/ - Actualizar control parcial
    - DELETE /api/controles/{id}/ - Eliminar control
    - GET /api/controles/por_embarazo/?embarazo_id=X - Controles de un embarazo
    - GET /api/controles/estadisticas/ - Estadísticas generales
    - GET /api/controles/alertas/ - Controles con valores anormales
    - GET /api/controles/recientes/ - Últimos controles realizados
    - GET /api/controles/proximos/ - Próximos controles programados
    - GET /api/controles/evolucion/?embarazo_id=X - Evolución de parámetros
    """
    
    queryset = ControlPrenatal.objects.select_related(
        'embarazo_id',
        'embarazo_id__paciente',
        'paciente',
        'medico_id'  # ✅ AGREGADO: Optimización para evitar N+1 queries
    ).all().order_by('-fecha_control')
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # ✅ CORRECCIÓN: Usar nombres correctos de campos del modelo
    filterset_fields = ['embarazo_id', 'semanas_gestacion', 'edema', 'proteinuria', 'numero_control']
    
    search_fields = [
        'embarazo_id__paciente__nombre',
        'embarazo_id__paciente__apellido_paterno',
        'embarazo_id__paciente__id_clinico',
        'paciente__nombre',
        'paciente__apellido_paterno',
        'observaciones',
    ]
    
    ordering_fields = ['fecha_control', 'semanas_gestacion', 'peso_actual', 'numero_control']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return ControlPrenatalListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ControlPrenatalCreateUpdateSerializer
        return ControlPrenatalSerializer
    
    def get_queryset(self):
        """Filtra el queryset según parámetros avanzados"""
        queryset = super().get_queryset()
        
        # Filtrar por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
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
        
        # Filtrar por semanas de gestación
        semanas_min = self.request.query_params.get('semanas_min', None)
        semanas_max = self.request.query_params.get('semanas_max', None)
        
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
        
        # Filtrar por alertas (valores anormales)
        con_alertas = self.request.query_params.get('con_alertas', None)
        if con_alertas == 'true':
            queryset = queryset.filter(
                Q(presion_arterial_sistolica__gte=140) |
                Q(presion_arterial_diastolica__gte=90) |
                Q(frecuencia_cardiaca_fetal__lt=110) |
                Q(frecuencia_cardiaca_fetal__gt=160) |
                Q(edema__in=['severo', 'generalizado']) |
                ~Q(proteinuria='negativa')  # ✅ CORRECCIÓN: 'negativa' en lugar de 'negativo'
            )
        
        # Filtrar solo embarazos activos
        solo_activos = self.request.query_params.get('solo_activos', None)
        if solo_activos == 'true':
            queryset = queryset.filter(embarazo_id__estado='activo')
        
        # ✅ NUEVO: Filtrar por paciente
        paciente_id = self.request.query_params.get('paciente_id', None)
        if paciente_id:
            try:
                queryset = queryset.filter(paciente__id=int(paciente_id))
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo control prenatal con validaciones"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retornar con serializer completo
        control = ControlPrenatal.objects.select_related(
            'embarazo_id',
            'embarazo_id__paciente',
            'paciente',
            'medico_id'
        ).get(id=serializer.instance.id)
        
        return_serializer = ControlPrenatalSerializer(control)
        
        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        """Actualizar control prenatal"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Recargar con relaciones
        control = ControlPrenatal.objects.select_related(
            'embarazo_id',
            'embarazo_id__paciente',
            'paciente',
            'medico_id'
        ).get(id=instance.id)
        
        return_serializer = ControlPrenatalSerializer(control)
        return Response(return_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar control (hard delete permitido)"""
        instance = self.get_object()
        control_id = instance.id
        embarazo_id = instance.embarazo_id.id if instance.embarazo_id else None
        numero_control = instance.numero_control
        
        self.perform_destroy(instance)
        
        return Response(
            {
                'message': 'Control prenatal eliminado correctamente',
                'control_id': control_id,
                'numero_control': numero_control,
                'embarazo_id': embarazo_id
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='por_embarazo')
    def por_embarazo(self, request):
        """Obtener todos los controles de un embarazo específico"""
        embarazo_id = request.query_params.get('embarazo_id', None)
        
        if not embarazo_id:
            return Response(
                {'error': 'Debe proporcionar el parámetro embarazo_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            embarazo = Embarazo.objects.select_related('paciente').get(id=embarazo_id)
        except Embarazo.DoesNotExist:
            return Response(
                {'error': 'Embarazo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        controles = self.queryset.filter(embarazo_id=embarazo).order_by('fecha_control')
        serializer = ControlPrenatalSerializer(controles, many=True)
        
        # ✅ CORRECCIÓN: Importar serializer solo cuando se necesita
        from embarazos.serializers import EmbarazoSerializer
        
        return Response({
            'embarazo': EmbarazoSerializer(embarazo).data,
            'controles': serializer.data,
            'total_controles': controles.count(),
            'primer_control': controles.first().fecha_control if controles.exists() else None,
            'ultimo_control': controles.last().fecha_control if controles.exists() else None
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de controles prenatales"""
        total = ControlPrenatal.objects.count()
        
        # Estadísticas de la última semana
        hace_una_semana = date.today() - timedelta(days=7)
        controles_semana = ControlPrenatal.objects.filter(
            fecha_control__gte=hace_una_semana
        ).count()
        
        # Estadísticas del último mes
        hace_un_mes = date.today() - timedelta(days=30)
        controles_mes = ControlPrenatal.objects.filter(
            fecha_control__gte=hace_un_mes
        ).count()
        
        # Promedios generales
        promedios = ControlPrenatal.objects.aggregate(
            peso_promedio=Avg('peso_actual'),
            altura_uterina_promedio=Avg('altura_uterina'),
            pa_sistolica_promedio=Avg('presion_arterial_sistolica'),
            pa_diastolica_promedio=Avg('presion_arterial_diastolica'),
            fcf_promedio=Avg('frecuencia_cardiaca_fetal'),
            fcm_promedio=Avg('frecuencia_cardiaca')
        )
        
        # Controles con alertas
        con_hipertension = ControlPrenatal.objects.filter(
            Q(presion_arterial_sistolica__gte=140) |
            Q(presion_arterial_diastolica__gte=90)
        ).count()
        
        con_fcf_anormal = ControlPrenatal.objects.filter(
            Q(frecuencia_cardiaca_fetal__lt=110) |
            Q(frecuencia_cardiaca_fetal__gt=160)
        ).count()
        
        # ✅ CORRECCIÓN: 'negativa' en lugar de 'negativo'
        con_proteinuria = ControlPrenatal.objects.exclude(
            Q(proteinuria='negativa') | Q(proteinuria__isnull=True)
        ).count()
        
        con_edema = ControlPrenatal.objects.filter(
            edema__in=['generalizado', 'severo']
        ).count()
        
        # Distribución por trimestre
        por_trimestre = {
            'primer_trimestre': ControlPrenatal.objects.filter(semanas_gestacion__lte=13).count(),
            'segundo_trimestre': ControlPrenatal.objects.filter(
                semanas_gestacion__gt=13,
                semanas_gestacion__lte=27
            ).count(),
            'tercer_trimestre': ControlPrenatal.objects.filter(semanas_gestacion__gt=27).count(),
        }
        
        # ✅ NUEVO: Número de embarazos únicos con controles
        embarazos_con_controles = ControlPrenatal.objects.values('embarazo_id').distinct().count()
        
        return Response({
            'total_controles': total,
            'controles_ultima_semana': controles_semana,
            'controles_ultimo_mes': controles_mes,
            'embarazos_con_controles': embarazos_con_controles,
            'promedios': promedios,
            'alertas': {
                'con_hipertension': con_hipertension,
                'con_fcf_anormal': con_fcf_anormal,
                'con_proteinuria': con_proteinuria,
                'con_edema_severo': con_edema,
                'total_con_alertas': con_hipertension + con_fcf_anormal + con_proteinuria + con_edema
            },
            'distribucion_trimestres': por_trimestre
        })
    
    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """Listar controles con valores anormales"""
        controles_alerta = self.queryset.filter(
            Q(presion_arterial_sistolica__gte=140) |
            Q(presion_arterial_diastolica__gte=90) |
            Q(frecuencia_cardiaca_fetal__lt=110) |
            Q(frecuencia_cardiaca_fetal__gt=160) |
            Q(edema__in=['severo', 'generalizado']) |
            ~Q(proteinuria='negativa')  # ✅ CORRECCIÓN
        ).order_by('-fecha_control')
        
        page = self.paginate_queryset(controles_alerta)
        if page is not None:
            serializer = ControlPrenatalSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ControlPrenatalSerializer(controles_alerta, many=True)
        return Response({
            'total_alertas': controles_alerta.count(),
            'controles': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        """Últimos controles realizados"""
        dias = int(request.query_params.get('dias', 7))
        fecha_desde = date.today() - timedelta(days=dias)
        
        controles = self.queryset.filter(
            fecha_control__gte=fecha_desde
        ).order_by('-fecha_control')
        
        page = self.paginate_queryset(controles)
        if page is not None:
            serializer = ControlPrenatalListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ControlPrenatalListSerializer(controles, many=True)
        return Response({
            'total': controles.count(),
            'dias': dias,
            'controles': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """
        Próximos controles programados
        NOTA: Este endpoint requiere un campo 'fecha_proximo_control' en el modelo
        Si no existe, este endpoint retornará los controles recientes
        """
        dias = int(request.query_params.get('dias', 30))
        fecha_hasta = date.today() + timedelta(days=dias)
        
        # ✅ CORRECCIÓN: Como no tienes campo 'proximo_control', 
        # retornamos controles que podrían necesitar seguimiento
        controles = self.queryset.filter(
            embarazo_id__estado='activo'
        ).order_by('-fecha_control')
        
        # Agrupar por embarazo y obtener el último control de cada uno
        embarazos_unicos = {}
        for control in controles:
            if control.embarazo_id.id not in embarazos_unicos:
                embarazos_unicos[control.embarazo_id.id] = control
        
        controles_filtrados = list(embarazos_unicos.values())[:20]
        
        serializer = ControlPrenatalListSerializer(controles_filtrados, many=True)
        return Response({
            'total': len(controles_filtrados),
            'mensaje': 'Últimos controles de embarazos activos que podrían requerir seguimiento',
            'controles': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def evolucion(self, request):
        """Gráfica de evolución de parámetros de un embarazo"""
        embarazo_id = request.query_params.get('embarazo_id', None)
        
        if not embarazo_id:
            return Response(
                {'error': 'Debe proporcionar el parámetro embarazo_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            embarazo = Embarazo.objects.select_related('paciente').get(id=embarazo_id)
        except Embarazo.DoesNotExist:
            return Response(
                {'error': 'Embarazo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        controles = self.queryset.filter(embarazo_id=embarazo).order_by('fecha_control')
        
        if not controles.exists():
            return Response({
                'embarazo_id': embarazo.id,
                'paciente': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
                'total_controles': 0,
                'mensaje': 'No hay controles registrados para este embarazo',
                'evolucion': {}
            })
        
        # Preparar datos para gráficas
        evolucion_data = {
            'fechas': [],
            'semanas': [],
            'peso': [],
            'altura_uterina': [],
            'presion_sistolica': [],
            'presion_diastolica': [],
            'fcf': [],
            'imc': [],
        }
        
        for control in controles:
            evolucion_data['fechas'].append(control.fecha_control.strftime('%Y-%m-%d'))
            evolucion_data['semanas'].append(control.semanas_gestacion)
            evolucion_data['peso'].append(float(control.peso_actual) if control.peso_actual else None)
            evolucion_data['altura_uterina'].append(float(control.altura_uterina) if control.altura_uterina else None)
            evolucion_data['presion_sistolica'].append(control.presion_arterial_sistolica)
            evolucion_data['presion_diastolica'].append(control.presion_arterial_diastolica)
            evolucion_data['fcf'].append(control.frecuencia_cardiaca_fetal)
            evolucion_data['imc'].append(control.imc)
        
        return Response({
            'embarazo_id': embarazo.id,
            'paciente': f"{embarazo.paciente.nombre} {embarazo.paciente.apellido_paterno}",
            'total_controles': controles.count(),
            'primer_control': controles.first().fecha_control.strftime('%Y-%m-%d'),
            'ultimo_control': controles.last().fecha_control.strftime('%Y-%m-%d'),
            'evolucion': evolucion_data
        })
    
    @action(detail=True, methods=['get'])
    def reporte_completo(self, request, pk=None):
        """Generar reporte completo de un control prenatal"""
        control = self.get_object()
        reporte = control.generar_reporte_completo()
        
        return Response(reporte)