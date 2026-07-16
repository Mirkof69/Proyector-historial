"""Reporte narrativo de IA local (LLM con visión, Ollama) grounded en el
resultado real del CNN EfficientNet-B4.

Diseño no negociable: los campos diagnósticos (clasificacion_clinica,
tipo_embarazo, patologias_detectadas, biometria) SIEMPRE vienen del CNN ya
verificado (ver ia_medica/services/result_mapping.py y
Microservicio_IA/app/routes.py) — el LLM nunca tiene autoridad para
sobreescribirlos. El LLM solo (a) redacta en prosa lo que el CNN ya
determinó y (b) puede sugerir hallazgos visuales adicionales fuera de las
15 clases del CNN, que se exponen aparte en "hallazgos_visuales_complementarios"
y nunca se mezclan con "patologias_detectadas".
"""
import base64
import json
import logging
import re

import requests
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5vl:7b"
OLLAMA_TIMEOUT_S = 90

CLASES_CNN = {
    "hidrocefalia", "anencefalia", "espina_bifida", "labio_leporino",
    "atresia_duodenal", "cardiopatia_congenita", "oligohidramnios",
    "polihidramnios", "restriccion_crecimiento", "macrosomia_fetal",
    "placenta_previa", "preeclampsia_signos", "muerte_fetal",
    "embarazo_multiple", "normal",
}


class BiometriaNarrativa(BaseModel):
    LCC_CRL: str | None = None
    DBP: str | None = None
    CC: str | None = None
    CA: str | None = None
    LF: str | None = None
    TN: str | None = None
    LA: str = "No evaluable"
    placenta: str = "No determinable"
    FCF: str | None = None
    peso_estimado: str | None = None


class ReporteNarrativoLLM(BaseModel):
    """Lo que se le PIDE al LLM que rellene. Los campos diagnósticos reales
    (clasificacion_clinica, tipo_embarazo, patologias_detectadas,
    diagnostico_presuntivo) se sobreescriben después con los datos reales
    del CNN — este esquema solo valida que el LLM devolvió una forma
    utilizable. tipo_imagen SÍ se toma del LLM (clasificación de modalidad
    por inspección visual): el CNN no clasifica esto, así que dejarlo fijo
    en el código sería inventar un dato sin evidencia real."""
    tipo_imagen: str = "No determinable"
    descripcion_ecografia: str = "No determinable"
    hallazgos: list[str] = Field(default_factory=list)
    signos_normales: list[str] = Field(default_factory=list)
    signos_alarma: list[str] = Field(default_factory=list)
    hallazgos_visuales_complementarios: list[str] = Field(default_factory=list)
    recomendaciones: list[str] = Field(default_factory=list)
    pronostico: str = "No determinable"
    nota_tecnica: str = ""


def _reparar_json(texto: str) -> dict | None:
    """Repara JSON truncado/con ruido del LLM antes de descartarlo.

    Mismo patrón que el usuario ya usaba en su prototipo HTML
    (safeParseJSON): recorta al primer '{' / último '}', quita comas
    colgantes, y cierra arrays/objetos sin cerrar contando llaves.
    """
    if not texto:
        return None
    s = re.sub(r"```json\s*|```\s*", "", texto).strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1:
        return None
    s = s[start: end + 1] if end != -1 else s[start:]
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    try:
        fixed = re.sub(r",\s*([\}\]])", r"\1", s)
        opens_curly = fixed.count("{") - fixed.count("}")
        opens_square = fixed.count("[") - fixed.count("]")
        fixed += "]" * max(opens_square, 0)
        fixed += "}" * max(opens_curly, 0)
        return json.loads(fixed)
    except json.JSONDecodeError:
        return None


