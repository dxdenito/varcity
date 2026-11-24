import re
from dataclasses import dataclass
from app.modules.iam.user_types import STARTER_ROLES  # noqa: F401

CODE_PATTERN = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*\.[a-z][a-z_]*$")

RISKS = ("normal", "sensitive", "critical")

STANDARD_ACTIONS = frozenset(
    {
        "view",
        "create",
        "update",
        "delete",
        "approve",
        "reject",
        "verify",
        "submit",
        "publish",
        "unpublish",
        "upload",
        "download",
        "export",
        "import",
        "assign",
        "transfer",
        "move",
        "close",
        "reopen",
        "configure",
        "manage",
        "restore",
        "archive",
    }
)
SPECIALISED_ACTIONS = frozenset({"initialize", "unlock", "assign_role"})



@dataclass(frozen=True)
class Permission:
    code: str
    description: str
    roles: tuple[str, ...] = ()
    risk: str = "normal"

    @property
    def module(self) -> str:
        return self.code.split(".")[0]

    @property
    def resource(self) -> str:
        return self.code.split(".")[1]

    @property
    def action(self) -> str:
        return self.code.split(".")[2]


_registry: dict[str, Permission] = {}
_labels: dict[str, str] = {}


def declare(*permissions: Permission) -> None:
    for permission in permissions:
        if not CODE_PATTERN.match(permission.code):
            raise ValueError(f"Invalid permission code: {permission.code}")
        if permission.code in _registry:
            raise ValueError(f"Duplicate permission code: {permission.code}")
        if permission.action not in STANDARD_ACTIONS | SPECIALISED_ACTIONS:
            raise ValueError(
                f"Unknown action '{permission.action}' in {permission.code}. "
                "Use a standard action or add it to SPECIALISED_ACTIONS."
            )
        if permission.risk not in RISKS:
            raise ValueError(f"Unknown risk '{permission.risk}' for {permission.code}")
        unknown = set(permission.roles) - STARTER_ROLES.keys()
        if unknown:
            raise ValueError(f"Unknown starter role for {permission.code}: {unknown}")
        _registry[permission.code] = permission


def declare_labels(labels: dict[str, str]) -> None:
    """Display names for a module ("org") and its resources ("org.node")."""
    for key, label in labels.items():
        if key in _labels:
            raise ValueError(f"Duplicate label for {key}")
        _labels[key] = label


def label_for(key: str) -> str:
    return _labels.get(key) or key.split(".")[-1].replace("_", " ").capitalize()


def all_permissions() -> list[Permission]:
    return list(_registry.values())