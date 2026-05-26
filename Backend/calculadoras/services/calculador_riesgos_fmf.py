"""=============================================================================
CALCULADOR DE RIESGOS FMF (FETAL MEDICINE FOUNDATION)
=============================================================================
Implementación completa del modelo Bayesiano para cálculo de riesgos:
    pass
- Preeclampsia (temprana <34s, tardía <37s, término)
- Trisomías (T21, T18, T13)
- SGA/FGR
- Parto prematuro

Basado en publicaciones FMF 2023
=============================================================================
"""


from .calculador_mom import CalculadorMoM


class CalculadorRiesgosFMF:
    """Calculador de riesgos obstétricos según algoritmos FMF
    """

    # =============================================================================
    # PREECLAMPSIA - RIESGOS BASALES POR EDAD (%)
    # =============================================================================

    RIESGO_BASAL_PE_EDAD = {
        15: 0.8,
        20: 0.9,
        25: 1.0,
        30: 1.2,
        35: 1.8,
        40: 3.5,
        45: 6.0,
    }

    @staticmethod
    def calcular_riesgo_preeclampsia_completo(
        edad_materna: int,
        peso_kg: float,
        talla_cm: float,
        semanas: int,
        origen_etnico: str = "mestizo",
        metodo_concepcion: str = "espontaneo",
        fumadora: bool = False,
        hipertension_cronica: bool = False,
        diabetes_tipo1: bool = False,
        diabetes_tipo2: bool = False,
        lupus: bool = False,
        sindrome_antifosfolipidos: bool = False,
        historia_preeclampsia: bool = False,
        intervalo_embarazo_meses: int | None = None,
        # Biomarcadores
        pas_mmhg: float | None = None,
        pad_mmhg: float | None = None,
        utap_ip_promedio: float | None = None,
        plgf_pg_ml: float | None = None,
    ) -> dict:
        """Cálculo COMPLETO de riesgo de preeclampsia según FMF

        Returns:
            Dict con riesgo_basal, riesgo_ajustado_historia, riesgo_ajustado_biomarcadores,
            riesgo_final, clasificacion, requiere_aspirina, MoM de biomarcadores

        """
        # 1. RIESGO BASAL (EDAD)
        riesgo_basal = CalculadorRiesgosFMF._obtener_riesgo_basal_edad(edad_materna)

        # 2. LIKELIHOOD RATIOS POR HISTORIA CLÍNICA
        lr_historia = 1.0

        # IMC
        imc = peso_kg / ((talla_cm / 100) ** 2)
        if imc >= 35:
            lr_historia *= 4.0
        elif imc >= 30:
            lr_historia *= 2.5
        elif imc >= 25:
            lr_historia *= 1.5

        # Etnia
        if origen_etnico == "afro":
            lr_historia *= 1.8
        elif origen_etnico == "asiatico":
            lr_historia *= 1.2

        # Método de concepción
        if metodo_concepcion in ["fiv", "ovodonacion"]:
            lr_historia *= 1.7
        elif metodo_concepcion == "icsi":
            lr_historia *= 1.4

        # Factores médicos
        if hipertension_cronica:
            lr_historia *= 3.0
        if diabetes_tipo1:
            lr_historia *= 3.0
        if diabetes_tipo2:
            lr_historia *= 2.5
        if lupus:
            lr_historia *= 4.0
        if sindrome_antifosfolipidos:
            lr_historia *= 6.0
        if historia_preeclampsia:
            lr_historia *= 8.0

        # Intervalo intergenésico
        if intervalo_embarazo_meses:
            if intervalo_embarazo_meses < 6:
                lr_historia *= 2.0
            elif intervalo_embarazo_meses > 120:
                lr_historia *= 1.5

        # Tabaquismo (protector paradójico)
        if fumadora:
            lr_historia *= 0.7

        # Riesgo ajustado por historia
        riesgo_ajustado_historia = riesgo_basal * lr_historia

        # 3. LIKELIHOOD RATIOS POR BIOMARCADORES
        lr_biomarcadores = 1.0
        mom_values = {}

        # MAP (Presión Arterial Media)
        if pas_mmhg and pad_mmhg:
            map_value = (pas_mmhg + 2 * pad_mmhg) / 3
            map_mom = CalculadorRiesgosFMF._calcular_map_mom(map_value, semanas)
            mom_values["map_mom"] = map_mom

            if map_mom > 1.2:
                lr_biomarcadores *= 3.5
            elif map_mom > 1.1:
                lr_biomarcadores *= 2.0

        # UtA-PI (Doppler arterias uterinas)
        if utap_ip_promedio:
            utap_mom = CalculadorRiesgosFMF._calcular_utap_mom(
                utap_ip_promedio, semanas,
            )
            mom_values["utap_mom"] = utap_mom

            if utap_mom > 1.5:
                lr_biomarcadores *= 8.0
            elif utap_mom > 1.2:
                lr_biomarcadores *= 4.0

        # PlGF (Factor de crecimiento placentario)
        if plgf_pg_ml:

            plgf_mom = float(
                CalculadorMoM.calcular_mom(
                    valor_medido=plgf_pg_ml,
                    marcador="PLGF",
                    semanas=semanas,
                    peso_kg=peso_kg,
                    etnia=origen_etnico,
                    fumadora=fumadora,
                    altitud_bolivia=True,
                ),
            )
            mom_values["plgf_mom"] = plgf_mom

            if plgf_mom < 0.3:
                lr_biomarcadores *= 15.0
            elif plgf_mom < 0.5:
                lr_biomarcadores *= 8.0
            elif plgf_mom < 0.8:
                lr_biomarcadores *= 3.0

        # Riesgo final
        riesgo_ajustado_biomarcadores = riesgo_ajustado_historia * lr_biomarcadores
        riesgo_final = min(riesgo_ajustado_biomarcadores, 99.9)  # Cap al 99.9%

        # 4. CLASIFICACIÓN
        if riesgo_final >= 10:
            clasificacion = "ALTO"
            requiere_aspirina = True
        elif riesgo_final >= 5:
            clasificacion = "INTERMEDIO"
            requiere_aspirina = False
        elif riesgo_final >= 1:
            clasificacion = "MEDIO"
            requiere_aspirina = False
        else:
            clasificacion = "BAJO"
            requiere_aspirina = False

        # 5. FACTORES DE RIESGO PRESENTES
        factores_riesgo = []
        if imc >= 30:
            factores_riesgo.append(f"Obesidad (IMC {imc:.1f})")
        if hipertension_cronica:
            factores_riesgo.append("Hipertensión crónica")
        if diabetes_tipo1 or diabetes_tipo2:
            factores_riesgo.append("Diabetes preexistente")
        if lupus:
            factores_riesgo.append("Lupus eritematoso sistémico")
        if sindrome_antifosfolipidos:
            factores_riesgo.append("Síndrome antifosfolípidos")
        if historia_preeclampsia:
            factores_riesgo.append("Historia de preeclampsia")
        if utap_ip_promedio and mom_values.get("utap_mom", 0) > 1.2:
            factores_riesgo.append("Doppler arterias uterinas anormal")
        if plgf_pg_ml and mom_values.get("plgf_mom", 1.0) < 0.8:
            factores_riesgo.append("PlGF bajo")

        # 6. RECOMENDACIONES
        recomendaciones = []
        if requiere_aspirina:
            recomendaciones.append(
                "✅ ASPIRINA 150 mg/día VO antes de las 16 semanas (idealmente antes de 12s)",
            )
            recomendaciones.append("Continuar hasta las 36 semanas")
        if riesgo_final >= 5:
            recomendaciones.append("Control Doppler cada 2-4 semanas")
            recomendaciones.append("Vigilancia estricta de PA en cada control")
            recomendaciones.append("Proteinuria mensual")
        if riesgo_final >= 10:
            recomendaciones.append("⚠️ Seguimiento en alto riesgo obstétrico")
            recomendaciones.append("Ecografía Doppler cada 2 semanas")
            recomendaciones.append("Considerar hospitalización si deterioro")

        # RESULTADO FINAL
        return {
            "riesgo_basal": round(riesgo_basal, 3),
            "riesgo_ajustado_historia": round(riesgo_ajustado_historia, 3),
            "riesgo_ajustado_biomarcadores": round(riesgo_ajustado_biomarcadores, 3),
            "riesgo_final": round(riesgo_final, 3),
            "clasificacion_riesgo": clasificacion,
            "requiere_aspirina": requiere_aspirina,
            "factores_riesgo_presentes": factores_riesgo,
            "recomendaciones": recomendaciones,
            "mom_pam": mom_values.get("map_mom"),
            "mom_utap": mom_values.get("utap_mom"),
            "mom_plg": mom_values.get("plgf_mom"),
            "lr_historia": round(lr_historia, 2),
            "lr_biomarcadores": round(lr_biomarcadores, 2),
            "imc": round(imc, 1),
        }

    @staticmethod
    def _obtener_riesgo_basal_edad(edad: int) -> float:
        """Obtiene riesgo basal por edad con interpolación"""
        edades = sorted(CalculadorRiesgosFMF.RIESGO_BASAL_PE_EDAD.keys())

        if edad <= min(edades):
            return CalculadorRiesgosFMF.RIESGO_BASAL_PE_EDAD[min(edades)]
        if edad >= max(edades):
            return CalculadorRiesgosFMF.RIESGO_BASAL_PE_EDAD[max(edades)]

        # Interpolación lineal
        for i in range(len(edades) - 1):
            e1, e2 = edades[i], edades[i + 1]
            if e1 <= edad <= e2:
                r1, r2 = (
                    CalculadorRiesgosFMF.RIESGO_BASAL_PE_EDAD[e1],
                    CalculadorRiesgosFMF.RIESGO_BASAL_PE_EDAD[e2],
                )
                return r1 + (r2 - r1) * (edad - e1) / (e2 - e1)

        return 1.0

    @staticmethod
    def _calcular_map_mom(map_value: float, semanas: int) -> float:
        """Calcula MoM de MAP"""
        # Medianas esperadas MAP por semana
        medianas_map = {11: 85.0, 12: 86.0, 13: 87.0, 20: 88.0, 22: 89.0, 24: 90.0}

        mediana = medianas_map.get(semanas, 87.0)
        mom = map_value / mediana
        return round(mom, 3)

    @staticmethod
    def _calcular_utap_mom(utap_value: float, semanas: int) -> float:
        """Calcula MoM de UtA-PI"""
        mediana = CalculadorMoM.obtener_mediana_esperada("UTA_PI", semanas)
        mom = utap_value / mediana
        return round(mom, 3)

    # =============================================================================
    # TRISOMÍAS - SCREENING COMBINADO T1
    # =============================================================================

    @staticmethod
    def calcular_riesgo_trisomias(
        edad_materna: int,
        semanas: int,
        translucencia_nucal_mm: float,
        papp_a_mom: float | None = None,
        free_bhcg_mom: float | None = None,
        hueso_nasal_presente: bool | None = None,
        flujo_ductus_venoso: str | None = None,  # 'normal', 'anormal'
        regurgitacion_tricuspidea: bool = False,
    ) -> dict:
        """Cálculo de riesgo de trisomías 21, 18 y 13

        Returns:
            Dict con riesgos para T21, T18, T13

        """
        # 1. RIESGO BASAL POR EDAD (T21)
        riesgo_basal_t21 = CalculadorRiesgosFMF._riesgo_basal_trisomia_edad(
            edad_materna, 21,
        )
        riesgo_basal_t18 = CalculadorRiesgosFMF._riesgo_basal_trisomia_edad(
            edad_materna, 18,
        )
        riesgo_basal_t13 = CalculadorRiesgosFMF._riesgo_basal_trisomia_edad(
            edad_materna, 13,
        )

        # 2. LIKELIHOOD RATIO POR TN (Translucencia Nucal)
        # CRL esperado para la semana
        crl_mm = semanas * 7 * 10  # Aproximación simple
        tn_esperada = CalculadorRiesgosFMF._tn_esperada_crl(crl_mm)
        delta_tn = translucencia_nucal_mm - tn_esperada

        # LR según delta TN
        if delta_tn > 2.0:
            lr_tn_t21 = 20.0
            lr_tn_t18 = 25.0
            lr_tn_t13 = 15.0
        elif delta_tn > 1.0:
            lr_tn_t21 = 8.0
            lr_tn_t18 = 10.0
            lr_tn_t13 = 6.0
        elif delta_tn > 0.5:
            lr_tn_t21 = 3.0
            lr_tn_t18 = 3.5
            lr_tn_t13 = 2.5
        elif delta_tn < -0.5:
            lr_tn_t21 = 0.3
            lr_tn_t18 = 0.2
            lr_tn_t13 = 0.3
        else:
            lr_tn_t21 = 1.0
            lr_tn_t18 = 1.0
            lr_tn_t13 = 1.0

        # 3. LR POR BIOQUÍMICA
        lr_biochem_t21 = 1.0
        lr_biochem_t18 = 1.0
        lr_biochem_t13 = 1.0

        if papp_a_mom:
            if papp_a_mom < 0.3:
                lr_biochem_t21 *= 4.0
                lr_biochem_t18 *= 8.0
            elif papp_a_mom < 0.5:
                lr_biochem_t21 *= 2.5
                lr_biochem_t18 *= 5.0
            elif papp_a_mom < 0.8:
                lr_biochem_t21 *= 1.5
                lr_biochem_t18 *= 2.0

        if free_bhcg_mom:
            if free_bhcg_mom > 2.0:
                lr_biochem_t21 *= 3.0
            elif free_bhcg_mom > 1.5:
                lr_biochem_t21 *= 1.8
            elif free_bhcg_mom < 0.5:
                lr_biochem_t18 *= 3.0
                lr_biochem_t13 *= 2.0

        # 4. LR POR MARCADORES ADICIONALES
        if hueso_nasal_presente is False:
            lr_tn_t21 *= 15.0
            lr_tn_t18 *= 8.0

        if flujo_ductus_venoso == "anormal":
            lr_tn_t21 *= 6.0
            lr_tn_t18 *= 10.0

        if regurgitacion_tricuspidea:
            lr_tn_t21 *= 4.0
            lr_tn_t18 *= 8.0

        # 5. RIESGO AJUSTADO FINAL
        riesgo_t21_ajustado = riesgo_basal_t21 * lr_tn_t21 * lr_biochem_t21
        riesgo_t18_ajustado = riesgo_basal_t18 * lr_tn_t18 * lr_biochem_t18
        riesgo_t13_ajustado = riesgo_basal_t13 * lr_tn_t13 * lr_biochem_t13

        # Límite 99.9%
        riesgo_t21_ajustado = min(riesgo_t21_ajustado, 99.9)
        riesgo_t18_ajustado = min(riesgo_t18_ajustado, 99.9)
        riesgo_t13_ajustado = min(riesgo_t13_ajustado, 99.9)

        # 6. CLASIFICACIÓN
        clasificacion_t21 = CalculadorRiesgosFMF._clasificar_riesgo_trisomia(
            riesgo_t21_ajustado,
        )
        clasificacion_t18 = CalculadorRiesgosFMF._clasificar_riesgo_trisomia(
            riesgo_t18_ajustado,
        )
        clasificacion_t13 = CalculadorRiesgosFMF._clasificar_riesgo_trisomia(
            riesgo_t13_ajustado,
        )

        # ¿Requiere prueba invasiva
        requiere_prueba_invasiva = (
            riesgo_t21_ajustado >= 1.0
            or riesgo_t18_ajustado >= 1.0
            or riesgo_t13_ajustado >= 1.0
        )

        # Recomendaciones
        recomendaciones = []
        if requiere_prueba_invasiva:
            recomendaciones.append("⚠️ ALTO RIESGO - Asesoramiento genético recomendado")
            recomendaciones.append(
                "Considerar amniocentesis o biopsia de vellosidades coriales",
            )
            recomendaciones.append("Opción: NIPT (cfDNA) como alternativa no invasiva")
        else:
            recomendaciones.append("✅ Riesgo bajo - Continuar controles habituales")
            recomendaciones.append("Ecografía morfológica 18-22 semanas")

        return {
            "riesgo_t21_basal": round(riesgo_basal_t21, 4),
            "riesgo_t21_ajustado": round(riesgo_t21_ajustado, 4),
            "riesgo_t18_basal": round(riesgo_basal_t18, 4),
            "riesgo_t18_ajustado": round(riesgo_t18_ajustado, 4),
            "riesgo_t13_basal": round(riesgo_basal_t13, 4),
            "riesgo_t13_ajustado": round(riesgo_t13_ajustado, 4),
            "clasificacion_t21": clasificacion_t21,
            "clasificacion_t18": clasificacion_t18,
            "clasificacion_t13": clasificacion_t13,
            "requiere_prueba_invasiva": requiere_prueba_invasiva,
            "recomendaciones": recomendaciones,
            "likelihood_ratios": {
                "lr_tn_t21": round(lr_tn_t21, 2),
                "lr_tn_t18": round(lr_tn_t18, 2),
                "lr_tn_t13": round(lr_tn_t13, 2),
                "lr_biochem_t21": round(lr_biochem_t21, 2),
            },
            "delta_tn": round(delta_tn, 2),
            "tn_esperada": round(tn_esperada, 2),
        }

    @staticmethod
    def _riesgo_basal_trisomia_edad(edad: int, trisomia: int) -> float:
        """Riesgo basal de trisomía según edad materna"""
        # Tabla edad vs riesgo T21 (%)
        tabla_t21 = {
            20: 0.06,
            25: 0.08,
            30: 0.12,
            31: 0.15,
            32: 0.19,
            33: 0.24,
            34: 0.30,
            35: 0.38,
            36: 0.48,
            37: 0.61,
            38: 0.77,
            39: 0.97,
            40: 1.23,
            41: 1.56,
            42: 1.97,
            43: 2.49,
            44: 3.14,
            45: 3.97,
        }

        # T18 y T13 son menos frecuentes
        if trisomia == 21:
            tabla = tabla_t21
        elif trisomia == 18:
            tabla = {k: v * 0.3 for k, v in tabla_t21.items()}
        elif trisomia == 13:
            tabla = {k: v * 0.2 for k, v in tabla_t21.items()}
        else:
            return 0.1

        # Interpolación
        edades = sorted(tabla.keys())
        if edad <= min(edades):
            return tabla[min(edades)]
        if edad >= max(edades):
            return tabla[max(edades)]

        for i in range(len(edades) - 1):
            e1, e2 = edades[i], edades[i + 1]
            if e1 <= edad <= e2:
                r1, r2 = tabla[e1], tabla[e2]
                return r1 + (r2 - r1) * (edad - e1) / (e2 - e1)

        return 0.1

    @staticmethod
    def _tn_esperada_crl(crl_mm: float) -> float:
        """TN esperada según CRL (mm)"""
        # Fórmula FMF: TN = 0.0154 * CRL + 0.8
        tn = 0.0154 * crl_mm + 0.8
        return max(tn, 1.0)

    @staticmethod
    def _clasificar_riesgo_trisomia(riesgo_pct: float) -> str:
        """Clasificación de riesgo de trisomía"""
        if riesgo_pct >= 1.0:  # 1:100 o mayor
            return "ALTO"
        if riesgo_pct >= 0.1:  # 1:
            return "INTERMEDIO"
        return "BAJO"


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    calculador = CalculadorRiesgosFMF()

    # Ejemplo Preeclampsia
    resultado_pe = calculador.calcular_riesgo_preeclampsia_completo(
        edad_materna=35,
        peso_kg=75,
        talla_cm=160,
        semanas=12,
        origen_etnico="mestizo",
        hipertension_cronica=True,
        historia_preeclampsia=False,
        pas_mmhg=125,
        pad_mmhg=80,
        utap_ip_promedio=1.45,
        plgf_pg_ml=38.5,
    )

    print("=" * 60)
    print("RESULTADO SCREENING PREECLAMPSIA")
    print("=" * 60)
    print(f"Riesgo basal (edad): {resultado_pe['riesgo_basal']}%")
    print(f"Riesgo ajustado (historia): {resultado_pe['riesgo_ajustado_historia']}%")
    print(f"RIESGO FINAL: {resultado_pe['riesgo_final']}%")
    print(f"Clasificación: {resultado_pe['clasificacion_riesgo']}")
    print(f"¿Requiere Aspirina: {resultado_pe['requiere_aspirina']}")
    print("\nFactores de riesgo:")
    for factor in resultado_pe["factores_riesgo_presentes"]:
        print(f"  - {factor}")
    print("\nRecomendaciones:")
    for rec in resultado_pe["recomendaciones"]:
        print(f"  • {rec}")
