"""Rutas API — Microservicio IA Fetal Medical
CNN EfficientNet-B4 (PyTorch + MONAI) + Chatbot obstétrico
"""

import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from .config import IMAGE_CONFIG
from .models import ModelManager
from .preprocessing import ImagePreprocessor

router = APIRouter(prefix="/api", tags=["AI Analysis"])

model_manager = ModelManager()
preprocessor = ImagePreprocessor()


# ── CNN: ANÁLISIS COMPLETO ────────────────────────────────────────────────────


@router.post("/analyze", summary="Análisis completo EfficientNet-B4")
async def analyze_ultrasound(file: UploadFile = File(...)) -> dict:
    """Análisis completo con EfficientNet-B4 (PyTorch 2.2 + MONAI):
    - 15 patologías fetales (umbral ≥ 0.50)
    - Biometría: BPD, HC, AC, FL, peso estimado
    - Grad-CAM sobre última capa convolucional
    - SHAP risk scores (preeclampsia, parto prematuro, etc.)
    """
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in IMAGE_CONFIG["allowed_extensions"]:
            raise HTTPException(
                status_code=400,
                detail=f"Extensión no permitida. Use: {IMAGE_CONFIG['allowed_extensions']}",
            )
        content = await file.read()
        if len(content) > IMAGE_CONFIG["max_size"]:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo muy grande. Máximo: {IMAGE_CONFIG['max_size'] // 1024 // 1024} MB",
            )
        image = preprocessor.load_image(content, ext)
        quality = preprocessor.calculate_image_quality(image)
        enhanced = preprocessor.enhance_image(image)
        result = model_manager.analyze(enhanced, compute_cam=True)
        result["filename"] = file.filename
        result["file_size_kb"] = round(len(content) / 1024, 1)
        result["image_quality"] = quality
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {e!s}") from e


@router.post("/detect-pathologies", summary="Detectar patologías fetales + biometría")
async def detect_pathologies(file: UploadFile = File(...)) -> dict:
    """Detect pathologies"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in IMAGE_CONFIG["allowed_extensions"]:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {IMAGE_CONFIG['allowed_extensions']}",
        )
    content = await file.read()
    if len(content) > IMAGE_CONFIG["max_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {IMAGE_CONFIG['max_size'] // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    enhanced = preprocessor.enhance_image(image)
    result = model_manager.analyze(enhanced, compute_cam=False)
    return {
        "status": result["status"],
        "filename": file.filename,
        "pathology_detection": result["pathology_detection"],
        "biometry": result["biometry"],
        "shap_risk_scores": result["shap_risk_scores"],
        "fuente": result["fuente"],
    }


@router.post("/detect-anomalies", summary="Detectar anomalías fetales")
async def detect_anomalies(file: UploadFile = File(...)) -> dict:
    """Detect anomalies"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in IMAGE_CONFIG["allowed_extensions"]:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {IMAGE_CONFIG['allowed_extensions']}",
        )
    content = await file.read()
    if len(content) > IMAGE_CONFIG["max_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {IMAGE_CONFIG['max_size'] // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    enhanced = preprocessor.enhance_image(image)
    result = model_manager.analyze(enhanced, compute_cam=False)
    return {
        "status": result["status"],
        "filename": file.filename,
        "anomaly_detection": result["pathology_detection"],
        "shap_risk_scores": result["shap_risk_scores"],
        "fuente": result["fuente"],
    }


@router.post("/classify", summary="Clasificar tipo de ecografía (legado)")
async def classify_ultrasound(file: UploadFile = File(...)) -> dict:
    """Classify ultrasound"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in IMAGE_CONFIG["allowed_extensions"]:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {IMAGE_CONFIG['allowed_extensions']}",
        )
    content = await file.read()
    if len(content) > IMAGE_CONFIG["max_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {IMAGE_CONFIG['max_size'] // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    enhanced = preprocessor.enhance_image(image)
    result = model_manager.analyze(enhanced, compute_cam=False)
    return {
        "status": result["status"],
        "filename": file.filename,
        "classification": {
            "pathology_detection": result["pathology_detection"],
            "score_global": result["score_global"],
        },
    }


@router.post("/quality-check", summary="Evaluar calidad de imagen médica")
async def check_image_quality(file: UploadFile = File(...)) -> dict:
    """Check image quality"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in IMAGE_CONFIG["allowed_extensions"]:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {IMAGE_CONFIG['allowed_extensions']}",
        )
    content = await file.read()
    if len(content) > IMAGE_CONFIG["max_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {IMAGE_CONFIG['max_size'] // 1024 // 1024} MB",
        )
    image = preprocessor.load_image(content, ext)
    quality = preprocessor.calculate_image_quality(image)
    return {"status": "success", "filename": file.filename, "quality": quality}


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
            "⚠️ EMERGENCIA OBSTÉTRICA — Activar protocolo institucional urgente. "
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

    start = datetime.utcnow()
    result = _chatbot_response(body.consulta.strip(), body.contexto)
    elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

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
