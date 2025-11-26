"""
Idea Inc - API Gateway

Central entry point for all client requests.
Handles routing, authentication, rate limiting, and GraphQL aggregation.
"""

import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Optional

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import make_asgi_app
import httpx

from shared.utils.config import get_settings
from shared.utils.logging import setup_logging, get_logger, log_request
from shared.utils.security import verify_token
from shared.utils.cache import create_cache, Cache

settings = get_settings()
logger = get_logger(__name__)

# Service URLs (would be from service discovery in production)
SERVICE_URLS = {
    "auth": "http://localhost:8000",
    "simulation": "http://localhost:8001",
    "ai": "http://localhost:8002",
}

# Global cache instance
cache: Optional[Cache] = None
security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global cache
    
    # Startup
    setup_logging(
        service_name="api-gateway",
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    logger.info("Starting API Gateway", version=settings.app_version)
    
    # Initialize cache
    cache = create_cache(
        use_redis=False,  # Use in-memory for MVP
        prefix="gateway",
    )
    
    yield
    
    # Shutdown
    logger.info("API Gateway shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Idea Inc - API Gateway",
    description="Central API gateway for Idea Inc platform",
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


# =============================================================================
# Middleware
# =============================================================================

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    
    log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware"""
    if cache is None:
        return await call_next(request)
    
    # Get client identifier (IP or user ID)
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit (100 requests per minute)
    allowed, remaining = await cache.check_rate_limit(
        identifier=f"ip:{client_ip}",
        limit=100,
        window=60,
    )
    
    if not allowed:
        return Response(
            content='{"error": "Rate limit exceeded"}',
            status_code=429,
            media_type="application/json",
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> Optional[dict]:
    """Get current user from JWT (optional)"""
    if not credentials:
        return None
    
    payload = verify_token(credentials.credentials, token_type="access")
    return payload


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict:
    """Get current user from JWT (required)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


# =============================================================================
# Health & Info Routes
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": settings.app_version,
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "Idea Inc API Gateway",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
        "endpoints": {
            "auth": "/api/v1/auth",
            "worlds": "/api/v1/worlds",
            "ideas": "/api/v1/worlds/{world_id}/ideas",
            "ai": "/api/v1/ai",
        },
    }


@app.get("/api/v1/services/status")
async def services_status():
    """Check status of all backend services"""
    statuses = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{url}/health")
                statuses[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                }
            except Exception as e:
                statuses[service_name] = {
                    "status": "unavailable",
                    "error": str(e),
                }
    
    return {"services": statuses}


# =============================================================================
# Proxy Routes (Forward to Backend Services)
# =============================================================================

async def proxy_request(
    request: Request,
    service: str,
    path: str,
    method: str = None,
) -> Response:
    """Proxy a request to a backend service"""
    if service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    url = f"{SERVICE_URLS[service]}{path}"
    method = method or request.method
    
    # Forward headers (except host)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Get body for POST/PUT/PATCH
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.RequestError as e:
        logger.error("Proxy error", service=service, error=str(e))
        raise HTTPException(status_code=502, detail="Service unavailable")


# Auth Service Routes
@app.api_route(
    "/api/v1/auth/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["auth"],
)
async def auth_proxy(request: Request, path: str):
    """Proxy to Auth Service"""
    return await proxy_request(request, "auth", f"/api/v1/auth/{path}")


# Simulation Service Routes
@app.api_route(
    "/api/v1/worlds/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["simulation"],
)
async def worlds_proxy(request: Request, path: str):
    """Proxy to Simulation Service"""
    return await proxy_request(request, "simulation", f"/api/v1/worlds/{path}")


@app.api_route(
    "/api/v1/worlds",
    methods=["GET", "POST"],
    tags=["simulation"],
)
async def worlds_root_proxy(request: Request):
    """Proxy to Simulation Service (root)"""
    return await proxy_request(request, "simulation", "/api/v1/worlds")


# AI Service Routes
@app.api_route(
    "/api/v1/ai/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["ai"],
)
async def ai_proxy(request: Request, path: str):
    """Proxy to AI Service"""
    return await proxy_request(request, "ai", f"/api/v1/{path}")


# =============================================================================
# GraphQL Endpoint (Stub for v1)
# =============================================================================

@app.post("/graphql")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint (stub for v1)"""
    return {
        "message": "GraphQL endpoint - coming in v1",
        "hint": "Use REST endpoints for MVP",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=8080,  # Gateway on port 8080
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
    )

