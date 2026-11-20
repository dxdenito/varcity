from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.settings import service
from app.modules.settings.schemas import BrandingPublic

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/branding", response_model=BrandingPublic)
def read_branding(response: Response, db: Session = Depends(get_db)):
    """University name, logo and colours. Public: the login page needs it."""
    response.headers["Cache-Control"] = "public, max-age=60"
    return service.get_branding(db)