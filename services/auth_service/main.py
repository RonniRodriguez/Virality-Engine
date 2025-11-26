"""
Idea Inc - Auth Service

Handles authentication and authorization:
- OAuth2/OIDC (Google, GitHub)
- JWT token management
- User registration and login
- Passkey support (future)
- Role-based access control
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
from app.db.database import init_db, close_db

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging(
        service_name="auth-service",
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    logger.info("Starting Auth Service", version=settings.app_version)
    
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    await close_db()
    logger.info("Auth Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Idea Inc - Auth Service",
    description="Authentication and authorization service for Idea Inc platform",
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
        "service": "auth-service",
        "version": settings.app_version,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "auth-service",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
    )

