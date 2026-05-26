"""Utilidades para cálculos clínicos obstétricos y ginecológicos
Fórmulas médicas validadas según estándares internacionales
"""

import math
from datetime import date, timedelta
from decimal import Decimal


class CalculadorasObstetricas:
    """Calculadoras para obstetricia"""

    @staticmethod
    def calcular_edad_gestacional(fum: date, fecha_actual: date = None) -> dict:
        """Calcula edad gestacional basada en FUM (Fecha de Última Menstruación)

        Args:
            fum: Fecha de última menstruación
            fecha_actual: Fecha de cálculo (default: hoy)

        Returns:
            dict con semanas, dias, fpp, trimestre

        """
        if not fecha_actual:
            fecha_actual = date.today()

        diferencia = fecha_actual - fum
        dias_totales = diferencia.days

        semanas = dias_totales // 7
        dias = dias_totales % 7

        # Fecha Probable de Parto (Regla de Naegele: FUM + 280 días)
        fpp = fum + timedelta(days=280)

        # Determinar trimestre
        if semanas < 13:
            trimestre = 1
        elif semanas < 27:
            trimestre = 2
        else:
            trimestre = 3

        return {
            "semanas": semanas,
            "dias": dias,
            "fpp": fpp,
            "trimestre": trimestre,
            "edad_gestacional_texto": f"{semanas} semanas + {dias} días",
        }

    @staticmethod
    def calcular_imc(peso: Decimal, altura: Decimal) -> dict:
        """Calcula Índice de Masa Corporal

        Args:
            peso: Peso en kg
            altura: Altura en cm

        Returns:
            dict con imc, clasificacion, ganancia_peso_recomendada

        """
        altura_m = float(altura) / 100
        imc = float(peso) / (altura_m * altura_m)

        # Clasificación según OMS
        if imc < 18.5:
            clasificacion = "bajo_peso"
            clasificacion_texto = "Bajo Peso"
            ganancia_min = 12.5
            ganancia_max = 18.0
        elif imc < 25:
            clasificacion = "normal"
            clasificacion_texto = "Normal"
            ganancia_min = 11.5
            ganancia_max = 16.0
        elif imc < 30:
            clasificacion = "sobrepeso"
            clasificacion_texto = "Sobrepeso"
            ganancia_min = 7.0
            ganancia_max = 11.5
        elif imc < 35:
            clasificacion = "obesidad_i"
            clasificacion_texto = "Obesidad Grado I"
            ganancia_min = 5.0
            ganancia_max = 9.0
        elif imc < 40:
            clasificacion = "obesidad_ii"
            clasificacion_texto = "Obesidad Grado II"
            ganancia_min = 5.0
            ganancia_max = 9.0
        else:
            clasificacion = "obesidad_iii"
            clasificacion_texto = "Obesidad Grado III"
            ganancia_min = 5.0
            ganancia_max = 9.0

        return {
            "imc": round(imc, 2),
            "clasificacion": clasificacion,
            "clasificacion_texto": clasificacion_texto,
            "ganancia_peso_recomendada_min": ganancia_min,
            "ganancia_peso_recomendada_max": ganancia_max,
        }

    @staticmethod
    def calcular_ganancia_peso(
        peso_pregestacional: Decimal,
        peso_actual: Decimal,
        semanas_gestacion: int,
        imc_pregestacional: Decimal,
    ) -> dict:
        """Calcula ganancia de peso gestacional y evalúa si es adecuada

        Args:
            peso_pregestacional: Peso antes del embarazo (kg)
            peso_actual: Peso actual (kg)
            semanas_gestacion: Semanas de gestación
            imc_pregestacional: IMC antes del embarazo

        Returns:
            dict con ganancia actual, esperada, interpretación

        """
        ganancia_actual = float(peso_actual) - float(peso_pregestacional)

        # Determinar rango de ganancia según IMC pregestacional
        imc = float(imc_pregestacional)
        if imc < 18.5:
            ganancia_total_min = 12.5
            ganancia_total_max = 18.0
        elif imc < 25:
            ganancia_total_min = 11.5
            ganancia_total_max = 16.0
        elif imc < 30:
            ganancia_total_min = 7.0
            ganancia_total_max = 11.5
        else:
            ganancia_total_min = 5.0
            ganancia_total_max = 9.0

        # Ganancia esperada según semana (lineal)
        ganancia_esperada_min = (ganancia_total_min / 40) * semanas_gestacion
        ganancia_esperada_max = (ganancia_total_max / 40) * semanas_gestacion

        # Evaluar si es adecuada
        if ganancia_actual < ganancia_esperada_min:
            adecuada = False
            interpretacion = f"Ganancia insuficiente. Se esperaba entre {ganancia_esperada_min:.1f} y {ganancia_esperada_max:.1f} kg"
        elif ganancia_actual > ganancia_esperada_max:
            adecuada = False
            interpretacion = f"Ganancia excesiva. Se esperaba entre {ganancia_esperada_min:.1f} y {ganancia_esperada_max:.1f} kg"
        else:
            adecuada = True
            interpretacion = f"Ganancia adecuada dentro del rango esperado ({ganancia_esperada_min:.1f}-{ganancia_esperada_max:.1f} kg)"

        return {
            "ganancia_peso_actual": round(ganancia_actual, 2),
            "ganancia_peso_esperada_min": round(ganancia_esperada_min, 2),
            "ganancia_peso_esperada_max": round(ganancia_esperada_max, 2),
            "adecuada": adecuada,
            "interpretacion": interpretacion,
        }

    @staticmethod
    def calcular_bishop(
        dilatacion: int,
        borramiento: int,
        estacion: int,
        consistencia: int,
        posicion: int,
    ) -> dict:
        """Calcula Puntaje de Bishop para maduración cervical

        Parámetros:
            pass
        - dilatacion: 0-10 cm (0=cerrado, 1-2=1punto, 3-4=2puntos, ≥5=3puntos)
        - borramiento: 0-100% (0-30=0puntos, 40-50=1punto, 60-70=2puntos, ≥80=3puntos)
        - estacion: -3 a +2 (-3=0puntos, -2=1punto, -1/0=2puntos, +1/+2=3puntos)
        - consistencia: 0=firme, 1=media, 2=blanda
        - posicion: 0=posterior, 1=media, 2=anterior

        Returns:
            dict con puntaje_total, interpretacion

        """
        # Puntaje de dilatación
        if dilatacion == 0:
            puntos_dilatacion = 0
        elif dilatacion <= 2:
            puntos_dilatacion = 1
        elif dilatacion <= 4:
            puntos_dilatacion = 2
        else:
            puntos_dilatacion = 3

        # Puntaje de borramiento
        if borramiento < 40:
            puntos_borramiento = 0
        elif borramiento < 60:
            puntos_borramiento = 1
        elif borramiento < 80:
            puntos_borramiento = 2
        else:
            puntos_borramiento = 3

        # Puntaje de estación
        if estacion == -3:
            puntos_estacion = 0
        elif estacion == -2:
            puntos_estacion = 1
        elif estacion in [-1, 0]:
            puntos_estacion = 2
        else:  # +1, +2
            puntos_estacion = 3

        puntaje_total = (
            puntos_dilatacion
            + puntos_borramiento
            + puntos_estacion
            + consistencia
            + posicion
        )

        # Interpretación
        if puntaje_total <= 4:
            interpretacion = "Cérvix desfavorable - Inducción difícil"
        elif puntaje_total <= 6:
            interpretacion = "Cérvix intermedio - Inducción posible"
        else:
            interpretacion = "Cérvix favorable - Inducción probable exitosa"

        return {
            "puntaje_total": puntaje_total,
            "interpretacion": interpretacion,
            "detalle": {
                "dilatacion": puntos_dilatacion,
                "borramiento": puntos_borramiento,
                "estacion": puntos_estacion,
                "consistencia": consistencia,
                "posicion": posicion,
            },
        }

    @staticmethod
    def calcular_riesgo_preeclampsia(
        edad: int,
        primiparidad: bool,
        antecedente_preeclampsia: bool,
        diabetes: bool,
        hipertension_cronica: bool,
        obesidad: bool,
        embarazo_multiple: bool,
        enfermedad_renal: bool,
        enfermedad_autoinmune: bool,
    ) -> dict:
        """Calcula riesgo de preeclampsia según factores de riesgo
        Basado en guías ACOG y recomendaciones de aspirina profiláctica

        Returns:
            dict con nivel_riesgo, recomienda_aspirina, factores_count

        """
        factores_alto_riesgo = 0
        factores_moderado_riesgo = 0

        # Factores de alto riesgo
        if antecedente_preeclampsia:
            factores_alto_riesgo += 1
        if embarazo_multiple:
            factores_alto_riesgo += 1
        if hipertension_cronica:
            factores_alto_riesgo += 1
        if enfermedad_renal:
            factores_alto_riesgo += 1
        if enfermedad_autoinmune:
            factores_alto_riesgo += 1
        if diabetes:
            factores_alto_riesgo += 1

        # Factores de riesgo moderado
        if primiparidad:
            factores_moderado_riesgo += 1
        if edad >= 35:
            factores_moderado_riesgo += 1
        if obesidad:
            factores_moderado_riesgo += 1

        # Determinar nivel de riesgo
        if factores_alto_riesgo >= 1:
            nivel_riesgo = "alto"
            recomienda_aspirina = True
            interpretacion = "Alto riesgo de preeclampsia. Se recomienda aspirina 100-150mg/día desde semana 12-16 hasta semana 36"
        elif factores_moderado_riesgo >= 2:
            nivel_riesgo = "moderado"
            recomienda_aspirina = True
            interpretacion = (
                "Riesgo moderado de preeclampsia. Considerar aspirina profiláctica"
            )
        else:
            nivel_riesgo = "bajo"
            recomienda_aspirina = False
            interpretacion = (
                "Bajo riesgo de preeclampsia. No requiere aspirina profiláctica"
            )

        return {
            "nivel_riesgo": nivel_riesgo,
            "recomienda_aspirina": recomienda_aspirina,
            "factores_riesgo_count": factores_alto_riesgo + factores_moderado_riesgo,
            "factores_alto_riesgo": factores_alto_riesgo,
            "factores_moderado_riesgo": factores_moderado_riesgo,
            "interpretacion": interpretacion,
        }

    @staticmethod
    def calcular_diabetes_gestacional(
        tipo_test: str,
        glucosa_ayunas: Decimal,
        glucosa_1h: Decimal = None,
        glucosa_2h: Decimal = None,
        glucosa_3h: Decimal = None,
    ) -> dict:
        """Evalúa tamizaje de diabetes gestacional

        Criterios OGTT 75g (2 horas - OMS):
            pass
        - Ayunas: ≥92 mg/dL
        - 1 hora: ≥180 mg/dL
        - 2 horas: ≥153 mg/dL

        Criterios OGTT 100g (3 horas - Carpenter-Coustan):
            pass
        - Ayunas: ≥95 mg/dL
        - 1 hora: ≥180 mg/dL
        - 2 horas: ≥155 mg/dL
        - 3 horas: ≥140 mg/dL

        Returns:
            dict con diagnostico, valores_alterados, requiere_seguimiento

        """
        valores_alterados = 0
        valores_alterados_lista = []

        if tipo_test == "ogtt_75g":
            # OGTT 75g - OMS (1 valor alterado = diagnóstico)
            if float(glucosa_ayunas) >= 92:
                valores_alterados += 1
                valores_alterados_lista.append("Ayunas")
            if glucosa_1h and float(glucosa_1h) >= 180:
                valores_alterados += 1
                valores_alterados_lista.append("1 hora")
            if glucosa_2h and float(glucosa_2h) >= 153:
                valores_alterados += 1
                valores_alterados_lista.append("2 horas")

            if valores_alterados >= 1:
                diagnostico = f"Diabetes Gestacional (OGTT 75g) - {valores_alterados} valor(es) alterado(s)"
                requiere_seguimiento = True
            else:
                diagnostico = "Normal - Sin diabetes gestacional"
                requiere_seguimiento = False

        elif tipo_test == "ogtt_100g":
            # OGTT 100g - Carpenter-Coustan (2 valores alterados = diagnóstico)
            if float(glucosa_ayunas) >= 95:
                valores_alterados += 1
                valores_alterados_lista.append("Ayunas")
            if glucosa_1h and float(glucosa_1h) >= 180:
                valores_alterados += 1
                valores_alterados_lista.append("1 hora")
            if glucosa_2h and float(glucosa_2h) >= 155:
                valores_alterados += 1
                valores_alterados_lista.append("2 horas")
            if glucosa_3h and float(glucosa_3h) >= 140:
                valores_alterados += 1
                valores_alterados_lista.append("3 horas")

            if valores_alterados >= 2:
                diagnostico = f"Diabetes Gestacional (OGTT 100g) - {valores_alterados} valores alterados"
                requiere_seguimiento = True
            elif valores_alterados == 1:
                diagnostico = "Intolerancia a la glucosa - Repetir prueba o seguimiento"
                requiere_seguimiento = True
            else:
                diagnostico = "Normal - Sin diabetes gestacional"
                requiere_seguimiento = False

        elif float(glucosa_ayunas) >= 92:
            diagnostico = "Glucosa en ayunas elevada - Requiere OGTT"
            requiere_seguimiento = True
            valores_alterados = 1
        else:
            diagnostico = "Glucosa en ayunas normal"
            requiere_seguimiento = False

        return {
            "diagnostico": diagnostico,
            "valores_alterados": valores_alterados,
            "valores_alterados_lista": valores_alterados_lista,
            "requiere_seguimiento": requiere_seguimiento,
        }

    @staticmethod
    def calcular_ila(
        cuadrante_1: Decimal,
        cuadrante_2: Decimal,
        cuadrante_3: Decimal,
        cuadrante_4: Decimal,
    ) -> dict:
        """Calcula Índice de Líquido Amniótico (ILA)
        Método de 4 cuadrantes

        Interpretación:
            pass
        - <5 cm: Oligohidramnios
        - 5-25 cm: Normal
        - >25 cm: Polihidramnios

        Returns:
            dict con ila, interpretacion

        """
        ila = (
            float(cuadrante_1)
            + float(cuadrante_2)
            + float(cuadrante_3)
            + float(cuadrante_4)
        )

        # Convertir de mm a cm
        ila_cm = ila / 10

        if ila_cm < 5:
            interpretacion = "oligohidramnios"
            interpretacion_texto = "Oligohidramnios - Líquido amniótico disminuido"
            recomendacion = "Requiere evaluación y seguimiento estrecho"
        elif ila_cm <= 25:
            interpretacion = "normal"
            interpretacion_texto = "Normal - Líquido amniótico adecuado"
            recomendacion = "Continuar controles rutinarios"
        else:
            interpretacion = "polihidramnios"
            interpretacion_texto = "Polihidramnios - Líquido amniótico aumentado"
            recomendacion = "Requiere evaluación de causas y seguimiento"

        return {
            "ila": round(ila, 2),
            "ila_cm": round(ila_cm, 2),
            "interpretacion": interpretacion,
            "interpretacion_texto": interpretacion_texto,
            "recomendacion": recomendacion,
        }

    @staticmethod
    def calcular_peso_fetal(
        dbp: Decimal, _cc: Decimal, ca: Decimal, lf: Decimal, semanas_gestacion: int,
    ) -> dict:
        """Estima peso fetal usando fórmula de Hadlock

        Fórmula de Hadlock:
            pass
        log10(PF) = 1.335 - 0.0034(CA)(LF) + 0.0316(DBP) + 0.0457(CA) + 0.1623(LF)

        Donde:
            pass
        - DBP: Diámetro Biparietal (mm)
        - CA: Circunferencia Abdominal (mm)
        - LF: Longitud del Fémur (mm)
        - CC: Circunferencia Cefálica (mm)

        Returns:
            dict con peso_estimado, percentil, clasificacion

        """
        dbp_val = float(dbp)
        ca_val = float(ca)
        lf_val = float(lf)

        # Fórmula de Hadlock (simplificada)
        log_peso = (
            1.335
            - 0.0034 * ca_val * lf_val
            + 0.0316 * dbp_val
            + 0.0457 * ca_val
            + 0.1623 * lf_val
        )

        peso_estimado = 10**log_peso

        # Estimación de percentil basado en tablas de referencia (simplificado)
        # Peso promedio por semana (aproximado)
        pesos_referencia = {
            20: 300,
            24: 600,
            28: 1000,
            30: 1300,
            32: 1700,
            34: 2100,
            36: 2600,
            38: 3000,
            40: 3400,
        }

        # Obtener peso de referencia más cercano
        peso_ref = pesos_referencia.get(semanas_gestacion, 3000)

        # Calcular percentil aproximado
        if peso_estimado < peso_ref * 0.9:
            percentil = 10
            if peso_estimado < peso_ref * 0.7:
                clasificacion = "rciu"
                clasificacion_texto = "Restricción de Crecimiento Intrauterino"
            else:
                clasificacion = "peg"
                clasificacion_texto = "Pequeño para Edad Gestacional"
        elif peso_estimado > peso_ref * 1.1:
            percentil = 90
            if peso_estimado > peso_ref * 1.2 or peso_estimado > 4000:
                clasificacion = "macrosomia"
                clasificacion_texto = "Macrosomía Fetal"
            else:
                clasificacion = "geg"
                clasificacion_texto = "Grande para Edad Gestacional"
        else:
            percentil = 50
            clasificacion = "aeg"
            clasificacion_texto = "Adecuado para Edad Gestacional"

        return {
            "peso_estimado": round(peso_estimado, 2),
            "percentil": percentil,
            "clasificacion": clasificacion,
            "clasificacion_texto": clasificacion_texto,
        }

    @staticmethod
    def calcular_apgar(
        frecuencia_cardiaca: int,
        esfuerzo_respiratorio: int,
        tono_muscular: int,
        irritabilidad_refleja: int,
        coloracion: int,
    ) -> dict:
        """Calcula Puntaje de Apgar

        Cada parámetro se puntúa de 0 a 2:
            pass
        - 0-3: Crítico
        - 4-6: Depresión moderada
        - 7-10: Normal

        Returns:
            dict con puntaje_total, interpretacion

        """
        puntaje_total = (
            frecuencia_cardiaca
            + esfuerzo_respiratorio
            + tono_muscular
            + irritabilidad_refleja
            + coloracion
        )

        if puntaje_total <= 3:
            interpretacion = "critico"
            interpretacion_texto = "Crítico - Requiere reanimación inmediata"
        elif puntaje_total <= 6:
            interpretacion = "depresion_moderada"
            interpretacion_texto = "Depresión Moderada - Requiere asistencia"
        else:
            interpretacion = "normal"
            interpretacion_texto = "Normal - Recién nacido saludable"

        return {
            "puntaje_total": puntaje_total,
            "interpretacion": interpretacion,
            "interpretacion_texto": interpretacion_texto,
        }


