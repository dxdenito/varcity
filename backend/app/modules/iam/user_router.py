import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.iam import permissions as perm
from app.modules.iam import user_service as service
from app.modules.iam.access import Access
from app.modules.iam.deps import get_access, require_permission
from app.modules.iam.http import execute
from app.modules.iam.service import AuthContext
from app.modules.iam.user_schemas import AssignIn, UserOut, UserPage

router = APIRouter(prefix="/api/v1/admin/users", tags=["users"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=UserPage)
def list_users(
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: AuthContext = Depends(require_permission(perm.USER_VIEW)),
    db: Session = Depends(get_db),
):
    return service.list_users(db, q=q, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserOut)
def read_user(
    user_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.USER_VIEW)),
    db: Session = Depends(get_db),
):
    return execute(db, lambda: service.get_user(db, user_id))


@router.post("/{user_id}/roles", status_code=201, response_model=UserOut)
def assign_role(
    user_id: uuid.UUID,
    payload: AssignIn,
    request: Request,
    ctx: AuthContext = Depends(require_permission(perm.ASSIGN_ROLE, anywhere=True)),
    access: Access = Depends(get_access),
    db: Session = Depends(get_db),
):
    return execute(
        db,
        lambda: service.assign_role(
            db,
            ctx,
            access,
            user_id,
            role_id=payload.role_id,
            node_id=payload.node_id,
            ip_address=_ip(request),
        ),
    )


@router.delete("/{user_id}/roles/{assignment_id}", response_model=UserOut)
def unassign_role(
    user_id: uuid.UUID,
    assignment_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_permission(perm.ASSIGN_ROLE, anywhere=True)),
    access: Access = Depends(get_access),
    db: Session = Depends(get_db),
):
    return execute(
        db,
        lambda: service.unassign_role(
            db, ctx, access, user_id, assignment_id, _ip(request)
        ),
    )