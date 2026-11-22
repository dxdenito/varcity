import re
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import tabular
from app.core.db import get_db
from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam.deps import require_auth, require_superuser
from app.modules.iam.service import AuthContext
from app.modules.org import bulk, service
from app.modules.org.models import Node
from app.modules.org.schemas import (
    ImportPreview,
    InitializeRequest,
    NodeCreate,
    NodeMove,
    NodeOut,
    NodeTypeOut,
    NodeUpdate,
)

router = APIRouter(prefix="/api/v1/org", tags=["organization"])

MEDIA_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}
TEMPLATE_ROWS = [
    ["College", "College of Engineering", "", ""],
    ["School", "School of Computing", "", "College of Engineering"],
    ["Department", "Computer Science", "", "College of Engineering > School of Computing"],
]


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


def _get_node(db: Session, node_id: uuid.UUID) -> Node:
    node = db.get(Node, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Entry not found.")
    return node


def _read_upload(file: UploadFile) -> list[tuple[int, dict[str, str]]]:
    data = file.file.read(tabular.MAX_FILE_BYTES + 1)
    try:
        return tabular.read_table(file.filename or "", data, bulk.REQUIRED)
    except tabular.TableError as error:
        raise HTTPException(status_code=422, detail=str(error))


def _download(file_format: str, base_name: str, title: str, headers: list[str], rows: list[list]):
    if file_format == "csv":
        content = tabular.write_csv(headers, rows)
    elif file_format == "xlsx":
        content = tabular.write_xlsx(headers, rows, sheet_name=title)
    else:
        content = tabular.write_pdf(title, headers, rows)

    safe_name = re.sub(r"[^A-Za-z0-9]+", "-", base_name).strip("-") or "organization"
    return Response(
        content=content,
        media_type=MEDIA_TYPES[file_format],
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.{file_format}"'},
    )


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
            db,
            ctx,
            node_id,
            code=payload.code if "code" in payload.model_fields_set else service.UNSET,
            name=payload.name,
            ip_address=_ip(request),
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


@router.post("/nodes/{node_id}/move", response_model=NodeOut)
def move_node(
    node_id: uuid.UUID,
    payload: NodeMove,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    return _execute(
        db, lambda: service.move_node(db, ctx, node_id, payload.new_parent_id, _ip(request))
    )


@router.post("/nodes/{node_id}/archive", response_model=NodeOut)
def archive_node(
    node_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    return _execute(db, lambda: service.archive_node(db, ctx, node_id, _ip(request)))


@router.post("/nodes/{node_id}/unarchive", response_model=NodeOut)
def unarchive_node(
    node_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    return _execute(db, lambda: service.unarchive_node(db, ctx, node_id, _ip(request)))


@router.get("/nodes/{node_id}/export")
def export_node(
    node_id: uuid.UUID,
    request: Request,
    file_format: Literal["csv", "xlsx", "pdf"] = Query("csv", alias="format"),
    ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    node = _get_node(db, node_id)
    rows = bulk.export_rows(db, node)
    audit.record(
        db,
        action="org.export",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        new_values={"format": file_format, "rows": len(rows)},
        ip_address=clean_ip(_ip(request)),
    )
    db.commit()
    return _download(file_format, f"{node.name}-structure", node.name, bulk.COLUMNS, rows)


@router.get("/import-template")
def import_template(
    file_format: Literal["csv", "xlsx"] = Query("xlsx", alias="format"),
    _: AuthContext = Depends(require_auth),
):
    return _download(file_format, "organization-import-template", "Template", bulk.COLUMNS[:4], TEMPLATE_ROWS)


@router.post("/nodes/{node_id}/import/preview", response_model=ImportPreview)
def preview_import(
    node_id: uuid.UUID,
    file: UploadFile,
    _: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    node = _get_node(db, node_id)
    results, _planned = bulk.plan_import(db, node, _read_upload(file))
    return {"summary": bulk.summarize(results), "rows": results}


@router.post("/nodes/{node_id}/import", status_code=201)
def import_nodes(
    node_id: uuid.UUID,
    file: UploadFile,
    request: Request,
    ctx: AuthContext = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    node = _get_node(db, node_id)
    rows = _read_upload(file)
    try:
        summary = bulk.apply_import(db, ctx, node, file.filename or "", rows, _ip(request))
        db.commit()
    except bulk.ImportRejected as rejected:
        db.rollback()
        return JSONResponse(
            status_code=422,
            content={
                "detail": "The file has errors. Nothing was imported.",
                "rows": rejected.results,
            },
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="A code was taken while importing. Run the preview again."
        )
    return summary