from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.ocr import router as ocr_router
from app.services.vllm_client import vllm_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that runs during application startup and shutdown.
    Handles startup configuration and closes pooled resources on exit.
    """
    # Startup: Initialize shared HTTP connection client for vLLM
    vllm_client.init_client()
    yield
    # Shutdown: Clean up client connections
    await vllm_client.close_client()

app = FastAPI(
    title="OCR Pipeline API",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware from environment-configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount OCR router with /api/v1 prefix
app.include_router(ocr_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint serving basic API metadata.
    """
    return {
        "service": "Modular OCR Pipeline API",
        "status": "healthy",
        "allowed_tags": settings.allowed_tags_list,
        "model": settings.VLLM_MODEL_NAME
    }
