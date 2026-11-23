from app.modules.iam.registry import Permission, declare

UNLOCK = "iam.user.unlock"
USER_VIEW = "iam.user.view"
ASSIGN_ROLE = "iam.user.assign_role"
ROLE_VIEW = "iam.role.view"
ROLE_MANAGE = "iam.role.manage"

declare(
    Permission(UNLOCK, "Unlock locked user accounts"),
    Permission(USER_VIEW, "View user accounts and their roles", roles=("auditor",)),
    Permission(ASSIGN_ROLE, "Assign and remove roles for users"),
    Permission(
        ROLE_VIEW, "View roles and the permissions they hold", roles=("auditor",)
    ),
    Permission(ROLE_MANAGE, "Create, edit and delete roles"),
)