class CalculadorasGinecologicas:
    """Calculadoras para ginecología"""

    @staticmethod
    def calcular_rmi_ovario(
        estado_menopausia: str,
        masa_multilocular: bool,
        masa_solida: bool,
        masa_bilateral: bool,
        ascitis: bool,
        metastasis: bool,
        ca125: Decimal,
    ) -> dict:
        """Calcula Risk of Malignancy Index (RMI) para masa ovárica

        RMI = U x M x CA-125

        Donde:
            pass
        - U (puntuación ecográfica): 1 punto por cada hallazgo
        - M (estado menopáusico): 1 si premenopausia, 3 si postmenopausia
        - CA-125: valor sérico

        Interpretación:
            pass
        - <25: Bajo riesgo
        - 25-250: Riesgo intermedio
        - >250: Alto riesgo

        Returns:
            dict con puntuacion_u, factor_m, rmi, nivel_riesgo

        """
        # Calcular puntuación ecográfica (U)
        puntuacion_u = 0
        if masa_multilocular:
            puntuacion_u += 1
        if masa_solida:
            puntuacion_u += 1
        if masa_bilateral:
            puntuacion_u += 1
        if ascitis:
            puntuacion_u += 1
        if metastasis:
            puntuacion_u += 1

        # Si U=0, se considera U=1 para el cálculo
        if puntuacion_u == 0:
            puntuacion_u = 1

        # Factor menopáusico (M)
        factor_m = 3 if estado_menopausia == "postmenopausia" else 1

        # Calcular RMI
        rmi = puntuacion_u * factor_m * float(ca125)

        # Determinar nivel de riesgo
        if rmi < 25:
            nivel_riesgo = "bajo"
            nivel_riesgo_texto = "Bajo Riesgo de Malignidad"
            recomendacion = "Seguimiento clínico e imagenológico"
        elif rmi <= 250:
            nivel_riesgo = "intermedio"
            nivel_riesgo_texto = "Riesgo Intermedio de Malignidad"
            recomendacion = "Evaluación por ginecología oncológica"
        else:
            nivel_riesgo = "alto"
            nivel_riesgo_texto = "Alto Riesgo de Malignidad"
            recomendacion = "Referir a ginecología oncológica de forma urgente"

        return {
            "puntuacion_u": puntuacion_u,
            "factor_m": factor_m,
            "rmi": round(rmi, 2),
            "nivel_riesgo": nivel_riesgo,
            "nivel_riesgo_texto": nivel_riesgo_texto,
            "recomendacion": recomendacion,
        }

    @staticmethod
    def calcular_riesgo_endometrio(
        edad: int,
        obesidad: bool,
        diabetes: bool,
        hipertension: bool,
        nuliparidad: bool,
        menarquia_temprana: bool,
        menopausia_tardia: bool,
        terapia_hormonal: bool,
        tamoxifeno: bool,
        sindrome_ovario_poliquistico: bool,
        antecedente_familiar: bool,
        grosor_endometrial: Decimal = None,
    ) -> dict:
        """Evalúa factores de riesgo de cáncer de endometrio

        Returns:
            dict con factores_riesgo_count, nivel_riesgo, requiere_biopsia

        """
        factores_count = 0
        factores_lista = []

        if edad >= 50:
            factores_count += 1
            factores_lista.append("Edad ≥50 años")
        if obesidad:
            factores_count += 1
            factores_lista.append("Obesidad")
        if diabetes:
            factores_count += 1
            factores_lista.append("Diabetes")
        if hipertension:
            factores_count += 1
            factores_lista.append("Hipertensión")
        if nuliparidad:
            factores_count += 1
            factores_lista.append("Nuliparidad")
        if menarquia_temprana:
            factores_count += 1
            factores_lista.append("Menarquia temprana")
        if menopausia_tardia:
            factores_count += 1
            factores_lista.append("Menopausia tardía")
        if terapia_hormonal:
            factores_count += 2  # Factor más importante
            factores_lista.append("Terapia estrogénica sin oposición")
        if tamoxifeno:
            factores_count += 2  # Factor más importante
            factores_lista.append("Uso de Tamoxifeno")
        if sindrome_ovario_poliquistico:
            factores_count += 1
            factores_lista.append("Síndrome de ovario poliquístico")
        if antecedente_familiar:
            factores_count += 1
            factores_lista.append("Antecedente familiar")

        # Evaluar grosor endometrial
        requiere_biopsia = False
        if grosor_endometrial:
            grosor = float(grosor_endometrial)
            # Postmenopausia: >4mm requiere biopsia
            # Premenopausia: >12mm puede requerir biopsia
            if (grosor > 4 and edad >= 50) or (grosor > 12 and edad < 50):
                requiere_biopsia = True
                factores_lista.append(f"Grosor endometrial aumentado ({grosor}mm)")

        # Determinar nivel de riesgo
        if factores_count <= 2 and not requiere_biopsia:
            nivel_riesgo = "bajo"
            nivel_riesgo_texto = "Bajo Riesgo"
            recomendacion = "Controles ginecológicos rutinarios"
        elif factores_count <= 4 or (factores_count <= 2 and requiere_biopsia):
            nivel_riesgo = "moderado"
            nivel_riesgo_texto = "Riesgo Moderado"
            recomendacion = "Seguimiento clínico cada 6 meses"
            if requiere_biopsia:
                recomendacion += " - Considerar biopsia endometrial"
        else:
            nivel_riesgo = "alto"
            nivel_riesgo_texto = "Alto Riesgo"
            recomendacion = "Evaluación especializada - Biopsia endometrial recomendada"
            requiere_biopsia = True

        return {
            "factores_riesgo_count": factores_count,
            "factores_lista": factores_lista,
            "nivel_riesgo": nivel_riesgo,
            "nivel_riesgo_texto": nivel_riesgo_texto,
            "requiere_biopsia": requiere_biopsia,
            "recomendacion": recomendacion,
        }


