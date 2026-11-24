from app.modules.iam import registry


def permission_tree() -> list[dict]:
    """Registered permissions grouped as module > resource > action."""
    groups: dict[str, dict] = {}
    for permission in sorted(registry.all_permissions(), key=lambda item: item.code):
        group = groups.setdefault(
            permission.module,
            {
                "module": permission.module,
                "label": registry.label_for(permission.module),
                "resources": {},
            },
        )
        resource = group["resources"].setdefault(
            permission.resource,
            {
                "resource": permission.resource,
                "label": registry.label_for(f"{permission.module}.{permission.resource}"),
                "permissions": [],
            },
        )
        resource["permissions"].append(
            {
                "code": permission.code,
                "action": permission.action,
                "description": permission.description,
                "risk": permission.risk,
            }
        )
    return [
        {**group, "resources": list(group["resources"].values())}
        for group in groups.values()
    ]