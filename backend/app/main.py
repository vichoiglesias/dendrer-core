"""
Dendrer API - Main FastAPI application
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📝 Environment: {settings.environment}")
    print(f"🔧 Debug mode: {settings.debug}")

    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection pool
    # TODO: Load ML model configurations

    yield

    # Shutdown
    print("👋 Shutting down gracefully...")
    # TODO: Close database connections
    # TODO: Close Redis connections


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Open-source LLM inference and fine-tuning platform",
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns 200 if service is healthy.
    """
    # TODO: Check database connection
    # TODO: Check Redis connection
    # TODO: Check vLLM service availability

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }
    )


# TODO: Include routers
# from app.routes import auth, api_keys, inference, admin
# app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["auth"])
# app.include_router(api_keys.router, prefix=f"{settings.api_prefix}/api-keys", tags=["api-keys"])
# app.include_router(inference.router, prefix="/v1", tags=["inference"])
# app.include_router(admin.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )
