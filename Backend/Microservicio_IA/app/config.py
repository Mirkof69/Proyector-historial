"""Configuración del microservicio de IA
"""

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
    "efficientnet_b4": str(MODELS_DIR / "efficientnet_b4.pth"),
    # Alias legados (ignorados en v3 pero mantenidos por compatibilidad)
    "classifier": str(MODELS_DIR / "efficientnet_b4.pth"),
    "pathology": str(MODELS_DIR / "efficientnet_b4.pth"),
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

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
