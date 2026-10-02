import logging
import time
from contextlib import asynccontextmanager

import numpy as np
from PIL import Image
from fastapi import FastAPI, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .routes import router

logger = logging.getLogger(__name__)


def precalentar() -> dict:
    """Carga cada red en la GPU y hace una inferencia de prueba.

    Sin esto, la PRIMERA consulta tras cada arranque cargaba PyTorch/CUDA y las
    redes una por una: más de 30 s, y la pantalla (que pide plano, cabeza y
    anomalías a la vez) cortaba por tiempo. Visto en la prueba E2E del
    01/10/2026; después del arranque cada análisis tarda 20–50 ms.
    """
    from .ecografia_real import ARCHIVO_CEREBRO, ARCHIVO_HC, ARCHIVO_PLANO, redes
    from .ginecologia import CLASIFICADORES, ginecologia
    from .segmentacion import TAREAS, segmentacion

    imagen = np.zeros((256, 256), dtype=np.uint8)
    cargadas, t0 = [], time.perf_counter()
    for nombre, prueba in ((ARCHIVO_PLANO, redes.clasificar_plano), (ARCHIVO_CEREBRO, redes.probabilidades_cerebro),
                           (ARCHIVO_HC, lambda im: redes.medir_circunferencia(im, 0.15))):
        if redes.disponible(nombre):
            prueba(imagen)
            cargadas.append(nombre)
    for tarea in TAREAS:
        if segmentacion.disponible(tarea):
            segmentacion.segmentar(tarea, imagen)
            cargadas.append(f"segmentacion_{tarea}")
    for nombre in CLASIFICADORES:
        if ginecologia.disponible(nombre):
            ginecologia.probabilidades(nombre, Image.fromarray(imagen))
            cargadas.append(f"clasificador_{nombre}")
    segundos = round(time.perf_counter() - t0, 1)
    logger.info("Redes precalentadas en %s s: %s", segundos, ", ".join(cargadas))
    return {"redes": cargadas, "segundos": segundos}


@asynccontextmanager
async def ciclo_de_vida(app_: FastAPI):
    try:
        app_.state.precalentado = await run_in_threadpool(precalentar)
    except Exception:  # sin GPU o sin pesos el servicio igual arranca; /health lo dice
        logger.exception("No se pudieron precalentar las redes")
        app_.state.precalentado = {"redes": [], "segundos": None}
    yield


app = FastAPI(
    title="Fetal Medical IA Service",
    version="3.0.0",
    description="Redes entrenadas con ecografías reales y medidas en pacientes no vistas.",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health(response: Response):
    """Listo solo si está la red de plano anatómico, la puerta de todo análisis.

    Cada red se informa con su disponibilidad, su métrica medida y la huella
    sha256 de sus pesos.
    """
    from .ecografia_real import ARCHIVO_PLANO, redes
    from .ginecologia import ginecologia
    from .segmentacion import segmentacion

    listo = redes.disponible(ARCHIVO_PLANO)
    if not listo:
        response.status_code = 503
    return {
        "status": "healthy" if listo else "unavailable",
        "model_loaded": listo,
        "precalentado": getattr(app.state, "precalentado", None),
        "redes": redes.estado() | segmentacion.estado() | ginecologia.estado(),
    }
