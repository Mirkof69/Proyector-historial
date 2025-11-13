from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    ScoreBishop, RiesgoPreeclampsia, CrecimientoFetal,
    RiesgoCromosomico, DosisMedicamentos, HemorragiaObstetrica,
    SufrimientoFetal
)
from .serializers import (
    ScoreBishopSerializer, RiesgoPreeclampsiaSerializer, CrecimientoFetalSerializer,
    RiesgoCromosomicoSerializer, DosisMedicamentosSerializer, HemorragiaObstetricaSerializer,
    SufrimientoFetalSerializer, ScoreBishopResumenSerializer, RiesgoPreeclampsiaResumenSerializer,
    CrecimientoFetalResumenSerializer
)
from datetime import datetime, timedelta
from django.utils import timezone


class ScoreBishopViewSet(viewsets.ModelViewSet):
    """ViewSet para Score de Bishop"""
    
    queryset = ScoreBishop.objects.all()
    serializer_class = ScoreBishopSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'paciente_id',
        'embarazo_id',
        'score_total',
        'interpretacion',
        'consistencia_cervical',
        'posicion_cervical',
    ]
    
    search_fields = ['paciente_id', 'embarazo_id']
    ordering_fields = ['fecha_evaluacion', 'score_total', 'edad_gestacional_semanas']
    ordering = ['-fecha_evaluacion']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ScoreBishopResumenSerializer
        return ScoreBishopSerializer
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de Scores de Bishop"""
        queryset = self.get_queryset()
        
        total_evaluaciones = queryset.count()
        score_promedio = queryset.aggregate(Avg('score_total'))['score_total__avg']
        
        # Distribución por categorías
        inmaduro = queryset.filter(score_total__lte=5).count()
        moderado = queryset.filter(score_total__range=(6, 8)).count()
        maduro = queryset.filter(score_total__gte=9).count()
        
        # Evaluaciones recientes
        hace_una_semana = timezone.now() - timedelta(days=7)
        evaluaciones_recientes = queryset.filter(fecha_evaluacion__gte=hace_una_semana).count()
        
        return Response({
            'resumen': {
                'total_evaluaciones': total_evaluaciones,
                'score_promedio': round(score_promedio, 1) if score_promedio else 0,
                'evaluaciones_ultima_semana': evaluaciones_recientes,
            },
            'distribucion': {
                'cervix_inmaduro': inmaduro,
                'cervix_moderado': moderado,
                'cervix_maduro': maduro,
            },
            'porcentajes': {
                'inmaduro_pct': round((inmaduro / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
                'moderado_pct': round((moderado / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
                'maduro_pct': round((maduro / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
            }
        })
    
    @action(detail=False, methods=['post'])
    def calcular_score(self, request):
        """Calculadora independiente de Score de Bishop"""
        data = request.data
        
        try:
            # Crear instancia temporal para cálculo
            score_temp = ScoreBishop(
                dilatacion_cervical=data.get('dilatacion_cervical', 0),
                borramiento_cervical=data.get('borramiento_cervical', 0),
                consistencia_cervical=data.get('consistencia_cervical', 'dura'),
                posicion_cervical=data.get('posicion_cervical', 'posterior'),
                estacion_fetal=data.get('estacion_fetal', '-3'),
            )
            
            score_temp.calcular_score()
            
            return Response({
                'score_total': score_temp.score_total,
                'interpretacion': score_temp.interpretacion,
                'probabilidad_parto_espontaneo': score_temp.probabilidad_parto_espontaneo,
                'recomendacion': score_temp.get_recomendacion_clinica(),
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def por_paciente(self, request):
        """Scores por paciente específico"""
        paciente_id = request.query_params.get('paciente_id')
        if not paciente_id:
            return Response({'error': 'paciente_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        scores = self.get_queryset().filter(paciente_id=paciente_id).order_by('-fecha_evaluacion')
        serializer = ScoreBishopResumenSerializer(scores, many=True)
        
        return Response({
            'paciente_id': paciente_id,
            'total_evaluaciones': scores.count(),
            'evaluaciones': serializer.data
        })


class RiesgoPreeclampsiaViewSet(viewsets.ModelViewSet):
    """ViewSet para Riesgo de Preeclampsia"""
    
    queryset = RiesgoPreeclampsia.objects.all()
    serializer_class = RiesgoPreeclampsiaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'paciente_id',
        'clasificacion_riesgo',
        'hipertension_cronica',
        'diabetes_tipo1',
        'diabetes_tipo2',
        'antecedente_preeclampsia',
        'embarazo_multiple',
        'raza',
    ]
    
    search_fields = ['paciente_id', 'embarazo_id']
    ordering_fields = ['fecha_evaluacion', 'riesgo_porcentaje', 'edad_materna']
    ordering = ['-fecha_evaluacion']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RiesgoPreeclampsiaResumenSerializer
        return RiesgoPreeclampsiaSerializer
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de Riesgo de Preeclampsia"""
        queryset = self.get_queryset()
        
        total_evaluaciones = queryset.count()
        riesgo_promedio = queryset.aggregate(Avg('riesgo_porcentaje'))['riesgo_porcentaje__avg']
        
        # Clasificación por riesgo
        alto_riesgo = queryset.filter(clasificacion_riesgo='Alto Riesgo').count()
        riesgo_intermedio = queryset.filter(clasificacion_riesgo='Riesgo Intermedio').count()
        bajo_riesgo = queryset.filter(clasificacion_riesgo='Bajo Riesgo').count()
        
        # Factores de riesgo más comunes
        factores = {
            'hipertension_cronica': queryset.filter(hipertension_cronica=True).count(),
            'diabetes': queryset.filter(Q(diabetes_tipo1=True) | Q(diabetes_tipo2=True)).count(),
            'antecedente_preeclampsia': queryset.filter(antecedente_preeclampsia=True).count(),
            'embarazo_multiple': queryset.filter(embarazo_multiple=True).count(),
            'edad_avanzada': queryset.filter(edad_materna__gte=35).count(),
        }
        
        return Response({
            'resumen': {
                'total_evaluaciones': total_evaluaciones,
                'riesgo_promedio': round(riesgo_promedio, 2) if riesgo_promedio else 0,
            },
            'clasificacion': {
                'alto_riesgo': alto_riesgo,
                'riesgo_intermedio': riesgo_intermedio,
                'bajo_riesgo': bajo_riesgo,
            },
            'factores_riesgo': factores,
            'porcentajes': {
                'alto_riesgo_pct': round((alto_riesgo / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
            }
        })
    
    @action(detail=False, methods=['get'])
    def alto_riesgo(self, request):
        """Pacientes con alto riesgo de preeclampsia"""
        alto_riesgo = self.get_queryset().filter(clasificacion_riesgo='Alto Riesgo')
        serializer = RiesgoPreeclampsiaResumenSerializer(alto_riesgo, many=True)
        
        return Response({
            'total_alto_riesgo': alto_riesgo.count(),
            'pacientes': serializer.data
        })


class CrecimientoFetalViewSet(viewsets.ModelViewSet):
    """ViewSet para Crecimiento Fetal"""
    
    queryset = CrecimientoFetal.objects.all()
    serializer_class = CrecimientoFetalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'paciente_id',
        'embarazo_id',
        'clasificacion_peso',
        'restriccion_crecimiento',
        'macrosomia',
    ]
    
    search_fields = ['paciente_id', 'embarazo_id', 'ecografia_id']
    ordering_fields = ['fecha_evaluacion', 'edad_gestacional_semanas', 'peso_fetal_estimado']
    ordering = ['-fecha_evaluacion']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CrecimientoFetalResumenSerializer
        return CrecimientoFetalSerializer
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de Crecimiento Fetal"""
        queryset = self.get_queryset()
        
        total_evaluaciones = queryset.count()
        peso_promedio = queryset.aggregate(Avg('peso_fetal_estimado'))['peso_fetal_estimado__avg']
        
        # Clasificaciones
        peg = queryset.filter(restriccion_crecimiento=True).count()  # Pequeño para EG
        aeg = queryset.filter(restriccion_crecimiento=False, macrosomia=False).count()  # Adecuado
        geg = queryset.filter(macrosomia=True).count()  # Grande para EG
        
        # Por trimestre
        segundo_trimestre = queryset.filter(edad_gestacional_semanas__lt=28).count()
        tercer_trimestre = queryset.filter(edad_gestacional_semanas__gte=28).count()
        
        return Response({
            'resumen': {
                'total_evaluaciones': total_evaluaciones,
                'peso_promedio': round(peso_promedio, 0) if peso_promedio else 0,
            },
            'clasificacion_peso': {
                'pequeno_para_eg': peg,
                'adecuado_para_eg': aeg,
                'grande_para_eg': geg,
            },
            'por_trimestre': {
                'segundo_trimestre': segundo_trimestre,
                'tercer_trimestre': tercer_trimestre,
            },
            'porcentajes': {
                'restriccion_crecimiento_pct': round((peg / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
                'macrosomia_pct': round((geg / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
            }
        })
    
    @action(detail=True, methods=['get'])
    def seguimiento_crecimiento(self, request, pk=None):
        """Seguimiento del crecimiento para un paciente específico"""
        evaluacion = self.get_object()
        
        # Obtener todas las evaluaciones del mismo paciente/embarazo
        evaluaciones_previas = CrecimientoFetal.objects.filter(
            paciente_id=evaluacion.paciente_id,
            embarazo_id=evaluacion.embarazo_id
        ).order_by('edad_gestacional_semanas')
        
        # Crear curva de crecimiento
        curva_peso = []
        for eval in evaluaciones_previas:
            if eval.peso_fetal_estimado:
                curva_peso.append({
                    'edad_gestacional': eval.edad_gestacional_semanas + (eval.edad_gestacional_dias or 0) / 7,
                    'peso': eval.peso_fetal_estimado,
                    'percentil': eval.percentil_peso,
                    'fecha': eval.fecha_evaluacion,
                })
        
        return Response({
            'paciente_id': evaluacion.paciente_id,
            'embarazo_id': evaluacion.embarazo_id,
            'total_evaluaciones': evaluaciones_previas.count(),
            'curva_crecimiento': curva_peso,
            'evaluacion_actual': CrecimientoFetalSerializer(evaluacion).data,
        })


class RiesgoCromosomicoViewSet(viewsets.ModelViewSet):
    """ViewSet para Riesgo Cromosómico"""
    
    queryset = RiesgoCromosomico.objects.all()
    serializer_class = RiesgoCromosomicoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'paciente_id',
        'clasificacion_down',
        'hueso_nasal_presente',
    ]
    
    search_fields = ['paciente_id', 'embarazo_id']
    ordering_fields = ['fecha_evaluacion', 'edad_materna', 'translucencia_nucal']
    ordering = ['-fecha_evaluacion']
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de Screening Cromosómico"""
        queryset = self.get_queryset()
        
        total_evaluaciones = queryset.count()
        
        # Clasificación por riesgo
        alto_riesgo = queryset.filter(clasificacion_down='alto').count()
        riesgo_intermedio = queryset.filter(clasificacion_down='intermedio').count()
        bajo_riesgo = queryset.filter(clasificacion_down='bajo').count()
        
        # Translucencia nucal promedio
        tn_promedio = queryset.aggregate(Avg('translucencia_nucal'))['translucencia_nucal__avg']
        
        # TN elevada (>3.5mm)
        tn_elevada = queryset.filter(translucencia_nucal__gt=3.5).count()
        
        return Response({
            'resumen': {
                'total_evaluaciones': total_evaluaciones,
                'tn_promedio': round(tn_promedio, 1) if tn_promedio else 0,
                'tn_elevada': tn_elevada,
            },
            'clasificacion_riesgo': {
                'alto_riesgo': alto_riesgo,
                'riesgo_intermedio': riesgo_intermedio,
                'bajo_riesgo': bajo_riesgo,
            },
            'porcentajes': {
                'alto_riesgo_pct': round((alto_riesgo / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
                'tn_elevada_pct': round((tn_elevada / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
            }
        })


class DosisMedicamentosViewSet(viewsets.ModelViewSet):
    """ViewSet para Dosis de Medicamentos"""
    
    queryset = DosisMedicamentos.objects.all()
    serializer_class = DosisMedicamentosSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'paciente_id',
        'medicamento',
        'indicacion',
    ]
    
    search_fields = ['paciente_id', 'embarazo_id', 'parto_id']
    ordering_fields = ['fecha_calculo', 'peso_materno']
    ordering = ['-fecha_calculo']
    
    @action(detail=False, methods=['get'])
    def por_medicamento(self, request):
        """Estadísticas por medicamento"""
        medicamento = request.query_params.get('medicamento')
        if not medicamento:
            return Response({'error': 'medicamento es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        calculos = self.get_queryset().filter(medicamento=medicamento)
        serializer = self.get_serializer(calculos, many=True)
        
        # Indicaciones más comunes
        indicaciones = calculos.values('indicacion').annotate(count=Count('id')).order_by('-count')
        
        return Response({
            'medicamento': medicamento,
            'total_calculos': calculos.count(),
            'indicaciones_frecuentes': indicaciones,
            'calculos': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def calcular_dosis(self, request):
        """Calculadora independiente de dosis"""
        data = request.data
        
        try:
            # Crear instancia temporal para cálculo
            dosis_temp = DosisMedicamentos(
                medicamento=data.get('medicamento'),
                indicacion=data.get('indicacion'),
                peso_materno=data.get('peso_materno'),
                edad_gestacional_semanas=data.get('edad_gestacional_semanas'),
                presion_arterial_sistolica=data.get('presion_arterial_sistolica'),
                presion_arterial_diastolica=data.get('presion_arterial_diastolica'),
            )
            
            dosis_temp.calcular_dosis()
            
            return Response({
                'medicamento': dosis_temp.get_medicamento_display(),
                'indicacion': dosis_temp.get_indicacion_display(),
                'protocolo': dosis_temp.get_protocolo_administracion(),
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HemorragiaObstetricaViewSet(viewsets.ModelViewSet):
    """ViewSet para Hemorragia Obstétrica"""
    
    queryset = HemorragiaObstetrica.objects.all()
    serializer_class = HemorragiaObstetricaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'paciente_id',
        'tipo_hemorragia',
        'causa_principal',
        'severidad_hemorragia',
        'requiere_transfusion',
        'hemorragia_controlada',
    ]
    
    search_fields = ['paciente_id', 'embarazo_id', 'parto_id']
    ordering_fields = ['fecha_evento', 'perdida_sanguinea_estimada']
    ordering = ['-fecha_evento']
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de Hemorragias Obstétricas"""
        queryset = self.get_queryset()
        
        total_hemorragias = queryset.count()
        perdida_promedio = queryset.aggregate(Avg('perdida_sanguinea_estimada'))['perdida_sanguinea_estimada__avg']
        
        # Por severidad
        leve = queryset.filter(severidad_hemorragia='Leve').count()
        moderada = queryset.filter(severidad_hemorragia='Moderada').count()
        severa = queryset.filter(severidad_hemorragia='Severa').count()
        masiva = queryset.filter(severidad_hemorragia='Masiva').count()
        
        # Causas principales
        causas = queryset.values('causa_principal').annotate(count=Count('id')).order_by('-count')[:5]
        
        # Resultados
        controladas = queryset.filter(hemorragia_controlada=True).count()
        requirieron_cirugia = queryset.filter(requirio_cirugia=True).count()
        requirieron_transfusion = queryset.filter(requiere_transfusion=True).count()
        
        return Response({
            'resumen': {
                'total_hemorragias': total_hemorragias,
                'perdida_promedio': round(perdida_promedio, 0) if perdida_promedio else 0,
            },
            'severidad': {
                'leve': leve,
                'moderada': moderada,
                'severa': severa,
                'masiva': masiva,
            },
            'causas_principales': causas,
            'resultados': {
                'controladas': controladas,
                'requirieron_cirugia': requirieron_cirugia,
                'requirieron_transfusion': requirieron_transfusion,
            },
            'porcentajes': {
                'control_pct': round((controladas / total_hemorragias * 100), 1) if total_hemorragias > 0 else 0,
                'cirugia_pct': round((requirieron_cirugia / total_hemorragias * 100), 1) if total_hemorragias > 0 else 0,
            }
        })
    
    @action(detail=False, methods=['get'])
    def casos_severos(self, request):
        """Casos severos y masivos"""
        casos_severos = self.get_queryset().filter(
            severidad_hemorragia__in=['Severa', 'Masiva']
        ).order_by('-fecha_evento')
        
        serializer = self.get_serializer(casos_severos, many=True)
        
        return Response({
            'total_casos_severos': casos_severos.count(),
            'casos': serializer.data
        })


class SufrimientoFetalViewSet(viewsets.ModelViewSet):
    """ViewSet para Sufrimiento Fetal"""
    
    queryset = SufrimientoFetal.objects.all()
    serializer_class = SufrimientoFetalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'paciente_id',
        'tipo_evaluacion',
        'tipo_monitoreo',
        'clasificacion_ctg',
        'riesgo_sufrimiento_fetal',
        'requiere_intervencion_inmediata',
    ]
    
    search_fields = ['paciente_id', 'embarazo_id', 'parto_id']
    ordering_fields = ['fecha_evaluacion', 'fcf_basal', 'score_fisher']
    ordering = ['-fecha_evaluacion']
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de Bienestar Fetal"""
        queryset = self.get_queryset()
        
        total_evaluaciones = queryset.count()
        
        # Por clasificación CTG
        categoria_1 = queryset.filter(clasificacion_ctg='categoria_1').count()
        categoria_2 = queryset.filter(clasificacion_ctg='categoria_2').count()
        categoria_3 = queryset.filter(clasificacion_ctg='categoria_3').count()
        
        # Por riesgo
        bajo_riesgo = queryset.filter(riesgo_sufrimiento_fetal='bajo').count()
        riesgo_intermedio = queryset.filter(riesgo_sufrimiento_fetal='intermedio').count()
        alto_riesgo = queryset.filter(riesgo_sufrimiento_fetal='alto').count()
        
        # Intervenciones inmediatas
        intervenciones = queryset.filter(requiere_intervencion_inmediata=True).count()
        
        # FCF promedio
        fcf_promedio = queryset.aggregate(Avg('fcf_basal'))['fcf_basal__avg']
        
        return Response({
            'resumen': {
                'total_evaluaciones': total_evaluaciones,
                'fcf_promedio': round(fcf_promedio, 0) if fcf_promedio else 0,
                'intervenciones_inmediatas': intervenciones,
            },
            'clasificacion_ctg': {
                'categoria_1': categoria_1,
                'categoria_2': categoria_2,
                'categoria_3': categoria_3,
            },
            'riesgo_sufrimiento': {
                'bajo_riesgo': bajo_riesgo,
                'riesgo_intermedio': riesgo_intermedio,
                'alto_riesgo': alto_riesgo,
            },
            'porcentajes': {
                'categoria_3_pct': round((categoria_3 / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
                'intervencion_pct': round((intervenciones / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
            }
        })
    
    @action(detail=False, methods=['get'])
    def alertas_activas(self, request):
        """Casos que requieren intervención inmediata"""
        alertas = self.get_queryset().filter(
            requiere_intervencion_inmediata=True
        ).order_by('-fecha_evaluacion')
        
        serializer = self.get_serializer(alertas, many=True)
        
        return Response({
            'total_alertas': alertas.count(),
            'casos_urgentes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_tipo_monitoreo(self, request):
        """Estadísticas por tipo de monitoreo"""
        tipo = request.query_params.get('tipo')
        if not tipo:
            return Response({'error': 'tipo es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        evaluaciones = self.get_queryset().filter(tipo_monitoreo=tipo)
        serializer = self.get_serializer(evaluaciones, many=True)
        
        return Response({
            'tipo_monitoreo': tipo,
            'total_evaluaciones': evaluaciones.count(),
            'evaluaciones': serializer.data
        })