import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam import permissions as perm
from app.modules.iam.access import Access
from app.modules.iam.models import UserAccount
from app.modules.iam.rbac_models import Role, RoleAssignment, RolePermission
from app.modules.iam.role_service import (
    RoleConflict,
    RoleForbidden,
    RoleInvalid,
    RoleNotFound,
)
from app.modules.iam.service import AuthContext
from app.modules.org.models import Node


def window_state(valid_from, valid_until, now: datetime) -> str:
    if valid_until is not None and valid_until <= now:
        return "expired"
    if valid_from is not None and valid_from > now:
        return "scheduled"
    return "active"


def check_window(valid_from, valid_until, now: datetime) -> None:
    if valid_until is not None and valid_until <= now:
        raise RoleInvalid("The end date must be in the future.")
    if valid_from is not None and valid_until is not None and valid_until <= valid_from:
        raise RoleInvalid("The end date must be after the start date.")


def clean_reason(reason: str | None) -> str | None:
    return (reason or "").strip() or None


def assignments_for(db: Session, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[dict]]:
    now = datetime.now(UTC)
    rows = db.execute(
        select(
            RoleAssignment.id,
            RoleAssignment.user_id,
            RoleAssignment.role_id,
            Role.name.label("role_name"),
            RoleAssignment.node_id,
            Node.name.label("node_name"),
            RoleAssignment.valid_from,
            RoleAssignment.valid_until,
            RoleAssignment.reason,
        )
        .join(Role, Role.id == RoleAssignment.role_id)
        .outerjoin(Node, Node.id == RoleAssignment.node_id)
        .where(RoleAssignment.user_id.in_(user_ids))
        .order_by(Role.name, Node.name)
    ).all()
    result: dict[uuid.UUID, list[dict]] = defaultdict(list)
    for row in rows:
        result[row.user_id].append(
            {
                "id": row.id,
                "role_id": row.role_id,
                "role_name": row.role_name,
                "node_id": row.node_id,
                "node_name": row.node_name,
                "valid_from": row.valid_from,
                "valid_until": row.valid_until,
                "reason": row.reason,
                "state": window_state(row.valid_from, row.valid_until, now),
            }
        )
    return result


def _user_out(user: UserAccount, assignments: list[dict]) -> dict:
    now = datetime.now(UTC)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "status": user.status,
        "is_superuser": user.is_superuser,
        "is_locked": user.locked_until is not None and user.locked_until > now,
        "last_login_at": user.last_login_at,
        "assignments": assignments,
    }


def list_users(db: Session, *, q: str | None, limit: int, offset: int) -> dict:
    query = select(UserAccount)
    if q and q.strip():
        term = q.strip()
        query = query.where(
            or_(
                UserAccount.email.icontains(term, autoescape=True),
                UserAccount.full_name.icontains(term, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    users = list(
        db.scalars(query.order_by(UserAccount.email).limit(limit).offset(offset))
    )
    assignments = assignments_for(db, [user.id for user in users])
    return {
        "items": [_user_out(user, assignments.get(user.id, [])) for user in users],
        "total": total,
    }


def get_user(db: Session, user_id: uuid.UUID) -> dict:
    user = db.get(UserAccount, user_id)
    if user is None:
        raise RoleNotFound("User not found.")
    return _user_out(user, assignments_for(db, [user.id]).get(user.id, []))


def may_assign_at(access: Access, node: Node | None) -> bool:
    if node is None:
        return access.can(perm.ASSIGN_ROLE)
    return access.can(perm.ASSIGN_ROLE, node.path)


def assign_role(
    db: Session,
    ctx: AuthContext,
    access: Access,
    user_id: uuid.UUID,
    *,
    role_id: uuid.UUID,
    node_id: uuid.UUID | None,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    reason: str | None = None,
    ip_address: str | None,
) -> dict:
    now = datetime.now(UTC)
    user = db.get(UserAccount, user_id)
    if user is None:
        raise RoleNotFound("User not found.")
    role = db.get(Role, role_id)
    if role is None:
        raise RoleInvalid("Role not found.")
    node = None
    if node_id is not None:
        node = db.get(Node, node_id)
        if node is None:
            raise RoleInvalid("Organization entry not found.")

    if not may_assign_at(access, node):
        raise RoleForbidden("You cannot assign roles here.")
    if role.grants_all:
        if not access.holds_everything():
            raise RoleForbidden("Only a super admin can assign the Super Admin role.")
    else:
        codes = db.scalars(
            select(RolePermission.permission_code).where(RolePermission.role_id == role.id)
        )
        path = node.path if node else None
        missing = sorted(code for code in codes if not access.can(code, path))
        if missing:
            raise RoleForbidden(
                "You can only assign roles whose permissions you hold here: "
                + ", ".join(missing)
            )

    reason = clean_reason(reason)
    check_window(valid_from, valid_until, now)

    same_scope = (
        RoleAssignment.node_id.is_(None)
        if node_id is None
        else RoleAssignment.node_id == node_id
    )
    existing = db.scalar(
        select(RoleAssignment).where(
            RoleAssignment.user_id == user.id,
            RoleAssignment.role_id == role.id,
            same_scope,
        )
    )
    if existing is None:
        db.add(
            RoleAssignment(
                user_id=user.id,
                role_id=role.id,
                node_id=node_id,
                valid_from=valid_from,
                valid_until=valid_until,
                reason=reason,
                granted_by_id=ctx.user.id,
            )
        )
        action = "iam.role.assigned"
    else:
        if window_state(existing.valid_from, existing.valid_until, now) != "expired":
            raise RoleConflict("The user already has this role here.")
        existing.valid_from = valid_from
        existing.valid_until = valid_until
        existing.reason = reason
        existing.granted_by_id = ctx.user.id
        action = "iam.role.renewed"
    db.flush()
    audit.record(
        db,
        action=action,
        module="iam",
        actor_id=ctx.user.id,
        entity_type="user_account",
        entity_id=str(user.id),
        new_values={
            "role_id": str(role.id),
            "role": role.name,
            "node_id": str(node_id) if node_id else None,
            "node": node.name if node else None,
            "valid_from": valid_from.isoformat() if valid_from else None,
            "valid_until": valid_until.isoformat() if valid_until else None,
        },
        reason=reason,
        ip_address=clean_ip(ip_address),
    )
    return get_user(db, user.id)


def unassign_role(
    db: Session,
    ctx: AuthContext,
    access: Access,
    user_id: uuid.UUID,
    assignment_id: uuid.UUID,
    ip_address: str | None,
) -> dict:
    row = db.get(RoleAssignment, assignment_id)
    if row is None or row.user_id != user_id:
        raise RoleNotFound("Assignment not found.")
    node = db.get(Node, row.node_id) if row.node_id else None
    if not may_assign_at(access, node):
        raise RoleForbidden("You cannot remove roles here.")
    role = db.get(Role, row.role_id)
    if role.grants_all and not access.holds_everything():
        raise RoleForbidden("Only a super admin can remove the Super Admin role.")

    old = {
        "role_id": str(role.id),
        "role": role.name,
        "node_id": str(row.node_id) if row.node_id else None,
        "node": node.name if node else None,
    }
    db.delete(row)
    db.flush()
    audit.record(
        db,
        action="iam.role.unassigned",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="user_account",
        entity_id=str(user_id),
        old_values=old,
        ip_address=clean_ip(ip_address),
    )
    return get_user(db, user_id)