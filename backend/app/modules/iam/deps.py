import hmac

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.iam import service
from app.modules.iam.service import AuthContext


def require_auth(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    """Dependency: the request must carry a valid session cookie."""
    token = request.cookies.get(settings.session_cookie_name)
    ctx = service.resolve_session(db, token) if token else None
    if ctx is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return ctx


def require_csrf(
    x_csrf_token: str = Header(default=""),
    ctx: AuthContext = Depends(require_auth),
) -> AuthContext:
    """Dependency for state-changing endpoints: also needs the CSRF header."""
    if not hmac.compare_digest(x_csrf_token.encode(), ctx.csrf_token.encode()):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    return ctx

def require_superuser(ctx: AuthContext = Depends(require_csrf)) -> AuthContext:
    # Temporary: replaced by permission checks in the RBAC phase.
    if not ctx.user.is_superuser:
        raise HTTPException(status_code=403, detail="Not permitted")
    return ctx