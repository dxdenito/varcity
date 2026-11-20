from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.version)


@app.get("/api/v1/health/live", tags=["health"])
def live():
    """Liveness check: the process is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }