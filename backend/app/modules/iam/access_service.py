import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam.access import Access
from app.modules.iam.models import UserAccount
from app.modules.iam.rbac_models import (
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
    UserPermission,
)
from app.modules.iam.role_service import RoleConflict, RoleForbidden, RoleInvalid, RoleNotFound
from app.modules.iam.service import AuthContext
from app.modules.iam.user_service import (
    assignments_for,
    check_window,
    clean_reason,
    may_assign_at,
    window_state,
)
from app.modules.org.models import Node


def _load_user(db: Session, user_id: uuid.UUID) -> UserAccount:
    user = db.get(UserAccount, user_id)
    if user is None:
        raise RoleNotFound("User not found.")
    return user


def _grants_for(db: Session, user_id: uuid.UUID, now: datetime) -> list[dict]:
    rows = db.execute(
        select(
            UserPermission.id,
            UserPermission.permission_code,
            UserPermission.node_id,
            Node.name.label("node_name"),
            UserPermission.valid_from,
            UserPermission.valid_until,
            UserPermission.reason,
        )
        .outerjoin(Node, Node.id == UserPermission.node_id)
        .where(UserPermission.user_id == user_id)
        .order_by(UserPermission.permission_code, Node.name)
    ).all()
    return [
        {
            "id": row.id,
            "permission": row.permission_code,
            "node_id": row.node_id,
            "node_name": row.node_name,
            "valid_from": row.valid_from,
            "valid_until": row.valid_until,
            "reason": row.reason,
            "state": window_state(row.valid_from, row.valid_until, now),
        }
        for row in rows
    ]


def get_access_detail(db: Session, user_id: uuid.UUID) -> dict:
    user = _load_user(db, user_id)
    now = datetime.now(UTC)
    access = Access.load(db, user, now)
    return {
        "assignments": assignments_for(db, [user.id]).get(user.id, []),
        "grants": _grants_for(db, user.id, now),
        "permissions": {
            code: [
                {
                    "kind": grant.source,
                    "label": grant.label,
                    "node_id": grant.node_id,
                    "node_name": grant.node_name,
                }
                for grant in grants
            ]
            for code, grants in sorted(access.permission_sources().items())
        },
    }


def grant_permission(
    db: Session,
    ctx: AuthContext,
    access: Access,
    user_id: uuid.UUID,
    *,
    code: str,
    node_id: uuid.UUID | None,
    valid_from: datetime | None,
    valid_until: datetime | None,
    reason: str | None,
    ip_address: str | None,
) -> dict:
    user = _load_user(db, user_id)
    permission = db.get(Permission, code)
    if permission is None:
        raise RoleInvalid("Unknown permission.")
    node = None
    if node_id is not None:
        node = db.get(Node, node_id)
        if node is None:
            raise RoleInvalid("Organization entry not found.")

    if not may_assign_at(access, node):
        raise RoleForbidden("You cannot assign permissions here.")
    if not access.can(code, node.path if node else None):
        raise RoleForbidden(f"You can only grant permissions you hold here: {code}")

    reason = clean_reason(reason)
    if permission.risk != "normal" and not reason:
        raise RoleInvalid("Give a reason when granting a sensitive or critical permission.")
    check_window(valid_from, valid_until, datetime.now(UTC))

    same_scope = (
        UserPermission.node_id.is_(None)
        if node_id is None
        else UserPermission.node_id == node_id
    )
    exists = db.scalar(
        select(UserPermission.id).where(
            UserPermission.user_id == user.id,
            UserPermission.permission_code == code,
            same_scope,
        )
    )
    if exists is not None:
        raise RoleConflict("The user already has this permission here.")

    db.add(
        UserPermission(
            user_id=user.id,
            permission_code=code,
            node_id=node_id,
            valid_from=valid_from,
            valid_until=valid_until,
            reason=reason,
            granted_by_id=ctx.user.id,
        )
    )
    db.flush()
    audit.record(
        db,
        action="iam.permission.granted",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="user_account",
        entity_id=str(user.id),
        new_values={
            "permission": code,
            "risk": permission.risk,
            "node_id": str(node_id) if node_id else None,
            "node": node.name if node else None,
            "valid_from": valid_from.isoformat() if valid_from else None,
            "valid_until": valid_until.isoformat() if valid_until else None,
        },
        reason=reason,
        ip_address=clean_ip(ip_address),
    )
    return get_access_detail(db, user.id)