class CalculadorasGenerales:
    """Calculadoras generales"""

    @staticmethod
    def calcular_pam(presion_sistolica: int, presion_diastolica: int) -> dict:
        """Calcula Presión Arterial Media (PAM)

        Fórmula: PAM = (PAS + 2*PAD) / 3

        Interpretación:
            pass
        - <70: Hipotensión
        - 70-100: Normal
        - 100-110: Elevada
        - >110: Hipertensión

        Returns:
            dict con pam, interpretacion

        """
        pam = (presion_sistolica + 2 * presion_diastolica) / 3

        if pam < 70:
            interpretacion = "hipotension"
            interpretacion_texto = "Hipotensión - PAM baja"
            recomendacion = "Evaluar perfusión tisular y causas"
        elif pam <= 100:
            interpretacion = "normal"
            interpretacion_texto = "Normal"
            recomendacion = "Presión arterial adecuada"
        elif pam <= 110:
            interpretacion = "elevada"
            interpretacion_texto = "Elevada - Prehipertensión"
            recomendacion = "Seguimiento y modificación de estilos de vida"
        else:
            interpretacion = "hipertension"
            interpretacion_texto = "Hipertensión"
            recomendacion = "Evaluación y tratamiento antihipertensivo"

        return {
            "pam": round(pam, 2),
            "interpretacion": interpretacion,
            "interpretacion_texto": interpretacion_texto,
            "recomendacion": recomendacion,
        }

    @staticmethod
    def calcular_superficie_corporal(peso: Decimal, altura: Decimal) -> dict:
        """Calcula Superficie Corporal según fórmula de Mosteller

        Fórmula: SC (m²) = √[(peso(kg) x altura(cm)) / 3600]

        Returns:
            dict con superficie_corporal

        """
        peso_val = float(peso)
        altura_val = float(altura)

        superficie_corporal = math.sqrt((peso_val * altura_val) / 3600)

        return {"superficie_corporal": round(superficie_corporal, 2)}


