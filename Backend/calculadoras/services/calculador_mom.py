"""=============================================================================
SERVICIO DE CÁLCULO MoM (MÚLTIPLOS DE LA MEDIANA)
=============================================================================
Implementación completa del estándar FMF para conversión a MoM
Incluye correcciones por peso, etnia, altura (Bolivia), tabaquismo, método
=============================================================================
"""

import math
from decimal import Decimal


class CalculadorMoM:
    """Calculador de Múltiplos de la Mediana (MoM) según estándares FMF
    """

    # Medianas esperadas por semana (PLGF en pg/mL - FMF)
    PLGF_MEDIANAS = {
        11: 35.0,
        12: 45.0,
        13: 60.0,
        14: 80.0,
        20: 150.0,
        22: 180.0,
        24: 200.0,
        26: 220.0,
        28: 240.0,
        30: 260.0,
        32: 280.0,
        34: 300.0,
        36: 320.0,
        38: 340.0,
        40: 350.0,
    }

    # Medianas PAPP-A (mIU/mL - Screening T1)
    PAPP_A_MEDIANAS = {11: 1.0, 12: 1.5, 13: 2.2, 14: 3.0}

    # Medianas free β-hCG (ng/mL)
    FREE_BHCG_MEDIANAS = {11: 40.0, 12: 60.0, 13: 70.0, 14: 65.0}

    # Medianas UtA-PI
    UTA_PI_MEDIANAS = {
        11: 2.20,
        12: 1.90,
        13: 1.65,
        14: 1.50,
        20: 1.20,
        22: 1.10,
        24: 1.00,
        26: 0.95,
        28: 0.90,
        30: 0.85,
        32: 0.80,
        34: 0.75,
    }

    @staticmethod
    def obtener_mediana_esperada(
        marcador: str, semanas: int, _peso_kg: float = 70.0,
    ) -> float:
        """Obtiene la mediana esperada para un marcador dado

        Args:
            marcador: 'PLGF', 'PAPP_A', 'FREE_BHCG', 'UTA_PI', etc.
            semanas: Edad gestacional en semanas
            peso_kg: Peso materno para corrección

        Returns:
            Mediana esperada

        """
        tablas = {
            "PLGF": CalculadorMoM.PLGF_MEDIANAS,
            "PAPP_A": CalculadorMoM.PAPP_A_MEDIANAS,
            "FREE_BHCG": CalculadorMoM.FREE_BHCG_MEDIANAS,
            "UTA_PI": CalculadorMoM.UTA_PI_MEDIANAS,
        }

        if marcador not in tablas:
            raise ValueError(f"Marcador '{marcador}' no reconocido")

        tabla = tablas[marcador]

        # Interpolación lineal si no hay valor exacto
        if semanas in tabla:
            mediana = tabla[semanas]
        else:
            # Buscar semanas más cercanas
            semanas_disponibles = sorted(tabla.keys())
            if semanas < min(semanas_disponibles):
                mediana = tabla[min(semanas_disponibles)]
            elif semanas > max(semanas_disponibles):
                mediana = tabla[max(semanas_disponibles)]
            else:
                # Interpolación
                for i in range(len(semanas_disponibles) - 1):
                    s1, s2 = semanas_disponibles[i], semanas_disponibles[i + 1]
                    if s1 <= semanas <= s2:
                        v1, v2 = tabla[s1], tabla[s2]
                        mediana = v1 + (v2 - v1) * (semanas - s1) / (s2 - s1)
                        break

        return mediana

    @staticmethod
    def calcular_mom(
        valor_medido: float,
        marcador: str,
        semanas: int,
        peso_kg: float = 70.0,
        etnia: str = "mestizo",
        fumadora: bool = False,
        diabetes: bool = False,
        fiv: bool = False,
        altitud_bolivia: bool = True,
    ) -> Decimal:
        """Calcula MoM con todas las correcciones necesarias

        Args:
            valor_medido: Valor del marcador medido en laboratorio
            marcador: Tipo de marcador
            semanas: Edad gestacional
            peso_kg: Peso materno
            etnia: caucasico, afro, asiatico, mestizo, indigena
            fumadora: Si fuma
            diabetes: Diabetes preexistente
            fiv: Concepción por FIV
            altitud_bolivia: Corrección por altura (La Paz)

        Returns:
            Valor MoM corregido

        """
        # 1. Obtener mediana base
        mediana_base = CalculadorMoM.obtener_mediana_esperada(
            marcador, semanas, peso_kg,
        )

        # 2. MoM sin corregir
        mom_crudo = valor_medido / mediana_base

        # 3. Corrección por peso
        factor_peso = CalculadorMoM._correccion_peso(peso_kg, marcador)

        # 4. Corrección por etnia
        factor_etnia = CalculadorMoM._correccion_etnia(etnia, marcador)

        # 5. Corrección por tabaquismo
        factor_tabaco = 0.90 if fumadora and marcador in ["PLGF", "PAPP_A"] else 1.0

        # 6. Corrección por diabetes
        factor_diabetes = 1.15 if diabetes and marcador == "FREE_BHCG" else 1.0

        # 7. Corrección por FIV
        factor_fiv = 1.10 if fiv and marcador in ["PAPP_A", "FREE_BHCG"] else 1.0

        # 8. Corrección por altitud (Bolivia - La Paz 3600 msnm)
        factor_altitud = 1.05 if altitud_bolivia and marcador == "PLGF" else 1.0

        # Aplicar todas las correcciones
        mom_corregido = (
            mom_crudo
            * factor_peso
            * factor_etnia
            * factor_tabaco
            * factor_diabetes
            * factor_fiv
            * factor_altitud
        )

        return Decimal(str(round(mom_corregido, 3)))

    @staticmethod
    def _correccion_peso(peso_kg: float, marcador: str) -> float:
        """Factor de corrección por peso materno
        PLGF y PAPP-A disminuyen con el peso
        """
        if marcador in ["PLGF", "PAPP_A"]:
            # Por cada 10 kg sobre 70 kg, disminuye ~5%
            if peso_kg > 70:
                exceso = (peso_kg - 70) / 10
                return 1.0 - (exceso * 0.05)
            return 1.0
        return 1.0

    @staticmethod
    def _correccion_etnia(etnia: str, marcador: str) -> float:
        """Factor de corrección por etnia (FMF)
        """
        factores = {
            "afro": {"PAPP_A": 0.85, "FREE_BHCG": 1.10, "PLGF": 0.95},
            "asiatico": {"PAPP_A": 1.05, "FREE_BHCG": 0.90, "PLGF": 1.00},
            "mestizo": {"PAPP_A": 1.00, "FREE_BHCG": 1.00, "PLGF": 1.00},
            "indigena": {"PAPP_A": 0.95, "FREE_BHCG": 1.05, "PLGF": 0.98},
            "caucasico": {"PAPP_A": 1.00, "FREE_BHCG": 1.00, "PLGF": 1.00},
        }

        return factores.get(etnia, {}).get(marcador, 1.0)

    @staticmethod
    def calcular_percentil_desde_mom(mom: float) -> int:
        """Convierte MoM a percentil aproximado
        Asume distribución log-normal
        """
        from scipy import stats

        # Log-transformación
        log_mom = math.log(mom)

        # Percentil (asumiendo media=0, sd=0.15 para log-MoM)
        percentil = stats.norm.cdf(log_mom, loc=0, scale=0.15) * 100

        return int(round(percentil))

    @staticmethod
    def clasificar_mom(mom: float) -> dict[str, any]:
        """Clasificación automática según valor MoM

        Returns:
            Dict con clasificación, color semáforo, alerta

        """
        if mom < 0.5:
            return {
                "clasificacion": "MUY_BAJO",
                "color": "rojo",
                "semaforo": "",
                "mensaje": "Valor muy bajo - Alto riesgo",
                "requiere_atencion": True,
            }
        if mom < 0.8:
            return {
                "clasificacion": "BAJO",
                "color": "amarillo",
                "semaforo": "",
                "mensaje": "Valor bajo - Vigilancia recomendada",
                "requiere_atencion": True,
            }
        if mom <= 1.2:
            return {
                "clasificacion": "NORMAL",
                "color": "verde",
                "semaforo": "",
                "mensaje": "Valor normal",
                "requiere_atencion": False,
            }
        if mom <= 1.5:
            return {
                "clasificacion": "ALGO_ELEVADO",
                "color": "amarillo",
                "semaforo": "",
                "mensaje": "Valor algo elevado - Control",
                "requiere_atencion": True,
            }
        return {
            "clasificacion": "MUY_ELEVADO",
            "color": "rojo",
            "semaforo": "",
            "mensaje": "Valor muy elevado - Requiere evaluación",
            "requiere_atencion": True,
        }

    @staticmethod
    def calcular_zscore_desde_mom(mom: float) -> float:
        """Convierte MoM a Z-score
        """
        log_mom = math.log(mom)
        # Asumiendo SD = 0.15 para log-MoM
        z_score = log_mom / 0.15
        return round(z_score, 2)


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Ejemplo: Calcular MoM de PlGF
    calculador = CalculadorMoM()

    plgf_medido = 42.5  # pg/mL
    mom_result = calculador.calcular_mom(
        valor_medido=plgf_medido,
        marcador="PLGF",
        semanas=12,
        peso_kg=75,
        etnia="mestizo",
        fumadora=False,
        altitud_bolivia=True,
    )

    print(f"PlGF medido: {plgf_medido} pg/mL")
    print(f"MoM: {mom_result}")
    print(f"Clasificación: {calculador.clasificar_mom(float(mom_result))}")
    print(f"Z-score: {calculador.calcular_zscore_desde_mom(float(mom_result))}")
    print(f"Percentil: {calculador.calcular_percentil_desde_mom(float(mom_result))}")
