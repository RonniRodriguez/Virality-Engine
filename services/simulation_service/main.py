"""
Idea Inc - Simulation Service

Core simulation engine for idea propagation:
- World management
- Agent-based simulation
- Idea spread mechanics
- Mutation triggers
- Snapshot generation
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
from app.engine.manager import SimulationManager

settings = get_settings()
logger = get_logger(__name__)

# Global simulation manager
simulation_manager: SimulationManager | None = None


def get_simulation_manager() -> SimulationManager:
    """Get the global simulation manager"""
    global simulation_manager
    if simulation_manager is None:
        raise RuntimeError("Simulation manager not initialized")
    return simulation_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global simulation_manager
    
    # Startup
    setup_logging(
        service_name="simulation-service",
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    logger.info("Starting Simulation Service", version=settings.app_version)
    
    # Initialize simulation manager
    simulation_manager = SimulationManager(
        max_concurrent_worlds=settings.max_concurrent_worlds,
    )
    await simulation_manager.start()
    logger.info("Simulation manager initialized")
    
    # Store in app state for dependency injection
    app.state.simulation_manager = simulation_manager
    
    yield
    
    # Shutdown
    if simulation_manager:
        await simulation_manager.stop()
    logger.info("Simulation Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Idea Inc - Simulation Service",
    description="Core simulation engine for idea propagation",
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
    manager = app.state.simulation_manager
    return {
        "status": "healthy",
        "service": "simulation-service",
        "version": settings.app_version,
        "active_worlds": manager.active_world_count if manager else 0,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "simulation-service",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=8001,  # Different port from auth service
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
    )

