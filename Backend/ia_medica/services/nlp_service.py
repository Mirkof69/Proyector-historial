"""=============================================================================
SERVICIO NLP - Procesamiento de Lenguaje Natural Multiidioma
=============================================================================
Sistema inteligente que entiende español e inglés con errores de tipeo
Especializado en terminología médica de ginecología y obstetricia
=============================================================================
"""

import re
from difflib import SequenceMatcher

import nltk
from langdetect import LangDetectException, detect
from unidecode import unidecode

# Descargar recursos de NLTK (solo primera vez)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)
    nltk.download("stopwords", quiet=True)


class NLPMedicoService:
    """Servicio de procesamiento de lenguaje natural para consultas médicas
    """

    def __init__(self):
        """Inicializar diccionarios médicos y términos clave"""
        # Términos médicos clave en español
        self.terminos_medicos_es = {
            "preeclampsia": [
                "preeclampsia",
                "preeclamsia",
                "presion alta embarazo",
                "hipertension gestacional",
                "eclampsia",
            ],
            "diabetes": [
                "diabetes",
                "diabetis",
                "glucosa alta",
                "azucar",
                "glicemia",
                "glicemia alta",
                "diabetes gestacional",
            ],
            "rciu": [
                "rciu",
                "restriccion crecimiento",
                "bebe pequeño",
                "crecimiento intrauterino",
                "crecimiento fetal",
            ],
            "laboratorio": [
                "laboratorio",
                "examenes",
                "analisis",
                "sangre",
                "hemograma",
                "pruebas",
            ],
            "edad_gestacional": [
                "edad gestacional",
                "semanas embarazo",
                "fum",
                "fpp",
                "fecha probable parto",
                "semanas",
            ],
            "presion": ["presion", "tension", "hipertension", "presion arterial"],
            "peso": ["peso", "sobrepeso", "bajo peso", "imc", "obesidad"],
            "ecografia": ["ecografia", "eco", "ultrasonido", "sonografia"],
            "parto": ["parto", "nacimiento", "dar a luz", "labor"],
            "sangrado": ["sangrado", "hemorragia", "sangre", "perdida sangre"],
            "dolor": ["dolor", "contracciones", "molestia"],
            "general": ["consulta", "pregunta", "ayuda", "informacion"],
        }

        # Términos médicos clave en inglés
        self.terminos_medicos_en = {
            "preeclampsia": [
                "preeclampsia",
                "high blood pressure",
                "hypertension",
                "eclampsia",
            ],
            "diabetes": [
                "diabetes",
                "glucose",
                "sugar",
                "gestational diabetes",
                "blood sugar",
            ],
            "rciu": ["iugr", "growth restriction", "small baby", "fetal growth"],
            "laboratorio": ["laboratory", "labs", "blood work", "tests", "analysis"],
            "edad_gestacional": [
                "gestational age",
                "weeks pregnant",
                "due date",
                "lmp",
            ],
            "presion": ["pressure", "blood pressure", "hypertension", "bp"],
            "peso": ["weight", "overweight", "underweight", "bmi", "obesity"],
            "ecografia": ["ultrasound", "sonogram", "scan"],
            "parto": ["delivery", "birth", "labor", "childbirth"],
            "sangrado": ["bleeding", "hemorrhage", "blood loss"],
            "dolor": ["pain", "contractions", "discomfort"],
            "general": ["question", "help", "information", "query"],
        }

        # Correcciones comunes de errores de tipeo médicos
        self.correcciones_tipeo = {
            "preeclamsia": "preeclampsia",
            "diabetis": "diabetes",
            "diabetees": "diabetes",
            "embarazo": "embarazo",
            "enbarazo": "embarazo",
            "enbaraso": "embarazo",
            "presion": "presion",
            "preccion": "presion",
            "prension": "presion",
            "glucosa": "glucosa",
            "glusosa": "glucosa",
            "hemograma": "hemograma",
            "emograma": "hemograma",
            "ecografia": "ecografia",
            "analisis": "analisis",
            "analis": "analisis",
        }

    def detectar_idioma(self, texto: str) -> str:
        """Detecta el idioma del texto
        Returns: 'es', 'en', o 'auto'
        """
        try:
            texto_limpio = self.limpiar_texto(texto)
            if len(texto_limpio) < 3:
                return "auto"

            idioma = detect(texto_limpio)

            # Validar si es español o inglés
            if idioma in ["es", "en"]:
                return idioma
            return "auto"
        except (LangDetectException, Exception):
            return "auto"

    def limpiar_texto(self, texto: str) -> str:
        """Limpia el texto eliminando caracteres especiales y normalizando
        """
        # Convertir a minúsculas
        texto = texto.lower()

        # Eliminar acentos para normalización
        texto_sin_acentos = unidecode(texto)

        # Eliminar caracteres especiales excepto letras, números y espacios
        texto_limpio = re.sub(r"[^a-z0-9\s]", " ", texto_sin_acentos)

        # Eliminar espacios múltiples
        return re.sub(r"\s+", " ", texto_limpio).strip()


    def corregir_errores_tipeo(self, texto: str) -> str:
        """Corrige errores comunes de tipeo usando diccionario y similitud
        """
        palabras = texto.split()
        palabras_corregidas = []

        for palabra in palabras:
            # Buscar en diccionario de correcciones
            if palabra in self.correcciones_tipeo:
                palabras_corregidas.append(self.correcciones_tipeo[palabra])
            else:
                # Buscar similitud con términos médicos conocidos
                mejor_match = self._encontrar_mejor_match(palabra)
                palabras_corregidas.append(mejor_match or palabra)

        return " ".join(palabras_corregidas)

    def _encontrar_mejor_match(self, palabra: str, umbral: float = 0.8) -> str:
        """Encuentra la mejor coincidencia para una palabra con errores
        """
        if len(palabra) < 4:  # No corregir palabras muy cortas
            return palabra

        mejor_similitud: float = 0.0
        mejor_palabra = palabra

        # Buscar en todos los términos médicos
        todos_terminos = []
        for terminos in self.terminos_medicos_es.values():
            todos_terminos.extend(terminos)

        for termino in todos_terminos:
            for palabra_termino in termino.split():
                if len(palabra_termino) < 4:
                    continue

                similitud = SequenceMatcher(None, palabra, palabra_termino).ratio()
                if similitud > mejor_similitud and similitud >= umbral:
                    mejor_similitud = similitud
                    mejor_palabra = palabra_termino

        return mejor_palabra

    def categorizar_consulta(
        self, texto: str, idioma: str = "auto",
    ) -> tuple[str, float]:
        """Categoriza la consulta médica
        Returns: (categoria, confianza)
        """
        texto_limpio = self.limpiar_texto(texto)

        # Seleccionar diccionario según idioma
        if idioma == "en":
            terminos_dict = self.terminos_medicos_en
        else:  # 'es' o 'auto'
            terminos_dict = self.terminos_medicos_es

        # Calcular puntuación para cada categoría
        puntuaciones = {}
        for categoria, terminos in terminos_dict.items():
            puntuacion = 0
            for termino in terminos:
                # Contar ocurrencias del término en el texto
                termino_limpio = self.limpiar_texto(termino)
                if termino_limpio in texto_limpio:
                    # Puntuación mayor para coincidencias exactas
                    puntuacion += 2
                else:
                    # Puntuación menor para coincidencias parciales
                    for palabra in termino_limpio.split():
                        if palabra in texto_limpio and len(palabra) > 3:
                            puntuacion += 1

            puntuaciones[categoria] = puntuacion

        # Obtener categoría con mayor puntuación
        if not puntuaciones or max(puntuaciones.values()) == 0:
            return ("general", 50.0)

        categoria_detectada = max(puntuaciones, key=lambda k: puntuaciones[k])
        puntuacion_max = puntuaciones[categoria_detectada]

        # Calcular confianza (0-100)
        total_puntuaciones = sum(puntuaciones.values())
        confianza = (
            (puntuacion_max / total_puntuaciones * 100)
            if total_puntuaciones > 0
            else 50.0
        )

        # Ajustar confianza
        confianza = min(confianza, 95.0)  # Máximo 95%
        confianza = (
            max(confianza, 60.0) if puntuacion_max > 0 else 50.0
        )  # Mínimo 60% si hay match

        return (categoria_detectada, round(confianza, 1))

    def extraer_keywords(self, texto: str) -> list[str]:
        """Extrae palabras clave médicas del texto
        """
        texto_limpio = self.limpiar_texto(texto)
        palabras = texto_limpio.split()

        # Stopwords español
        stopwords_es = {
            "el",
            "la",
            "de",
            "que",
            "y",
            "a",
            "en",
            "un",
            "una",
            "es",
            "por",
            "para",
            "con",
            "no",
            "se",
            "los",
            "las",
            "del",
            "al",
            "como",
            "mi",
            "su",
            "me",
        }

        # Filtrar palabras relevantes (más de 3 caracteres y no stopwords)
        keywords = [p for p in palabras if len(p) > 3 and p not in stopwords_es]

        # Limitar a las 10 más relevantes
        return keywords[:10]

    def procesar_consulta(self, texto: str) -> dict:
        """Procesa una consulta médica completa
        Returns: {
            'texto_original': str,
            'texto_procesado': str,
            'texto_corregido': str,
            'idioma': str,
            'categoria': str,
            'confianza': float,
            'keywords': List[str]
        }
        """
        # Detectar idioma
        idioma = self.detectar_idioma(texto)

        # Limpiar texto
        texto_limpio = self.limpiar_texto(texto)

        # Corregir errores de tipeo
        texto_corregido = self.corregir_errores_tipeo(texto_limpio)

        # Categorizar
        categoria, confianza = self.categorizar_consulta(texto_corregido, idioma)

        # Extraer keywords
        keywords = self.extraer_keywords(texto_corregido)

        return {
            "texto_original": texto,
            "texto_procesado": texto_limpio,
            "texto_corregido": texto_corregido,
            "idioma": idioma,
            "categoria": categoria,
            "confianza": confianza,
            "keywords": keywords,
        }


# Instancia global del servicio
nlp_service = NLPMedicoService()
