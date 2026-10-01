from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .routes import router

app = FastAPI(
    title="Fetal Medical IA Service",
    version="3.0.0",
    description="Redes entrenadas con ecografías reales y medidas en pacientes no vistas.",
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
    from .segmentacion import segmentacion

    listo = redes.disponible(ARCHIVO_PLANO)
    if not listo:
        response.status_code = 503
    return {
        "status": "healthy" if listo else "unavailable",
        "model_loaded": listo,
        "redes": redes.estado() | segmentacion.estado(),
    }
