import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.modules.iam import registry
from app.modules.iam.rbac_models import (
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
    UserPermission,
)
from app.modules.org.models import Node


def _ensure_starter_roles(db: Session) -> tuple[dict[str, Role], set[str]]:
    existing = {
        role.system_key: role
        for role in db.scalars(select(Role).where(Role.system_key.is_not(None)))
    }
    custom_by_name = {
        role.name.lower(): role
        for role in db.scalars(select(Role).where(Role.system_key.is_(None)))
    }
    created: set[str] = set()
    for key, (name, description, category) in registry.STARTER_ROLES.items():
        role = existing.get(key)
        if role is None:
            role = custom_by_name.get(name.lower())
            if role is not None:
                role.system_key = key
            else:
                role = Role(
                    system_key=key,
                    name=name,
                    description=description,
                    category=category,
                    grants_all=(key == "super_admin"),
                )
                db.add(role)
                created.add(key)
            existing[key] = role
        if role.category is None:
            role.category = category
    db.flush()
    return existing, created


def sync_registry(db: Session) -> None:
    """Make the database match the permissions and starter user types declared in code.

    A new permission, or a new starter user type, receives its default grants once.
    Later changes made by admins are never overwritten.
    """
    roles, new_roles = _ensure_starter_roles(db)
    stored = {p.code: p for p in db.scalars(select(Permission))}
    created: set[str] = set()
    for declared in registry.all_permissions():
        row = stored.get(declared.code)
        if row is None:
            db.add(
                Permission(
                    code=declared.code,
                    module=declared.module,
                    description=declared.description,
                    risk=declared.risk,
                )
            )
            created.add(declared.code)
        else:
            row.description = declared.description
            row.risk = declared.risk
    db.flush()
    for declared in registry.all_permissions():
        for key in declared.roles:
            if declared.code in created or key in new_roles:
                db.add(
                    RolePermission(
                        role_id=roles[key].id, permission_code=declared.code
                    )
                )
    db.flush()


@dataclass(frozen=True)
class Grant:
    permissions: frozenset[str]
    grants_all: bool
    path: str | None
    node_id: uuid.UUID | None = None
    source: str = "role"
    label: str = ""
    node_name: str | None = None
    valid_until: datetime | None = None

    def allows(self, code: str) -> bool:
        return self.grants_all or code in self.permissions

    def covers(self, node_path: str | None) -> bool:
        return self.path is None or (
            node_path is not None and node_path.startswith(self.path)
        )


SUPERUSER_GRANT = Grant(
    frozenset(), True, None, source="superuser", label="System administrator"
)


@dataclass(frozen=True)
class Scope:
    everywhere: bool
    paths: tuple[str, ...]


def _active(table, now: datetime):
    return and_(
        or_(table.valid_from.is_(None), table.valid_from <= now),
        or_(table.valid_until.is_(None), table.valid_until > now),
    )


class Access:
    """What one user may do. Load once per request, then ask it questions."""

    def __init__(self, db: Session, is_superuser: bool, grants: list[Grant]):
        self._db = db
        self._is_superuser = is_superuser
        self._grants = grants

    @classmethod
    def load(cls, db: Session, user, now: datetime | None = None) -> "Access":
        now = now or datetime.now(UTC)
        rows = db.execute(
            select(
                RoleAssignment.role_id,
                RoleAssignment.node_id,
                RoleAssignment.valid_until,
                Role.name,
                Role.grants_all,
                Node.name.label("node_name"),
                Node.path,
            )
            .join(Role, Role.id == RoleAssignment.role_id)
            .outerjoin(Node, Node.id == RoleAssignment.node_id)
            .where(RoleAssignment.user_id == user.id, _active(RoleAssignment, now))
        ).all()
        role_ids = {row.role_id for row in rows}
        permissions: dict[uuid.UUID, set[str]] = defaultdict(set)
        if role_ids:
            for role_id, code in db.execute(
                select(RolePermission.role_id, RolePermission.permission_code).where(
                    RolePermission.role_id.in_(role_ids)
                )
            ):
                permissions[role_id].add(code)
        grants = [
            Grant(
                frozenset(permissions[row.role_id]),
                row.grants_all,
                row.path,
                row.node_id,
                source="role",
                label=row.name,
                node_name=row.node_name,
                valid_until=row.valid_until,
            )
            for row in rows
        ]

        direct = db.execute(
            select(
                UserPermission.permission_code,
                UserPermission.node_id,
                UserPermission.valid_until,
                Node.name.label("node_name"),
                Node.path,
            )
            .outerjoin(Node, Node.id == UserPermission.node_id)
            .where(UserPermission.user_id == user.id, _active(UserPermission, now))
        ).all()
        grants += [
            Grant(
                frozenset({row.permission_code}),
                False,
                row.path,
                row.node_id,
                source="individual",
                label="Added for this user",
                node_name=row.node_name,
                valid_until=row.valid_until,
            )
            for row in direct
        ]
        return cls(db, user.is_superuser, grants)

    def can(self, code: str, node_path: str | None = None) -> bool:
        """With no node_path, only a university-wide grant counts."""
        if self._is_superuser:
            return True
        return any(
            grant.allows(code) and grant.covers(node_path) for grant in self._grants
        )

    def can_on_node(self, code: str, node_id: uuid.UUID) -> bool:
        node = self._db.get(Node, node_id)
        return node is not None and self.can(code, node.path)

    def can_anywhere(self, code: str) -> bool:
        return self._is_superuser or any(g.allows(code) for g in self._grants)

    def holds_everything(self) -> bool:
        return self._is_superuser or any(
            g.grants_all and g.node_id is None for g in self._grants
        )

    def scope(self, code: str) -> Scope:
        if self._is_superuser:
            return Scope(True, ())
        paths = []
        for grant in self._grants:
            if not grant.allows(code):
                continue
            if grant.path is None:
                return Scope(True, ())
            paths.append(grant.path)
        return Scope(False, tuple(paths))

    def covering(self, code: str, node_path: str | None = None) -> list[Grant]:
        if self._is_superuser:
            return [SUPERUSER_GRANT]
        return [g for g in self._grants if g.allows(code) and g.covers(node_path)]

    def elsewhere(self, code: str, node_path: str | None = None) -> list[Grant]:
        return [g for g in self._grants if g.allows(code) and not g.covers(node_path)]

    def permission_sources(self) -> dict[str, list[Grant]]:
        registered = {p.code for p in registry.all_permissions()}
        grants = [SUPERUSER_GRANT] if self._is_superuser else self._grants
        sources: dict[str, list[Grant]] = defaultdict(list)
        for grant in grants:
            for code in registered if grant.grants_all else grant.permissions:
                sources[code].append(grant)
        return sources

    def effective(self) -> dict:
        """A summary for the frontend: university-wide codes and node-scoped codes."""
        if self.holds_everything():
            return {"all": True, "everywhere": [], "scoped": {}}
        registered = {p.code for p in registry.all_permissions()}
        everywhere: set[str] = set()
        scoped: dict[str, set[uuid.UUID]] = defaultdict(set)
        for grant in self._grants:
            codes = registered if grant.grants_all else grant.permissions
            if grant.node_id is None:
                everywhere |= codes
            else:
                for code in codes:
                    scoped[code].add(grant.node_id)
        return {
            "all": False,
            "everywhere": sorted(everywhere),
            "scoped": {code: sorted(ids) for code, ids in sorted(scoped.items())},
        }