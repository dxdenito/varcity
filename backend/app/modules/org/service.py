import uuid

from sqlalchemy import func, select, update

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam.service import AuthContext
from app.modules.org.models import Node, NodeType, NodeTypeParent
from app.modules.settings.service import get_branding

LEVEL_NAMES = {"college": ("College", "Colleges"), "faculty": ("Faculty", "Faculties")}


class OrgError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFound(OrgError):
    pass


class Conflict(OrgError):
    pass


def initialize_structure(
    db: Session, ctx: AuthContext, template: str, institution_code: str, ip_address: str | None
) -> None:
    if db.scalar(select(NodeType.id).limit(1)) is not None:
        raise Conflict("The organization structure has already been set up.")

    name, plural = LEVEL_NAMES[template]
    definitions = [
        ("university", "University", "Universities", False, []),
        ("campus", "Campus", "Campuses", True, ["university"]),
        (template, name, plural, False, ["campus", "university"]),
        ("school", "School", "Schools", False, [template]),
        ("department", "Department", "Departments", False, ["school", template]),
    ]

    types: dict[str, NodeType] = {}
    for order, (code, type_name, type_plural, is_campus, _) in enumerate(definitions):
        types[code] = NodeType(
            code=code, name=type_name, plural_name=type_plural, is_campus=is_campus, sort_order=order
        )
        db.add(types[code])
    db.flush()

    for code, _, _, _, parents in definitions:
        for parent_code in parents:
            db.add(NodeTypeParent(type_id=types[code].id, parent_type_id=types[parent_code].id))

    root_id = new_id()
    root = Node(
        id=root_id,
        type_id=types["university"].id,
        code=institution_code.upper(),
        name=get_branding(db).university_name,
        path=f"/{root_id}/",
    )
    db.add(root)
    db.flush()
    audit.record(
        db,
        action="org.initialize",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(root.id),
        new_values={"template": template, "institution_code": root.code},
        ip_address=clean_ip(ip_address),
    )


def list_node_types(db: Session) -> list[dict]:
    parents: dict[uuid.UUID, list[uuid.UUID]] = {}
    for link in db.scalars(select(NodeTypeParent)):
        parents.setdefault(link.type_id, []).append(link.parent_type_id)

    return [
        {
            "id": node_type.id,
            "code": node_type.code,
            "name": node_type.name,
            "plural_name": node_type.plural_name,
            "is_campus": node_type.is_campus,
            "allowed_parent_type_ids": parents.get(node_type.id, []),
        }
        for node_type in db.scalars(select(NodeType).order_by(NodeType.sort_order))
    ]


def list_nodes(db: Session) -> list[Node]:
    return list(db.scalars(select(Node).order_by(Node.path)))


def _code_taken(db: Session, type_id: uuid.UUID, code: str, except_id: uuid.UUID | None = None) -> bool:
    query = select(Node.id).where(Node.type_id == type_id, Node.code == code)
    if except_id is not None:
        query = query.where(Node.id != except_id)
    return db.scalar(query) is not None


def create_node(
    db: Session,
    ctx: AuthContext,
    *,
    type_id: uuid.UUID,
    parent_id: uuid.UUID | None,
    code: str,
    name: str,
    ip_address: str | None,
) -> Node:
    node_type = db.get(NodeType, type_id)
    if node_type is None:
        raise NotFound("Level type not found.")
    allowed = set(db.scalars(select(NodeTypeParent.parent_type_id).where(NodeTypeParent.type_id == type_id)))

    node_id = new_id()
    if parent_id is None:
        if allowed:
            raise OrgError(f"A {node_type.name} must be placed under another level.")
        if db.scalar(select(Node.id).where(Node.parent_id.is_(None)).limit(1)) is not None:
            raise OrgError("The institution already has a top-level entry.")
        path = f"/{node_id}/"
    else:
        parent = db.get(Node, parent_id)
        if parent is None:
            raise NotFound("Parent not found.")
        if parent.status != "active":
            raise OrgError("The parent is archived.")
        if parent.type_id not in allowed:
            parent_type = db.get(NodeType, parent.type_id)
            raise OrgError(f"A {node_type.name} cannot be placed under a {parent_type.name}.")
        path = f"{parent.path}{node_id}/"

    code = code.upper()
    if _code_taken(db, type_id, code):
        raise Conflict(f"A {node_type.name} with the code {code} already exists.")

    node = Node(id=node_id, type_id=type_id, parent_id=parent_id, code=code, name=name, path=path)
    db.add(node)
    db.flush()
    audit.record(
        db,
        action="org.node.create",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        new_values={"type": node_type.code, "code": code, "name": name, "parent_id": str(parent_id) if parent_id else None},
        ip_address=clean_ip(ip_address),
    )
    return node