def _construir_prompt(cnn_result: dict) -> str:
    pathology_detection = cnn_result.get("pathology_detection", {}) or {}
    validation = cnn_result.get("ultrasound_validation", {}) or {}
    biometry = cnn_result.get("biometry", {}) or {}

    contexto_real = json.dumps({
        "es_ecografia_obstetrica_valida": validation.get("es_ecografia_obstetrica_valida"),
        "motivo_validez": validation.get("motivo_validez"),
        "motivo_calidad": validation.get("motivo_calidad"),
        "patologias_confirmadas_por_cnn": [
            {"patologia": p.get("pathology"), "confianza": p.get("confidence")}
            for p in pathology_detection.get("pathologies", [])
        ],
        "todas_las_probabilidades_cnn": pathology_detection.get("all_probabilities", {}),
        "biometria_real_cnn": {
            k: v for k, v in biometry.items()
            if k in ("BPD_mm", "HC_mm", "AC_mm", "FL_mm", "peso_estimado_g")
        },
    }, ensure_ascii=False, indent=2)

    return f"""Eres un médico especialista en ginecología y obstetricia con 20 años de experiencia en diagnóstico ecográfico, trabajando como asistente de un sistema que YA tiene un diagnóstico confirmado por una red neuronal convolucional (EfficientNet-B4) verificada clínicamente. Tu trabajo NO es diagnosticar desde cero — es:

1. Describir técnicamente lo que observas en la imagen (estructuras visibles, plano de corte, calidad).
2. Redactar en lenguaje médico formal los hallazgos, basándote ÚNICAMENTE en el resultado YA CONFIRMADO por el CNN (abajo) — NO agregues detalles anatómicos nuevos (ej. corionicidad, número de membranas, septos, posición placentaria específica) que no estén ya en "patologias_confirmadas_por_cnn" o "biometria_real_cnn".
3. Si observas algo visualmente relevante que NO está en el JSON del CNN (cualquier estructura, anomalía o detalle anatómico nuevo, sin excepción), ponlo ÚNICAMENTE en "hallazgos_visuales_complementarios" — JAMÁS en "hallazgos", "signos_normales", "descripcion_ecografia" ni en ningún otro campo. Esta regla es absoluta: cualquier afirmación clínica específica que no provenga literalmente del JSON del CNN es una alucinación y debe ir en ese campo, marcada como no validada.

EJEMPLO DE LO QUE NO DEBES HACER: si el CNN confirmó "embarazo_multiple" pero tú crees ver una membrana o septo entre los sacos gestacionales, NO escribas "embarazo múltiple con septación placentaria" en hallazgos ni en la descripción — eso es inventar un hallazgo clínico no confirmado. Describe solo "embarazo múltiple (confirmado por CNN)" en los campos normales, y si quieres mencionar la membrana, hazlo ÚNICAMENTE en "hallazgos_visuales_complementarios" con la advertencia de que no está validada.

REGLA ABSOLUTA SOBRE EDAD GESTACIONAL: el CNN NO determina edad gestacional, trimestre ni semanas de embarazo — ese dato NO existe en el JSON que se te dio. NUNCA menciones un trimestre, semana o etapa gestacional (ni siquiera términos médicamente inválidos como "cuarto trimestre", que no existe) en ningún campo, incluyendo "descripcion_ecografia". Si necesitas referirte a la edad gestacional, escribe literalmente "edad gestacional no determinada por el CNN".

RESULTADO YA CONFIRMADO POR EL CNN (fuente de verdad — NO LO CONTRADIGAS, NO LO AMPLÍES CON DETALLES NUEVOS):
{contexto_real}

Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin bloques de código markdown, con EXACTAMENTE estos campos:
{{
  "tipo_imagen": "string — UNA DE: Ecografía 2D transabdominal | Ecografía 2D transvaginal | Ecografía 3D/4D volumétrica | Panel multiplanar | Doppler color | No determinable. Clasifica solo por lo que ves, no inventes si no es claro.",
  "descripcion_ecografia": "string — descripción técnica de calidad/plano de imagen; menciona la patología confirmada por su nombre exacto del CNN, sin agregar detalles anatómicos nuevos no confirmados",
  "hallazgos": ["array de strings — SOLO reafirmaciones de lo que ya está en patologias_confirmadas_por_cnn y biometria_real_cnn, en lenguaje médico formal. Nada nuevo."],
  "signos_normales": ["array de strings — SOLO estructuras/parámetros de biometria_real_cnn que estén en rango normal. Nada nuevo."],
  "signos_alarma": ["array de strings — vacío [] si no hay ninguno"],
  "hallazgos_visuales_complementarios": ["array de strings — cualquier observación visual nueva que NO esté en el JSON del CNN va aquí, nunca en otro campo; vacío [] si no observas nada adicional"],
  "recomendaciones": ["array de strings — mínimo 3 recomendaciones clínicas concretas"],
  "pronostico": "string — pronóstico clínico basado SOLO en los hallazgos confirmados por el CNN",
  "nota_tecnica": "string — observaciones sobre calidad de imagen o limitaciones del estudio"
}}

Si "es_ecografia_obstetrica_valida" es false, dilo explícitamente en descripcion_ecografia y deja los demás campos honestos (sin inventar hallazgos de una imagen que no es una ecografía válida)."""


