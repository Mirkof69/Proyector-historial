"""Inicialización del paquete app
"""

from .config import (
    BASE_DIR,
    CONFIDENCE_THRESHOLDS,
    CORS_ORIGINS,
    DATASETS_DIR,
    IMAGE_CONFIG,
    MODEL_PATHS,
    MODELS_DIR,
    TEMP_DIR,
)
from .models import ModelManager
from .preprocessing import PILImagePreprocessor as ImagePreprocessor
from .routes import router

__version__ = "1.0.0"
__author__ = "Fetal Medical Team"