def update_node(
    db: Session,
    ctx: AuthContext,
    node_id: uuid.UUID,
    *,
    code: str | None,
    name: str | None,
    ip_address: str | None,
) -> Node:
    node = db.get(Node, node_id)
    if node is None:
        raise NotFound("Entry not found.")

    old = {"code": node.code, "name": node.name}
    if code is not None and code.upper() != node.code:
        if node.code_locked:
            raise Conflict("The code cannot be changed because it has already been used.")
        if _code_taken(db, node.type_id, code.upper(), except_id=node.id):
            raise Conflict(f"The code {code.upper()} is already in use at this level.")
        node.code = code.upper()
    if name is not None:
        node.name = name

    audit.record(
        db,
        action="org.node.update",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        old_values=old,
        new_values={"code": node.code, "name": node.name},
        ip_address=clean_ip(ip_address),
    )
    return node


def delete_node(db: Session, ctx: AuthContext, node_id: uuid.UUID, ip_address: str | None) -> None:
    node = db.get(Node, node_id)
    if node is None:
        raise NotFound("Entry not found.")

    blockers = []
    children = db.scalar(select(func.count()).select_from(Node).where(Node.parent_id == node.id))
    if children:
        blockers.append(f"it still contains {children} entr{'y' if children == 1 else 'ies'}")
    if node.parent_id is None:
        blockers.append("the institution's top-level entry cannot be deleted")
    if node.code_locked:
        blockers.append("its code has already been used (archive it instead)")
    if blockers:
        raise Conflict("Cannot delete: " + "; ".join(blockers) + ".")

    audit.record(
        db,
        action="org.node.delete",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        old_values={"code": node.code, "name": node.name},
        ip_address=clean_ip(ip_address),
    )
    db.delete(node)

def move_node(
    db: Session,
    ctx: AuthContext,
    node_id: uuid.UUID,
    new_parent_id: uuid.UUID,
    ip_address: str | None,
) -> Node:
    node = db.get(Node, node_id)
    new_parent = db.get(Node, new_parent_id)
    if node is None or new_parent is None:
        raise NotFound("Entry not found.")
    if node.parent_id is None:
        raise OrgError("The institution's top-level entry cannot be moved.")
    if node.parent_id == new_parent.id:
        raise OrgError("It is already under that parent.")
    if new_parent.path.startswith(node.path):
        raise OrgError("An entry cannot be moved inside itself.")
    if new_parent.status != "active":
        raise OrgError("The new parent is archived.")

    allowed = set(
        db.scalars(select(NodeTypeParent.parent_type_id).where(NodeTypeParent.type_id == node.type_id))
    )
    if new_parent.type_id not in allowed:
        node_type = db.get(NodeType, node.type_id)
        parent_type = db.get(NodeType, new_parent.type_id)
        raise OrgError(f"A {node_type.name} cannot be placed under a {parent_type.name}.")

    old_parent_id = node.parent_id
    old_prefix = node.path
    new_prefix = f"{new_parent.path}{node.id}/"
    db.execute(
        update(Node)
        .where(Node.path.startswith(old_prefix, autoescape=True))
        .values(path=func.concat(new_prefix, func.substr(Node.path, len(old_prefix) + 1)))
        .execution_options(synchronize_session=False)
    )
    node.parent_id = new_parent.id
    db.flush()
    db.refresh(node)

    audit.record(
        db,
        action="org.node.move",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        old_values={"parent_id": str(old_parent_id)},
        new_values={"parent_id": str(new_parent.id)},
        ip_address=clean_ip(ip_address),
    )
    return node


def archive_node(db: Session, ctx: AuthContext, node_id: uuid.UUID, ip_address: str | None) -> Node:
    node = db.get(Node, node_id)
    if node is None:
        raise NotFound("Entry not found.")
    if node.parent_id is None:
        raise OrgError("The institution's top-level entry cannot be archived.")

    active_children = db.scalar(
        select(func.count())
        .select_from(Node)
        .where(Node.parent_id == node.id, Node.status == "active")
    )
    if active_children:
        raise Conflict(
            f"Cannot archive: it still contains {active_children} active "
            f"entr{'y' if active_children == 1 else 'ies'}. Move or archive them first."
        )

    node.status = "archived"
    audit.record(
        db,
        action="org.node.archive",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        ip_address=clean_ip(ip_address),
    )
    return node


def unarchive_node(db: Session, ctx: AuthContext, node_id: uuid.UUID, ip_address: str | None) -> Node:
    node = db.get(Node, node_id)
    if node is None:
        raise NotFound("Entry not found.")

    parent = db.get(Node, node.parent_id) if node.parent_id else None
    if parent is not None and parent.status != "active":
        raise Conflict("Cannot restore: its parent is archived. Restore the parent first.")

    node.status = "active"
    audit.record(
        db,
        action="org.node.unarchive",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        ip_address=clean_ip(ip_address),
    )
    return node