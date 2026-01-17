"""
FastAPI main application initialization.
Central entry point for the KnowFlow backend with enhanced error handling.
"""

import logging
import traceback
from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api import ingest, query
from app.config import settings

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS with proper origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # React/Next.js dev
    "http://localhost:7860",      # Gradio default port
    "http://localhost:8000",      # FastAPI
    "http://127.0.0.1:7860",      # Gradio alt
    "http://127.0.0.1:8000",      # FastAPI alt
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)


# Include routers
app.include_router(ingest.router)
app.include_router(query.router)


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return JSONResponse({
        "name": "KnowFlow API",
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "health": "/api/query/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    })


@app.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "service": "KnowFlow API"
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information."""
    logger.warning(f"Validation error from {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "message": "Invalid request parameters",
            "details": exc.errors()[:3]  # Limit to first 3 errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception in {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": request.headers.get("x-request-id", "unknown")
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests and responses."""
    import time
    start = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s"
        )
        return response
    except Exception as exc:
        logger.error(f"Request failed: {request.method} {request.url.path} - {str(exc)}")
        raise


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
