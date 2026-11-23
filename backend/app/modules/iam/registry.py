import re
from dataclasses import dataclass

CODE_PATTERN = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*\.[a-z][a-z_]*$")

STARTER_ROLES = {
    "super_admin": ("Super Admin", "Full access to everything, including future modules."),
    "registrar": ("Registrar", "Runs academic records and university-wide academic setup."),
    "dean": ("Dean", "Approves academic decisions for a college or faculty."),
    "cod": ("Chair of Department (COD)", "Manages and approves work within a department."),
    "lecturer": ("Lecturer", "Teaching staff with mostly read access."),
    "auditor": ("Auditor", "Read-only access for audit and review."),
}


@dataclass(frozen=True)
class Permission:
    code: str
    description: str
    roles: tuple[str, ...] = ()

    @property
    def module(self) -> str:
        return self.code.split(".")[0]


_registry: dict[str, Permission] = {}


def declare(*permissions: Permission) -> None:
    for permission in permissions:
        if not CODE_PATTERN.match(permission.code):
            raise ValueError(f"Invalid permission code: {permission.code}")
        if permission.code in _registry:
            raise ValueError(f"Duplicate permission code: {permission.code}")
        unknown = set(permission.roles) - STARTER_ROLES.keys()
        if unknown:
            raise ValueError(f"Unknown starter role for {permission.code}: {unknown}")
        _registry[permission.code] = permission


def all_permissions() -> list[Permission]:
    return list(_registry.values())