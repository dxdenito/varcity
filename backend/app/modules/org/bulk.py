import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam.service import AuthContext
from app.modules.org.models import Node, NodeType, NodeTypeParent
from app.modules.org.schemas import CODE_PATTERN

COLUMNS = ["Level", "Name", "Code", "Parent", "Status"]
REQUIRED = ["Level", "Name"]
SEPARATOR = " > "
CODE_RE = re.compile(CODE_PATTERN)


class ImportRejected(Exception):
    def __init__(self, results: list[dict]):
        super().__init__("The file has errors.")
        self.results = results


@dataclass
class Planned:
    id: uuid.UUID
    type_id: uuid.UUID
    parent_id: uuid.UUID
    code: str | None
    name: str
    path: str


def _subtree(db: Session, node: Node) -> dict[uuid.UUID, list[Node]]:
    items = db.scalars(select(Node).where(Node.path.startswith(node.path, autoescape=True)))
    children: dict[uuid.UUID, list[Node]] = {}
    for item in items:
        if item.parent_id:
            children.setdefault(item.parent_id, []).append(item)
    for siblings in children.values():
        siblings.sort(key=lambda sibling: sibling.name.lower())
    return children


def export_rows(db: Session, node: Node) -> list[list[str]]:
    type_names = {item.id: item.name for item in db.scalars(select(NodeType))}
    children = _subtree(db, node)
    rows: list[list[str]] = []

    def walk(parent: Node, trail: list[str]) -> None:
        for child in children.get(parent.id, []):
            rows.append(
                [
                    type_names[child.type_id],
                    child.name,
                    child.code or "",
                    SEPARATOR.join(trail),
                    "Archived" if child.status == "archived" else "Active",
                ]
            )
            walk(child, trail + [child.name])

    walk(node, [])
    return rows


def plan_import(
    db: Session, node: Node, rows: list[tuple[int, dict[str, str]]]
) -> tuple[list[dict], list[Planned]]:
    types = list(db.scalars(select(NodeType)))
    type_names = {item.id: item.name for item in types}
    by_label: dict[str, NodeType] = {}
    for item in types:
        by_label[item.name.lower()] = item
        by_label.setdefault(item.plural_name.lower(), item)

    allowed: dict[uuid.UUID, set[uuid.UUID]] = {}
    for link in db.scalars(select(NodeTypeParent)):
        allowed.setdefault(link.type_id, set()).add(link.parent_type_id)

    taken_codes = {
        (row.type_id, row.code)
        for row in db.execute(select(Node.type_id, Node.code).where(Node.code.is_not(None)))
    }

    index: dict[tuple, list[dict]] = {
        (): [{"id": node.id, "type_id": node.type_id, "status": node.status, "path": node.path}]
    }
    children = _subtree(db, node)

    def walk(parent: Node, trail: tuple) -> None:
        for child in children.get(parent.id, []):
            key = trail + (child.name.lower(),)
            index.setdefault(key, []).append(
                {"id": child.id, "type_id": child.type_id, "status": child.status, "path": child.path}
            )
            walk(child, key)

    walk(node, ())

    results: list[dict] = []
    planned: list[Planned] = []

    for number, record in rows:
        level_text = record.get("level", "")
        name = record.get("name", "")
        raw_code = record.get("code", "")
        parent_text = record.get("parent", "")
        messages: list[str] = []

        node_type = by_label.get(level_text.lower())
        if node_type is None:
            known = ", ".join(sorted(type_names.values()))
            messages.append(f"Unknown level '{level_text}'. Use one of: {known}.")
        if not name:
            messages.append("Name is required.")
        elif len(name) > 200:
            messages.append("Name is longer than 200 characters.")

        code = None
        if raw_code:
            if not CODE_RE.match(raw_code):
                messages.append("Code must be letters and digits only (up to 20).")
            else:
                code = raw_code.upper()
                if node_type and (node_type.id, code) in taken_codes:
                    messages.append(f"The code {code} is already in use.")

        parts = [part.strip() for part in parent_text.split(">") if part.strip()]
        key = tuple(part.lower() for part in parts)
        candidates = index.get(key, [])
        parent = None
        if not candidates:
            messages.append(
                f"Parent '{parent_text}' was not found. List parents before the entries inside them."
            )
        elif len(candidates) > 1:
            messages.append(f"Parent '{parent_text}' matches more than one entry.")
        else:
            parent = candidates[0]

        if parent and parent["status"] != "active":
            messages.append("The parent is archived.")
        if parent and node_type and parent["type_id"] not in allowed.get(node_type.id, set()):
            messages.append(
                f"A {node_type.name} cannot be placed under a {type_names[parent['type_id']]}."
            )

        status = "error" if messages else "create"
        if not messages:
            sibling_key = key + (name.lower(),)
            if any(entry["type_id"] == node_type.id for entry in index.get(sibling_key, [])):
                status = "skip"
                messages.append("Already exists.")
            else:
                node_id = new_id()
                path = f"{parent['path']}{node_id}/"
                planned.append(
                    Planned(
                        id=node_id,
                        type_id=node_type.id,
                        parent_id=parent["id"],
                        code=code,
                        name=name,
                        path=path,
                    )
                )
                index.setdefault(sibling_key, []).append(
                    {"id": node_id, "type_id": node_type.id, "status": "active", "path": path}
                )
                if code:
                    taken_codes.add((node_type.id, code))

        results.append(
            {
                "row": number,
                "status": status,
                "level": level_text,
                "name": name,
                "code": raw_code,
                "parent": parent_text,
                "messages": messages,
            }
        )

    return results, planned


def summarize(results: list[dict]) -> dict[str, int]:
    return {
        label: sum(1 for result in results if result["status"] == label)
        for label in ("create", "skip", "error")
    }


def apply_import(
    db: Session,
    ctx: AuthContext,
    node: Node,
    filename: str,
    rows: list[tuple[int, dict[str, str]]],
    ip_address: str | None,
) -> dict[str, int]:
    results, planned = plan_import(db, node, rows)
    if any(result["status"] == "error" for result in results):
        raise ImportRejected(results)

    for item in planned:
        db.add(
            Node(
                id=item.id,
                type_id=item.type_id,
                parent_id=item.parent_id,
                code=item.code,
                name=item.name,
                path=item.path,
            )
        )
    db.flush()

    ip = clean_ip(ip_address)
    for item in planned:
        audit.record(
            db,
            action="org.node.create",
            module="org",
            actor_id=ctx.user.id,
            entity_type="node",
            entity_id=str(item.id),
            new_values={"code": item.code, "name": item.name},
            reason="import",
            ip_address=ip,
        )

    summary = summarize(results)
    audit.record(
        db,
        action="org.import",
        module="org",
        actor_id=ctx.user.id,
        entity_type="node",
        entity_id=str(node.id),
        new_values={"file": filename, **summary},
        ip_address=ip,
    )
    return summary