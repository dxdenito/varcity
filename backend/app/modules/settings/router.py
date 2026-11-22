from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.iam.deps import require_auth, require_superuser
from app.modules.iam.service import AuthContext
from app.modules.settings import service
from app.modules.settings.schemas import BrandingConfig, BrandingPublic, UniversityProfile,GeneralConfig

router = APIRouter(prefix="/api/v1/public", tags=["public"])
admin_router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/branding", response_model=BrandingPublic)
def read_branding(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "public, max-age=60"
    return service.get_branding(db)


@router.get("/branding/logo")
def read_logo(db: Session = Depends(get_db)):
    asset = service.get_logo(db)
    if asset is None:
        raise HTTPException(status_code=404, detail="No logo has been uploaded.")
    return Response(
        content=asset.data,
        media_type=asset.content_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )


@admin_router.get("/university", response_model=UniversityProfile)
def read_university(_: AuthContext = Depends(require_auth), db: Session = Depends(get_db)):
    return service.get_university_profile(db)


@admin_router.put("/university", response_model=UniversityProfile)
def update_university(
    payload: BrandingConfig,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    service.update_university_profile(db, ctx, payload, _ip(request))
    db.commit()
    return service.get_university_profile(db)


@admin_router.post("/university/logo", status_code=204)
def upload_logo(
    file: UploadFile,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    data = file.file.read(service.MAX_LOGO_BYTES + 1)
    try:
        service.set_logo(db, ctx, data, _ip(request))
    except service.InvalidLogo as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error))
    db.commit()


@admin_router.delete("/university/logo", status_code=204)
def delete_logo(
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    service.remove_logo(db, ctx, _ip(request))
    db.commit()

@admin_router.get("/general", response_model=GeneralConfig)
def read_general(_: AuthContext = Depends(require_auth), db: Session = Depends(get_db)):
    return service.get_general(db)


@admin_router.put("/general", response_model=GeneralConfig)
def update_general(
    payload: GeneralConfig,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    service.update_general(db, ctx, payload, _ip(request))
    db.commit()
    return service.get_general(db)