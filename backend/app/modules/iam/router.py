import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.iam import service
from app.modules.iam.deps import require_auth, require_csrf, require_superuser
from app.modules.iam.schemas import AuthResponse, LoginRequest
from app.modules.iam.service import AuthContext
from app.modules.iam.tokens import csrf_for

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    result = service.login(
        db,
        email=payload.email,
        password=payload.password,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()  # saves a success, but also the counters/audit of a failure

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password, or the account is temporarily locked.",
        )

    response.set_cookie(
        key=settings.session_cookie_name,
        value=result.token,
        max_age=settings.session_absolute_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return AuthResponse(user=result.user, csrf_token=csrf_for(result.token))


@router.get("/me", response_model=AuthResponse)
def me(ctx: AuthContext = Depends(require_auth)):
    """Who is signed in? Also how the frontend gets its CSRF token after a reload."""
    return AuthResponse(user=ctx.user, csrf_token=ctx.csrf_token)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    service.logout(db, ctx, _client_ip(request))
    db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")

admin_router = APIRouter(prefix="/api/v1/admin/users", tags=["admin"])


@admin_router.post("/{user_id}/unlock", status_code=204)
def unlock_user(
    user_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        service.unlock_account(db, ctx, user_id, _client_ip(request))
    except service.AccountNotFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="Account not found")
    db.commit()