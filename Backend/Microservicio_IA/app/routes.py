"""Rutas API — Microservicio IA Fetal Medical
CNN EfficientNet-B4 (PyTorch + MONAI) + Chatbot obstétrico
"""

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from .config import CITY_ALTITUDE_M, IMAGE_CONFIG
from .models import PATHOLOGY_CLASSES, ModelManager
from .preprocessing import PILImagePreprocessor as ImagePreprocessor

router = APIRouter(prefix="/api", tags=["AI Analysis"])

model_manager = ModelManager()
preprocessor = ImagePreprocessor()


def _build_non_ultrasound_response(
    filename: str, file_size: int, quality: dict, validation: dict,
) -> dict:
    """Respuesta rapida cuando validate_ultrasound determina que la imagen
    claramente no es una ecografia. NO corre el modelo."""
    return {
        "status": "success",
        "fuente": "pre_validation",
        "modelo_version": "N/A",
        "ultrasound_validation": {
            "es_ecografia_obstetrica_valida": False,
            "tipo_ecografia": "desconocida",
            "calidad_suficiente": False,
            "motivo": validation.get("motivo", ""),
            "motivo_calidad": validation.get("motivo", ""),
            "saturacion_media": validation.get("color", {}).get("saturacion_media"),
        },
        "pregnancy_assessment": {
            "feto_presente": False,
            "actividad_cardiaca": False,
            "semanas_gestacion_estimadas": None,
            "crecimiento_adecuado": None,
        },
        "pathology_detection": {
            "pathologies": [],
            "total_detected": 0,
            "requires_specialist": False,
            "all_probabilities": dict.fromkeys(PATHOLOGY_CLASSES, 0.0),
        },
        "biometry": {"BPD_mm": None, "HC_mm": None, "AC_mm": None, "FL_mm": None, "peso_estimado_g": None, "disponible": False, "motivo": "No se procesó la imagen."},
        "score_global": 0.0,
        "shap_risk_scores": {},
        "riesgo_preeclampsia": 0.0,
        "riesgo_parto_prematuro": 0.0,
        "ajuste_altitud": {},
        "liquido_amniotico": {"evaluacion": "no evaluado", "nota": ""},
        "placenta": {"posicion": "no evaluada", "nota": ""},
        "clinical_recommendations": {
            "urgencia": "N/A",
            "especialista_requerido": "Obstetra tratante",
            "tiempo_recomendado": "Repetir con una ecografia valida",
            "estudios_adicionales": ["Verificar que el archivo sea una ecografia obstetrica"],
        },
        "gradcam_base64": "",
        "gradcam_disponible": False,
        "filename": filename,
        "file_size_kb": round(file_size / 1024, 1),
        "image_quality": quality,
        "modelo_solicitado": "N/A",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device": "N/A",
        "advertencia": (
            "La imagen no paso la validacion preliminar de calidad. "
            "Verifique que el archivo subido sea una ecografia obstetrica valida."
        ),
    }