def _llamar_ollama(imagen_path: str, prompt: str) -> str:
    with open(imagen_path, "rb") as f:
        imagen_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt, "images": [imagen_b64]}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT_S)
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", {}).get("content", "")


def _campos_honestos_desde_cnn(cnn_result: dict) -> dict:
    """Campos diagnósticos AUTORITATIVOS — siempre del CNN, nunca del LLM."""
    validation = cnn_result.get("ultrasound_validation", {}) or {}
    pathology_detection = cnn_result.get("pathology_detection", {}) or {}
    biometry = cnn_result.get("biometry", {}) or {}
    pathologies = pathology_detection.get("pathologies", [])

    if validation.get("es_ecografia_obstetrica_valida") is False:
        clasificacion_clinica = "No concluyente"
        tipo_embarazo = "No determinable"
        patologias_detectadas: list[str] = []
    else:
        top = max(pathologies, key=lambda p: p.get("confidence", 0), default=None)
        top_name = top.get("pathology") if top else None
        if top_name == "embarazo_multiple":
            tipo_embarazo = "Múltiple (sin clasificar corionicidad por el CNN)"
        else:
            tipo_embarazo = "Único o no determinable por el CNN"
        if not pathologies or top_name == "baja_confianza":
            clasificacion_clinica = "Requiere seguimiento"
            patologias_detectadas = []
        elif top_name == "normal":
            clasificacion_clinica = "Normal"
            patologias_detectadas = []
        else:
            clasificacion_clinica = "Patología detectada"
            patologias_detectadas = [
                f"{p.get('pathology')} ({p.get('confidence', 0) * 100:.1f}%)"
                for p in pathologies if p.get("pathology") not in ("normal", "baja_confianza")
            ]

    # diagnostico_presuntivo es 100% derivado del CNN, NUNCA del LLM: se
    # comprobo empiricamente que el LLM agrega detalles no confirmados (ej.
    # "con septacion placentaria") y los presenta como si el CNN los hubiera
    # confirmado, justo la fabricacion que esta prohibida en este proyecto.
    if clasificacion_clinica == "No concluyente":
        diagnostico_presuntivo = "No concluyente — no se realizó el análisis"
    elif clasificacion_clinica == "Normal":
        diagnostico_presuntivo = "Sin hallazgos patológicos detectados por el modelo"
    elif clasificacion_clinica == "Requiere seguimiento":
        diagnostico_presuntivo = "Resultado no concluyente — requiere evaluación médica presencial"
    else:
        diagnostico_presuntivo = "; ".join(patologias_detectadas)

    bio = BiometriaNarrativa(
        LCC_CRL=None,
        DBP=f"{biometry.get('BPD_mm')} mm" if biometry.get("BPD_mm") else None,
        CC=f"{biometry.get('HC_mm')} mm" if biometry.get("HC_mm") else None,
        CA=f"{biometry.get('AC_mm')} mm" if biometry.get("AC_mm") else None,
        LF=f"{biometry.get('FL_mm')} mm" if biometry.get("FL_mm") else None,
        peso_estimado=f"{biometry.get('peso_estimado_g')} g" if biometry.get("peso_estimado_g") else None,
    )

    return {
        "clasificacion_clinica": clasificacion_clinica,
        "tipo_embarazo": tipo_embarazo,
        "edad_gestacional": "No determinable (el CNN no estima edad gestacional por fecha de última menstruación)",
        "trimestre": "No determinable",
        "biometria": bio.model_dump(),
        "patologias_detectadas": patologias_detectadas,
        "diagnostico_presuntivo": diagnostico_presuntivo,
        "clasificacion_riesgo": (
            "Alto riesgo" if any(p.get("severity") == "alta" for p in pathologies)
            else "Riesgo moderado" if patologias_detectadas
            else "Bajo riesgo" if clasificacion_clinica == "Normal"
            else "No evaluable"
        ),
        "tipo_seguimiento": (
            "Control prenatal de rutina" if clasificacion_clinica == "Normal"
            else "Evaluación médica presencial obligatoria" if clasificacion_clinica in ("No concluyente", "Requiere seguimiento")
            else "Seguimiento especializado según patología detectada"
        ),
    }


