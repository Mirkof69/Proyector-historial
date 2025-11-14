# =============================================================================
# VIEWS DE CALCULADORAS OBSTÉTRICAS FMF
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: calculadoras
# Descripción: API REST para las 15 calculadoras FMF (Fetal Medicine Foundation).
#              Endpoints para predicciones de riesgo y evaluaciones obstétricas.
# Versión: 2.0.0
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .calculos_obstetricos import CalculadoraObstetrica
from .serializers import *


# =============================================================================
# VIEWSET PRINCIPAL DE CALCULADORAS
# =============================================================================

class CalculadorasViewSet(viewsets.ViewSet):
    """
    ViewSet para calculadoras obstétricas FMF.

    Endpoints disponibles (15 calculadoras):

    **Predicción de Riesgos:**
    1. POST /calculadoras/preeclampsia/ - Predicción de preeclampsia
    2. POST /calculadoras/sga/ - Predicción de SGA (restricción crecimiento)
    3. POST /calculadoras/diabetes_gestacional/ - Predicción diabetes gestacional
    4. POST /calculadoras/parto_pretermino/ - Predicción parto pretérmino
    5. POST /calculadoras/trisomias/ - Screening de trisomías 21, 18, 13

    **Evaluaciones Fetales:**
    6. POST /calculadoras/peso_fetal/ - Estimación peso fetal (Hadlock)
    7. POST /calculadoras/crecimiento_fetal/ - Evaluación curva crecimiento
    8. POST /calculadoras/translucencia_nucal/ - Evaluación translucencia nucal

    **Evaluaciones Doppler:**
    9. POST /calculadoras/doppler/ - Doppler arterias (umbilical/cerebral media)
    10. POST /calculadoras/ip_uterinas/ - IP de arterias uterinas

    **Evaluaciones Maternas:**
    11. POST /calculadoras/pam/ - Presión Arterial Media + MoM
    12. POST /calculadoras/biomarcadores/ - Ratio sFLT-1/PlGF
    13. POST /calculadoras/indice_shock/ - Índice de shock materno

    **Evaluaciones de Bienestar Fetal:**
    14. POST /calculadoras/test_no_estresante/ - Test No Estresante (NST)

    **Utilitarios:**
    15. GET /calculadoras/lista/ - Lista de todas las calculadoras disponibles
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def lista(self, request):
        """
        Retorna lista de todas las calculadoras disponibles con descripción.
        """
        calculadoras = [
            {
                'nombre': 'prediccion_preeclampsia',
                'endpoint': '/calculadoras/preeclampsia/',
                'descripcion': 'Predicción de riesgo de preeclampsia usando algoritmo FMF',
                'trimestre': 'Primer trimestre (11-13 semanas)',
                'parametros_requeridos': [
                    'edad_materna', 'peso', 'talla', 'etnia', 'paridad',
                    'historia_preeclampsia', 'hipertension_cronica', 'diabetes',
                    'pam', 'ip_uterinas_promedio', 'eg_semanas'
                ],
                'parametros_opcionales': ['plgf', 'papp_a']
            },
            {
                'nombre': 'screening_trisomias',
                'endpoint': '/calculadoras/trisomias/',
                'descripcion': 'Screening combinado de trisomías 21, 18 y 13',
                'trimestre': 'Primer trimestre (11-13+6 semanas)',
                'parametros_requeridos': [
                    'edad_materna', 'eg_semanas', 'nt_mm',
                    'papp_a_mom', 'beta_hcg_mom', 'hueso_nasal_presente'
                ]
            },
            {
                'nombre': 'prediccion_sga',
                'endpoint': '/calculadoras/sga/',
                'descripcion': 'Predicción de restricción de crecimiento intrauterino (SGA)',
                'trimestre': 'Primer trimestre',
                'parametros_requeridos': [
                    'edad_materna', 'peso_pregestacional', 'talla', 'paridad',
                    'fuma', 'eg_semanas'
                ]
            },
            {
                'nombre': 'prediccion_diabetes_gestacional',
                'endpoint': '/calculadoras/diabetes_gestacional/',
                'descripcion': 'Predicción de riesgo de diabetes gestacional',
                'trimestre': 'Primer trimestre',
                'parametros_requeridos': [
                    'edad_materna', 'peso', 'talla', 'etnia',
                    'diabetes_familiar', 'diabetes_gestacional_previa'
                ]
            },
            {
                'nombre': 'prediccion_parto_pretermino',
                'endpoint': '/calculadoras/parto_pretermino/',
                'descripcion': 'Predicción de parto pretérmino basado en historia y longitud cervical',
                'trimestre': 'Segundo trimestre (16-24 semanas)',
                'parametros_requeridos': [
                    'edad_materna', 'paridad', 'parto_pretermino_previo',
                    'embarazo_multiple', 'longitud_cervical', 'eg_medicion'
                ]
            },
            {
                'nombre': 'peso_fetal_estimado',
                'endpoint': '/calculadoras/peso_fetal/',
                'descripcion': 'Estimación de peso fetal usando fórmulas de Hadlock',
                'trimestre': 'Segundo y tercer trimestre',
                'parametros_requeridos': ['dbp', 'cc', 'ca'],
                'parametros_opcionales': ['lf', 'formula']
            },
            {
                'nombre': 'crecimiento_fetal',
                'endpoint': '/calculadoras/crecimiento_fetal/',
                'descripcion': 'Evaluación de curva de crecimiento fetal con percentiles',
                'trimestre': 'Segundo y tercer trimestre',
                'parametros_requeridos': ['peso_estimado_g', 'eg_semanas']
            },
            {
                'nombre': 'translucencia_nucal',
                'endpoint': '/calculadoras/translucencia_nucal/',
                'descripcion': 'Evaluación de translucencia nucal con percentiles',
                'trimestre': 'Primer trimestre (11-13+6 semanas)',
                'parametros_requeridos': ['nt_mm', 'eg_semanas', 'lcc_mm']
            },
            {
                'nombre': 'doppler',
                'endpoint': '/calculadoras/doppler/',
                'descripcion': 'Evaluación Doppler de arteria umbilical o cerebral media',
                'trimestre': 'Segundo y tercer trimestre',
                'parametros_requeridos': [
                    'tipo', 'pico_sistolico', 'velocidad_diastolica', 'eg_semanas'
                ]
            },
            {
                'nombre': 'ip_arterias_uterinas',
                'endpoint': '/calculadoras/ip_uterinas/',
                'descripcion': 'Índice de pulsatilidad de arterias uterinas',
                'trimestre': 'Primer y segundo trimestre',
                'parametros_requeridos': ['ip_derecha', 'ip_izquierda', 'eg_semanas']
            },
            {
                'nombre': 'presion_arterial_media',
                'endpoint': '/calculadoras/pam/',
                'descripcion': 'Cálculo de PAM y MoM para predicción preeclampsia',
                'trimestre': 'Cualquier trimestre',
                'parametros_requeridos': ['pas', 'pad', 'eg_semanas']
            },
            {
                'nombre': 'biomarcadores',
                'endpoint': '/calculadoras/biomarcadores/',
                'descripcion': 'Ratio sFLT-1/PlGF para diagnóstico de preeclampsia',
                'trimestre': 'Segundo y tercer trimestre',
                'parametros_requeridos': ['sflt1', 'plgf', 'eg_semanas']
            },
            {
                'nombre': 'indice_shock',
                'endpoint': '/calculadoras/indice_shock/',
                'descripcion': 'Índice de shock materno para evaluación hemodinámica',
                'trimestre': 'Cualquier trimestre',
                'parametros_requeridos': ['frecuencia_cardiaca', 'presion_sistolica']
            },
            {
                'nombre': 'test_no_estresante',
                'endpoint': '/calculadoras/test_no_estresante/',
                'descripcion': 'Evaluación de bienestar fetal mediante NST',
                'trimestre': 'Tercer trimestre (≥ 28 semanas)',
                'parametros_requeridos': [
                    'fcf_basal', 'aceleraciones', 'desaceleraciones',
                    'variabilidad', 'eg_semanas'
                ]
            }
        ]

        return Response({
            'success': True,
            'total_calculadoras': len(calculadoras),
            'calculadoras': calculadoras
        })

    # =========================================================================
    # PREDICCIÓN DE PREECLAMPSIA
    # =========================================================================

    @action(detail=False, methods=['post'])
    def preeclampsia(self, request):
        """
        Predicción de riesgo de preeclampsia usando algoritmo FMF.

        Basado en factores maternos, biofísicos y biomarcadores.
        """
        serializer = PreeclampsiaInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.prediccion_preeclampsia_primer_trimestre(
                edad_materna=data['edad_materna'],
                peso=float(data['peso']),
                talla=float(data['talla']),
                etnia=data['etnia'],
                paridad=data['paridad'],
                historia_preeclampsia=data['historia_preeclampsia'],
                hipertension_cronica=data['hipertension_cronica'],
                diabetes=data['diabetes'],
                lupus=data['lupus'],
                concepcion_asistida=data['concepcion_asistida'],
                pam=float(data['pam']),
                ip_uterinas_promedio=float(data['ip_uterinas_promedio']),
                eg_semanas=data['eg_semanas'],
                plgf=float(data['plgf']) if data.get('plgf') else None,
                papp_a=float(data['papp_a']) if data.get('papp_a') else None
            )

            output_serializer = PreeclampsiaOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Predicción Preeclampsia FMF',
                    'resultado': output_serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Error en formato de resultado'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # SCREENING DE TRISOMÍAS
    # =========================================================================

    @action(detail=False, methods=['post'])
    def trisomias(self, request):
        """
        Screening combinado de trisomías 21, 18 y 13.

        Algoritmo FMF de primer trimestre (11-13+6 semanas).
        """
        serializer = ScreeningTrisomiasInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.screening_trisomias_primer_trimestre(
                edad_materna=data['edad_materna'],
                eg_semanas=data['eg_semanas'],
                nt_mm=float(data['nt_mm']),
                papp_a_mom=float(data['papp_a_mom']),
                beta_hcg_mom=float(data['beta_hcg_mom']),
                hueso_nasal_presente=data['hueso_nasal_presente']
            )

            output_serializer = ScreeningTrisomiasOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Screening Trisomías FMF',
                    'resultado': output_serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Error en formato de resultado',
                    'detalles': output_serializer.errors
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # PREDICCIÓN DE SGA
    # =========================================================================

    @action(detail=False, methods=['post'])
    def sga(self, request):
        """
        Predicción de restricción de crecimiento intrauterino (SGA).

        SGA = Small for Gestational Age (peso < percentil 10).
        """
        serializer = SGAInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.prediccion_sga_primer_trimestre(
                edad_materna=data['edad_materna'],
                peso_pregestacional=float(data['peso_pregestacional']),
                talla=float(data['talla']),
                paridad=data['paridad'],
                fuma=data['fuma'],
                cigarrillos_dia=data.get('cigarrillos_dia', 0),
                diabetes_previa=data['diabetes_previa'],
                hipertension_cronica=data['hipertension_cronica'],
                sga_previo=data['sga_previo'],
                eg_semanas=data['eg_semanas'],
                papp_a_mom=float(data['papp_a_mom']) if data.get('papp_a_mom') else None
            )

            output_serializer = SGAOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Predicción SGA FMF',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # PREDICCIÓN DE DIABETES GESTACIONAL
    # =========================================================================

    @action(detail=False, methods=['post'])
    def diabetes_gestacional(self, request):
        """
        Predicción de riesgo de diabetes gestacional.
        """
        serializer = DiabetesGestacionalInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.prediccion_diabetes_gestacional(
                edad_materna=data['edad_materna'],
                peso=float(data['peso']),
                talla=float(data['talla']),
                etnia=data['etnia'],
                diabetes_familiar=data['diabetes_familiar'],
                diabetes_gestacional_previa=data['diabetes_gestacional_previa'],
                sop=data['sop'],
                macrosomia_previa=data['macrosomia_previa']
            )

            output_serializer = DiabetesGestacionalOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Predicción Diabetes Gestacional',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # PREDICCIÓN DE PARTO PRETÉRMINO
    # =========================================================================

    @action(detail=False, methods=['post'])
    def parto_pretermino(self, request):
        """
        Predicción de parto pretérmino basado en historia y longitud cervical.
        """
        serializer = PartoPreterminoInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.prediccion_parto_pretermino(
                edad_materna=data['edad_materna'],
                paridad=data['paridad'],
                parto_pretermino_previo=data['parto_pretermino_previo'],
                eg_parto_previo=data.get('eg_parto_previo'),
                embarazo_multiple=data['embarazo_multiple'],
                longitud_cervical=float(data['longitud_cervical']),
                eg_medicion=data['eg_medicion']
            )

            output_serializer = PartoPreterminoOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Predicción Parto Pretérmino',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # PESO FETAL ESTIMADO
    # =========================================================================

    @action(detail=False, methods=['post'])
    def peso_fetal(self, request):
        """
        Estimación de peso fetal usando fórmulas de Hadlock.

        Fórmulas disponibles:
        - Hadlock IV (DBP, CC, CA, LF) - más precisa
        - Hadlock III (DBP, CC, CA)
        - Shepard (DBP, CA)
        """
        serializer = PesoFetalInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.peso_fetal_estimado(
                dbp=float(data['dbp']),
                cc=float(data['cc']),
                ca=float(data['ca']),
                lf=float(data['lf']) if data.get('lf') else None,
                formula=data.get('formula', 'hadlock_iv')
            )

            output_serializer = PesoFetalOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Peso Fetal Estimado',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # EVALUACIÓN DE CRECIMIENTO FETAL
    # =========================================================================

    @action(detail=False, methods=['post'])
    def crecimiento_fetal(self, request):
        """
        Evaluación de curva de crecimiento fetal con percentiles.
        """
        serializer = CrecimientoFetalInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.evaluar_crecimiento_fetal(
                peso_estimado_g=data['peso_estimado_g'],
                eg_semanas=data['eg_semanas'],
                sexo_fetal=data.get('sexo_fetal', 'desconocido')
            )

            output_serializer = CrecimientoFetalOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Evaluación Crecimiento Fetal',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # TRANSLUCENCIA NUCAL
    # =========================================================================

    @action(detail=False, methods=['post'])
    def translucencia_nucal(self, request):
        """
        Evaluación de translucencia nucal con percentiles FMF.
        """
        serializer = TranslucenciaNucalInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.calcular_percentil_translucencia_nucal(
                nt_mm=float(data['nt_mm']),
                eg_semanas=data['eg_semanas'],
                eg_dias=data.get('eg_dias', 0),
                lcc_mm=float(data['lcc_mm'])
            )

            output_serializer = TranslucenciaNucalOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Translucencia Nucal',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # DOPPLER
    # =========================================================================

    @action(detail=False, methods=['post'])
    def doppler(self, request):
        """
        Evaluación Doppler de arteria umbilical o cerebral media.
        """
        serializer = DopplerInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            if data['tipo'] == 'umbilical':
                resultado = CalculadoraObstetrica.doppler_arteria_umbilical(
                    pico_sistolico=float(data['pico_sistolico']),
                    velocidad_diastolica=float(data['velocidad_diastolica']),
                    eg_semanas=data['eg_semanas']
                )
            else:  # cerebral_media
                resultado = CalculadoraObstetrica.doppler_arteria_cerebral_media(
                    pico_sistolico=float(data['pico_sistolico']),
                    velocidad_diastolica=float(data['velocidad_diastolica']),
                    eg_semanas=data['eg_semanas']
                )

            output_serializer = DopplerOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': f'Doppler {data["tipo"].title()}',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # IP ARTERIAS UTERINAS
    # =========================================================================

    @action(detail=False, methods=['post'])
    def ip_uterinas(self, request):
        """
        Cálculo de IP de arterias uterinas con MoM.
        """
        serializer = IPUterinasInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.calcular_mom_ip_uterinas_detallado(
                ip_derecha=float(data['ip_derecha']),
                ip_izquierda=float(data['ip_izquierda']),
                eg_semanas=data['eg_semanas']
            )

            output_serializer = IPUterinasOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'IP Arterias Uterinas',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # PRESIÓN ARTERIAL MEDIA (PAM)
    # =========================================================================

    @action(detail=False, methods=['post'])
    def pam(self, request):
        """
        Cálculo de Presión Arterial Media con MoM.
        """
        serializer = PAMInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            # Calcular PAM
            pam_valor = (data['pas'] + 2 * data['pad']) / 3

            # Calcular MoM
            mom = CalculadoraObstetrica.calcular_mom_pam(pam_valor, data['eg_semanas'])

            resultado = {
                'pam': round(pam_valor, 2),
                'mom': mom,
                'percentil': 95 if mom > 1.30 else (75 if mom > 1.10 else 50),
                'elevada': mom > 1.10
            }

            output_serializer = PAMOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Presión Arterial Media',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # BIOMARCADORES
    # =========================================================================

    @action(detail=False, methods=['post'])
    def biomarcadores(self, request):
        """
        Ratio sFLT-1/PlGF para diagnóstico de preeclampsia.
        """
        serializer = BiomarcadoresInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.ratio_sflt1_plgf(
                sflt1=float(data['sflt1']),
                plgf=float(data['plgf']),
                eg_semanas=data['eg_semanas']
            )

            output_serializer = BiomarcadoresOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Biomarcadores sFLT-1/PlGF',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # ÍNDICE DE SHOCK
    # =========================================================================

    @action(detail=False, methods=['post'])
    def indice_shock(self, request):
        """
        Cálculo de índice de shock materno.

        Índice de Shock = FC / PAS
        Normal: < 0.9
        Shock leve: 0.9-1.0
        Shock moderado: 1.0-1.4
        Shock severo: > 1.4
        """
        serializer = IndiceShockInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.calcular_indice_shock(
                frecuencia_cardiaca=data['frecuencia_cardiaca'],
                presion_sistolica=data['presion_sistolica']
            )

            output_serializer = IndiceShockOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Índice de Shock',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =========================================================================
    # TEST NO ESTRESANTE
    # =========================================================================

    @action(detail=False, methods=['post'])
    def test_no_estresante(self, request):
        """
        Evaluación de Test No Estresante (NST) para bienestar fetal.

        Test reactivo:
        - ≥ 2 aceleraciones en 20 minutos
        - FCF basal 110-160 lpm
        - Variabilidad moderada (10-25 lpm)
        - Sin desaceleraciones
        """
        serializer = TestNoEstresanteInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            resultado = CalculadoraObstetrica.test_no_estresante(
                fcf_basal=data['fcf_basal'],
                aceleraciones=data['aceleraciones'],
                desaceleraciones=data['desaceleraciones'],
                variabilidad=data['variabilidad'],
                duracion_minutos=data.get('duracion_minutos', 20),
                eg_semanas=data['eg_semanas']
            )

            output_serializer = TestNoEstresanteOutputSerializer(data=resultado)
            if output_serializer.is_valid():
                return Response({
                    'success': True,
                    'calculadora': 'Test No Estresante',
                    'resultado': output_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
