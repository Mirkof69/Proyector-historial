"""=============================================================================
SERVICIO DE CÁLCULO DE RIESGOS - ALGORITMOS FMF
=============================================================================
Implementa algoritmos Bayesianos y modelos de riesgo competitivo
según protocolos Fetal Medicine Foundation

Calculadoras:
    pass
1. Preeclampsia (1º, 2º, 3º trimestre)
2. Trisomías 21, 18, 13 (cribado combinado)
3. Diabetes Gestacional
=============================================================================
"""

import math
from typing import cast

from scipy.stats import norm


class RiskCalculator:
    """Calculador de riesgos obstétricos según FMF"""

    # ==========================================================================
    # 1. PREECLAMPSIA
    # ==========================================================================

    def calcular_riesgo_preeclampsia(
        self,
        edad_materna: int,
        imc: float,
        etnia: str,
        hta_cronica: bool,
        preeclampsia_previa: bool,
        diabetes: bool,
        lupus: bool,
        sindrome_antifosfolipido: bool,
        madre_con_pe: bool,
        paridad: int,
        intervalo_meses: int | None,
        metodo_concepcion: str,
        # Biomarcadores MoM
        pam_mom: float,
        utpi_mom: float,
        plgf_mom: float | None = None,
        sflt1_mom: float | None = None,
        pappa_mom: float | None = None,
        _bhcg_mom: float | None = None,
        # Edad gestacional
        edad_gestacional_semanas: int = 12,
    ) -> dict:
        """Calcula riesgo de preeclampsia usando modelo FMF

        Modelo: Competing Risks + Likelihood Ratios Bayesianos

        Returns:
            Dict con riesgo_porcentaje, riesgo_ratio, categoria, recomendaciones

        """
        # 1. RIESGO A PRIORI (basado en historia)
        riesgo_priori = self._calcular_riesgo_basal_pe(
            edad=edad_materna,
            imc=imc,
            etnia=etnia,
            hta_cronica=hta_cronica,
            pe_previa=preeclampsia_previa,
            diabetes=diabetes,
            lupus=lupus,
            saf=sindrome_antifosfolipido,
            madre_pe=madre_con_pe,
            paridad=paridad,
            intervalo_meses=intervalo_meses,
            ivf=(metodo_concepcion == "iv"),
        )

        # 2. LIKELIHOOD RATIOS de biomarcadores
        lr_pam = self._lr_biomarcador_pe(pam_mom, "PAM")
        lr_utpi = self._lr_biomarcador_pe(utpi_mom, "UTPI")

        # Biomarcadores opcionales (2º-3º trimestre)
        lr_plgf = self._lr_biomarcador_pe(plgf_mom, "PLGF") if plgf_mom else 1.0
        lr_sflt1 = self._lr_biomarcador_pe(sflt1_mom, "sFlt-1") if sflt1_mom else 1.0
        lr_pappa = self._lr_biomarcador_pe(pappa_mom, "PAPP-A") if pappa_mom else 1.0

        # 3. APLICAR TEOREMA DE BAYES
        # Riesgo posterior = Riesgo priori × ∏(LRs)

        odds_priori = riesgo_priori / (1 - riesgo_priori)
        odds_posterior = odds_priori * lr_pam * lr_utpi * lr_plgf * lr_sflt1 * lr_pappa

        riesgo_posterior = odds_posterior / (1 + odds_posterior)

        # 4. CATEGORIZAR RIESGO
        # Punto de corte FMF: ≥1:100 (1%) = Alto riesgo
        if riesgo_posterior >= 0.10:  # ≥10% = 1:10
            categoria = "critico"
            semaforo = "rojo"
        elif riesgo_posterior >= 0.01:  # ≥1% = 1:100
            categoria = "alto"
            semaforo = "rojo"
        elif riesgo_posterior >= 0.005:  # 0.5-1%
            categoria = "intermedio"
            semaforo = "amarillo"
        else:
            categoria = "bajo"
            semaforo = "verde"

        # 5. GENERAR RECOMENDACIONES
        recomendaciones = self._generar_recomendaciones_pe(
            riesgo_posterior, categoria, edad_gestacional_semanas,
        )

        # 6. INTERPRETACIÓN CLÍNICA
        interpretacion = self._interpretar_riesgo_pe(
            riesgo_posterior, pam_mom, utpi_mom, plgf_mom, categoria,
        )

        return {
            "riesgo_porcentaje": round(riesgo_posterior * 100, 2),
            "riesgo_ratio": f"1:{int(1 / riesgo_posterior)}"
            if riesgo_posterior > 0
            else "1:>999",
            "categoria_riesgo": categoria,
            "semaforo": semaforo,
            "riesgo_priori": round(riesgo_priori * 100, 2),
            "likelihood_ratios": {
                "PAM": round(lr_pam, 2),
                "UTPI": round(lr_utpi, 2),
                "PLGF": round(lr_plgf, 2) if plgf_mom else None,
                "sFlt-1": round(lr_sflt1, 2) if sflt1_mom else None,
            },
            "interpretacion_clinica": interpretacion,
            "recomendaciones": recomendaciones,
            "conducta_sugerida": self._conducta_pe(categoria, edad_gestacional_semanas),
        }

    def _calcular_riesgo_basal_pe(
        self,
        edad,
        imc,
        etnia,
        hta_cronica,
        pe_previa,
        diabetes,
        lupus,
        saf,
        madre_pe,
        paridad,
        intervalo_meses,
        ivf,
    ) -> float:
        """Riesgo basal de PE según características maternas (modelo FMF)"""
        # Riesgo base por edad (curva parabólica)
        if edad < 25:
            riesgo_edad = 0.02  # 2%
        elif edad <= 35:
            riesgo_edad = 0.015  # 1.5%
        elif edad <= 40:
            riesgo_edad = 0.025  # 2.5%
        else:
            riesgo_edad = 0.04  # 4%

        # Multiplicadores
        mult = 1.0

        if hta_cronica:
            mult *= 3.5
        if pe_previa:
            mult *= 8.0  # Muy alto
        if diabetes:
            mult *= 2.0
        if lupus or saf:
            mult *= 4.0
        if madre_pe:
            mult *= 1.5
        if imc >= 35:
            mult *= 2.5
        elif imc >= 30:
            mult *= 1.8
        if etnia == "afrocaribeña":
            mult *= 1.3
        if ivf:
            mult *= 1.2
        if paridad == 0:  # Nulípara
            mult *= 1.5
        elif intervalo_meses and intervalo_meses > 120:  # >10 años
            mult *= 1.3

        return min(riesgo_edad * mult, 0.50)  # Cap al 50%


    def _lr_biomarcador_pe(self, mom: float, marcador: str) -> float:
        """Likelihood Ratio para biomarcadores de PE

        LR = f(MoM | afectado) / f(MoM | no afectado)

        Usa distribuciones gaussianas según FMF
        """
        if mom is None:
            return 1.0

        # Parámetros distribuciones  (media, SD) para afectados y no afectados
        params = {
            "PAM": {
                "afectado": (1.20, 0.12),  # Media MoM 1.20, SD 0.12
                "no_afectado": (1.00, 0.10),
            },
            "UTPI": {
                "afectado": (1.40, 0.15),
                "no_afectado": (1.00, 0.12),
            },
            "PLGF": {
                "afectado": (0.50, 0.15),  # Bajo en PE
                "no_afectado": (1.00, 0.12),
            },
            "sFlt-1": {
                "afectado": (1.80, 0.20),  # Alto en PE
                "no_afectado": (1.00, 0.15),
            },
            "PAPP-A": {
                "afectado": (0.60, 0.18),  # Bajo en PE
                "no_afectado": (1.00, 0.12),
            },
        }

        if marcador not in params:
            return 1.0

        media_af, sd_af = params[marcador]["afectado"]
        media_no, sd_no = params[marcador]["no_afectado"]

        # Densidad de probabilidad
        prob_afectado = norm.pdf(mom, media_af, sd_af)
        prob_no_afectado = norm.pdf(mom, media_no, sd_no)

        if prob_no_afectado == 0:
            return 10.0  # Cap

        lr = prob_afectado / prob_no_afectado

        return cast(float, max(0.1, min(lr, 10.0)))  # LR entre 0.1 y 10

    def _generar_recomendaciones_pe(
        self, _riesgo: float, categoria: str, _eg_semanas: int,
    ) -> list[str]:
        """Genera recomendaciones según nivel de riesgo"""
        recomendaciones = []

        if categoria in ["alto", "critico"]:
            recomendaciones.append(
                " ASPIRINA PROFILÁCTICA: 150 mg/día vía oral, "
                "iniciar antes de 16 semanas hasta 36 semanas. "
                "Reduce riesgo de PE pretérmino en 62%.",
            )
            recomendaciones.append(" Vigilancia doppler: UtA-PI cada 2-4 semanas")
            recomendaciones.append(" PLGF/sFlt-1: Medir ratio a partir de 20 semanas")
            recomendaciones.append(
                " Controles prenatales: Cada 2 semanas desde 20s, semanales desde 32s",
            )
            recomendaciones.append(
                "⚠️ Educación signos alarma: Cefalea, alteraciones visuales, dolor epigástrico",
            )
        elif categoria == "intermedio":
            recomendaciones.append(
                " Aspirina: Considerar 100-150 mg/día (discutir riesgo/beneficio)",
            )
            recomendaciones.append(" Control doppler: UtA-PI a las 20-24 semanas")
            recomendaciones.append(
                " Seguimiento: Controles mensuales con PA y proteinuria",
            )
        else:
            recomendaciones.append(
                " Seguimiento rutinario: Controles prenatales estándar",
            )
            recomendaciones.append(" Educación: Signos de alarma de PE")

        return recomendaciones

    def _interpretar_riesgo_pe(
        self,
        riesgo: float,
        pam_mom: float,
        utpi_mom: float,
        plgf_mom: float | None,
        categoria: str,
    ) -> str:
        """Genera interpretación clínica narrativa"""
        texto = f"El riesgo calculado de preeclampsia es de {riesgo * 100:.2f}% ({categoria}).\n\n"

        # Análisis de biomarcadores
        if pam_mom > 1.2:
            texto += f" Presión arterial media elevada ({pam_mom:.2f} MoM) indica resistencia vascular aumentada. "
        elif pam_mom < 0.9:
            texto += f"✅ Presión arterial media normal-baja ({pam_mom:.2f} MoM). "

        if utpi_mom > 1.2:
            texto += f" Índice de pulsatilidad uterino elevado ({utpi_mom:.2f} MoM) sugiere resistencia placentaria. "
        elif utpi_mom < 0.9:
            texto += f"✅ Flujo uterino adecuado ({utpi_mom:.2f} MoM). "

        if plgf_mom:
            if plgf_mom < 0.5:
                texto += f" PLGF muy bajo ({plgf_mom:.2f} MoM) - Marcador crítico de disfunción placentaria. "
            elif plgf_mom < 0.8:
                texto += f"⚠️ PLGF disminuido ({plgf_mom:.2f} MoM). "

        texto += "\n\n"

        if categoria == "alto":
            texto += "⚠️ ALTO RIESGO: Se requiere vigilancia intensiva y profilaxis farmacológica."
        elif categoria == "critico":
            texto += (
                " RIESGO CRÍTICO: Manejo por especialista en medicina materno-fetal."
            )

        return texto

    def _conducta_pe(self, categoria: str, _eg: int) -> str:
        """Conducta médica sugerida"""
        if categoria in ["alto", "critico"]:
            return (
                "1. Iniciar Aspirina 150mg (si <16s)\n"
                "2. Doppler UtA cada 2-4 semanas\n"
                "3. PLGF/sFlt-1 a partir de 20s\n"
                "4. Derivar a Medicina Materno-Fetal\n"
                "5. Plan de parto: 37-38 semanas (según evolución)"
            )
        if categoria == "intermedio":
            return (
                "1. Considerar Aspirina 100mg\n"
                "2. Control doppler 20-24 semanas\n"
                "3. Seguimiento mensual con PA"
            )
        return "Control prenatal rutinario según normas nacionales"

    # ==========================================================================
    # 2. TRISOMÍAS (21, 18, 13) - CRIBADO COMBINADO 1º TRIMESTRE
    # ==========================================================================

    def calcular_riesgo_trisomias(
        self,
        edad_materna: int,
        edad_gestacional_dias: int,
        nt_mm: float,
        fcf_lpm: int | None,
        pappa_mom: float,
        bhcg_mom: float,
        historia_trisomias: bool = False,
    ) -> dict:
        """Cribado combinado de trisomías (T21, T18, T13)

        Modelo FMF: Edad materna + NT + PAPP-A + β-hCG libre

        Returns:
            Dict con riesgos para T21, T18, T13

        """
        # 1. Riesgo basal por edad
        riesgo_edad_t21 = self._riesgo_edad_trisomia_21(edad_materna)
        riesgo_edad_t18 = self._riesgo_edad_trisomia_18(edad_materna)
        riesgo_edad_t13 = self._riesgo_edad_trisomia_13(edad_materna)

        # Ajuste por historia
        if historia_trisomias:
            riesgo_edad_t21 *= 1.5
            riesgo_edad_t18 *= 1.5
            riesgo_edad_t13 *= 1.5

        # 2. Likelihood Ratios biomarcadores
        lr_nt_t21 = self._lr_nt(nt_mm, edad_gestacional_dias, "t21")
        lr_nt_t18 = self._lr_nt(nt_mm, edad_gestacional_dias, "t18")
        lr_nt_t13 = self._lr_nt(nt_mm, edad_gestacional_dias, "t13")

        lr_pappa_t21 = self._lr_bioquimico_trisomia(pappa_mom, "PAPP-A", "t21")
        lr_bhcg_t21 = self._lr_bioquimico_trisomia(bhcg_mom, "bhCG", "t21")

        lr_pappa_t18 = self._lr_bioquimico_trisomia(pappa_mom, "PAPP-A", "t18")
        lr_bhcg_t18 = self._lr_bioquimico_trisomia(bhcg_mom, "bhCG", "t18")

        # T13: bioquímica menos específica
        lr_pappa_t13 = self._lr_bioquimico_trisomia(pappa_mom, "PAPP-A", "t13")

        # LR FCF (opcional)
        lr_fcf_t21 = self._lr_fcf(fcf_lpm, "t21") if fcf_lpm else 1.0
        lr_fcf_t18 = self._lr_fcf(fcf_lpm, "t18") if fcf_lpm else 1.0

        # 3. Calcular riesgos posteriores (Bayes)
        riesgo_t21 = self._aplicar_bayes(
            riesgo_edad_t21, [lr_nt_t21, lr_pappa_t21, lr_bhcg_t21, lr_fcf_t21],
        )

        riesgo_t18 = self._aplicar_bayes(
            riesgo_edad_t18, [lr_nt_t18, lr_pappa_t18, lr_bhcg_t18, lr_fcf_t18],
        )

        riesgo_t13 = self._aplicar_bayes(riesgo_edad_t13, [lr_nt_t13, lr_pappa_t13])

        # 4. Categorizar (punto corte: ≥1:250)
        umbral = 1 / 250

        return {
            "trisomia_21": {
                "riesgo_porcentaje": round(riesgo_t21 * 100, 3),
                "riesgo_ratio": f"1:{int(1 / riesgo_t21)}"
                if riesgo_t21 > 0
                else "1:>9999",
                "categoria": "alto_riesgo" if riesgo_t21 >= umbral else "bajo_riesgo",
                "semaforo": "rojo" if riesgo_t21 >= umbral else "verde",
            },
            "trisomia_18": {
                "riesgo_porcentaje": round(riesgo_t18 * 100, 3),
                "riesgo_ratio": f"1:{int(1 / riesgo_t18)}"
                if riesgo_t18 > 0
                else "1:>9999",
                "categoria": "alto_riesgo" if riesgo_t18 >= umbral else "bajo_riesgo",
                "semaforo": "rojo" if riesgo_t18 >= umbral else "verde",
            },
            "trisomia_13": {
                "riesgo_porcentaje": round(riesgo_t13 * 100, 3),
                "riesgo_ratio": f"1:{int(1 / riesgo_t13)}"
                if riesgo_t13 > 0
                else "1:>9999",
                "categoria": "alto_riesgo" if riesgo_t13 >= umbral else "bajo_riesgo",
                "semaforo": "rojo" if riesgo_t13 >= umbral else "verde",
            },
            "recomendaciones": self._recomendaciones_trisomias(
                riesgo_t21, riesgo_t18, riesgo_t13,
            ),
            "interpretacion_clinica": self._interpretar_trisomias(
                nt_mm, pappa_mom, bhcg_mom, riesgo_t21,
            ),
        }

    def _riesgo_edad_trisomia_21(self, edad: int) -> float:
        """Riesgo basal de T21 por edad materna (tablas FMF)"""
        tabla = {
            20: 1 / 1530,
            25: 1 / 1350,
            30: 1 / 900,
            31: 1 / 800,
            32: 1 / 650,
            33: 1 / 500,
            34: 1 / 380,
            35: 1 / 280,
            36: 1 / 230,
            37: 1 / 180,
            38: 1 / 140,
            39: 1 / 110,
            40: 1 / 85,
            41: 1 / 65,
            42: 1 / 50,
            43: 1 / 40,
            44: 1 / 30,
            45: 1 / 25,
        }
        if edad < 20:
            return 1 / 1530
        if edad > 45:
            return 1 / 20
        return tabla.get(edad, 1 / 900)  # Default 30 años

    def _riesgo_edad_trisomia_18(self, edad: int) -> float:
        """Riesgo T18 por edad"""
        return self._riesgo_edad_trisomia_21(edad) * 0.33  # ~1/3 del riesgo de T21

    def _riesgo_edad_trisomia_13(self, edad: int) -> float:
        """Riesgo T13 por edad"""
        return self._riesgo_edad_trisomia_21(edad) * 0.25  # ~1/4 del riesgo de T21

    def _lr_nt(self, nt_mm: float, eg_dias: int, trisomia: str) -> float:
        """LR de translucencia nucal"""
        # Mediana esperada NT según CRL/EG (aproximación)
        mediana_nt = 1.5 + (eg_dias - 70) * 0.02  # mm

        # Delta NT
        delta_nt = nt_mm - mediana_nt

        # Parámetros distribuciones (media delta NT, SD)
        params = {
            "t21": {"media": 0.8, "sd": 0.4},  # NT aumentado
            "t18": {"media": 1.2, "sd": 0.5},  # Muy aumentado
            "t13": {"media": 1.0, "sd": 0.5},
        }

        media_af = params[trisomia]["media"]
        sd_af = params[trisomia]["sd"]
        sd_normal = 0.3

        prob_af = norm.pdf(delta_nt, media_af, sd_af)
        prob_normal = norm.pdf(delta_nt, 0, sd_normal)

        lr = prob_af / prob_normal if prob_normal > 0 else 10.0

        return cast(float, max(0.1, min(lr, 20.0)))

    def _lr_bioquimico_trisomia(
        self, mom: float, marcador: str, trisomia: str,
    ) -> float:
        """LR de marcadores bioquímicos para trisomías"""
        # Parámetros (log MoM media, SD) para afectados
        params = {
            "t21": {
                "PAPP-A": (-0.35, 0.20),  # Bajo
                "bhCG": (0.30, 0.25),  # Alto
            },
            "t18": {
                "PAPP-A": (-0.60, 0.25),  # Muy bajo
                "bhCG": (-0.40, 0.25),  # Bajo
            },
            "t13": {
                "PAPP-A": (-0.45, 0.25),  # Bajo
            },
        }

        if marcador not in params.get(trisomia, {}):
            return 1.0

        log_mom = math.log(mom)
        media_af, sd_af = params[trisomia][marcador]
        sd_normal = 0.15

        prob_af = norm.pdf(log_mom, media_af, sd_af)
        prob_normal = norm.pdf(log_mom, 0, sd_normal)

        lr = prob_af / prob_normal if prob_normal > 0 else 10.0

        return cast(float, max(0.1, min(lr, 15.0)))

    def _lr_fcf(self, fcf: int, trisomia: str) -> float:
        """LR de frecuencia cardíaca fetal"""
        # FCF elevada en T21
        if trisomia == "t21":
            if fcf > 170:
                return 1.5
            if fcf < 140:
                return 0.8
        return 1.0

    def _aplicar_bayes(
        self, riesgo_priori: float, likelihood_ratios: list[float],
    ) -> float:
        """Aplica teorema de Bayes con múltiples LRs"""
        odds_priori = riesgo_priori / (1 - riesgo_priori)

        lr_total = 1.0
        for lr in likelihood_ratios:
            lr_total *= lr

        odds_posterior = odds_priori * lr_total
        riesgo_posterior = odds_posterior / (1 + odds_posterior)

        return min(riesgo_posterior, 0.99)  # Cap al 99%

    def _recomendaciones_trisomias(self, r_t21, r_t18, r_t13) -> list[str]:
        """Recomendaciones según riesgo de trisomías"""
        umbral = 1 / 250
        recom = []

        alto_riesgo = r_t21 >= umbral or r_t18 >= umbral or r_t13 >= umbral

        if alto_riesgo:
            recom.append(" ALTO RIESGO: Se recomienda diagnóstico invasivo")
            recom.append(
                " Opciones: Amniocentesis (15-20s) o Biopsia corial (11-14s)",
            )
            recom.append(
                " Alternativa: Test prenatal no invasivo (NIPT/cfDNA) - Sensibilidad >99% para T21",
            )
            recom.append(" Asesoramiento genético obligatorio")
            recom.append("❤️ Ecocardiografía fetal (20-24s) - Mayor riesgo cardiopatías")
        else:
            recom.append(
                " BAJO RIESGO: No se requiere diagnóstico invasivo de rutina",
            )
            recom.append(
                " Ecografía morfológica 20-24 semanas (vigilar marcadores blandos)",
            )
            recom.append("ℹ️ NIPT disponible si desea mayor tranquilidad (opcional)")

        return recom

    def _interpretar_trisomias(self, nt, pappa_mom, bhcg_mom, riesgo_t21) -> str:
        """Interpretación clínica de cribado de trisomías"""
        texto = "Cribado combinado del primer trimestre:\n\n"

        if nt > 3.5:
            texto += f"⚠️ NT muy elevada ({nt} mm, >3.5 mm) - Marcador crítico de aneuploidía. "
        elif nt > 2.5:
            texto += f" NT ligeramente elevada ({nt} mm). "
        else:
            texto += f"✅ NT normal ({nt} mm). "

        if pappa_mom < 0.5:
            texto += f"⚠️ PAPP-A bajo ({pappa_mom:.2f} MoM). "

        if bhcg_mom > 2.0:
            texto += f"⚠️ β-hCG elevado ({bhcg_mom:.2f} MoM) - Aumenta riesgo T21. "
        elif bhcg_mom < 0.5:
            texto += f"⚠️ β-hCG bajo ({bhcg_mom:.2f} MoM) - Aumenta riesgo T18. "

        texto += f"\n\nRiesgo final T21: {riesgo_t21 * 100:.3f}%\n"

        if riesgo_t21 >= 1 / 250:
            texto += "⚠️ Supera punto de corte para diagnóstico invasivo."
        else:
            texto += "✅ Bajo riesgo, seguimiento habitual."

        return texto

    # ==========================================================================
    # 3. DIABETES GESTACIONAL
    # ==========================================================================

    def calcular_riesgo_diabetes_gestacional(
        self,
        edad_materna: int,
        imc: float,
        etnia: str,
        diabetes_familiar: bool,
        diabetes_gestacional_previa: bool,
        macrosomia_previa: bool,
        pappa_mom: float | None = None,
        bhcg_mom: float | None = None,
    ) -> dict:
        """Calcula riesgo de diabetes gestacional

        Basado en factores de riesgo + biomarcadores 1T
        """
        # 1. Riesgo basal
        riesgo_base = 0.05  # 5% poblacional

        # 2. Multiplicadores
        mult = 1.0

        if imc >= 35:
            mult *= 4.0
        elif imc >= 30:
            mult *= 2.5
        elif imc >= 25:
            mult *= 1.5

        if edad_materna >= 40:
            mult *= 2.0
        elif edad_materna >= 35:
            mult *= 1.5

        if diabetes_familiar:
            mult *= 2.5

        if diabetes_gestacional_previa:
            mult *= 7.0  # Muy alto

        if macrosomia_previa:
            mult *= 2.0

        if etnia in ["sudasiatica", "afrocaribeña"]:
            mult *= 1.5

        # Biomarcadores
        if pappa_mom and pappa_mom < 0.8:
            mult *= 1.3
        if bhcg_mom and bhcg_mom > 1.5:
            mult *= 1.2

        riesgo = min(riesgo_base * mult, 0.80)  # Cap 80%

        # 3. Categorizar
        if riesgo >= 0.25:  # ≥25%
            categoria = "alto"
            semaforo = "rojo"
        elif riesgo >= 0.10:
            categoria = "intermedio"
            semaforo = "amarillo"
        else:
            categoria = "bajo"
            semaforo = "verde"

        return {
            "riesgo_porcentaje": round(riesgo * 100, 2),
            "riesgo_ratio": f"1:{int(1 / riesgo)}" if riesgo > 0 else "1:>999",
            "categoria_riesgo": categoria,
            "semaforo": semaforo,
            "recomendaciones": self._recomendaciones_diabetes(categoria),
            "interpretacion_clinica": self._interpretar_diabetes(
                riesgo, imc, categoria,
            ),
        }

    def _recomendaciones_diabetes(self, categoria: str) -> list[str]:
        """Recomendaciones para diabetes gestacional"""
        if categoria == "alto":
            return [
                " OGTT PRECOZ: Realizar a las 16-18 semanas",
                " OGTT REPETIR: A las 24-28 semanas si el primero es normal",
                " Automonitoreo: Glucemia capilar si diagnóstico confirmado",
                " Derivación nutricional inmediata",
                " Considerar metformina profiláctica (evidencia limitada)",
            ]
        if categoria == "intermedio":
            return [
                " OGTT ESTÁNDAR: 24-28 semanas",
                " Educación: Estilo de vida, dieta, ejercicio",
                "⚖️ Control de peso",
            ]
        return [
            " OGTT RUTINARIO: 24-28 semanas",
            " Educación prenatal estándar",
        ]

    def _interpretar_diabetes(self, riesgo: float, imc: float, categoria: str) -> str:
        """Interpretación clínica de riesgo DG"""
        texto = f"Riesgo de diabetes gestacional: {riesgo * 100:.1f}% ({categoria})\n\n"

        if imc >= 30:
            texto += (
                f"⚠️ IMC {imc:.1f} (obesidad) - Principal factor de riesgo modificable. "
            )

        if categoria == "alto":
            texto += (
                "\n ALTO RIESGO: Se requiere cribado precoz y vigilancia intensiva."
            )

        return texto
