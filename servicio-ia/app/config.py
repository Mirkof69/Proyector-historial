"""Configuración del microservicio de IA
"""

import functools
import hashlib
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent
MODELS_DIR = Path(os.environ.get("MODELOS_IA_DIR", REPO_DIR / "modelos-ia" / "redes"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_CONFIG = {
    "max_size": 10 * 1024 * 1024,  # 10 MB
    "allowed_extensions": [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".dicom", ".dcm"],
    "input_size": (384, 384),
}

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