def _apply_safety_checks(result: dict, quality: dict, color_check: dict) -> None:
    """Capas de seguridad que no dependen del modelo:
    de color. Se anotan en ultrasound_validation sin pisar un resultado
    exitoso del modelo, solo lo complementan."""
    validation = result.setdefault("ultrasound_validation", {})

    if quality.get("resolucion_baja"):
        min_rec = quality.get("resolucion_minima_recomendada_px")
        validation["motivo_calidad"] = (
            f"Resolucion de imagen baja ({quality.get('ancho_px')}x{quality.get('alto_px')} px). "
            f"Se recomienda al menos {min_rec}x{min_rec} px para un analisis confiable."
        )
        validation["calidad_suficiente"] = False

    # Si el modelo ya detecto con confianza una patologia real (p. ej. Doppler
    # color en placenta previa, que tiene saturacion alta por el flujo a
    # color pero SI es una ecografia valida), se confia en el modelo y no se
    # pisa con la heuristica de color: solo se reporta como dato informativo.
    # Tambien protege el caso de senal real por debajo del umbral clinico de
    # confirmacion (p. ej. embarazo_multiple al 92.9%, cuyo umbral de
    # confirmacion es 0.95 por ser una clase con pocas imagenes de
    # entrenamiento): esa imagen SI es una ecografia real, solo no alcanza a
    # confirmarse clinicamente, y no debe acusarse de "ser una foto".
    pathologies = result.get("pathology_detection", {}).get("pathologies", [])
    all_probs = result.get("pathology_detection", {}).get("all_probabilities", {})
    # "normal" SI cuenta como senal real (un caso real verificado: imagen
    # valida con saturacion 0.184 por compresion JPEG, "normal" en 40.8% sin
    # llegar a su propio umbral de confirmacion — excluirla de la proteccion
    # hacia que se acusara de "ser una foto" a una ecografia real solo
    # ambigua). Solo "no_ecografia" se excluye, porque esa clase es
    # justamente la opinion del modelo de que NO es una ecografia.
    señal_real_detectada = any(
        v >= 0.40 for k, v in all_probs.items() if k != "no_ecografia"
    )
    detecciones_confiables = (
        any(p.get("pathology") not in ("normal", "baja_confianza") for p in pathologies)
        or señal_real_detectada
    )

    if not color_check.get("parece_ecografia", True) and not detecciones_confiables:
        validation["motivo_validez"] = (
            "La imagen tiene colores tipicos de una fotografia (no de una ecografia en "
            "escala de grises). Verifique que el archivo subido sea realmente una ecografia."
        )
        validation["es_ecografia_obstetrica_valida"] = False
        validation["calidad_suficiente"] = False

    validation["saturacion_media"] = color_check.get("saturacion_media")
    motivo_previo = validation.get("motivo")
    motivos = [
        m for m in (motivo_previo, validation.get("motivo_calidad"), validation.get("motivo_validez"))
        if m
    ]
    if motivos:
        validation["motivo"] = " ".join(dict.fromkeys(motivos))


# ── CNN: ANÁLISIS COMPLETO ────────────────────────────────────────────────────


@router.post("/analyze", summary="Análisis completo EfficientNet-B4")
async def analyze_ultrasound(
    file: UploadFile = File(...),
    modelo: str = "efficientnet",
    ciudad: str | None = Form(None),
    altitud_m: float | None = Form(None),
) -> dict:
    """Análisis completo con EfficientNet-B4 (PyTorch 2.2 + MONAI):
    - 15 patologías fetales (umbral ≥ 0.50)
    - Biometría: BPD, HC, AC, FL, peso estimado
    - Grad-CAM sobre última capa convolucional
    - SHAP risk scores (preeclampsia, parto prematuro, etc.), con ajuste por
      altitud si se indica `ciudad` (Bolivia) o `altitud_m` directamente.
    """
    try:
        resolved_altitude = altitud_m
        if resolved_altitude is None and ciudad:
            resolved_altitude = CITY_ALTITUDE_M.get(ciudad.strip().lower())

        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        allowed: list = IMAGE_CONFIG["allowed_extensions"]  # type: ignore[assignment]
        if ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Extensión no permitida. Use: {allowed}",
            )
        content = await file.read()
        max_size: int = IMAGE_CONFIG["max_size"]  # type: ignore[assignment]
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo muy grande. Máximo: {max_size // 1024 // 1024} MB",
            )
        image = preprocessor.load_image(content, ext)
        quality = preprocessor.calculate_image_quality(image)
        color_check = preprocessor.looks_like_ultrasound(image)

        # SIEMPRE correr el modelo primero. validate_ultrasound se usa solo
        # como anotacion post-analisis en _apply_safety_checks, nunca como
        # bloqueo pre-analisis: imagenes chicas o con algo de saturacion
        # (Doppler color, JPEG artifacts) deben llegar al modelo para que
        # decida si hay senial real.
        enhanced = preprocessor.enhance_image(image)
        result = model_manager.analyze(enhanced, compute_cam=True, altitude_m=resolved_altitude)
        result["filename"] = filename
        result["file_size_kb"] = round(len(content) / 1024, 1)
        result["image_quality"] = quality
        result["modelo_solicitado"] = modelo
        _apply_safety_checks(result, quality, color_check)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {e!s}") from e


@router.post("/detect-pathologies", summary="Detectar patologías fetales + biometría")
async def detect_pathologies(file: UploadFile = File(...)) -> dict:
    """Detect pathologies"""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    allowed2: list = IMAGE_CONFIG["allowed_extensions"]  # type: ignore[assignment]
    if ext not in allowed2:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {allowed2}",
        )
    content = await file.read()
    max_size2: int = IMAGE_CONFIG["max_size"]  # type: ignore[assignment]
    if len(content) > max_size2:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {max_size2 // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    enhanced = preprocessor.enhance_image(image)
    result = model_manager.analyze(enhanced, compute_cam=True)
    return {
        "status": result["status"],
        "filename": filename,
        "pathology_detection": result["pathology_detection"],
        "biometry": result["biometry"],
        "shap_risk_scores": result["shap_risk_scores"],
        "fuente": result["fuente"],
    }


@router.post("/detect-anomalies", summary="Detectar anomalías fetales")
async def detect_anomalies(file: UploadFile = File(...)) -> dict:
    """Detect anomalies"""
    filename3 = file.filename or ""
    ext = os.path.splitext(filename3)[1].lower()
    allowed3: list = IMAGE_CONFIG["allowed_extensions"]  # type: ignore[assignment]
    if ext not in allowed3:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {allowed3}",
        )
    content = await file.read()
    max_size3: int = IMAGE_CONFIG["max_size"]  # type: ignore[assignment]
    if len(content) > max_size3:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {max_size3 // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    enhanced = preprocessor.enhance_image(image)
    result = model_manager.analyze(enhanced, compute_cam=True)
    return {
        "status": result["status"],
        "filename": filename3,
        "anomaly_detection": result["pathology_detection"],
        "shap_risk_scores": result["shap_risk_scores"],
        "fuente": result["fuente"],
    }


@router.post("/classify", summary="Clasificar tipo de ecografía (legado)")
async def classify_ultrasound(file: UploadFile = File(...)) -> dict:
    """Classify ultrasound"""
    filename4 = file.filename or ""
    ext = os.path.splitext(filename4)[1].lower()
    allowed4: list = IMAGE_CONFIG["allowed_extensions"]  # type: ignore[assignment]
    if ext not in allowed4:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {allowed4}",
        )
    content = await file.read()
    max_size4: int = IMAGE_CONFIG["max_size"]  # type: ignore[assignment]
    if len(content) > max_size4:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {max_size4 // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    enhanced = preprocessor.enhance_image(image)
    result = model_manager.analyze(enhanced, compute_cam=True)
    return {
        "status": result["status"],
        "filename": filename4,
        "classification": {
            "pathology_detection": result["pathology_detection"],
            "score_global": result["score_global"],
        },
    }


@router.post("/quality-check", summary="Evaluar calidad de imagen médica")
async def check_image_quality(file: UploadFile = File(...)) -> dict:
    """Check image quality"""
    filename5 = file.filename or ""
    ext = os.path.splitext(filename5)[1].lower()
    allowed5: list = IMAGE_CONFIG["allowed_extensions"]  # type: ignore[assignment]
    if ext not in allowed5:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {allowed5}",
        )
    content = await file.read()
    max_size5: int = IMAGE_CONFIG["max_size"]  # type: ignore[assignment]
    if len(content) > max_size5:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {max_size5 // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    quality = preprocessor.calculate_image_quality(image)
    return {"status": "success", "filename": filename5, "quality": quality}


# ── CHATBOT OBSTÉTRICO ────────────────────────────────────────────────────────

_OBSTETRIC_KB = {
    "preeclampsia": {
        "keywords": [
            "preeclampsia",
            "presion arterial",
            "hipertension",
            "proteinas",
            "edema",
        ],
        "categoria": "preeclampsia",
        "respuesta": (
            "Preeclampsia: PA ≥ 140/90 mmHg después de semana 20 + proteinuria ≥ 300 mg/24h. "
            "Signos de alarma: cefalea intensa, visión borrosa, epigastralgia, edema facial severo. "
            "Manejo: hospitalización, sulfato de magnesio (preeclampsia severa/≥34sem), "
            "antihipertensivos (labetalol 200mg VO o nifedipino 10mg), considerar finalización del embarazo. "
            "Registrar en historia clínica: PA, proteinuria, creatinina, plaquetas (Ley 3131)."
        ),
    },
    "rciu": {
        "keywords": [
            "rciu",
            "restriccion crecimiento",
            "crecimiento intrauterino",
            "peso fetal bajo",
            "percentil",
        ],
        "categoria": "rciu",
        "respuesta": (
            "RCIU: peso fetal estimado < percentil 10 para edad gestacional. "
            "Clasificación: precoz (< 32 sem, Doppler alterado, peor pronóstico) vs tardío (> 32 sem). "
            "Manejo: Doppler fetal semanal (arteria umbilical, cerebral media, ductus venoso), "
            "corticoides si < 34 semanas, finalizar embarazo según perfil biofísico y Doppler. "
            "El sistema CNN calcula BPD/HC/AC/FL automáticamente para seguimiento biométrico."
        ),
    },
    "diabetes": {
        "keywords": [
            "diabetes",
            "glucosa",
            "glicemia",
            "insulina",
            "macrosomia",
            "hipoglicemia",
        ],
        "categoria": "diabetes",
        "respuesta": (
            "DMG: glucemia ayunas ≥ 92 mg/dL o PTOG 75g con valores ≥ 180/153 mg/dL. "
            "Control: dieta (50-55% CHO), ejercicio moderado, insulina si no se controla con dieta. "
            "Metas: ayunas < 95, 1h posprandial < 140, 2h < 120 mg/dL. "
            "Seguimiento ecográfico: cada 4 semanas desde sem 28. Complicaciones: macrosomía, polihidramnios, "
            "hipoglucemia neonatal. Riesgo de DM2 posparto 50% a 10 años."
        ),
    },
    "laboratorio": {
        "keywords": [
            "laboratorio",
            "hemograma",
            "resultado",
            "analisis",
            "valor",
            "referencia",
            "hematocrito",
            "hemoglobina",
        ],
        "categoria": "laboratorio",
        "respuesta": (
            "Valores de referencia en embarazo: Hb ≥ 11 g/dL (1er/3er trim), ≥ 10.5 (2do trim). "
            "Hematocrito ≥ 33%. Plaquetas > 100,000/μL (alarma < 50,000). "
            "Creatinina < 0.9 mg/dL. Proteinuria < 300 mg/24h. "
            "GGT/ALT/AST pueden elevarse moderadamente (hasta 2× normal). "
            "Resultados CRÍTICOS generan alerta automática al médico por WebSocket en el sistema."
        ),
    },
    "edad_gestacional": {
        "keywords": [
            "edad gestacional",
            "semanas",
            "fum",
            "fecha ultima menstruacion",
            "trimestre",
            "capurro",
        ],
        "categoria": "edad_gestacional",
        "respuesta": (
            "Cálculo EG: por FUM (Naegele: FPP = FUM + 280 días), o ecografía (más precisa). "
            "Precisión ecográfica: 1er trim ±5 días (LCC), 2do trim ±10 días, 3er trim ±3 semanas. "
            "Discordancia FUM-eco > 7 días en 1er trim → usar fecha ecográfica. "
            "El sistema calcula EG automáticamente desde FUM ingresada en historia clínica."
        ),
    },
    "ecografia": {
        "keywords": [
            "ecografia",
            "ecografia",
            "ultrasonido",
            "dicom",
            "biometria",
            "bpd",
            "fl",
            "hc",
            "ac",
            "ila",
        ],
        "categoria": "general",
        "respuesta": (
            "El sistema analiza ecografías con EfficientNet-B4 (PyTorch + MONAI, input 384×384). "
            "Mide automáticamente: BPD, HC, AC, FL y peso estimado (fórmula Hadlock). "
            "Genera Grad-CAM para explicabilidad visual y SHAP scores de riesgo materno. "
            "El médico DEBE validar cada análisis. La CNN es herramienta de apoyo (Ley 3131)."
        ),
    },
    "parto": {
        "keywords": [
            "parto",
            "cesarea",
            "cesárea",
            "trabajo de parto",
            "contracciones",
            "dilatacion",
        ],
        "categoria": "general",
        "respuesta": (
            "Indicaciones de cesárea: presentación podálica, macrosomía > 4500 g, placenta previa, "
            "RCIU severo con Doppler alterado, cicatriz uterina vertical previa. "
            "Manejo activo del alumbramiento: oxitocina 10 UI IM tras expulsión hombro anterior. "
            "Registrar en historia clínica: tipo de parto, hora, Apgar 1' y 5', complicaciones."
        ),
    },
    "emergencia": {
        "keywords": [
            "emergencia",
            "urgente",
            "hemorragia",
            "desprendimiento",
            "prolapso",
            "eclampsia",
            "convulsion",
        ],
        "categoria": "emergencia",
        "respuesta": (
            "EMERGENCIA OBSTETRICA — Activar protocolo institucional urgente. "
            "Hemorragia posparto: masaje uterino, oxitocina 20 UI/500mL IV, misoprostol 600μg SL, "
            "ácido tranexámico 1g IV (primeras 3h). "
            "Eclampsia: MgSO4 4g IV lento (15 min) + 1g/h mantenimiento, posición lateral izquierda. "
            "Prolapso de cordón: posición genupectoral, no reintroducir cordón, cesárea urgente."
        ),
    },
}


def _chatbot_response(consulta: str, contexto: dict | None = None) -> dict:
    """Chatbot response"""
    consulta_lower = consulta.lower()
    best_cat, best_score = None, 0
    for cat, data in _OBSTETRIC_KB.items():
        score = sum(1 for kw in data["keywords"] if kw in consulta_lower)
        if score > best_score:
            best_score, best_cat = score, cat

    if best_cat and best_score > 0:
        entry = _OBSTETRIC_KB[best_cat]
        respuesta = entry["respuesta"]
        if contexto and "paciente_actual" in contexto:
            p = contexto["paciente_actual"]
            if p.get("nombre"):
                respuesta = f"[Contexto: {p['nombre']}] {respuesta}"
        return {
            "respuesta": respuesta,
            "categoria": entry["categoria"],
            "confianza": min(95, 60 + best_score * 10),
            "fuente": "base_conocimiento_obstetrica",
        }

    return {
        "respuesta": (
            "Consulta recibida. Para una respuesta precisa, use términos como: "
            "preeclampsia, RCIU, diabetes gestacional, laboratorio, edad gestacional, "
            "ecografía, parto, emergencia obstétrica. "
            "Para emergencias contacte al médico de guardia de inmediato."
        ),
        "categoria": "general",
        "confianza": 25,
        "fuente": "fallback_general",
    }


class ConsultaRequest(BaseModel):
    """Consultarequest"""
    consulta: str
    user_id: int | None = None
    contexto: dict[str, Any] | None = None


@router.post("/consultar", summary="Chatbot médico obstétrico")
async def chatbot_consultar(body: ConsultaRequest) -> dict:
    """Chatbot de asistencia médica obstétrica con base de conocimiento boliviana.
    Responde consultas sobre preeclampsia, RCIU, DMG, laboratorio, ecografía, parto y emergencias.

    La IA nunca reemplaza el criterio médico (Ley 3131/2005 Bolivia).
    """
    if not body.consulta or not body.consulta.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía")

    start = datetime.now(timezone.utc)
    result = _chatbot_response(body.consulta.strip(), body.contexto)
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

    return {
        "status": "success",
        "consulta_original": body.consulta,
        "respuesta": result["respuesta"],
        "categoria": result["categoria"],
        "confianza": result["confianza"],
        "fuente": result["fuente"],
        "tiempo_respuesta_ms": elapsed_ms,
        "disclaimer": "La IA es herramienta de apoyo. El médico tiene responsabilidad legal del diagnóstico.",
        "timestamp": start.isoformat(),
    }
