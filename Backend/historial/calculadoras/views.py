from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import CalculoClinico
from .serializers import (
    CalculoClinicoSerializer,
    EdadGestacionalSerializer,
    IMCSerializer,
    GananciaPesoSerializer,
    BishopSerializer,
    RiesgoPreeclampsiaSerializer,
    DiabetesGestacionalSerializer,
    ILASerializer,
    PesoFetalSerializer,
    ApgarSerializer,
    RMIOvarioSerializer,
    RiesgoEndometrioSerializer,
    PAMSerializer,
    SuperficieCorporalSerializer,
)


class CalculadorasViewSet(viewsets.ViewSet):
    """
    ViewSet unificado para todas las calculadoras clínicas
    
    Endpoints disponibles:
    - POST /api/calculadoras/edad-gestacional/
    - POST /api/calculadoras/imc/
    - POST /api/calculadoras/ganancia-peso/
    - POST /api/calculadoras/bishop/
    - POST /api/calculadoras/riesgo-preeclampsia/
    - POST /api/calculadoras/diabetes-gestacional/
    - POST /api/calculadoras/ila/
    - POST /api/calculadoras/peso-fetal/
    - POST /api/calculadoras/apgar/
    - POST /api/calculadoras/rmi-ovario/
    - POST /api/calculadoras/riesgo-endometrio/
    - POST /api/calculadoras/pam/
    - POST /api/calculadoras/superficie-corporal/
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='edad-gestacional')
    def edad_gestacional(self, request):
        """
        Calcula edad gestacional y fecha probable de parto
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo (opcional)
        - fum: Fecha de última menstruación (YYYY-MM-DD)
        - fecha_calculo: Fecha del cálculo (opcional, default: hoy)
        """
        serializer = EdadGestacionalSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='imc')
    def imc(self, request):
        """
        Calcula Índice de Masa Corporal
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo (opcional)
        - peso: Peso en kg
        - altura: Altura en cm
        """
        serializer = IMCSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='ganancia-peso')
    def ganancia_peso(self, request):
        """
        Calcula ganancia de peso gestacional
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo
        - peso_pregestacional: Peso antes del embarazo (kg)
        - peso_actual: Peso actual (kg)
        - semanas_gestacion: Semanas de gestación
        - imc_pregestacional: IMC antes del embarazo
        """
        serializer = GananciaPesoSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='bishop')
    def bishop(self, request):
        """
        Calcula puntaje de Bishop (maduración cervical)
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo
        - dilatacion: Dilatación cervical (0-10 cm)
        - borramiento: Borramiento cervical (0-100%)
        - estacion: Estación de la presentación (-3 a +2)
        - consistencia: Consistencia cervical (0=firme, 1=media, 2=blanda)
        - posicion: Posición cervical (0=posterior, 1=media, 2=anterior)
        """
        serializer = BishopSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='riesgo-preeclampsia')
    def riesgo_preeclampsia(self, request):
        """
        Calcula riesgo de preeclampsia
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo
        - edad: Edad de la paciente
        - primiparidad: Boolean
        - antecedente_preeclampsia: Boolean
        - diabetes: Boolean
        - hipertension_cronica: Boolean
        - obesidad: Boolean
        - embarazo_multiple: Boolean
        - enfermedad_renal: Boolean
        - enfermedad_autoinmune: Boolean
        """
        serializer = RiesgoPreeclampsiaSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='diabetes-gestacional')
    def diabetes_gestacional(self, request):
        """
        Evalúa tamizaje de diabetes gestacional
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo
        - tipo_test: 'ogtt_75g', 'ogtt_100g', 'glucosa_ayunas'
        - semanas_gestacion: Semanas de gestación
        - glucosa_ayunas: Glucosa en ayunas (mg/dL)
        - glucosa_1h: Glucosa 1 hora (mg/dL) - opcional
        - glucosa_2h: Glucosa 2 horas (mg/dL) - opcional
        - glucosa_3h: Glucosa 3 horas (mg/dL) - opcional
        """
        serializer = DiabetesGestacionalSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='ila')
    def ila(self, request):
        """
        Calcula Índice de Líquido Amniótico
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo
        - semanas_gestacion: Semanas de gestación
        - cuadrante_1: Medición cuadrante superior derecho (mm)
        - cuadrante_2: Medición cuadrante superior izquierdo (mm)
        - cuadrante_3: Medición cuadrante inferior derecho (mm)
        - cuadrante_4: Medición cuadrante inferior izquierdo (mm)
        """
        serializer = ILASerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='peso-fetal')
    def peso_fetal(self, request):
        """
        Estima peso fetal (Fórmula de Hadlock)
        
        Parámetros:
        - paciente_id: ID del paciente
        - embarazo_id: ID del embarazo
        - semanas_gestacion: Semanas de gestación
        - dbp: Diámetro Biparietal (mm)
        - cc: Circunferencia Cefálica (mm)
        - ca: Circunferencia Abdominal (mm)
        - lf: Longitud del Fémur (mm)
        """
        serializer = PesoFetalSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='apgar')
    def apgar(self, request):
        """
        Calcula puntaje Apgar
        
        Parámetros:
        - paciente_id: ID del paciente
        - minuto: 1, 5 o 10
        - frecuencia_cardiaca: 0-2
        - esfuerzo_respiratorio: 0-2
        - tono_muscular: 0-2
        - irritabilidad_refleja: 0-2
        - coloracion: 0-2
        """
        serializer = ApgarSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='rmi-ovario')
    def rmi_ovario(self, request):
        """
        Calcula Risk of Malignancy Index para masa ovárica
        
        Parámetros:
        - paciente_id: ID del paciente
        - estado_menopausia: 'premenopausia' o 'postmenopausia'
        - masa_multilocular: Boolean
        - masa_solida: Boolean
        - masa_bilateral: Boolean
        - ascitis: Boolean
        - metastasis: Boolean
        - ca125: Valor de CA-125 (U/ml)
        """
        serializer = RMIOvarioSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='riesgo-endometrio')
    def riesgo_endometrio(self, request):
        """
        Evalúa factores de riesgo de cáncer de endometrio
        
        Parámetros:
        - paciente_id: ID del paciente
        - edad: Edad de la paciente
        - obesidad: Boolean
        - diabetes: Boolean
        - hipertension: Boolean
        - nuliparidad: Boolean
        - menarquia_temprana: Boolean
        - menopausia_tardia: Boolean
        - terapia_hormonal: Boolean
        - tamoxifeno: Boolean
        - sindrome_ovario_poliquistico: Boolean
        - antecedente_familiar: Boolean
        - grosor_endometrial: Grosor endometrial (mm) - opcional
        """
        serializer = RiesgoEndometrioSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='pam')
    def pam(self, request):
        """
        Calcula Presión Arterial Media
        
        Parámetros:
        - paciente_id: ID del paciente
        - control_prenatal_id: ID del control prenatal (opcional)
        - presion_sistolica: Presión sistólica (mmHg)
        - presion_diastolica: Presión diastólica (mmHg)
        """
        serializer = PAMSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='superficie-corporal')
    def superficie_corporal(self, request):
        """
        Calcula Superficie Corporal (fórmula de Mosteller)
        
        Parámetros:
        - paciente_id: ID del paciente
        - peso: Peso (kg)
        - altura: Altura (cm)
        """
        serializer = SuperficieCorporalSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CalculoClinicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar historial de cálculos clínicos
    
    Endpoints:
    - GET /api/calculadoras/historial/ - Listar todos los cálculos
    - GET /api/calculadoras/historial/{id}/ - Ver detalle de un cálculo
    - GET /api/calculadoras/historial/por-paciente/?paciente_id=X
    - GET /api/calculadoras/historial/por-tipo/?tipo=edad_gestacional
    """
    
    queryset = CalculoClinico.objects.select_related(
        'paciente',
        'embarazo',
        'control_prenatal',
        'realizado_por'
    ).all().order_by('-fecha_calculo')
    
    serializer_class = CalculoClinicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_calculo', 'paciente', 'embarazo', 'realizado_por']
    search_fields = ['paciente__nombre', 'paciente__apellido_paterno', 'interpretacion']
    ordering_fields = ['fecha_calculo']
    
    @action(detail=False, methods=['get'], url_path='por-paciente')
    def por_paciente(self, request):
        """
        Obtiene todos los cálculos de un paciente
        
        Parámetros query:
        - paciente_id: ID del paciente (requerido)
        """
        paciente_id = request.query_params.get('paciente_id', None)
        
        if not paciente_id:
            return Response(
                {'error': 'Debe proporcionar paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calculos = self.queryset.filter(paciente_id=paciente_id)
        
        page = self.paginate_queryset(calculos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(calculos, many=True)
        return Response({
            'total': calculos.count(),
            'calculos': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='por-tipo')
    def por_tipo(self, request):
        """
        Obtiene todos los cálculos de un tipo específico
        
        Parámetros query:
        - tipo: Tipo de cálculo (requerido)
        """
        tipo = request.query_params.get('tipo', None)
        
        if not tipo:
            return Response(
                {'error': 'Debe proporcionar tipo de cálculo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calculos = self.queryset.filter(tipo_calculo=tipo)
        
        page = self.paginate_queryset(calculos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(calculos, many=True)
        return Response({
            'tipo': tipo,
            'total': calculos.count(),
            'calculos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de uso de calculadoras"""
        
        from django.db.models import Count
        
        # Por tipo de cálculo
        por_tipo = CalculoClinico.objects.values('tipo_calculo').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Por usuario
        por_usuario = CalculoClinico.objects.filter(
            realizado_por__isnull=False
        ).values(
            'realizado_por__nombre',
            'realizado_por__apellido_paterno'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        # Totales
        total_calculos = CalculoClinico.objects.count()
        
        return Response({
            'total_calculos': total_calculos,
            'por_tipo': list(por_tipo),
            'top_usuarios': list(por_usuario)
        })