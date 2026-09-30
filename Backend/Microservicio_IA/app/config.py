"""Configuración del microservicio de IA
"""

import functools
import hashlib
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "trained_models"
DATASETS_DIR = BASE_DIR / "datasets"
TEMP_DIR = BASE_DIR / "temp"

MODELS_DIR.mkdir(exist_ok=True)
DATASETS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Rutas de modelos — EfficientNet-B4 es el modelo principal (PyTorch state_dict .pth)
MODEL_PATHS = {
    "efficientnet_b4": str(MODELS_DIR / "efficientnet_b4_renamed.pth"),
    # Alias legados (ignorados en v3 pero mantenidos por compatibilidad)
    "classifier": str(MODELS_DIR / "efficientnet_b4_renamed.pth"),
    "pathology": str(MODELS_DIR / "efficientnet_b4_renamed.pth"),
}

IMAGE_CONFIG = {
    "max_size": 10 * 1024 * 1024,  # 10 MB
    "allowed_extensions": [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".dicom", ".dcm"],
    "input_size": (384, 384),
}

# Umbral mínimo de confianza para reportar patología (Sensibilidad ≥ 0.92 en producción)
CONFIDENCE_THRESHOLDS = {
    "pathology_detection": 0.50,
    "classification": 0.60,
    "anomaly_detection": 0.50,
}

# Temperatura de inferencia para sigmoid(logits / T). T=0.33 amplifica cualquier
# logit pequeño a 0%/100% (sigmoid(3x)); T=1.0 da la probabilidad sigmoid real.
INFERENCE_TEMPERATURE = float(os.environ.get("INFERENCE_TEMPERATURE", "1.0"))

PATHOLOGY_THRESHOLD = float(os.environ.get("PATHOLOGY_THRESHOLD", "0.90"))

# Umbrales recalibrados empiricamente (2026-06-20) contra la confianza real
# que da el modelo con INFERENCE_TEMPERATURE=1.0. El umbral 0.90 universal
# venia de cuando la temperatura 0.33 inflaba todo a 0%/100%; con probabilidad
# real, la mayoria de verdaderos positivos cae entre 0.55 y 0.90 y antes se
# descartaba en silencio (ej.: preeclampsia_signos daba 0.79-0.87 siempre como
# top-1 pero nunca se reportaba por el umbral 0.90).
_DEFAULT_CLASS_THRESHOLDS = {
    # Recalibrado 2026-06-23 contra datasets_pathology/validation/ real (1037
    # imagenes, nunca vistas en entrenamiento) usando curva ROC real y el
    # estadistico de Youden (J = sensibilidad + especificidad - 1) por clase.
    # No se tomo el punto optimo exacto de Youden a ciegas: se deja margen de
    # seguridad sobre ese punto, mayor cuanto menor es el tamano de muestra
    # de validacion de esa clase. Comentario por clase con AUC/sensibilidad
    # medida antes y despues del ajuste.
    # AUC=0.994, sensibilidad real al umbral viejo (0.65) = 94.4% — ya buena,
    # bajado un poco mas cerca del optimo Youden (0.509) para exprimir mejor.
    "hidrocefalia": 0.55,
    # AUC=0.987, sensibilidad real al umbral viejo (0.65) = SOLO 65.3% (se
    # perdia 1 de cada 3 casos reales). Youden optimo=0.151; se deja margen.
    "anencefalia": 0.35,
    # AUC=0.997, sensibilidad real al umbral viejo (0.65) = 90.7%. Youden=0.371.
    "espina_bifida": 0.50,
    # AUC=0.997 (separacion casi perfecta), sensibilidad real al umbral viejo
    # (0.55) = SOLO 56%. Youden=0.069; se deja bastante margen de seguridad.
    "labio_leporino": 0.25,
    # AUC=1.000, sensibilidad y especificidad YA al 100% con el umbral viejo
    # (0.65) — no se toca, esta perfecto.
    "atresia_duodenal": 0.65,
    # AUC=0.986, sensibilidad real al umbral viejo (0.65) = SOLO 50% (la clase
    # mas debil documentada, confirmado ahora con datos reales de validacion).
    # Youden optimo=0.074; se sube bastante mas que el optimo por ser la clase
    # historicamente mas inestable (ver ESTADO_RED_NEURONAL.md).
    "cardiopatia_congenita": 0.30,
    # AUC=0.964, sensibilidad real al umbral viejo (0.35) = 88.1%. Youden=0.130.
    "oligohidramnios": 0.25,
    # Recalibrado 2026-09-04 contra datasets_pathology_v2 (calibrado en
    # valid/, medido en test/, 2.911 imagenes). El umbral de 0.18 estaba
    # calibrado solo por sensibilidad y arruinaba la precision: 0.158, o sea
    # 84 de cada 100 alertas eran falsas. Un detector en el que el medico deja
    # de creer no sirve, por muy sensible que sea.
    # AUC=0.959 (la separacion SI esta), F1 medido: 0.268 -> 0.430 con 0.49.
    "polihidramnios": 0.49,
    # AUC=0.999, sensibilidad real al umbral viejo (0.40) = 86.3%. Youden=0.059.
    "restriccion_crecimiento": 0.28,
    # Recalibrado 2026-09-04 igual que polihidramnios. Con 0.22 la precision
    # era 0.225: 3 de cada 4 alertas, falsas. F1 medido: 0.305 -> 0.429.
    # AUC=0.838, la MAS BAJA de las 14: aqui el limite no es el umbral sino el
    # modelo, que no separa bien esta clase. Mejorarla de verdad necesita mas
    # y mejores imagenes de entrenamiento, no recalibrar.
    "macrosomia_fetal": 0.37,
    # AUC=1.000, sensibilidad real al umbral viejo (0.85) = 95% — ya excelente,
    # Youden=0.817 (casi igual al actual). No se toca.
    "placenta_previa": 0.85,
    # AUC=0.998, sensibilidad real al umbral viejo (0.65) = 100% YA. Youden
    # optimo real (0.694) es MAS ALTO que el actual, pero se mantiene el
    # umbral bajo deliberado: condicion grave donde un falso negativo es mucho
    # peor que un falso positivo (el medico siempre revisa el caso).
    "preeclampsia_signos": 0.65,
    # AUC=1.000 (separacion perfecta), sensibilidad real al umbral viejo (0.60)
    # = 87.5%. Youden optimo=0.368; se baja un poco mas, sigue siendo "la peor
    # condicion posible para no detectar".
    "muerte_fetal": 0.45,
    # AUC=1.000 (separacion perfecta), pero sensibilidad real al umbral viejo
    # (0.95) = SOLO 64.7% — mas de un tercio de los embarazos multiples reales
    # quedaban en "baja_confianza" en vez de confirmarse, pese a que el modelo
    # SI los distingue bien (AUC perfecto). El umbral de 0.95 fue fijado por
    # precaucion ante pocas imagenes de entrenamiento (194), no por evidencia
    # real de mala separacion — la validacion real muestra que sí separa bien.
    # Se baja a 0.75: por encima del optimo de Youden (0.660) por margen de
    # seguridad extra, dado que la muestra de validacion es chica (n=17
    # positivos), pero muy por debajo del 0.95 anterior, que era injustificado.
    "embarazo_multiple": float(os.environ.get("THRESHOLD_EMBARAZO_MULTIPLE", "0.75")),
    "normal": float(os.environ.get("THRESHOLD_NORMAL", "0.50")),
    "no_ecografia": 0.999,  # No se reporta como patologia, solo como señal de pre-analisis
}
CLASS_THRESHOLDS = {
    cls: float(os.environ.get(f"THRESHOLD_{cls.upper()}", default))
    for cls, default in _DEFAULT_CLASS_THRESHOLDS.items()
}

