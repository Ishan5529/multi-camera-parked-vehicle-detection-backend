"""
FastAPI backend server for multi-camera parked vehicle detection.
"""
from dotenv import load_dotenv
load_dotenv()
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import config, predict, parking


def parse_bool(value: str, default: bool = False) -> bool:
    """Parse common truthy values from environment variables."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_origins(value: str) -> list[str]:
    """Parse comma-separated CORS origins; fallback to wildcard when unset."""
    if not value:
        return ["*"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


CORS_ORIGINS = parse_origins(os.getenv("CORS_ORIGINS", ""))
ALLOW_CREDENTIALS = parse_bool(os.getenv("CORS_ALLOW_CREDENTIALS"), default=False)
APP_HOST = os.getenv("HOST", os.getenv("SERVER_HOST", "0.0.0.0"))
APP_PORT = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))
APP_RELOAD = parse_bool(os.getenv("DEBUG"), default=False)
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Create FastAPI app instance
app = FastAPI(
    title="Multi-Camera Parked Vehicle Detection API",
    description="Backend API for detecting parked vehicles using multiple camera feeds",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router)
app.include_router(predict.router)
app.include_router(parking.router)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables before serving requests."""
    init_db()


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify server is running.
    """
    return {
        "status": "healthy",
        "service": "multi-camera-parked-vehicle-detection-backend"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": "Multi-Camera Parked Vehicle Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_RELOAD,
        log_level=LOG_LEVEL,
    )
