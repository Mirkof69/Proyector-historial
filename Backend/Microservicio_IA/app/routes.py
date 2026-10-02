"""Rutas API — Microservicio de IA de Fetal Medical Bolivia.

Todas las redes que se sirven aquí están entrenadas con ecografías REALES y
medidas en pacientes que no vieron (las métricas viajan en cada respuesta):

    POST /api/analyze                      análisis completo (plano → red de su plano → medidas)
    POST /api/analisis-ecografia           lo mismo, con nombre en castellano
    POST /api/plano-anatomico              solo el plano
    POST /api/biometria/circunferencia-cefalica
    POST /api/anomalias-cerebrales
    POST /api/segmentacion/{cabeza|torax|abdomen|intraparto}   (intraparto: ángulo de progresión)
    POST /api/quality-check · POST /api/consultar (chatbot) · GET /api/modelos

La EfficientNet-B4 de «14 patologías» se retiró: se había entrenado con
etiquetas no verificables (ver datos/CATALOGO.md) y no tenía ninguna métrica
válida. Sus rutas /detect-pathologies, /detect-anomalies y /classify ya no existen.
"""

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from .config import IMAGE_CONFIG
from .ecografia_real import redes as redes_reales
from .preprocessing import PILImagePreprocessor as ImagePreprocessor
from .segmentacion import TAREAS, segmentacion

router = APIRouter(prefix="/api", tags=["AI Analysis"])

preprocessor = ImagePreprocessor()


def _calidad(imagen) -> tuple[dict, list[str]]:
    """Calidad y aspecto de la imagen: no bloquean, se informan como avisos."""
    avisos = []
    calidad = preprocessor.calculate_image_quality(imagen)
    if calidad.get("resolucion_baja"):
        avisos.append(f"Resolución baja ({calidad.get('ancho_px')}×{calidad.get('alto_px')} px): "
                      "las medidas pueden ser menos precisas.")
    if not preprocessor.looks_like_ultrasound(imagen).get("parece_ecografia", True):
        avisos.append("La imagen tiene colores de fotografía, no de ecografía en escala de grises: "
                      "verifique que el archivo sea una ecografía.")
    return calidad, avisos


async def _analisis_completo(file: UploadFile, tamano_pixel_mm: float | None) -> dict:
    from .analisis_ecografia import analizar

    if tamano_pixel_mm is not None and not (0.01 <= tamano_pixel_mm <= 2.0):
        raise HTTPException(status_code=400, detail="tamano_pixel_mm fuera de rango (0,01–2,0 mm por píxel).")
    imagen = await _leer_imagen(file)
    calidad, avisos = _calidad(imagen)
    try:
        informe = await run_in_threadpool(analizar, imagen, tamano_pixel_mm)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    informe["avisos"] = avisos + informe["avisos"]
    return {"status": "success", "fuente": "redes_medidas", "filename": file.filename,
            "image_quality": calidad, **informe}


@router.post("/analyze", summary="Análisis completo de la ecografía con las redes medidas")
async def analyze_ultrasound(
    file: UploadFile = File(...),
    tamano_pixel_mm: float | None = Form(None, description="Milímetros por píxel (del ecógrafo o DICOM)"),
    modelo: str | None = Form(None, description="Ignorado; se mantiene por compatibilidad"),
    ciudad: str | None = Form(None, description="Ignorado; se mantiene por compatibilidad"),
) -> dict:
    """Plano anatómico → red de segmentación de ese plano → medidas, hallazgos e
    imagen con las estructuras dibujadas. Informe estructurado en JSON."""
    return await _analisis_completo(file, tamano_pixel_mm)


@router.post("/analisis-ecografia", summary="Análisis completo de la ecografía (igual que /analyze)")
async def analisis_ecografia(
    file: UploadFile = File(...),
    tamano_pixel_mm: float | None = Form(None),
) -> dict:
    return await _analisis_completo(file, tamano_pixel_mm)


