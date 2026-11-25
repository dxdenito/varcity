import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam.access import Access
from app.modules.iam.rbac_models import Permission, Role, RoleAssignment, RolePermission
from app.modules.iam.service import AuthContext
from contextlib import contextmanager
from contextvars import ContextVar


class RoleError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class RoleNotFound(RoleError):
    pass


class RoleConflict(RoleError):
    pass


class RoleInvalid(RoleError):
    pass


class RoleForbidden(RoleError):
    pass


class RoleReauth(RoleError):
    pass


_probe: ContextVar[list | None] = ContextVar("fresh_probe", default=None)


@contextmanager
def probing_fresh():
    """Record the password confirmation requirement instead of enforcing it (dry runs)."""
    calls: list[bool] = []
    token = _probe.set(calls)
    try:
        yield calls
    finally:
        _probe.reset(token)


def require_fresh(ctx: AuthContext) -> None:
    """The session must have confirmed the user's password recently."""
    probe = _probe.get()
    if probe is not None:
        probe.append(True)
        return
    until = ctx.session.elevated_until
    if until is None or until <= datetime.now(UTC):
        raise RoleReauth("Please confirm your password to continue.")


def list_permissions(db: Session) -> list[Permission]:
    return list(db.scalars(select(Permission).order_by(Permission.module, Permission.code)))


def _out(role: Role, codes: list[str], count: int) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "category": role.category,
        "is_system": role.system_key is not None,
        "is_active": role.is_active,
        "grants_all": role.grants_all,
        "permissions": codes,
        "assignment_count": count,
    }


def list_roles(db: Session) -> list[dict]:
    codes: dict[uuid.UUID, list[str]] = defaultdict(list)
    for role_id, code in db.execute(
        select(RolePermission.role_id, RolePermission.permission_code).order_by(
            RolePermission.permission_code
        )
    ):
        codes[role_id].append(code)
    counts = dict(
        db.execute(
            select(RoleAssignment.role_id, func.count()).group_by(RoleAssignment.role_id)
        ).all()
    )
    roles = db.scalars(select(Role).order_by(Role.name))
    return [_out(role, codes.get(role.id, []), counts.get(role.id, 0)) for role in roles]


def _load(db: Session, role_id: uuid.UUID) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise RoleNotFound("Role not found.")
    return role


def _codes_for(db: Session, role_id: uuid.UUID) -> list[str]:
    return list(
        db.scalars(
            select(RolePermission.permission_code)
            .where(RolePermission.role_id == role_id)
            .order_by(RolePermission.permission_code)
        )
    )


def _count_for(db: Session, role_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(RoleAssignment).where(RoleAssignment.role_id == role_id)
    )


def get_role(db: Session, role_id: uuid.UUID) -> dict:
    role = _load(db, role_id)
    return _out(role, _codes_for(db, role.id), _count_for(db, role.id))


def _clean(name: str, description: str | None, category: str | None) -> tuple[str, str | None, str | None]:
    name = name.strip()
    if not name:
        raise RoleInvalid("Enter a role name.")
    return name, (description or "").strip() or None, (category or "").strip() or None


def _ensure_unique_name(db: Session, name: str, exclude_id: uuid.UUID | None = None) -> None:
    query = select(Role.id).where(func.lower(Role.name) == name.lower())
    if exclude_id is not None:
        query = query.where(Role.id != exclude_id)
    if db.scalar(query) is not None:
        raise RoleConflict("A role with that name already exists.")


def _resolve_codes(db: Session, requested: list[str]) -> set[str]:
    """Validate the codes and add the matching view permission for each write."""
    known = set(db.scalars(select(Permission.code)))
    unknown = sorted(set(requested) - known)
    if unknown:
        raise RoleInvalid("Unknown permission: " + ", ".join(unknown))
    codes = set(requested)
    for code in list(codes):
        module, resource, action = code.split(".")
        view = f"{module}.{resource}.view"
        if action != "view" and view in known:
            codes.add(view)
    return codes


def _ensure_can_grant(access: Access, added: set[str]) -> None:
    missing = sorted(code for code in added if not access.can(code))
    if missing:
        raise RoleForbidden(
            "You can only grant permissions you hold yourself: " + ", ".join(missing)
        )