# El biometry_head (BPD/HC/AC/FL/peso) se entrenó con objetivos SINTETICOS por
# categoria clinica (train_biometry_head.py), no con mediciones reales, porque
# no existe un dataset de biometria fetal anotado. Da una estimacion
# orientativa en vez de nada, pero NUNCA debe tratarse como medicion validada.
# Apagado por defecto: un número sintético con forma de medición (BPD 48 mm)
# se copia a la historia clínica como si fuera real. La circunferencia cefálica
# real la da la red de HC18 (/api/biometria/circunferencia-cefalica).
BIOMETRY_AVAILABLE = os.environ.get("BIOMETRY_AVAILABLE", "false").lower() == "true"
BIOMETRY_METHOD = "estimacion_sintetica_no_validada"

# Altitud aproximada (msnm) de ciudades bolivianas, usada para el ajuste de
# riesgo de preeclampsia por gran altura (ver models.py ALTITUDE_PREECLAMPSIA_FACTOR).
CITY_ALTITUDE_M = {
    "la paz": 3640,
    "el alto": 4150,
    "potosi": 3960,
    "oruro": 3709,
    "sucre": 2810,
    "cochabamba": 2558,
    "tarija": 1866,
    "santa cruz": 416,
    "santa cruz de la sierra": 416,
    "trinidad": 156,
    "cobija": 235,
}

# La red de 14 patologías se entrenó con positivos en su mayoría sintéticos
# y no tiene métricas en una cohorte clínica independiente: se sirve marcada
# como experimental. Las redes de ecografia_real.py (plano anatómico y
# circunferencia cefálica) sí están medidas en pacientes no vistas.
ADVERTENCIA_B4 = (
    "Detector experimental: entrenado mayormente con imágenes sintéticas y sin validación "
    "clínica independiente. Sirve como apoyo a la lectura, nunca como diagnóstico."
)

def huella_sha256(ruta) -> str | None:
    """sha256 del archivo de pesos: identifica EXACTAMENTE qué modelo produjo
    un resultado (dos .pth con el mismo nombre pueden ser entrenamientos
    distintos). Se calcula una vez por archivo y fecha de modificación."""
    ruta = Path(ruta)
    if not ruta.is_file():
        return None
    return _huella(str(ruta), ruta.stat().st_mtime_ns)


@functools.lru_cache(maxsize=16)
def _huella(ruta: str, _mtime: int) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


CORS_ORIGINS = [
    "http://localhost:3000",
    os.environ.get("BACKEND_CORS_URL", "http://localhost:8000"),
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