@router.post("/segmentacion/{tarea}", summary="Segmentar cabeza, tórax o abdomen y medir")
async def segmentar(tarea: str, file: UploadFile = File(...), tamano_pixel_mm: float | None = Form(None)) -> dict:
    if tarea not in TAREAS:
        raise HTTPException(status_code=404, detail=f"Tarea desconocida. Use una de: {', '.join(TAREAS)}")
    imagen = await _leer_imagen(file)
    try:
        if tarea == "cabeza":
            return await run_in_threadpool(segmentacion.medir_cabeza, imagen, tamano_pixel_mm)
        if tarea == "torax":
            return await run_in_threadpool(segmentacion.medir_torax, imagen)
        if tarea == "intraparto":
            return await run_in_threadpool(segmentacion.medir_intraparto, imagen)
        return await run_in_threadpool(segmentacion.analizar_abdomen, imagen)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.get("/modelos", summary="Redes disponibles y sus métricas medidas")
async def modelos() -> dict:
    return redes_reales.estado() | segmentacion.estado()


async def _leer_imagen(file: UploadFile):
    """Valida extensión y tamaño y devuelve la imagen como array RGB."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    allowed: list = IMAGE_CONFIG["allowed_extensions"]  # type: ignore[assignment]
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Extensión no permitida. Use: {allowed}")
    content = await file.read()
    max_size: int = IMAGE_CONFIG["max_size"]  # type: ignore[assignment]
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {max_size // 1024 // 1024} MB",
        )
    try:
        return preprocessor.load_image(content, ext)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/biometria/circunferencia-cefalica",
    summary="Circunferencia cefálica y edad gestacional (red entrenada con HC18 real)",
)
async def medir_circunferencia_cefalica(
    file: UploadFile = File(...),
    tamano_pixel_mm: float = Form(..., description="Milímetros por píxel, del ecógrafo o DICOM"),
) -> dict:
    """Mide la circunferencia cefálica sobre un corte transtalámico y deriva la
    edad gestacional con Hadlock 1984. Error medido: 7,0 mm de media sobre 146
    imágenes de 117 madres que la red no vio (R² 0,978)."""
    imagen = await _leer_imagen(file)
    try:
        return await run_in_threadpool(redes_reales.medir_circunferencia, imagen, tamano_pixel_mm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.post(
    "/plano-anatomico",
    summary="Plano anatómico de la ecografía (red entrenada con FETAL_PLANES_DB real)",
)
async def clasificar_plano_anatomico(file: UploadFile = File(...)) -> dict:
    """Abdomen, cerebro, fémur, tórax, cuello uterino materno u otro.
    Exactitud medida: 92,7% sobre 5.271 imágenes de 896 madres no vistas."""
    imagen = await _leer_imagen(file)
    try:
        return await run_in_threadpool(redes_reales.clasificar_plano, imagen)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.post(
    "/anomalias-cerebrales",
    summary="Cribado de anomalías cerebrales fetales (red entrenada con ecografías reales)",
)
async def detectar_anomalias_cerebrales(file: UploadFile = File(...)) -> dict:
    """Normal o ventriculomegalia/hidrocefalia, fosa posterior, encefalocele o
    lesión quística/vascular, sobre un corte axial de la cabeza. Las métricas
    medidas (validación cruzada agrupada y prueba externa de falsos positivos)
    vienen en `modelo.metricas_prueba`."""
    imagen = await _leer_imagen(file)
    try:
        return await run_in_threadpool(redes_reales.detectar_anomalia_cerebral, imagen)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


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
            "El sistema mide HC y DBP sobre la imagen (red de segmentación) y estima el peso con Hadlock."
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
            "El sistema reconoce el plano de la ecografía (92,7 % de exactitud medida) y, según el plano, "
            "segmenta la cabeza (HC y DBP; error medio 4,4 mm en otro hospital), el tórax y el corazón "
            "(índice cardiotorácico) o el abdomen (estómago, vena umbilical, hígado, aorta), y dibuja las "
            "estructuras sobre la imagen. El peso fetal lo calcula Hadlock con las medidas cargadas. "
            "El médico DEBE validar cada análisis: la IA es herramienta de apoyo (Ley 3131)."
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