def create_role(
    db: Session,
    ctx: AuthContext,
    access: Access,
    *,
    name: str,
    description: str | None,
    category: str | None = None,
    is_active: bool = True,
    permissions: list[str],
    duplicated_from: str | None = None,
    ip_address: str | None,
) -> dict:
    name, description, category = _clean(name, description, category)
    _ensure_unique_name(db, name)
    codes = _resolve_codes(db, permissions)
    _ensure_can_grant(access, set(permissions))
    require_fresh(ctx)

    role = Role(name=name, description=description, category=category, is_active=is_active)
    db.add(role)
    db.flush()
    db.add_all(RolePermission(role_id=role.id, permission_code=c) for c in sorted(codes))
    db.flush()
    new_values = {
        "name": name,
        "description": description,
        "category": category,
        "is_active": is_active,
        "permissions": sorted(codes),
    }
    if duplicated_from:
        new_values["duplicated_from"] = duplicated_from
    audit.record(
        db,
        action="iam.role.created",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="role",
        entity_id=str(role.id),
        new_values=new_values,
        ip_address=clean_ip(ip_address),
    )
    return get_role(db, role.id)


def update_role(
    db: Session,
    ctx: AuthContext,
    access: Access,
    role_id: uuid.UUID,
    *,
    name: str,
    description: str | None,
    category: str | None = None,
    is_active: bool = True,
    permissions: list[str],
    ip_address: str | None,
) -> dict:
    role = _load(db, role_id)
    if role.grants_all:
        raise RoleForbidden("The Super Admin role cannot be changed.")
    name, description, category = _clean(name, description, category)
    _ensure_unique_name(db, name, role.id)

    old = set(_codes_for(db, role.id))
    new = _resolve_codes(db, permissions)
    _ensure_can_grant(access, set(permissions) - old)
    require_fresh(ctx)

    before = {
        "name": role.name,
        "description": role.description,
        "category": role.category,
        "is_active": role.is_active,
        "permissions": sorted(old),
    }
    removed, added = old - new, new - old
    if removed:
        db.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_code.in_(removed),
            )
        )
    db.add_all(RolePermission(role_id=role.id, permission_code=c) for c in sorted(added))
    role.name = name
    role.description = description
    role.category = category
    role.is_active = is_active
    role.updated_at = datetime.now(UTC)
    db.flush()
    audit.record(
        db,
        action="iam.role.updated",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="role",
        entity_id=str(role.id),
        old_values=before,
        new_values={
            "name": name,
            "description": description,
            "category": category,
            "is_active": is_active,
            "permissions": sorted(new),
        },
        ip_address=clean_ip(ip_address),
    )
    return get_role(db, role.id)


def duplicate_role(
    db: Session,
    ctx: AuthContext,
    access: Access,
    role_id: uuid.UUID,
    *,
    name: str,
    ip_address: str | None,
) -> dict:
    source = _load(db, role_id)
    if source.grants_all:
        raise RoleForbidden("The Super Admin role cannot be duplicated.")
    return create_role(
        db,
        ctx,
        access,
        name=name,
        description=source.description,
        category=source.category,
        permissions=_codes_for(db, source.id),
        duplicated_from=source.name,
        ip_address=ip_address,
    )


def delete_role(
    db: Session, ctx: AuthContext, role_id: uuid.UUID, ip_address: str | None
) -> None:
    role = _load(db, role_id)
    if role.system_key is not None:
        raise RoleForbidden("Starter roles cannot be deleted.")
    count = _count_for(db, role.id)
    if count:
        raise RoleConflict(
            f"This role is assigned to {count} user(s). Remove those assignments first."
        )
    require_fresh(ctx)
    before = {
        "name": role.name,
        "description": role.description,
        "permissions": _codes_for(db, role.id),
    }
    db.delete(role)
    db.flush()
    audit.record(
        db,
        action="iam.role.deleted",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="role",
        entity_id=str(role_id),
        old_values=before,
        ip_address=clean_ip(ip_address),
    )