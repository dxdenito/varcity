import hmac
import uuid

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.iam import service
from app.modules.iam.access import Access
from app.modules.iam.service import AuthContext

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def require_auth(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    """Dependency: the request must carry a valid session cookie."""
    token = request.cookies.get(settings.session_cookie_name)
    ctx = service.resolve_session(db, token) if token else None
    if ctx is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return ctx


def _check_csrf(sent: str, ctx: AuthContext) -> None:
    if not hmac.compare_digest(sent.encode(), ctx.csrf_token.encode()):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


def require_csrf(
    x_csrf_token: str = Header(default=""),
    ctx: AuthContext = Depends(require_auth),
) -> AuthContext:
    """Dependency for state-changing endpoints: also needs the CSRF header."""
    _check_csrf(x_csrf_token, ctx)
    return ctx


def get_access(
    request: Request,
    ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Access:
    """The signed-in user's permissions, loaded once per request."""
    access = getattr(request.state, "access", None)
    if access is None:
        access = Access.load(db, ctx.user)
        request.state.access = access
    return access


def require_permission(
    code: str, *, node_param: str | None = None, anywhere: bool = False
):
    """Dependency factory: signed in, CSRF on writes, and holding `code`.

    Default: a university-wide grant is needed.
    node_param: the named path parameter holds a node id; a grant covering that node counts.
    anywhere: a grant at any scope counts (used for read-only visibility).
    """

    def dependency(
        request: Request,
        ctx: AuthContext = Depends(require_auth),
        access: Access = Depends(get_access),
    ) -> AuthContext:
        if request.method not in SAFE_METHODS:
            _check_csrf(request.headers.get("x-csrf-token", ""), ctx)
        if anywhere:
            allowed = access.can_anywhere(code)
        elif node_param is None:
            allowed = access.can(code)
        else:
            try:
                node_id = uuid.UUID(str(request.path_params[node_param]))
            except (KeyError, ValueError):
                raise HTTPException(status_code=404, detail="Not found")
            allowed = access.can_on_node(code, node_id)
        if not allowed:
            raise HTTPException(status_code=403, detail="Not permitted")
        return ctx

    dependency.permission_code = code
    return dependency