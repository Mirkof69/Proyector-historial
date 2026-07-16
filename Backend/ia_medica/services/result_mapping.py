"""Result mapping module.

Centraliza la traduccion de la respuesta del microservicio de IA (FastAPI,
Backend/Microservicio_IA) al veredicto que se muestra en el frontend.

Antes esta logica estaba duplicada en ia_medica/views.py y
ecografias/ai_views.py, cada una con su propio umbral plano de 0.50 y su
propia mezcla de "probabilidad de normal" + score_global como "confianza"
mostrada al usuario — ignorando los umbrales ya calibrados por clase que el
microservicio aplica en ModelManager.analyze() (ver
Microservicio_IA/app/config.py CLASS_THRESHOLDS). Esa duplicacion era la
causa real de que la misma imagen mostrara resultados incoherentes entre
los dos botones de analisis del frontend.
"""
from typing import Any


def normalizar_pathologies(ai_result: dict) -> list[dict]:
    """Normaliza pathology_detection.pathologies al formato {name, probability, ...}.

    El microservicio devuelve {pathology, confidence, severity, ...}; codigo
    legado en Django usa {name, probability}. Se preservan el resto de
    campos (severity, requires_specialist, recommendation, etc.) en vez de
    descartarlos al normalizar. Si pathologies viene vacio (no deberia pasar
    salvo el caso no_ecografia), se cae a all_probabilities como ultimo
    recurso, sin severity ni los demas campos.
    """
    path_detection = ai_result.get("pathology_detection", {}) or {}
    raw_pathologies = path_detection.get("pathologies", [])
    all_probs = path_detection.get("all_probabilities", {})

    def _norm(p: dict) -> dict:
        if "name" in p:
            out = dict(p)
            out.setdefault("probability", 0)
            return out
        out = dict(p)
        out["name"] = p.get("pathology", "")
        out["probability"] = p.get("confidence", 0)
        return out

    if not raw_pathologies and all_probs:
        return [{"name": k, "probability": v} for k, v in all_probs.items()]
    return [_norm(p) for p in raw_pathologies]


def mapear_resultado_microservicio(ai_result: dict) -> dict[str, Any]:
    """Traduce la respuesta del microservicio a un veredicto coherente.

    Confia en pathology_detection.pathologies, que el microservicio ya
    filtra con los umbrales calibrados por clase (CLASS_THRESHOLDS) — no
    vuelve a aplicar un umbral plano de 0.50 ni mezcla la probabilidad de
    "normal" con score_global para calcular la "confianza" mostrada.

    Devuelve:
        resultado: "normal" | "requiere_revision" | "anomalia_leve" |
            "anomalia_moderada" | "anomalia_grave"
        confianza: confianza de LO QUE REALMENTE SE ESTA REPORTANDO (no una
            mezcla de todas las probabilidades)
        pathologies: lista normalizada completa (para construir
            predicciones/anomalias/clases_detectadas como antes)
        top: la entrada de mayor probabilidad (o None si no hay ninguna)
    """
    pathologies = normalizar_pathologies(ai_result)
    score_global = float(ai_result.get("score_global", 0))

    if not pathologies:
        # No deberia pasar en el flujo normal (ver _non_ultrasound_response
        # en el microservicio para el caso no_ecografia); mantenido como
        # red de seguridad para no romper si el contrato cambia.
        return {
            "resultado": "requiere_revision",
            "confianza": score_global,
            "pathologies": [],
            "top": None,
        }

    top = max(pathologies, key=lambda p: p.get("probability", 0))
    top_name = top.get("name", "")
    top_prob = float(top.get("probability", 0))

    if top_name == "normal":
        resultado = "normal"
    elif top_name == "baja_confianza":
        resultado = "requiere_revision"
    else:
        severidad = top.get("severity")
        if severidad == "alta":
            resultado = "anomalia_grave"
        elif severidad == "media-alta":
            resultado = "anomalia_moderada"
        elif severidad:
            resultado = "anomalia_leve"
        # Fallback si la entrada no trae severity (ej. vino del fallback de
        # all_probabilities en vez de pathology_detection.pathologies real).
        elif top_prob >= 0.70:
            resultado = "anomalia_grave"
        elif top_prob >= 0.50:
            resultado = "anomalia_moderada"
        else:
            resultado = "anomalia_leve"

    return {
        "resultado": resultado,
        "confianza": top_prob,
        "pathologies": pathologies,
        "top": top,
    }
