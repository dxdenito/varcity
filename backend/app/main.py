from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.iam.router import router as auth_router
from app.modules.settings.router import router as settings_router
from app.modules.setup.router import router as setup_router
from app.modules.setup.service import announce_setup_code_if_needed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    announce_setup_code_if_needed()
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.include_router(settings_router)
app.include_router(auth_router)
app.include_router(setup_router)


@app.get("/api/v1/health/live", tags=["health"])
def live():
    """Liveness check: the process is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }


@app.get("/api/v1/health/ready", tags=["health"])
def ready(response: Response, db: Session = Depends(get_db)):
    """Readiness check: the app can reach its database."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "unavailable", "database": "down"}
    return {"status": "ok", "database": "up"}