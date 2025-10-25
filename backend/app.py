import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, generate_latest
import time

from config import settings
from modules.database import Database
from modules.security import SecurityManager
from modules.error_handler import ErrorHandler

# Import API routers
from api.document import router as document_router
from api.education import router as education_router
from api.generation import router as generation_router
from api.research import router as research_router
from api.user import router as user_router

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Rate limiter
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.rate_limit_storage_url)

# Database
database = Database()

# Security
security_manager = SecurityManager()

# Error handler
error_handler = ErrorHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await database.connect()
    logging.info("Database connected")
    
    # Create upload directories
    os.makedirs(settings.upload_folder, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    yield
    
    # Shutdown
    await database.disconnect()
    logging.info("Database disconnected")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan
    )
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.sovereignlegal.com", "localhost", "127.0.0.1"]
        )
    
    # Security middleware
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        # Add security headers
        response = await call_next(request)
        security_manager.add_security_headers(response)
        return response
    
    # Metrics middleware
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
        
        REQUEST_DURATION.observe(time.time() - start_time)
        
        return response
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Error handling
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error_handler.handle_http_exception(request, exc)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return error_handler.handle_general_exception(request, exc)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            await database.health_check()
            
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "version": settings.app_version,
                "environment": settings.environment,
                "database": "connected",
                "uptime": time.time()
            }
        except Exception as e:
            logging.error(f"Health check failed: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": "Database connection failed",
                    "timestamp": time.time()
                }
            )
    
    # Metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint"""
        return generate_latest()
    
    # Include routers
    app.include_router(document_router, prefix="/api/v1/document", tags=["Document Processing"])
    app.include_router(education_router, prefix="/api/v1/education", tags=["Education"])
    app.include_router(generation_router, prefix="/api/v1/generation", tags=["Document Generation"])
    app.include_router(research_router, prefix="/api/v1/research", tags=["Legal Research"])
    app.include_router(user_router, prefix="/api/v1/user", tags=["User Management"])
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )