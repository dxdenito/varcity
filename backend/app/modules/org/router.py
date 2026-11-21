import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.iam.deps import require_auth, require_superuser
from app.modules.iam.service import AuthContext
from app.modules.org import service
from app.modules.org.schemas import (
    InitializeRequest,
    NodeCreate,
    NodeOut,
    NodeTypeOut,
    NodeUpdate,
)

router = APIRouter(prefix="/api/v1/org", tags=["organization"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _execute(db: Session, action):
    try:
        result = action()
        db.commit()
        return result
    except service.NotFound as error:
        db.rollback()
        raise HTTPException(status_code=404, detail=error.message)
    except service.Conflict as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=error.message)
    except service.OrgError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=error.message)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That code is already in use.")


@router.get("/node-types", response_model=list[NodeTypeOut])
def list_node_types(_: AuthContext = Depends(require_auth), db: Session = Depends(get_db)):
    return service.list_node_types(db)


@router.get("/nodes", response_model=list[NodeOut])
def list_nodes(_: AuthContext = Depends(require_auth), db: Session = Depends(get_db)):
    return service.list_nodes(db)


@router.post("/initialize", status_code=201)
def initialize(
    payload: InitializeRequest,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    _execute(
        db,
        lambda: service.initialize_structure(
            db, ctx, payload.template, payload.institution_code, _ip(request)
        ),
    )
    return {"status": "initialized"}


@router.post("/nodes", status_code=201, response_model=NodeOut)
def create_node(
    payload: NodeCreate,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    return _execute(
        db,
        lambda: service.create_node(
            db,
            ctx,
            type_id=payload.type_id,
            parent_id=payload.parent_id,
            code=payload.code,
            name=payload.name,
            ip_address=_ip(request),
        ),
    )


@router.patch("/nodes/{node_id}", response_model=NodeOut)
def update_node(
    node_id: uuid.UUID,
    payload: NodeUpdate,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    return _execute(
        db,
        lambda: service.update_node(
            db, ctx, node_id, code=payload.code, name=payload.name, ip_address=_ip(request)
        ),
    )


@router.delete("/nodes/{node_id}", status_code=204)
def delete_node(
    node_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    _execute(db, lambda: service.delete_node(db, ctx, node_id, _ip(request)))