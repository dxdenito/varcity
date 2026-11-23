from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.iam.router import admin_router, router as auth_router
from app.modules.settings.router import admin_router as settings_admin_router
from app.modules.settings.router import router as settings_router
from app.modules.setup.router import router as setup_router
from app.modules.setup.service import announce_setup_code_if_needed
from app.modules.org.router import router as org_router
import app.modules.all_permissions  # noqa: F401
from app.core.db import SessionLocal
from app.modules.iam.access import sync_registry
from app.modules.iam.role_router import router as role_router
from app.modules.iam.user_router import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with SessionLocal() as db:
        sync_registry(db)
        db.commit()
    announce_setup_code_if_needed()
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.include_router(settings_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(setup_router)
app.include_router(settings_admin_router)
app.include_router(org_router)
app.include_router(role_router)
app.include_router(user_router)


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