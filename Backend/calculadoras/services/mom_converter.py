"""=============================================================================
SERVICIO DE CONVERSIÓN MOM
=============================================================================
Convierte valores crudos de laboratorio a MoM (Múltiplos de la Mediana)
aplicando correcciones por características maternas

Basado en protocolos FMF adaptados para La Paz, Bolivia (altura)
=============================================================================
"""


from django.core.exceptions import ObjectDoesNotExist

# El modelo ReferenciaMOM (medianas y factores poblacionales validados) aún no
# existe; mientras tanto se usa _PlaceholderReferencia y el resultado se marca
# como no ajustado. Ver nota de honestidad clínica más abajo.


# NOTA CLÍNICA IMPORTANTE
# ------------------------
# No existe todavía un dataset poblacional validado (modelo ReferenciaMOM) con
# medianas por marcador/edad gestacional ni coeficientes de corrección (peso,
# etnia, tabaquismo, diabetes, altitud de La Paz) derivados de una cohorte real.
#
# Mientras eso no exista, esta clase devuelve factores neutros (1.0). Eso NO es
# un MoM ajustado clínicamente: es un cociente valor/mediana_base sin corrección
# poblacional. Para evitar transmitir una precisión que no tenemos, MOMConverter
# marca cada resultado con `ajustado_poblacionalmente = False` y una advertencia
# explícita (ver calcular_mom). NO usar estos MoM para decisiones de cribado sin
# cargar antes las referencias reales.
class _PlaceholderReferencia:
    """Referencia neutra (factores 1.0) usada hasta que exista ReferenciaMOM real.

    Marca `es_placeholder = True` para que el convertidor pueda advertir que el
    resultado no está ajustado poblacionalmente.
    """

    es_placeholder = True

    def __init__(self, marcador, eg_dias):
        """Init"""
        self.marcador = marcador
        self.edad_gestacional_dias = eg_dias
        self.mediana = 1.0          # Placeholder value
        self.mediana_base = 1.0     # Used by calcular_mom
        self.unidad = "MoM"
        # Correction factors — all 1.0 (no adjustment) until real data is loaded
        self.factor_fumadora = 1.0
        self.factor_diabetes_tipo1 = 1.0
        self.factor_diabetes_tipo2 = 1.0
        self.factor_altura_lapaz = 1.0

    def get_factor_peso(self, peso_kg: float) -> float:
        """Placeholder: no weight correction until ReferenciaMOM is implemented."""
        return 1.0

    def get_factor_etnia(self, etnia: str) -> float:
        """Placeholder: no ethnic correction until ReferenciaMOM is implemented."""
        return 1.0


class MOMConverter:
    """Servicio para conversión de valores crudos a MoM"""

    def __init__(self):
        """Inicializar el convertidor"""
        self.cache_referencias = {}  # Cache para optimizar consultas

    def calcular_mom(
        self,
        marcador: str,
        valor_crudo: float,
        edad_gestacional_dias: int,
        peso_kg: float,
        etnia: str = "mestiza",
        tabaquismo: bool = False,
        diabetes_tipo: str | None = None,
    ) -> dict:
        """Calcula el MoM de un biomarcador

        Args:
            marcador: Tipo de marcador ('pappa', 'bhcg', 'plg', etc.)
            valor_crudo: Valor medido en el laboratorio
            edad_gestacional_dias: Edad gestacional en días
            peso_kg: Peso materno en kg
            etnia: Etnia materna
            tabaquismo: Si la madre es fumadora activa
            diabetes_tipo: 'tipo1', 'tipo2', o None

        Returns:
            Dict con:
                - mom: float - MoM calculado
                - mediana_base: float - Mediana sin ajustes
                - mediana_ajustada: float - Mediana con correcciones
                - correcciones: Dict - Factores aplicados
                - interpretacion: str - Interpretación del MoM
                - semaforo: str - 'verde', 'amarillo', 'rojo'

        """
        # 1. Obtener referencia MoM
        try:
            referencia = self._get_referencia(marcador, edad_gestacional_dias)
        except ObjectDoesNotExist as exc:
            raise ValueError(
                f"No existe referencia MoM para {marcador} a {edad_gestacional_dias} días",
            ) from exc

        # 2. Obtener factores de corrección
        factor_peso = referencia.get_factor_peso(peso_kg)
        factor_etnia = referencia.get_factor_etnia(etnia)
        factor_tabaco = float(referencia.factor_fumadora) if tabaquismo else 1.0

        # Factor diabetes
        factor_diabetes = 1.0
        if diabetes_tipo == "tipo1":
            factor_diabetes = float(referencia.factor_diabetes_tipo1)
        elif diabetes_tipo == "tipo2":
            factor_diabetes = float(referencia.factor_diabetes_tipo2)

        # Factor altitud La Paz (ya incluido en la mediana base)
        factor_altura = float(referencia.factor_altura_lapaz)

        # 3. Calcular mediana ajustada
        mediana_base = float(referencia.mediana_base)
        mediana_ajustada = (
            mediana_base
            * factor_peso
            * factor_etnia
            * factor_tabaco
            * factor_diabetes
            * factor_altura
        )

        # 4. Calcular MoM
        mom = valor_crudo / mediana_ajustada if mediana_ajustada > 0 else 0

        # 5. Interpretar MoM
        interpretacion, semaforo = self._interpretar_mom(mom, marcador)

        # 6. ¿El resultado está realmente ajustado a una población validada?
        ajustado = not getattr(referencia, "es_placeholder", False)
        advertencia = None
        if not ajustado:
            advertencia = (
                "MoM SIN ajuste poblacional validado: aún no hay referencias "
                "(medianas y factores por peso/etnia/tabaquismo/diabetes/altitud) "
                "cargadas para esta población. No usar para decisiones de cribado."
            )

        return {
            "mom": round(mom, 3),
            "mediana_base": round(mediana_base, 4),
            "mediana_ajustada": round(mediana_ajustada, 4),
            "correcciones": {
                "peso": round(factor_peso, 3),
                "etnia": round(factor_etnia, 3),
                "tabaco": round(factor_tabaco, 3),
                "diabetes": round(factor_diabetes, 3),
                "altura": round(factor_altura, 3),
            },
            "interpretacion": interpretacion,
            "semaforo": semaforo,
            "unidad": referencia.unidad,
            "ajustado_poblacionalmente": ajustado,
            "advertencia": advertencia,
        }

    def _get_referencia(self, marcador: str, eg_dias: int):
        """Obtiene la referencia MoM desde la BD o cache"""
        cache_key = f"{marcador}_{eg_dias}"

        if cache_key in self.cache_referencias:
            return self.cache_referencias[cache_key]

        # Sin modelo ReferenciaMOM todavía: se devuelve la referencia neutra
        # (factores 1.0). El resultado se marca como no ajustado en calcular_mom.
        referencia = _PlaceholderReferencia(marcador, eg_dias)

        # # Buscar referencia exacta o más cercana
        # try:
        #     referencia = ReferenciaMOM.objects.get(
        #         marcador=marcador,
        #         edad_gestacional_dias=eg_dias
        #     )
        # except ReferenciaMOM.DoesNotExist:
        #     # Buscar la más cercana (± 3 días)
        #     referencia = ReferenciaMOM.objects.filter(
        #         marcador=marcador,
        #         edad_gestacional_dias__gte=eg_dias - 3,
        #         edad_gestacional_dias__lte=eg_dias + 3
        #     ).order_by('edad_gestacional_dias').first()
        #
        #     if not referencia:
        #         raise ObjectDoesNotExist(
        #             f"No reference found for {marcador} near {eg_dias} days"
        #         )

        # Guardar en cache
        self.cache_referencias[cache_key] = referencia

        return referencia

    def _interpretar_mom(self, mom: float, marcador: str) -> tuple:
        """Interpreta el valor MoM según rangos FMF

        Returns:
            (interpretacion: str, semaforo: str)

        """
        # Reglas generales FMF
        if 0.8 <= mom <= 1.2:
            interpretacion = (
                f"✅ Normal ({mom:.2f} MoM) - Valor dentro del rango esperado"
            )
            semaforo = "verde"

        elif mom < 0.5:
            interpretacion = f" Muy bajo ({mom:.2f} MoM) - ALTO RIESGO"
            semaforo = "rojo"

            # Interpretaciones específicas
            if marcador in ["pappa", "plg"]:
                interpretacion += " - Riesgo elevado de preeclampsia/SGA"

        elif 0.5 <= mom < 0.8:
            interpretacion = f" Bajo ({mom:.2f} MoM) - Riesgo moderado"
            semaforo = "amarillo"

            if marcador in ["pappa", "plg"]:
                interpretacion += " - Aumenta riesgo de complicaciones placentarias"

        elif mom > 1.5:
            interpretacion = f" Muy alto ({mom:.2f} MoM) - ALTO RIESGO"
            semaforo = "rojo"

            if marcador == "bhcg":
                interpretacion += " - Riesgo de trisomías/mola"
            elif marcador == "sflt1":
                interpretacion += " - Riesgo elevado de preeclampsia"
            elif marcador in ["pam", "utpi"]:
                interpretacion += " - Alta resistencia vascular"

        else:  # 1.2 < mom <= 1.5
            interpretacion = f" Alto ({mom:.2f} MoM) - Riesgo moderado"
            semaforo = "amarillo"

        return interpretacion, semaforo

    def calcular_z_score(
        self, valor: float, media: float, desviacion_estandar: float,
    ) -> float:
        """Calcula el Z-score

        Z = (Valor - Media) / Desviación Estándar
        """
        if desviacion_estandar == 0:
            return 0

        return (valor - media) / desviacion_estandar

    def z_score_to_percentil(self, z_score: float) -> int:
        """Convierte Z-score a percentil usando distribución normal

        Percentil = Φ(Z) × 100
        """
        from scipy.stats import norm

        percentil = norm.cdf(z_score) * 100
        return int(round(float(percentil), 1))

    def calcular_tendencia(
        self, valores_historicos: list, semanas_historicas: list,
    ) -> dict:
        """Calcula la tendencia de un marcador en el tiempo

        Pendiente = (Valor_t2 - Valor_t1) / Δsemanas

        Args:
            valores_historicos: Lista de valores MoM históricos
            semanas_historicas: Lista de semanas correspondientes

        Returns:
            Dict con pendiente, tendencia ('mejorando'/'empeorando'/'estable')

        """
        if len(valores_historicos) < 2:
            return {
                "pendiente": 0,
                "tendencia": "sin_datos",
                "interpretacion": "Se requieren al menos 2 mediciones",
            }

        # Calcular pendiente (último vs primero)
        delta_valor = valores_historicos[-1] - valores_historicos[0]
        delta_semanas = semanas_historicas[-1] - semanas_historicas[0]

        pendiente = 0 if delta_semanas == 0 else delta_valor / delta_semanas

        # Interpretar tendencia
        if abs(pendiente) < 0.01:  # Cambio < 0.01 MoM/semana
            tendencia = "estable"
            interpretacion = "Valores estables sin cambios significativos"
        elif pendiente > 0:
            tendencia = "mejorando" if valores_historicos[0] < 1.0 else "empeorando"
            interpretacion = f"Tendencia ascendente (+{abs(pendiente):.3f} MoM/semana)"
        else:
            tendencia = "empeorando" if valores_historicos[0] > 1.0 else "mejorando"
            interpretacion = f"Tendencia descendente (-{abs(pendiente):.3f} MoM/semana)"

        return {
            "pendiente": round(pendiente, 4),
            "tendencia": tendencia,
            "interpretacion": interpretacion,
            "delta_total": round(delta_valor, 3),
            "delta_semanas": delta_semanas,
        }

    def validar_calidad_medicion_poblacional(self, moms_poblacionales: list) -> dict:
        """Valida calidad de mediciones según FMF

        La mediana poblacional de MoMs debe ser ≈ 1.0
        Esto indica que los equipos y técnicas están bien calibrados

        Args:
            moms_poblacionales: Lista de MoMs de todas las mediciones recientes

        Returns:
            Dict con mediana, alerta de calidad

        """
        import numpy as np

        if len(moms_poblacionales) < 30:
            return {
                "mediana": None,
                "alerta": "Se requieren al menos 30 mediciones para validación",
                "calidad": "insuficiente",
            }

        mediana = np.median(moms_poblacionales)

        # Reglas FMF: mediana entre 0.95 y 1.05 = BUENA calidad
        if 0.95 <= mediana <= 1.05:
            alerta = (
                f"✅ Calidad EXCELENTE - Mediana: {mediana:.3f} (muy cercana a 1.0)"
            )
            calidad = "excelente"
        elif 0.90 <= mediana < 0.95 or 1.05 < mediana <= 1.10:
            alerta = (
                f"⚠️ Calidad ACEPTABLE - Mediana: {mediana:.3f} (revisar calibración)"
            )
            calidad = "aceptable"
        else:
            alerta = (
                f" Calidad DEFICIENTE - Mediana: {mediana:.3f} (RECALIBRAR EQUIPOS)"
            )
            calidad = "deficiente"

        return {
            "mediana": round(mediana, 3),
            "alerta": alerta,
            "calidad": calidad,
            "n_mediciones": len(moms_poblacionales),
        }
