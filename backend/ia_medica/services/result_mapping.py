"""Result mapping module.

Centraliza la traduccion de la respuesta del microservicio de IA (FastAPI,
servicio-ia) al veredicto que se muestra en el frontend.

Antes esta logica estaba duplicada en ia_medica/views.py y
ecografias/ai_views.py, cada una con su propio umbral plano de 0.50 y su
propia mezcla de "probabilidad de normal" + score_global como "confianza"
mostrada al usuario — ignorando los umbrales ya calibrados por clase que el
microservicio aplica en ModelManager.analyze() (ver
servicio-ia/app/config.py CLASS_THRESHOLDS). Esa duplicacion era la
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


def _version_con_huella(ai_result: dict) -> str:
    version = ai_result.get("modelo_version", "efficientnet_b4")
    huella = (ai_result.get("modelo") or {}).get("sha256")
    return f"{version}@{huella[:12]}" if huella else version


class IANoDisponible(Exception):
    """El microservicio respondió sin modelo (fallback): no hay análisis que guardar."""


#: Veredicto → nivel de riesgo. Antes salía de score_global, que incluía la
#: probabilidad de «normal»: una ecografía normal quedaba en riesgo ALTO.
NIVEL_POR_RESULTADO = {
    "normal": "BAJO",
    "requiere_revision": "MODERADO",
    "anomalia_leve": "MODERADO",
    "anomalia_moderada": "MODERADO",
    "anomalia_grave": "ALTO",
}


def defaults_analisis_cnn(ai_result: dict, usuario=None, modelo: str = "efficientnet") -> dict[str, Any]:
    """Campos de ia_medica.AnalisisCNN a partir de la respuesta del microservicio.

    Única traducción: antes ecografias/ai_views.py e ia_medica/views.py la
    repetían con diferencias (recomendaciones, patologías, estructuras).
    Lanza IANoDisponible si el microservicio no tenía modelo: antes se
    guardaba igual un «análisis» vacío marcado como hecho.
    """
    if ai_result.get("status") != "success":
        raise IANoDisponible(ai_result.get("advertencia") or "El servicio de IA no tiene el modelo cargado.")
    if "version_flujo" in ai_result:
        return defaults_analisis_medido(ai_result, usuario)

    mapeo = mapear_resultado_microservicio(ai_result)
    pathologies = mapeo["pathologies"]
    detected = [p for p in pathologies if p.get("name") not in ("normal", "baja_confianza")]
    biometry = ai_result.get("biometry") if isinstance(ai_result.get("biometry"), dict) else {}
    medidas = biometry if biometry.get("disponible") else {}
    shap = ai_result.get("shap_risk_scores") or {}
    sugerencia = ai_result.get("sugerencia_diagnostica")
    sugerencia = sugerencia if isinstance(sugerencia, dict) else None

    recomendaciones = []
    if sugerencia and sugerencia.get("recomendacion"):
        recomendaciones.append(sugerencia["recomendacion"])
    for p in detected:
        nombre, prob = p.get("name", "").replace("_", " "), p.get("probability", 0)
        if prob >= 0.8:
            recomendaciones.append(f"Remisión urgente: {nombre} ({prob * 100:.0f}%)")
        else:
            recomendaciones.append(f"Evaluar: {nombre} ({prob * 100:.0f}%) - requiere confirmación")
    if not recomendaciones:
        recomendaciones.append("Control prenatal de rutina")

    alertas = list(biometry.get("alerts", []))
    if ai_result.get("advertencia"):
        alertas.append(ai_result["advertencia"])
    ms = ai_result.get("inference_time_ms")

    return {
        "realizado_por": usuario if getattr(usuario, "is_authenticated", False) else None,
        "modelo_usado": modelo,
        # Con la huella de los pesos (12 primeros caracteres del sha256):
        # identifica exactamente qué modelo produjo este análisis.
        "version_modelo": _version_con_huella(ai_result),
        "resultado": mapeo["resultado"],
        "confianza": round(float(mapeo["confianza"]), 4),
        "score_general": round(float(ai_result.get("score_global", 0)) * 100, 1),
        "predicciones": [{"clase": p.get("name", ""), "confianza": p.get("probability", 0)} for p in pathologies],
        "clases_detectadas": [p.get("name", "") for p in pathologies],
        "estructuras_detectadas": {p.get("name", ""): {"confianza": p.get("probability", 0)} for p in pathologies},
        "medidas_estimadas": medidas or None,
        "anomalias_detectadas": [
            {"tipo": p.get("name", ""), "confianza": p.get("probability", 0),
             "severidad": "alta" if p.get("probability", 0) >= 0.8 else "media"}
            for p in detected
        ],
        "alertas": alertas,
        "recomendaciones": recomendaciones,
        "mapa_calor": ai_result.get("gradcam_base64") or None,
        "bpd_mm": medidas.get("BPD_mm"),
        "hc_mm": medidas.get("HC_mm"),
        "ac_mm": medidas.get("AC_mm"),
        "fl_mm": medidas.get("FL_mm"),
        "riesgo_preeclampsia": shap.get("riesgo_preeclampsia"),
        "riesgo_parto_prematuro": shap.get("riesgo_parto_prematuro"),
        "nivel_riesgo": NIVEL_POR_RESULTADO.get(mapeo["resultado"], "MODERADO"),
        "shap_valores": shap or None,
        "patologias": [p.get("name", "") for p in detected],
        "sugerencia_diagnostica": sugerencia,
        "tiempo_inferencia_ms": ms,
        "tiempo_procesamiento_ms": ms or 0,
    }


def resultado_del_informe(informe: dict) -> str:
    """Veredicto del análisis con las redes medidas.

    - alarma del cribado cerebral → «anomalia_moderada» (cribado positivo: lo
      confirma un especialista; no se gradúa una sospecha como «grave»);
    - índice cardiotorácico sobre el rango, plano dudoso o corte no adecuado
      → «requiere_revision»;
    - en otro caso → «normal»: sin hallazgos EN LO QUE SE EVALUÓ (el informe
      dice qué se evaluó y qué no).
    """
    anomalias = informe.get("anomalias_cerebrales") or {}
    if anomalias.get("alarma_anomalia"):
        return "anomalia_moderada"
    medidas = informe.get("medidas") or {}
    ict = medidas.get("indice_cardiotoracico_areas")
    referencia = medidas.get("referencia_areas") or [0, 0.35]
    if (ict is not None and ict > referencia[1]) or informe.get("requiere_revision")             or medidas.get("plano_adecuado_para_ca") is False:
        return "requiere_revision"
    return "normal"


def defaults_analisis_medido(informe: dict, usuario=None) -> dict[str, Any]:
    """Campos de AnalisisCNN a partir del informe de las redes medidas
    (servicio-ia/app/analisis_ecografia.py)."""
    plano = informe.get("plano") or {}
    medidas = informe.get("medidas") or {}
    anomalias = informe.get("anomalias_cerebrales") or {}
    resultado = resultado_del_informe(informe)
    alarma = bool(anomalias.get("alarma_anomalia"))
    huella = next((m.get("sha256") for m in informe.get("modelos_usados", []) if m.get("sha256")), None)
    recomendaciones = list(informe.get("hallazgos") or [])
    if resultado == "requiere_revision":
        recomendaciones.append("Revisar la imagen y repetir el corte si hace falta.")
    if not recomendaciones:
        recomendaciones.append("Sin hallazgos en lo evaluado: control prenatal de rutina.")
    vistas = informe.get("estructuras_vistas") or {}
    return {
        "realizado_por": usuario if getattr(usuario, "is_authenticated", False) else None,
        "modelo_usado": "redes_medidas",
        "version_modelo": f"flujo {informe.get('version_flujo')}" + (f"@{huella[:12]}" if huella else ""),
        "resultado": resultado,
        "confianza": round(float(anomalias.get("probabilidad_anomalia") if alarma else plano.get("confianza", 0)), 4),
        "score_general": round(float(plano.get("confianza", 0)) * 100, 1),
        "predicciones": [{"clase": k, "confianza": v} for k, v in (plano.get("probabilidades") or {}).items()],
        "clases_detectadas": [plano.get("plano")] if plano.get("plano") else [],
        "estructuras_detectadas": {k: {"vista": v} for k, v in vistas.items()},
        "medidas_estimadas": medidas or None,
        "anomalias_detectadas": [{"tipo": anomalias.get("familia_sospechada"),
                                  "nombre": anomalias.get("familia_sospechada_nombre"),
                                  "confianza": anomalias.get("probabilidad_anomalia"), "severidad": "media"}] if alarma else [],
        "alertas": list(informe.get("avisos") or []),
        "recomendaciones": recomendaciones,
        "mapa_calor": informe.get("superposicion_png") or None,
        "bpd_mm": medidas.get("diametro_biparietal_mm"),
        "hc_mm": medidas.get("circunferencia_cefalica_mm"),
        "ac_mm": None,
        "fl_mm": None,
        "riesgo_preeclampsia": None,
        "riesgo_parto_prematuro": None,
        "nivel_riesgo": NIVEL_POR_RESULTADO.get(resultado, "MODERADO"),
        "shap_valores": None,
        "patologias": [anomalias.get("familia_sospechada")] if alarma else [],
        "sugerencia_diagnostica": {"informe": informe.get("informe_texto"),
                                   "hallazgos": list(informe.get("hallazgos") or []),
                                   "anomalias_cerebrales": anomalias or None,
                                   "modelos": [{"archivo": m.get("archivo"), "dataset": m.get("dataset")}
                                               for m in informe.get("modelos_usados", [])]},
        "tiempo_inferencia_ms": informe.get("tiempo_ms"),
        "tiempo_procesamiento_ms": informe.get("tiempo_ms") or 0,
    }


def defaults_analisis_ginecologico(nombre_tarea: str, datos: dict, usuario=None) -> dict[str, Any]:
    """Campos de AnalisisCNN a partir de la respuesta de ecografía ginecológica.

    Igual que en el cribado cerebral, una sospecha no se gradúa como «grave»: la
    alarma de malignidad es «anomalia_moderada» y la confirma el especialista. No
    encontrar lesión ni mioma no descarta nada: pide revisión, no sale «normal».
    """
    malignidad = datos.get("malignidad") or {}
    alarma = bool(malignidad.get("alarma"))
    categoria = datos.get("tipo_probable") or datos.get("categoria_probable")
    if alarma:
        resultado = "anomalia_moderada"
    elif datos.get("lesion_encontrada") or datos.get("mioma_ubicado") or "poliqu" in (categoria or "").lower():
        resultado = "anomalia_leve"
    elif datos.get("categoria_probable"):
        resultado = "normal"
    else:
        resultado = "requiere_revision"

    probabilidades = datos.get("probabilidades") or []
    confianza = max((float(p.get("probabilidad", 0)) for p in probabilidades), default=0.0)
    hallazgos = list(datos.get("hallazgos") or [])
    if alarma:
        hallazgos.insert(0, "Alarma: rasgos compatibles con carcinoma seroso de alto grado "
                            f"(probabilidad {float(malignidad.get('probabilidad', 0)) * 100:.1f} %). Lo confirma un especialista.")
    modelos = [{"archivo": m.get("archivo"), "dataset": m.get("dataset")} for m in datos.get("modelos") or []]
    return {
        "realizado_por": usuario if getattr(usuario, "is_authenticated", False) else None,
        "modelo_usado": "redes_medidas",
        "version_modelo": f"ginecologia {datos.get('tarea')}",
        "resultado": resultado,
        "confianza": round(confianza, 4),
        "score_general": round(confianza * 100, 1),
        "predicciones": [{"clase": p.get("tipo") or p.get("categoria"), "confianza": p.get("probabilidad", 0)}
                         for p in probabilidades],
        "clases_detectadas": [f"{nombre_tarea}: {categoria}" if categoria else nombre_tarea],
        "estructuras_detectadas": {},
        "medidas_estimadas": datos.get("medidas") or None,
        "anomalias_detectadas": [{"tipo": "carcinoma_seroso_alto_grado", "nombre": "Carcinoma seroso de alto grado",
                                  "confianza": malignidad.get("probabilidad"), "severidad": "media"}] if alarma else [],
        "alertas": list(datos.get("avisos") or []),
        "recomendaciones": hallazgos or ["Sin hallazgos en lo evaluado."],
        "mapa_calor": datos.get("superposicion_png") or None,
        "nivel_riesgo": NIVEL_POR_RESULTADO.get(resultado, "MODERADO"),
        "patologias": ["carcinoma_seroso_alto_grado"] if alarma else [],
        "sugerencia_diagnostica": {"tarea": datos.get("tarea"), "hallazgos": hallazgos, "modelos": modelos,
                                   "informe": f"{nombre_tarea}. Apoyo al diagnóstico: lo confirma un especialista."},
        "tiempo_procesamiento_ms": 0,
    }


#: Recomendaciones que agrega `defaults_analisis_medido`: no son hallazgos de la red.
_RECOMENDACIONES_FIJAS = {
    "Revisar la imagen y repetir el corte si hace falta.",
    "Sin hallazgos en lo evaluado: control prenatal de rutina.",
}


def informe_guardado(imagen, analisis) -> dict[str, Any]:
    """El informe de un análisis ya guardado, con la forma del recién hecho.

    Así la misma pantalla muestra un análisis nuevo o uno de cualquier paciente.
    Los anteriores a guardar `hallazgos` y `anomalias_cerebrales` en la sugerencia
    los recuperan de `recomendaciones` y `anomalias_detectadas`; de ellos solo se
    sabe el cribado cerebral cuando dio alarma.
    """
    sugerencia = analisis.sugerencia_diagnostica if isinstance(analisis.sugerencia_diagnostica, dict) else {}
    anomalias = sugerencia.get("anomalias_cerebrales")
    # En ginecología la alarma no es del cribado cerebral: va como hallazgo.
    if not anomalias and analisis.anomalias_detectadas and "tarea" not in sugerencia:
        detectada = analisis.anomalias_detectadas[0]
        anomalias = {"aplicable": True, "alarma_anomalia": True,
                     "probabilidad_anomalia": detectada.get("confianza") or 0,
                     "familia_sospechada": detectada.get("tipo"), "familia_sospechada_nombre": detectada.get("nombre")}
    hallazgos = sugerencia.get("hallazgos")
    if hallazgos is None:
        hallazgos = [r for r in analisis.recomendaciones or [] if r not in _RECOMENDACIONES_FIJAS]
    paciente = imagen.paciente
    return {
        "status": "success",
        "fuente": "guardado",
        "version_flujo": analisis.version_modelo,
        "filename": imagen.nombre_original,
        "plano": {
            "plano": (analisis.clases_detectadas or ["sin dato"])[0],
            "confianza": (analisis.score_general or 0) / 100,
            "probabilidades": {p["clase"]: p.get("confianza", 0) for p in analisis.predicciones or [] if "clase" in p},
            "avisos": [],
        },
        "medidas": analisis.medidas_estimadas or {},
        "estructuras_vistas": {k: bool(v.get("vista")) for k, v in (analisis.estructuras_detectadas or {}).items()},
        "anomalias_cerebrales": anomalias,
        "hallazgos": hallazgos,
        "avisos": list(analisis.alertas or []),
        "requiere_revision": analisis.resultado == "requiere_revision",
        "superposicion_url": f"data:image/png;base64,{analisis.mapa_calor}" if analisis.mapa_calor else None,
        "modelos_usados": sugerencia.get("modelos") or [],
        "informe_texto": sugerencia.get("informe") or "",
        "tiempo_ms": analisis.tiempo_inferencia_ms or analisis.tiempo_procesamiento_ms or 0,
        "resultado": analisis.resultado,
        "nivel_riesgo": analisis.nivel_riesgo,
        "fecha_analisis": analisis.fecha_analisis,
        "realizado_por": str(analisis.realizado_por) if analisis.realizado_por else None,
        "imagen_url": imagen.url_imagen,
        "imagen_id": imagen.id,
        "semana_gestacional": imagen.semana_gestacional,
        "paciente": {"id": paciente.id, "nombre": paciente.nombre_completo, "ci": paciente.ci, "edad": paciente.edad},
    }
