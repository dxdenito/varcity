import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.iam import permissions as perm
from app.modules.iam import role_service as service
from app.modules.iam.access import Access
from app.modules.iam.deps import get_access, require_permission
from app.modules.iam.role_schemas import GroupNode, PermissionOut, RoleIn, RoleOut
from app.modules.iam.service import AuthContext
from app.modules.iam.http import execute as _execute
from app.modules.iam import catalogue

router = APIRouter(prefix="/api/v1/admin", tags=["roles"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None





@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(
    _: AuthContext = Depends(require_permission(perm.ROLE_VIEW)),
    db: Session = Depends(get_db),
):
    return service.list_permissions(db)


@router.get("/permission-tree", response_model=list[GroupNode])
def permission_tree(_: AuthContext = Depends(require_permission(perm.ROLE_VIEW))):
    return catalogue.permission_tree()

@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    _: AuthContext = Depends(require_permission(perm.ROLE_VIEW)),
    db: Session = Depends(get_db),
):
    return service.list_roles(db)


@router.get("/roles/{role_id}", response_model=RoleOut)
def read_role(
    role_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ROLE_VIEW)),
    db: Session = Depends(get_db),
):
    return _execute(db, lambda: service.get_role(db, role_id))


@router.post("/roles", status_code=201, response_model=RoleOut)
def create_role(
    payload: RoleIn,
    request: Request,
    ctx: AuthContext = Depends(require_permission(perm.ROLE_MANAGE)),
    access: Access = Depends(get_access),
    db: Session = Depends(get_db),
):
    return _execute(
        db,
        lambda: service.create_role(
            db,
            ctx,
            access,
            name=payload.name,
            description=payload.description,
            permissions=payload.permissions,
            ip_address=_ip(request),
        ),
    )


@router.put("/roles/{role_id}", response_model=RoleOut)
def update_role(
    role_id: uuid.UUID,
    payload: RoleIn,
    request: Request,
    ctx: AuthContext = Depends(require_permission(perm.ROLE_MANAGE)),
    access: Access = Depends(get_access),
    db: Session = Depends(get_db),
):
    return _execute(
        db,
        lambda: service.update_role(
            db,
            ctx,
            access,
            role_id,
            name=payload.name,
            description=payload.description,
            permissions=payload.permissions,
            ip_address=_ip(request),
        ),
    )


@router.delete("/roles/{role_id}", status_code=204)
def delete_role(
    role_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_permission(perm.ROLE_MANAGE)),
    db: Session = Depends(get_db),
):
    _execute(db, lambda: service.delete_role(db, ctx, role_id, _ip(request)))