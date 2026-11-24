from fastapi.routing import APIRoute

from app.main import app
from app.modules.iam import registry
from app.modules.iam.deps import require_auth

PUBLIC = {
    "/api/v1/health/live",
    "/api/v1/health/ready",
    "/api/v1/public/branding",
    "/api/v1/public/branding/logo",
    "/api/v1/setup/status",
    "/api/v1/setup/complete",
    "/api/v1/auth/login",
}
SIGNED_IN_ONLY = {"/api/v1/auth/me", "/api/v1/auth/logout", "/api/v1/auth/reauth"}


def _calls(dependant):
    for dep in dependant.dependencies:
        yield dep.call
        yield from _calls(dep)


def _api_routes():
    return [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/v1")
    ]


def test_every_route_is_public_signed_in_only_or_permission_checked():
    problems = []
    for route in _api_routes():
        calls = list(_calls(route.dependant))
        codes = [c.permission_code for c in calls if hasattr(c, "permission_code")]
        if route.path in PUBLIC:
            if require_auth in calls:
                problems.append(f"{route.path} is listed public but requires sign-in")
        elif route.path in SIGNED_IN_ONLY:
            if require_auth not in calls:
                problems.append(f"{route.path} must require sign-in")
        elif not codes:
            problems.append(f"{sorted(route.methods)} {route.path} has no permission check")
    assert not problems, "\n".join(problems)


def test_every_checked_permission_is_declared():
    declared = {p.code for p in registry.all_permissions()}
    used = {
        c.permission_code
        for route in _api_routes()
        for c in _calls(route.dependant)
        if hasattr(c, "permission_code")
    }
    assert used <= declared, used - declared