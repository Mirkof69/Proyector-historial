from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime
from .calculos_obstetricos import CalculadoraObstetrica

class CalculadoraEdadGestacionalView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        fum = request.data.get('fum')
        if not fum:
            return Response({'error': 'FUM requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            fum_date = datetime.strptime(fum, '%Y-%m-%d')
            resultado = CalculadoraObstetrica.calcular_edad_gestacional(fum_date)
            fpp = CalculadoraObstetrica.calcular_fpp(fum_date)
            resultado['fpp'] = fpp.strftime('%Y-%m-%d')
            return Response(resultado)
        except ValueError:
            return Response({'error': 'Formato de fecha inválido'}, status=status.HTTP_400_BAD_REQUEST)

class CalculadoraIMCView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        peso = request.data.get('peso')
        altura = request.data.get('altura')
        
        if not peso or not altura:
            return Response({'error': 'Peso y altura requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        
        resultado = CalculadoraObstetrica.calcular_imc(peso, altura)
        return Response(resultado)

class CalculadoraRiesgoPreeclampsiaView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pa_sistolica = request.data.get('pa_sistolica')
        pa_diastolica = request.data.get('pa_diastolica')
        edad = request.data.get('edad')
        semanas = request.data.get('semanas_gestacion')
        imc = request.data.get('imc')
        
        if not all([pa_sistolica, pa_diastolica, edad, semanas, imc]):
            return Response({'error': 'Todos los campos son requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        
        resultado = CalculadoraObstetrica.calcular_riesgo_preeclampsia(
            int(pa_sistolica), int(pa_diastolica), int(edad), int(semanas), float(imc)
        )
        return Response(resultado)