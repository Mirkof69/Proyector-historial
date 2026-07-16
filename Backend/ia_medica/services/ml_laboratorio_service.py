"""=============================================================================
SERVICIO ML - Machine Learning para Análisis de Laboratorio
=============================================================================
Sistema predictivo para detectar patologías en resultados de laboratorio
Especializado en ginecología y obstetricia
=============================================================================
"""

from typing import Any

from django.utils import timezone


class MLLaboratorioService:
    """Servicio de Machine Learning para análisis predictivo de laboratorio
    """

    def __init__(self):
        """Inicializar rangos de referencia y reglas clínicas"""
        # Rangos normales para embarazo (valores de referencia médica real)
        self.rangos_normales = {
            # Hemograma
            "hemoglobina": {
                "min": 11.0,
                "max": 14.0,
                "unidad": "g/dL",
                "nombre": "Hemoglobina",
            },
            "hematocrito": {
                "min": 33.0,
                "max": 44.0,
                "unidad": "%",
                "nombre": "Hematocrito",
            },
            "leucocitos": {
                "min": 6000,
                "max": 17000,
                "unidad": "/µL",
                "nombre": "Leucocitos",
            },
            "plaquetas": {
                "min": 150000,
                "max": 400000,
                "unidad": "/µL",
                "nombre": "Plaquetas",
            },
            # Glucosa
            "glucosa_basal": {
                "min": 60,
                "max": 92,
                "unidad": "mg/dL",
                "nombre": "Glucosa Basal",
            },
            "glucosa_1h": {
                "min": 0,
                "max": 180,
                "unidad": "mg/dL",
                "nombre": "Glucosa 1 hora",
            },
            "glucosa_2h": {
                "min": 0,
                "max": 153,
                "unidad": "mg/dL",
                "nombre": "Glucosa 2 horas",
            },
            "hba1c": {"min": 4.0, "max": 5.7, "unidad": "%", "nombre": "HbA1c"},
            # Función Hepática
            "tgo_ast": {"min": 10, "max": 35, "unidad": "U/L", "nombre": "TGO/AST"},
            "tgp_alt": {"min": 10, "max": 35, "unidad": "U/L", "nombre": "TGP/ALT"},
            "bilirrubina_total": {
                "min": 0.1,
                "max": 1.2,
                "unidad": "mg/dL",
                "nombre": "Bilirrubina Total",
            },
            "fosfatasa_alcalina": {
                "min": 35,
                "max": 250,
                "unidad": "U/L",
                "nombre": "Fosfatasa Alcalina",
            },
            "ldh": {"min": 200, "max": 400, "unidad": "U/L", "nombre": "LDH"},
            # Función Renal
            "creatinina": {
                "min": 0.4,
                "max": 0.9,
                "unidad": "mg/dL",
                "nombre": "Creatinina",
            },
            "urea": {"min": 10, "max": 40, "unidad": "mg/dL", "nombre": "Urea"},
            "acido_urico": {
                "min": 2.5,
                "max": 5.5,
                "unidad": "mg/dL",
                "nombre": "Ácido Úrico",
            },
            # Proteínas
            "proteinas_totales": {
                "min": 6.0,
                "max": 8.0,
                "unidad": "g/dL",
                "nombre": "Proteínas Totales",
            },
            "albumina": {
                "min": 3.0,
                "max": 5.0,
                "unidad": "g/dL",
                "nombre": "Albúmina",
            },
            "proteinuria_24h": {
                "min": 0,
                "max": 300,
                "unidad": "mg/24h",
                "nombre": "Proteinuria 24h",
            },
            # Tiroides
            "tsh": {"min": 0.5, "max": 2.5, "unidad": "µUI/mL", "nombre": "TSH"},
            "t4_libre": {
                "min": 0.8,
                "max": 1.8,
                "unidad": "ng/dL",
                "nombre": "T4 Libre",
            },
        }

    def analizar_hemograma(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Analiza hemograma completo
        """
        resultados: dict[str, Any] = {
            "valores_anormales": [],
            "patologias_detectadas": [],
            "alertas": [],
            "recomendaciones": [],
            "riesgo": "bajo",
        }

        # Hemoglobina
        hb = datos.get("hemoglobina")
        if hb:
            if hb < 9:
                resultados["patologias_detectadas"].append("Anemia Severa")
                resultados["alertas"].append(
                    "⚠️ CRÍTICO: Hemoglobina < 9 g/dL - Requiere atención inmediata",
                )
                resultados["recomendaciones"].append(
                    "Transfusión sanguínea si Hb < 7 g/dL",
                )
                resultados["recomendaciones"].append("Hierro endovenoso")
                resultados["riesgo"] = "critico"
            elif hb < 11:
                resultados["patologias_detectadas"].append("Anemia Moderada")
                resultados["alertas"].append(
                    "⚠️ Anemia gestacional - Requiere suplementación",
                )
                resultados["recomendaciones"].append("Sulfato ferroso 325mg/día")
                resultados["recomendaciones"].append("Ácido fólico 1mg/día")
                resultados["riesgo"] = (
                    max(resultados["riesgo"], "medio")
                    if resultados["riesgo"] != "critico"
                    else "critico"
                )

            if hb and (hb < 11 or hb > 14):
                resultados["valores_anormales"].append(
                    {
                        "parametro": "Hemoglobina",
                        "valor": hb,
                        "rango_normal": "11-14 g/dL",
                        "estado": "bajo" if hb < 11 else "alto",
                    },
                )

        # Plaquetas
        plaq = datos.get("plaquetas")
        if plaq:
            if plaq < 100000:
                resultados["patologias_detectadas"].append("Trombocitopenia")
                resultados["alertas"].append(
                    "⚠️ CRÍTICO: Plaquetas bajas - Riesgo de sangrado",
                )
                resultados["recomendaciones"].append("Descartar HELLP syndrome")
                resultados["recomendaciones"].append("Evaluación hematológica urgente")
                resultados["riesgo"] = "critico"
            elif plaq < 150000:
                resultados["alertas"].append(
                    "Plaquetas levemente disminuidas - Monitorear",
                )
                resultados["riesgo"] = (
                    max(resultados["riesgo"], "medio")
                    if resultados["riesgo"] != "critico"
                    else "critico"
                )

            if plaq and (plaq < 150000 or plaq > 400000):
                resultados["valores_anormales"].append(
                    {
                        "parametro": "Plaquetas",
                        "valor": plaq,
                        "rango_normal": "150,000-400,000 /µL",
                        "estado": "bajo" if plaq < 150000 else "alto",
                    },
                )

        return resultados

    def analizar_glucosa(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Analiza perfil de glucosa para diabetes gestacional
        """
        resultados: dict[str, Any] = {
            "valores_anormales": [],
            "patologias_detectadas": [],
            "alertas": [],
            "recomendaciones": [],
            "riesgo": "bajo",
        }

        glucosa_basal = datos.get("glucosa_basal")
        glucosa_1h = datos.get("glucosa_1h")
        glucosa_2h = datos.get("glucosa_2h")

        # Criterios de diabetes gestacional (ADA 2024)
        if glucosa_basal:
            if glucosa_basal >= 126:
                resultados["patologias_detectadas"].append(
                    "Diabetes Gestacional - Confirmado",
                )
                resultados["alertas"].append(" DIABETES GESTACIONAL CONFIRMADA")
                resultados["recomendaciones"].append("Iniciar insulina NPH + rápida")
                resultados["recomendaciones"].append("Monitoreo glicémico 4 veces/día")
                resultados["recomendaciones"].append("Dieta ADA 2000-2500 kcal/día")
                resultados["riesgo"] = "alto"
            elif glucosa_basal >= 92:
                resultados["patologias_detectadas"].append("Diabetes Gestacional")
                resultados["alertas"].append(
                    "⚠️ Glucosa basal elevada - Diabetes Gestacional",
                )
                resultados["recomendaciones"].append("Dieta diabética estricta")
                resultados["recomendaciones"].append("Automonitoreo glicémico")
                resultados["recomendaciones"].append("Consulta nutrición")
                resultados["riesgo"] = "alto"

            if glucosa_basal >= 92:
                resultados["valores_anormales"].append(
                    {
                        "parametro": "Glucosa Basal",
                        "valor": glucosa_basal,
                        "rango_normal": "60-92 mg/dL",
                        "estado": "alto",
                    },
                )

        # Test O'Sullivan / PTOG
        if glucosa_1h and glucosa_1h >= 180:
            resultados["alertas"].append("⚠️ Test O'Sullivan positivo - Requiere PTOG")
            resultados["recomendaciones"].append("Realizar PTOG 100g")
            resultados["riesgo"] = (
                max(resultados["riesgo"], "medio")
                if resultados["riesgo"] != "alto"
                else "alto"
            )

        if glucosa_2h and glucosa_2h >= 153:
            resultados["patologias_detectadas"].append("Intolerancia a Glucosa")
            resultados["alertas"].append("⚠️ Glucosa 2h elevada")
            resultados["recomendaciones"].append("Dieta y ejercicio")
            resultados["riesgo"] = (
                max(resultados["riesgo"], "medio")
                if resultados["riesgo"] != "alto"
                else "alto"
            )

        return resultados

    def analizar_funcion_hepatica(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Analiza función hepática - Detecta HELLP syndrome
        """
        resultados: dict[str, Any] = {
            "valores_anormales": [],
            "patologias_detectadas": [],
            "alertas": [],
            "recomendaciones": [],
            "riesgo": "bajo",
        }

        tgo = datos.get("tgo_ast")
        tgp = datos.get("tgp_alt")
        ldh = datos.get("ldh")
        plaquetas = datos.get("plaquetas", 150000)

        # Detección de HELLP Syndrome
        hellp_score = 0

        if tgo and tgo > 70:
            hellp_score += 1
        if tgp and tgp > 70:
            hellp_score += 1
        if ldh and ldh > 600:
            hellp_score += 1
        if plaquetas < 100000:
            hellp_score += 1

        if hellp_score >= 2:
            resultados["patologias_detectadas"].append("HELLP Syndrome Sospechoso")
            resultados["alertas"].append(" EMERGENCIA: Sospecha de HELLP Syndrome")
            resultados["recomendaciones"].append("HOSPITALIZACIÓN INMEDIATA")
            resultados["recomendaciones"].append(
                "Sulfato de Magnesio profilaxis eclampsia",
            )
            resultados["recomendaciones"].append(
                "Evaluación de finalización de embarazo",
            )
            resultados["recomendaciones"].append("Laboratorio c/6h")
            resultados["riesgo"] = "critico"

        elif tgo and tgp and (tgo > 40 or tgp > 40):
            resultados["patologias_detectadas"].append("Elevación de Transaminasas")
            resultados["alertas"].append("⚠️ Función hepática alterada")
            resultados["recomendaciones"].append(
                "Monitoreo estrecho de función hepática",
            )
            resultados["recomendaciones"].append("Evaluar preeclampsia")
            resultados["riesgo"] = "alto"

        return resultados

    def analizar_funcion_renal(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Analiza función renal - Detecta preeclampsia
        """
        resultados: dict[str, Any] = {
            "valores_anormales": [],
            "patologias_detectadas": [],
            "alertas": [],
            "recomendaciones": [],
            "riesgo": "bajo",
        }

        creatinina = datos.get("creatinina")
        proteinuria = datos.get("proteinuria_24h")
        presion_sistolica = datos.get("presion_sistolica", 0)
        presion_diastolica = datos.get("presion_diastolica", 0)

        # Criterios de preeclampsia
        if proteinuria and proteinuria > 300:
            if presion_sistolica >= 140 or presion_diastolica >= 90:
                resultados["patologias_detectadas"].append("Preeclampsia Confirmada")
                resultados["alertas"].append(
                    " PREECLAMPSIA - Requiere manejo urgente",
                )
                resultados["recomendaciones"].append("Hospitalización si PA ≥ 160/110")
                resultados["recomendaciones"].append(
                    "Laboratorio completo (hemograma, función hepática, renal)",
                )
                resultados["recomendaciones"].append(
                    "Evaluación de bienestar fetal (NST, Doppler)",
                )
                resultados["recomendaciones"].append(
                    "Considerar finalización si >34 semanas",
                )
                resultados["riesgo"] = "critico"
            else:
                resultados["alertas"].append("⚠️ Proteinuria significativa")
                resultados["recomendaciones"].append("Monitoreo de presión arterial")
                resultados["riesgo"] = "alto"

        if creatinina and creatinina > 1.1:
            resultados["patologias_detectadas"].append("Insuficiencia Renal")
            resultados["alertas"].append(
                "⚠️ Creatinina elevada - Deterioro de función renal",
            )
            resultados["recomendaciones"].append("Evaluación nefrológica")
            resultados["riesgo"] = "alto"

        return resultados

    def analizar_completo(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Análisis completo de todos los parámetros de laboratorio
        """
        resultado_final: dict[str, Any] = {
            "paciente_id": datos.get("paciente_id"),
            "fecha_analisis": timezone.localtime().isoformat(),
            "datos_entrada": datos,
            "valores_anormales": [],
            "patologias_detectadas": [],
            "alertas_criticas": [],
            "recomendaciones": [],
            "riesgo_global": "bajo",
            # HONESTIDAD CLÍNICA: este servicio NO es un modelo de ML entrenado.
            # Es análisis por reglas sobre umbrales de laboratorio (hemograma,
            # glucosa, hepática, renal). "confianza"/"probabilidad" son
            # heurísticas derivadas de esas reglas, no salidas de un modelo.
            "metodo": "reglas_clinicas_por_umbral",
            "es_modelo_entrenado": False,
            "confianza_modelo": 0.0,
            "acciones_sugeridas": [],
        }

        # Análisis por secciones
        analisis_hemograma = self.analizar_hemograma(datos)
        analisis_glucosa = self.analizar_glucosa(datos)
        analisis_hepatica = self.analizar_funcion_hepatica(datos)
        analisis_renal = self.analizar_funcion_renal(datos)

        # Consolidar resultados
        for analisis in [
            analisis_hemograma,
            analisis_glucosa,
            analisis_hepatica,
            analisis_renal,
        ]:
            resultado_final["valores_anormales"].extend(analisis["valores_anormales"])
            resultado_final["patologias_detectadas"].extend(
                analisis["patologias_detectadas"],
            )
            resultado_final["alertas_criticas"].extend(analisis["alertas"])
            resultado_final["recomendaciones"].extend(analisis["recomendaciones"])

        # Determinar riesgo global (el más alto)
        riesgos = [
            analisis_hemograma["riesgo"],
            analisis_glucosa["riesgo"],
            analisis_hepatica["riesgo"],
            analisis_renal["riesgo"],
        ]

        orden_riesgos = {"critico": 4, "alto": 3, "medio": 2, "bajo": 1}
        riesgo_maximo = max(riesgos, key=lambda x: orden_riesgos.get(x, 0))
        resultado_final["riesgo_global"] = riesgo_maximo

        # Calcular confianza del modelo
        total_parametros = len([k for k in datos if k in self.rangos_normales])
        if total_parametros > 0:
            # Confianza basada en cantidad de datos
            confianza = min(70 + (total_parametros * 3), 95)
            resultado_final["confianza_modelo"] = round(confianza, 1)
        else:
            resultado_final["confianza_modelo"] = 50.0

        # Acciones sugeridas según riesgo
        if riesgo_maximo == "critico":
            resultado_final["acciones_sugeridas"] = [
                "HOSPITALIZACIÓN INMEDIATA",
                "Evaluación médica urgente",
                "Laboratorio de control en 6-12 horas",
                "Evaluación de bienestar fetal",
            ]
        elif riesgo_maximo == "alto":
            resultado_final["acciones_sugeridas"] = [
                "Consulta médica en 24-48 horas",
                "Repetir laboratorio en 1 semana",
                "Monitoreo ambulatorio estricto",
            ]
        elif riesgo_maximo == "medio":
            resultado_final["acciones_sugeridas"] = [
                "Control prenatal en 1-2 semanas",
                "Repetir laboratorio en 2-4 semanas",
                "Seguir recomendaciones médicas",
            ]
        else:
            resultado_final["acciones_sugeridas"] = [
                "Valores dentro de rango normal",
                "Continuar control prenatal rutinario",
            ]

        # Resumen heurístico basado en las reglas de arriba (NO es la salida de
        # un modelo entrenado; ver "metodo"/"es_modelo_entrenado" en el resultado).
        if resultado_final["patologias_detectadas"]:
            resultado_final["prediccion"] = (
                f"Detectadas {len(resultado_final['patologias_detectadas'])} patologías - Requiere atención médica"
            )
            resultado_final["probabilidad"] = 0.85
        else:
            resultado_final["prediccion"] = (
                "Resultados dentro de parámetros normales para embarazo"
            )
            resultado_final["probabilidad"] = 0.15

        return resultado_final


# Instancia global del servicio
ml_laboratorio_service = MLLaboratorioService()