def revoke_permission(
    db: Session,
    ctx: AuthContext,
    access: Access,
    user_id: uuid.UUID,
    grant_id: uuid.UUID,
    ip_address: str | None,
) -> dict:
    row = db.get(UserPermission, grant_id)
    if row is None or row.user_id != user_id:
        raise RoleNotFound("Permission grant not found.")
    node = db.get(Node, row.node_id) if row.node_id else None
    if not may_assign_at(access, node):
        raise RoleForbidden("You cannot remove permissions here.")

    old = {
        "permission": row.permission_code,
        "node_id": str(row.node_id) if row.node_id else None,
        "node": node.name if node else None,
    }
    db.delete(row)
    db.flush()
    audit.record(
        db,
        action="iam.permission.revoked",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="user_account",
        entity_id=str(user_id),
        old_values=old,
        ip_address=clean_ip(ip_address),
    )
    return get_access_detail(db, user_id)


def _source(grant) -> dict:
    return {
        "kind": grant.source,
        "label": grant.label,
        "scope": grant.node_name or "Whole university",
        "state": "active",
        "valid_until": grant.valid_until,
    }


def _inactive_sources(db: Session, user_id: uuid.UUID, code: str, now: datetime) -> list[dict]:
    result = []
    roles = db.execute(
        select(
            RoleAssignment.role_id,
            RoleAssignment.valid_from,
            RoleAssignment.valid_until,
            Role.name,
            Role.grants_all,
            Node.name.label("node_name"),
        )
        .join(Role, Role.id == RoleAssignment.role_id)
        .outerjoin(Node, Node.id == RoleAssignment.node_id)
        .where(
            RoleAssignment.user_id == user_id,
            or_(RoleAssignment.valid_until <= now, RoleAssignment.valid_from > now),
        )
    ).all()
    for row in roles:
        holds = row.grants_all or (
            db.scalar(
                select(RolePermission.role_id).where(
                    RolePermission.role_id == row.role_id,
                    RolePermission.permission_code == code,
                )
            )
            is not None
        )
        if holds:
            result.append(
                {
                    "kind": "role",
                    "label": row.name,
                    "scope": row.node_name or "Whole university",
                    "state": window_state(row.valid_from, row.valid_until, now),
                    "valid_until": row.valid_until,
                }
            )

    direct = db.execute(
        select(
            UserPermission.valid_from,
            UserPermission.valid_until,
            Node.name.label("node_name"),
        )
        .outerjoin(Node, Node.id == UserPermission.node_id)
        .where(
            UserPermission.user_id == user_id,
            UserPermission.permission_code == code,
            or_(UserPermission.valid_until <= now, UserPermission.valid_from > now),
        )
    ).all()
    for row in direct:
        result.append(
            {
                "kind": "individual",
                "label": "Added for this user",
                "scope": row.node_name or "Whole university",
                "state": window_state(row.valid_from, row.valid_until, now),
                "valid_until": row.valid_until,
            }
        )
    return result


def explain(
    db: Session, user_id: uuid.UUID, code: str, node_id: uuid.UUID | None
) -> dict:
    user = _load_user(db, user_id)
    if db.get(Permission, code) is None:
        raise RoleInvalid("Unknown permission.")
    node = None
    if node_id is not None:
        node = db.get(Node, node_id)
        if node is None:
            raise RoleInvalid("Organization entry not found.")

    now = datetime.now(UTC)
    path = node.path if node else None
    access = Access.load(db, user, now)
    allowed = access.can(code, path)
    result = {
        "permission": code,
        "scope": node.name if node else "Whole university",
        "allowed": allowed,
        "granted_by": [_source(g) for g in access.covering(code, path)] if allowed else [],
        "held_elsewhere": [],
        "inactive": [],
    }
    if not allowed:
        result["held_elsewhere"] = [_source(g) for g in access.elsewhere(code, path)]
        result["inactive"] = _inactive_sources(db, user.id, code, now)
    return result