def generar_reporte_narrativo(imagen, cnn_result: dict) -> dict:
    """Genera el reporte narrativo completo para una ImagenEcografica ya
    analizada por el CNN. `cnn_result` es la respuesta cruda del
    microservicio /api/analyze (no la del ViewSet de Django)."""
    campos_honestos = _campos_honestos_desde_cnn(cnn_result)
    validation = cnn_result.get("ultrasound_validation", {}) or {}

    # Guardrail duro: si el CNN ya determinó que la imagen NO es una
    # ecografia obstetrica valida, NUNCA se le pide al LLM que describa
    # anatomia fetal — probado empiricamente que el LLM de vision igual
    # "ve" un feto e inventa estructuras aunque la imagen sea una foto
    # real. Se devuelve un reporte honesto sin invocar al LLM en absoluto.
    if validation.get("es_ecografia_obstetrica_valida") is False:
        motivo = validation.get("motivo_validez") or validation.get("motivo") or "La imagen no corresponde a una ecografía obstétrica válida."
        return {
            **campos_honestos,
            "tipo_imagen": "No determinable — la imagen no fue confirmada como ecografía",
            "biometria": BiometriaNarrativa(LA="No evaluable", placenta="No determinable").model_dump(),
            "descripcion_ecografia": f"No se realizó análisis clínico: {motivo}",
            "hallazgos": [],
            "signos_normales": [],
            "signos_alarma": [],
            "hallazgos_visuales_complementarios": [],
            "recomendaciones": ["Verifique que el archivo subido sea realmente una ecografía obstétrica.", "Repita la captura con el equipo de ultrasonido adecuado."],
            "diagnostico_presuntivo": "No concluyente — no se realizó el análisis",
            "pronostico": "No disponible",
            "nota_tecnica": motivo,
        }

    prompt = _construir_prompt(cnn_result)

    llm_data: dict = {}
    error_llm = None
    try:
        raw = _llamar_ollama(imagen.imagen.path, prompt)
        parsed = _reparar_json(raw)
        if parsed is None:
            error_llm = "El LLM local no devolvió un JSON válido."
        else:
            try:
                llm_data = ReporteNarrativoLLM(**parsed).model_dump()
            except ValidationError as e:
                error_llm = f"JSON del LLM no cumple el esquema esperado: {e}"
    except requests.RequestException as e:
        error_llm = f"No se pudo conectar con el LLM local (Ollama): {e}"
    except Exception as e:  # noqa: BLE001 — nunca debe tumbar el reporte, solo degradar
        error_llm = f"Error inesperado generando narrativa: {e}"
        logger.exception("Error en generar_reporte_narrativo")

    if not llm_data:
        llm_data = ReporteNarrativoLLM(
            descripcion_ecografia=error_llm or "No se pudo generar la descripción narrativa.",
            nota_tecnica=error_llm or "",
        ).model_dump()

    # Las patologias_visuales_complementarias que el LLM proponga y que
    # YA esten en las clases que el CNN conoce se descartan: si el CNN
    # conoce esa clase y no la confirmo, no es un hallazgo "complementario"
    # valido, es ruido del LLM.
    llm_data["hallazgos_visuales_complementarios"] = [
        h for h in llm_data.get("hallazgos_visuales_complementarios", [])
        if not any(clase.replace("_", " ") in h.lower() for clase in CLASES_CNN)
    ]

    # Red de seguridad server-side (no depender solo de que el LLM obedezca
    # el prompt): cualquier hallazgo/signo normal que NO mencione algo del
    # vocabulario realmente confirmado por el CNN (patologia + biometria) se
    # mueve a hallazgos_visuales_complementarios. Esto es lo que detecto el
    # caso real de "septacion placentaria" presentado como confirmado.
    nombres_confirmados = {p.split(" (")[0] for p in campos_honestos.get("patologias_detectadas", [])}
    vocabulario_confirmado = {n.replace("_", " ") for n in nombres_confirmados}
    vocabulario_confirmado |= {"bpd", "dbp", "hc", "cc", "ac", "ca", "fl", "lf", "peso", "biometria", "biometría",
                               "fetal", "ecografia", "ecografía", "imagen", "calidad"}

    # Terminos de "bandera roja": el CNN NUNCA determina edad gestacional,
    # trimestre o semanas — cualquier mencion de estos en texto libre es
    # forzosamente inventada (caso real detectado: el LLM escribio "feto en
    # cuarto trimestre", un valor que ni siquiera existe medicamente, y paso
    # el filtro de vocabulario solo porque la frase tambien contenia "feto").
    # Estos terminos SIEMPRE se consideran no-groundeados, sin excepcion,
    # incluso si la frase contiene otras palabras del vocabulario confirmado.
    terminos_prohibidos = ("trimestre", "semana", "gestacion", "gestación", "semanas")

    def _grounded(texto: str) -> bool:
        t = texto.lower()
        if any(term in t for term in terminos_prohibidos):
            return False
        # Veto duro: si la frase nombra CUALQUIER patologia que el CNN
        # conoce (de las 15 clases) pero esa patologia especifica NO esta en
        # las confirmadas para ESTA imagen, es una afirmacion fabricada —
        # sin importar que tambien contenga palabras "seguras" como "feto"
        # o "embarazo" (caso real: "la patologia confirmada es
        # embarazo_multiple" cuando en realidad NO fue confirmada, solo
        # estaba en all_probabilities por debajo del umbral).
        for clase in CLASES_CNN:
            clase_legible = clase.replace("_", " ")
            if (clase in t or clase_legible in t) and clase not in nombres_confirmados:
                return False
        if not vocabulario_confirmado:
            return False
        return any(palabra in t for palabra in vocabulario_confirmado)

    for campo in ("hallazgos", "signos_normales"):
        items = llm_data.get(campo, [])
        grounded = [i for i in items if _grounded(i)]
        no_grounded = [i for i in items if not _grounded(i)]
        llm_data[campo] = grounded
        llm_data["hallazgos_visuales_complementarios"] = llm_data.get("hallazgos_visuales_complementarios", []) + no_grounded

    # descripcion_ecografia/pronostico/nota_tecnica son texto libre, no listas
    # — se limpian oracion por oracion: cualquier oracion con un termino
    # prohibido (trimestre/semana/gestacion inventados) o que nombre una
    # patologia NO confirmada se elimina directamente (no se mueve a
    # complementarios, son afirmaciones temporales/diagnosticas que no
    # aportan nada util como "hallazgo visual" ahi tampoco).
    def _oracion_invalida(oracion: str) -> bool:
        o = oracion.lower()
        if any(term in o for term in terminos_prohibidos):
            return True
        for clase in CLASES_CNN:
            clase_legible = clase.replace("_", " ")
            if (clase in o or clase_legible in o) and clase not in nombres_confirmados:
                return True
        return False

    for campo in ("descripcion_ecografia", "pronostico", "nota_tecnica"):
        texto = llm_data.get(campo, "")
        if not texto:
            continue
        oraciones = re.split(r"(?<=[.!?])\s+", texto)
        oraciones_limpias = [o for o in oraciones if not _oracion_invalida(o)]
        llm_data[campo] = " ".join(oraciones_limpias).strip() or "No determinable."

    reporte = {**campos_honestos, **llm_data}
    if error_llm:
        reporte["_error_llm"] = error_llm
    return reporte
