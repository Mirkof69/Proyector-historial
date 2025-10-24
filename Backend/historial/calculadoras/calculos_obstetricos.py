from datetime import datetime, timedelta
from decimal import Decimal

class CalculadoraObstetrica:
    
    @staticmethod
    def calcular_edad_gestacional(fum, fecha_actual=None):
        """Calcula edad gestacional basada en FUM"""
        if not fecha_actual:
            fecha_actual = datetime.now().date()
        if isinstance(fum, datetime):
            fum = fum.date()
        
        diferencia = (fecha_actual - fum).days
        semanas = diferencia // 7
        dias = diferencia % 7
        
        return {
            'semanas': semanas,
            'dias': dias,
            'total_dias': diferencia,
            'descripcion': f"{semanas} semanas + {dias} días"
        }
    
    @staticmethod
    def calcular_fpp(fum):
        """Calcula Fecha Probable de Parto (Regla de Naegele)"""
        if isinstance(fum, datetime):
            fum = fum.date()
        fpp = fum + timedelta(days=280)
        return fpp
    
    @staticmethod
    def calcular_imc(peso, altura):
        """Calcula Índice de Masa Corporal"""
        altura_m = Decimal(altura) / 100
        imc = Decimal(peso) / (altura_m * altura_m)
        
        if imc < 18.5:
            clasificacion = "Bajo peso"
            riesgo = "Moderado"
        elif imc < 25:
            clasificacion = "Normal"
            riesgo = "Bajo"
        elif imc < 30:
            clasificacion = "Sobrepeso"
            riesgo = "Moderado"
        else:
            clasificacion = "Obesidad"
            riesgo = "Alto"
        
        return {
            'imc': float(round(imc, 2)),
            'clasificacion': clasificacion,
            'riesgo': riesgo
        }
    
    @staticmethod
    def calcular_riesgo_preeclampsia(pa_sistolica, pa_diastolica, edad, semanas_gestacion, imc):
        """Calcula riesgo de preeclampsia"""
        puntos = 0
        
        if pa_sistolica >= 140:
            puntos += 3
        elif pa_sistolica >= 130:
            puntos += 2
            
        if pa_diastolica >= 90:
            puntos += 3
        elif pa_diastolica >= 85:
            puntos += 2
            
        if edad >= 35:
            puntos += 2
        elif edad >= 40:
            puntos += 3
            
        if imc >= 30:
            puntos += 2
        elif imc >= 35:
            puntos += 3
            
        if puntos >= 7:
            nivel = "Alto"
        elif puntos >= 4:
            nivel = "Moderado"
        else:
            nivel = "Bajo"
            
        return {
            'puntos': puntos,
            'nivel_riesgo': nivel,
            'recomendacion': 'Seguimiento estrecho' if puntos >= 4 else 'Control normal'
        }