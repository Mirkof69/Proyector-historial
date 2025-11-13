from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Parto, RecienNacido, PartogramaRegistro
from .serializers import PartoSerializer, RecienNacidoSerializer, PartogramaRegistroSerializer
from datetime import datetime, timedelta
from django.utils import timezone


class PartoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar partos
    """
    queryset = Parto.objects.all()
    serializer_class = PartoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Campos para filtrar
    filterset_fields = [
        'tipo_parto',
        'presentacion_fetal',
        'parto_finalizado',
        'hemorragia_postparto',
        'episiotomia',
        'analgesia_utilizada',
        'paciente_id',
        'medico_responsable_id',
    ]
    
    # Campos para búsqueda
    search_fields = [
        'numero_parto',
        'observaciones_parto',
        'complicaciones_maternas',
        'edad_gestacional_parto',
    ]
    
    # Campos para ordenamiento
    ordering_fields = [
        'fecha_parto',
        'fecha_ingreso',
        'numero_parto',
        'tipo_parto',
    ]
    
    ordering = ['-fecha_parto']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por rango de fechas
        fecha_inicio = self.request.query_params.get('fecha_inicio')
        fecha_fin = self.request.query_params.get('fecha_fin')
        
        if fecha_inicio:
            queryset = queryset.filter(fecha_parto__gte=fecha_inicio)
        
        if fecha_fin:
            queryset = queryset.filter(fecha_parto__lte=fecha_fin)
        
        # Filtro por estado del parto
        estado = self.request.query_params.get('estado')
        if estado == 'finalizados':
            queryset = queryset.filter(parto_finalizado=True)
        elif estado == 'en_proceso':
            queryset = queryset.filter(parto_finalizado=False)
        
        # Filtro por complicaciones
        con_complicaciones = self.request.query_params.get('con_complicaciones')
        if con_complicaciones == 'true':
            queryset = queryset.filter(
                Q(hemorragia_postparto=True) |
                Q(desgarros=True) |
                Q(complicaciones_maternas__isnull=False)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def finalizar_parto(self, request, pk=None):
        """Marca un parto como finalizado"""
        parto = self.get_object()
        parto.parto_finalizado = True
        parto.fecha_parto = timezone.now()
        parto.save()
        
        return Response({
            'message': 'Parto finalizado exitosamente',
            'numero_parto': parto.numero_parto,
            'estado': parto.get_estado_parto()
        })
    
    @action(detail=True, methods=['get'])
    def resumen_completo(self, request, pk=None):
        """Obtiene un resumen completo del parto"""
        parto = self.get_object()
        
        # Obtener recién nacidos
        recien_nacidos = parto.recien_nacidos.all()
        
        # Obtener registros de partograma
        partograma = parto.partograma.all().order_by('hora_registro')
        
        data = {
            'parto': PartoSerializer(parto).data,
            'resumen_parto': parto.get_resumen_parto(),
            'evaluacion_perdida_sanguinea': parto.get_evaluacion_perdida_sanguinea(),
            'complicaciones': parto.get_complicaciones_totales(),
            'recien_nacidos': RecienNacidoSerializer(recien_nacidos, many=True).data,
            'partograma': PartogramaRegistroSerializer(partograma, many=True).data,
            'estadisticas': {
                'total_recien_nacidos': recien_nacidos.count(),
                'duracion_trabajo_parto': parto.get_duracion_trabajo_parto_horas(),
                'registros_partograma': partograma.count(),
            }
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de partos"""
        queryset = self.get_queryset()
        
        # Estadísticas básicas
        total_partos = queryset.count()
        partos_finalizados = queryset.filter(parto_finalizado=True).count()
        partos_en_proceso = total_partos - partos_finalizados
        
        # Estadísticas por tipo de parto
        tipos_parto = queryset.values('tipo_parto').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Estadísticas de complicaciones
        con_hemorragia = queryset.filter(hemorragia_postparto=True).count()
        con_desgarros = queryset.filter(desgarros=True).count()
        con_episiotomia = queryset.filter(episiotomia=True).count()
        
        # Promedios
        duracion_promedio = queryset.filter(
            duracion_trabajo_parto_horas__isnull=False
        ).aggregate(Avg('duracion_trabajo_parto_horas'))['duracion_trabajo_parto_horas__avg']
        
        perdida_promedio = queryset.filter(
            perdida_sanguinea_estimada__isnull=False
        ).aggregate(Avg('perdida_sanguinea_estimada'))['perdida_sanguinea_estimada__avg']
        
        data = {
            'resumen': {
                'total_partos': total_partos,
                'partos_finalizados': partos_finalizados,
                'partos_en_proceso': partos_en_proceso,
                'porcentaje_finalizados': round((partos_finalizados / total_partos * 100), 2) if total_partos > 0 else 0,
            },
            'tipos_parto': tipos_parto,
            'complicaciones': {
                'hemorragia_postparto': con_hemorragia,
                'desgarros': con_desgarros,
                'episiotomia': con_episiotomia,
                'porcentaje_complicaciones': round(((con_hemorragia + con_desgarros) / total_partos * 100), 2) if total_partos > 0 else 0,
            },
            'promedios': {
                'duracion_trabajo_parto_horas': round(duracion_promedio, 2) if duracion_promedio else 0,
                'perdida_sanguinea_ml': round(perdida_promedio, 2) if perdida_promedio else 0,
            }
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def partos_hoy(self, request):
        """Partos de hoy"""
        hoy = timezone.now().date()
        partos_hoy = self.get_queryset().filter(fecha_parto__date=hoy)
        
        serializer = self.get_serializer(partos_hoy, many=True)
        return Response({
            'fecha': hoy,
            'total': partos_hoy.count(),
            'partos': serializer.data
        })


class RecienNacidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar recién nacidos
    """
    queryset = RecienNacido.objects.all()
    serializer_class = RecienNacidoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'sexo',
        'estado_nacimiento',
        'requirio_reanimacion',
        'malformaciones_congenitas',
        'destino_rn',
        'parto',
    ]
    
    search_fields = [
        'parto__numero_parto',
        'observaciones_rn',
        'descripcion_malformaciones',
    ]
    
    ordering_fields = [
        'fecha_nacimiento',
        'peso_nacimiento',
        'apgar_5_minutos',
    ]
    
    ordering = ['-fecha_nacimiento']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por peso
        peso_min = self.request.query_params.get('peso_min')
        peso_max = self.request.query_params.get('peso_max')
        
        if peso_min:
            queryset = queryset.filter(peso_nacimiento__gte=peso_min)
        
        if peso_max:
            queryset = queryset.filter(peso_nacimiento__lte=peso_max)
        
        # Filtro por Apgar
        apgar_min = self.request.query_params.get('apgar_min')
        if apgar_min:
            queryset = queryset.filter(apgar_5_minutos__gte=apgar_min)
        
        # Filtro por rango de fechas
        fecha_inicio = self.request.query_params.get('fecha_inicio')
        fecha_fin = self.request.query_params.get('fecha_fin')
        
        if fecha_inicio:
            queryset = queryset.filter(fecha_nacimiento__gte=fecha_inicio)
        
        if fecha_fin:
            queryset = queryset.filter(fecha_nacimiento__lte=fecha_fin)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def resumen_completo(self, request, pk=None):
        """Resumen completo del recién nacido"""
        rn = self.get_object()
        
        data = {
            'recien_nacido': RecienNacidoSerializer(rn).data,
            'clasificacion_peso': rn.get_clasificacion_peso(),
            'evaluacion_apgar': rn.get_evaluacion_apgar(),
            'evaluacion_estado_general': rn.get_evaluacion_estado_general(),
            'resumen_completo': rn.get_resumen_completo(),
            'parto_relacionado': {
                'numero_parto': rn.parto.numero_parto,
                'tipo_parto': rn.parto.get_tipo_parto_display(),
                'fecha_parto': rn.parto.fecha_parto,
            }
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de recién nacidos"""
        queryset = self.get_queryset()
        
        total_rn = queryset.count()
        
        # Estadísticas por sexo
        por_sexo = queryset.values('sexo').annotate(count=Count('id'))
        
        # Estadísticas por peso
        bajo_peso = queryset.filter(peso_nacimiento__lt=2500).count()
        peso_normal = queryset.filter(peso_nacimiento__gte=2500, peso_nacimiento__lte=4000).count()
        macrosomia = queryset.filter(peso_nacimiento__gt=4000).count()
        
        # Estadísticas de Apgar
        apgar_bajo = queryset.filter(apgar_5_minutos__lt=7).count()
        apgar_normal = queryset.filter(apgar_5_minutos__gte=7).count()
        
        # Reanimación
        requirio_reanimacion = queryset.filter(requirio_reanimacion=True).count()
        
        # Malformaciones
        con_malformaciones = queryset.filter(malformaciones_congenitas=True).count()
        
        # Promedios
        peso_promedio = queryset.aggregate(Avg('peso_nacimiento'))['peso_nacimiento__avg']
        talla_promedio = queryset.aggregate(Avg('talla_nacimiento'))['talla_nacimiento__avg']
        apgar_promedio = queryset.aggregate(Avg('apgar_5_minutos'))['apgar_5_minutos__avg']
        
        data = {
            'resumen': {
                'total_recien_nacidos': total_rn,
                'por_sexo': por_sexo,
            },
            'clasificacion_peso': {
                'bajo_peso': bajo_peso,
                'peso_normal': peso_normal,
                'macrosomia': macrosomia,
                'porcentaje_bajo_peso': round((bajo_peso / total_rn * 100), 2) if total_rn > 0 else 0,
            },
            'apgar': {
                'apgar_bajo': apgar_bajo,
                'apgar_normal': apgar_normal,
                'porcentaje_apgar_bajo': round((apgar_bajo / total_rn * 100), 2) if total_rn > 0 else 0,
            },
            'complicaciones': {
                'requirio_reanimacion': requirio_reanimacion,
                'con_malformaciones': con_malformaciones,
                'porcentaje_reanimacion': round((requirio_reanimacion / total_rn * 100), 2) if total_rn > 0 else 0,
            },
            'promedios': {
                'peso_gramos': round(peso_promedio, 0) if peso_promedio else 0,
                'talla_cm': round(talla_promedio, 1) if talla_promedio else 0,
                'apgar_5_min': round(apgar_promedio, 1) if apgar_promedio else 0,
            }
        }
        
        return Response(data)


class PartogramaRegistroViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar registros de partograma
    """
    queryset = PartogramaRegistro.objects.all()
    serializer_class = PartogramaRegistroSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'parto',
        'alerta_fcf_anormal',
        'alerta_progreso_lento',
        'alerta_signos_vitales',
        'intensidad_contracciones',
        'variabilidad_fcf',
    ]
    
    search_fields = [
        'parto__numero_parto',
        'observaciones',
    ]
    
    ordering_fields = [
        'hora_registro',
        'horas_trabajo_parto',
        'dilatacion_cervical',
        'fcf_baseline',
    ]
    
    ordering = ['hora_registro']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por parto específico
        parto_id = self.request.query_params.get('parto_id')
        if parto_id:
            queryset = queryset.filter(parto_id=parto_id)
        
        # Filtro por rango de dilatación
        dilatacion_min = self.request.query_params.get('dilatacion_min')
        dilatacion_max = self.request.query_params.get('dilatacion_max')
        
        if dilatacion_min:
            queryset = queryset.filter(dilatacion_cervical__gte=dilatacion_min)
        
        if dilatacion_max:
            queryset = queryset.filter(dilatacion_cervical__lte=dilatacion_max)
        
        # Filtro solo con alertas
        solo_alertas = self.request.query_params.get('solo_alertas')
        if solo_alertas == 'true':
            queryset = queryset.filter(
                Q(alerta_fcf_anormal=True) |
                Q(alerta_progreso_lento=True) |
                Q(alerta_signos_vitales=True)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        # Asignar el usuario que registra
        serializer.save(registrado_por_id=self.request.user.id if self.request.user.is_authenticated else None)
    
    @action(detail=False, methods=['get'])
    def por_parto(self, request):
        """Obtiene todos los registros de un parto específico"""
        parto_id = request.query_params.get('parto_id')
        if not parto_id:
            return Response({'error': 'parto_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        parto = get_object_or_404(Parto, id=parto_id)
        registros = self.get_queryset().filter(parto=parto).order_by('hora_registro')
        
        serializer = self.get_serializer(registros, many=True)
        
        # Agregar información del parto
        data = {
            'parto': {
                'numero_parto': parto.numero_parto,
                'fecha_inicio': parto.fecha_inicio_trabajo_parto,
                'estado': parto.get_estado_parto(),
            },
            'total_registros': registros.count(),
            'registros': serializer.data,
            'ultima_dilatacion': registros.last().dilatacion_cervical if registros.exists() else 0,
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def alertas_activas(self, request):
        """Obtiene todos los registros con alertas activas"""
        registros_con_alertas = self.get_queryset().filter(
            Q(alerta_fcf_anormal=True) |
            Q(alerta_progreso_lento=True) |
            Q(alerta_signos_vitales=True)
        ).order_by('-hora_registro')
        
        serializer = self.get_serializer(registros_con_alertas, many=True)
        
        data = {
            'total_alertas': registros_con_alertas.count(),
            'registros_con_alertas': serializer.data,
        }
        
        return Response(data)