from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .models import ModelManager
from .routes import router

model_manager = ModelManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_manager.load_models()
    import app.routes
    app.routes.model_manager = model_manager
    yield


app = FastAPI(
    title="Fetal Medical IA Service",
    version="2.0.0",
    lifespan=lifespan,
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
    """Estado real: 503 si la red principal no tiene pesos.

    Antes respondía «healthy» siempre, también con pesos aleatorios.
    """
    from .ecografia_real import redes

    listo = model_manager._loaded and model_manager.model is not None
    if not listo:
        response.status_code = 503
    return {
        "status": "healthy" if listo else "unavailable",
        "model_loaded": listo,
        "error": model_manager.error_carga,
        "device": str(model_manager.device),
        "redes_reales": redes.estado(),
    }
