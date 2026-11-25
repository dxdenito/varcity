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
from app.modules.iam.role_service import (
    RoleConflict,
    RoleForbidden,
    RoleInvalid,
    RoleNotFound,
    probing_fresh,
    require_fresh,
)
from app.modules.iam.service import AuthContext
from app.modules.iam.user_service import (
    assign_role,
    assignments_for,
    check_window,
    clean_reason,
    may_assign_at,
    unassign_role,
    update_assignment,
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

    require_fresh(ctx)

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




def _risky_codes(db: Session, role_id: uuid.UUID) -> dict[str, str]:
    rows = db.execute(
        select(Permission.code, Permission.risk)
        .join(RolePermission, RolePermission.permission_code == Permission.code)
        .where(RolePermission.role_id == role_id, Permission.risk != "normal")
    ).all()
    return {code: risk for code, risk in rows}


def _is_fresh(ctx: AuthContext) -> bool:
    until = ctx.session.elevated_until
    return until is not None and until > datetime.now(UTC)


def _describe_assignment(db: Session, assignment_id: uuid.UUID, user_id: uuid.UUID):
    return db.execute(
        select(Role.name, Node.name.label("node_name"))
        .select_from(RoleAssignment)
        .join(Role, Role.id == RoleAssignment.role_id)
        .outerjoin(Node, Node.id == RoleAssignment.node_id)
        .where(RoleAssignment.id == assignment_id, RoleAssignment.user_id == user_id)
    ).first()


def _describe_grant(db: Session, grant_id: uuid.UUID, user_id: uuid.UUID):
    return db.execute(
        select(Permission.description, Node.name.label("node_name"))
        .select_from(UserPermission)
        .join(Permission, Permission.code == UserPermission.permission_code)
        .outerjoin(Node, Node.id == UserPermission.node_id)
        .where(UserPermission.id == grant_id, UserPermission.user_id == user_id)
    ).first()


def _run_changes(db, ctx, access, user_id, changes, ip_address):
    _load_user(db, user_id)
    items: list[dict] = []
    sensitive: set[str] = set()
    critical: set[str] = set()

    for assignment_id in changes.remove_assignments:
        row = _describe_assignment(db, assignment_id, user_id)
        unassign_role(db, ctx, access, user_id, assignment_id, ip_address)
        items.append(
            {
                "kind": "assignment",
                "action": "remove",
                "label": row.name,
                "scope": row.node_name or "Whole university",
            }
        )

    for grant_id in changes.remove_grants:
        row = _describe_grant(db, grant_id, user_id)
        revoke_permission(db, ctx, access, user_id, grant_id, ip_address)
        items.append(
            {
                "kind": "grant",
                "action": "remove",
                "label": row.description,
                "scope": row.node_name or "Whole university",
            }
        )

    for change in changes.update_assignments:
        row = _describe_assignment(db, change.id, user_id)
        update_assignment(
            db,
            ctx,
            access,
            user_id,
            change.id,
            valid_from=change.valid_from,
            valid_until=change.valid_until,
            reason=change.reason,
            ip_address=ip_address,
        )
        items.append(
            {
                "kind": "assignment",
                "action": "update",
                "label": row.name,
                "scope": row.node_name or "Whole university",
            }
        )

    for add in changes.add_assignments:
        assign_role(
            db,
            ctx,
            access,
            user_id,
            role_id=add.role_id,
            node_id=add.node_id,
            valid_from=add.valid_from,
            valid_until=add.valid_until,
            reason=add.reason,
            ip_address=ip_address,
        )
        role = db.get(Role, add.role_id)
        node = db.get(Node, add.node_id) if add.node_id else None
        items.append(
            {
                "kind": "assignment",
                "action": "add",
                "label": role.name,
                "scope": node.name if node else "Whole university",
            }
        )
        if role.grants_all:
            critical.add("All permissions (Super Admin)")
        else:
            for code, risk in _risky_codes(db, role.id).items():
                (critical if risk == "critical" else sensitive).add(code)

    for add in changes.add_grants:
        grant_permission(
            db,
            ctx,
            access,
            user_id,
            code=add.permission,
            node_id=add.node_id,
            valid_from=add.valid_from,
            valid_until=add.valid_until,
            reason=add.reason,
            ip_address=ip_address,
        )
        permission = db.get(Permission, add.permission)
        node = db.get(Node, add.node_id) if add.node_id else None
        items.append(
            {
                "kind": "grant",
                "action": "add",
                "label": permission.description,
                "scope": node.name if node else "Whole university",
            }
        )
        if permission.risk == "critical":
            critical.add(permission.code)
        elif permission.risk == "sensitive":
            sensitive.add(permission.code)

    return items, sensitive, critical


def apply_changes(db, ctx, access, user_id, changes, ip_address) -> dict:
    _run_changes(db, ctx, access, user_id, changes, ip_address)
    return get_access_detail(db, user_id)


def review_changes(db, ctx, access, user_id, changes, ip_address) -> dict:
    """Check the changes exactly as apply would, then roll everything back."""
    with probing_fresh() as probe:
        items, sensitive, critical = _run_changes(db, ctx, access, user_id, changes, ip_address)
    needs_confirmation = bool(probe) and not _is_fresh(ctx)
    db.rollback()
    return {
        "items": items,
        "sensitive": sorted(sensitive),
        "critical": sorted(critical),
        "requires_confirmation": needs_confirmation,
    }