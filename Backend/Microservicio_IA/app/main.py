from contextlib import asynccontextmanager

from fastapi import FastAPI
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
async def health():
    return {
        "status": "healthy",
        "model_loaded": model_manager._loaded,
        "device": str(model_manager.device),
    }
