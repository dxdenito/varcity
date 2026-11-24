from app.modules.iam.registry import Permission, declare, declare_labels

UNLOCK = "iam.user.unlock"
USER_VIEW = "iam.user.view"
ASSIGN_ROLE = "iam.user.assign_role"
ROLE_VIEW = "iam.role.view"
ROLE_MANAGE = "iam.role.manage"

declare_labels(
    {"iam": "Users and access", "iam.user": "User accounts", "iam.role": "User types"}
)

declare(
    Permission(UNLOCK, "Unlock locked user accounts", risk="sensitive"),
    Permission(
        USER_VIEW,
        "View user accounts and their roles",
        roles=("auditor",),
        risk="sensitive",
    ),
    Permission(ASSIGN_ROLE, "Assign and remove roles for users", risk="critical"),
    Permission(
        ROLE_VIEW, "View roles and the permissions they hold", roles=("auditor",)
    ),
    Permission(ROLE_MANAGE, "Create, edit and delete roles", risk="critical"),
)