# ============================================================================
# FUNCIONES DE CONVENIENCIA (Para uso directo en tests y APIs)
# ============================================================================


def calcular_edad_gestacional(fur=None, fecha_actual=None):
    """Wrapper para calcular edad gestacional"""
    return CalculadorasObstetricas.calcular_edad_gestacional(fur, fecha_actual)


def calcular_fecha_probable_parto(fur):
    """Calcula FPP como FUM + 280 días"""

    return fur + timedelta(days=280)


def calcular_imc(peso, talla):
    """Calcula IMC - talla en metros"""
    if talla > 3:  # Asumiendo que se pasó en cm
        talla = talla / 100
    return round(float(peso) / (float(talla) ** 2), 2)


def interpretar_imc_gestacional(imc, semanas_gestacion=None):
    """Interpreta IMC en contexto gestacional"""
    _ = semanas_gestacion  # reserved for trimester-specific adjustments
    if imc < 18.5:
        categoria = "bajo_peso"
        recomendacion = "Se recomienda evaluación nutricional"
    elif imc < 25:
        categoria = "normal"
        recomendacion = "IMC adecuado para embarazo"
    elif imc < 30:
        categoria = "sobrepeso"
        recomendacion = "Control nutricional recomendado"
    else:
        categoria = "obesidad"
        recomendacion = "Seguimiento especializado recomendado"

    return {"categoria": categoria, "recomendacion": recomendacion, "imc": imc}
