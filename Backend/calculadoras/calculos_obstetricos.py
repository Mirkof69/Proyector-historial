"""Calculos obstetricos module."""
from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone


class CalculadoraObstetrica:
    """Calculadoraobstetrica"""
    @staticmethod
    def calcular_edad_gestacional(fum, fecha_actual=None):
        """Calcula edad gestacional basada en FUM"""
        if not fecha_actual:
            fecha_actual = timezone.localdate()
        if isinstance(fum, datetime):
            fum = fum.date()

        diferencia = (fecha_actual - fum).days
        semanas = diferencia // 7
        dias = diferencia % 7

        return {
            "semanas": semanas,
            "dias": dias,
            "total_dias": diferencia,
            "descripcion": f"{semanas} semanas + {dias} días",
        }

    @staticmethod
    def calcular_fpp(fum):
        """Calcula Fecha Probable de Parto (Regla de Naegele)"""
        if isinstance(fum, datetime):
            fum = fum.date()
        return fum + timedelta(days=280)

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
            "imc": float(round(imc, 2)),
            "clasificacion": clasificacion,
            "riesgo": riesgo,
        }

    @staticmethod
    def calcular_riesgo_preeclampsia(
        pa_sistolica, pa_diastolica, edad, semanas_gestacion, imc,
    ):
        """Calcula riesgo de preeclampsia por puntos.
        Factores: PA sistólica, PA diastólica, edad materna, IMC.
        IMPORTANTE: los umbrales mayores deben evaluarse PRIMERO para evitar
        que el elif superior enmascare el caso más grave.
        """
        puntos = 0

        # Presión arterial sistólica
        if pa_sistolica >= 140:
            puntos += 3
        elif pa_sistolica >= 130:
            puntos += 2

        # Presión arterial diastólica
        if pa_diastolica >= 90:
            puntos += 3
        elif pa_diastolica >= 85:
            puntos += 2

        # Edad materna — umbral mayor (>= 40) debe ir PRIMERO
        if edad >= 40:
            puntos += 3
        elif edad >= 35:
            puntos += 2

        # IMC — umbral mayor (>= 35) debe ir PRIMERO
        if imc >= 35:
            puntos += 3
        elif imc >= 30:
            puntos += 2

        # Edad gestacional temprana con factores = mayor riesgo
        if semanas_gestacion and semanas_gestacion < 20 and puntos >= 2:
            puntos += 1

        if puntos >= 7:
            nivel = "Alto"
        elif puntos >= 4:
            nivel = "Moderado"
        else:
            nivel = "Bajo"

        recomendaciones = {
            "Alto": "Interconsulta urgente. Iniciar AAS 150 mg/día si < 16 semanas. Control PA diario.",
            "Moderado": "Seguimiento estrecho. Repetir PA en 48h. Considerar AAS 100 mg/día.",
            "Bajo": "Control prenatal rutinario. Educación sobre síntomas de alarma.",
        }

        return {
            "puntos": puntos,
            "nivel_riesgo": nivel,
            "recomendacion": recomendaciones[nivel],
        }
