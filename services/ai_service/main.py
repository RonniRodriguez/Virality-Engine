"""
Idea Inc - AI Service

Handles AI/LLM integration for:
- Idea generation
- Idea mutation
- Embedding generation
- RAG-based context retrieval
- Cultural sensitivity analysis
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from shared.utils.config import get_settings
from shared.utils.logging import setup_logging, get_logger

from app.api.routes import router as api_router
from app.llm.client import LLMClient
from app.vector.store import VectorStore

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging(
        service_name="ai-service",
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    logger.info("Starting AI Service", version=settings.app_version)
    
    # Initialize LLM client
    llm_client = LLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        enabled=settings.llm_enabled,
    )
    app.state.llm_client = llm_client
    
    # Initialize vector store
    vector_store = VectorStore(
        persist_directory=settings.chroma_persist_directory,
    )
    await vector_store.initialize()
    app.state.vector_store = vector_store
    
    logger.info("AI Service initialized", llm_enabled=settings.llm_enabled)
    
    yield
    
    # Shutdown
    logger.info("AI Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Idea Inc - AI Service",
    description="AI/LLM service for idea generation and mutation",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics endpoint
if settings.metrics_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": settings.app_version,
        "llm_enabled": settings.llm_enabled,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ai-service",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=8002,  # Different port from other services
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
    )

