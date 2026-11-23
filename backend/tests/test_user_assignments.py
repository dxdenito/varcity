import uuid

from app.core.db import SessionLocal
from app.modules.audit.models import AuditLog

USERS = "/api/v1/admin/users"
ROLES = "/api/v1/admin/roles"


def _role(admin, name, permissions=()):
    response = admin.post(ROLES, json={"name": name, "permissions": list(permissions)})
    assert response.status_code == 201
    return response.json()["id"]


def _assign(client, user, role_id, node_id=None):
    return client.post(
        f"{USERS}/{user['id']}/roles",
        json={"role_id": role_id, "node_id": str(node_id) if node_id else None},
    )


def test_user_list_needs_the_view_permission(signed_in, grant):
    client = signed_in()
    assert client.get(USERS).status_code == 403

    grant(client.user, "iam.user.view")
    page = client.get(USERS, params={"q": client.user["email"]}).json()
    assert page["total"] == 1
    user = page["items"][0]
    assert user["email"] == client.user["email"]
    assert len(user["assignments"]) == 1 and user["assignments"][0]["node_id"] is None
    assert client.get(f"{USERS}/{client.user['id']}").status_code == 200
    assert client.get(f"{USERS}/{uuid.uuid4()}").status_code == 404


def test_user_list_is_paged(signed_in, make_user, grant):
    client = signed_in()
    make_user()
    grant(client.user, "iam.user.view")
    page = client.get(USERS, params={"q": "@example.com", "limit": 1}).json()
    assert len(page["items"]) == 1 and page["total"] >= 2


def test_assigning_and_removing_a_role(role_name, two_nodes, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _role(admin, role_name(), ["org.node.view"])
    college = two_nodes[0]

    assert _assign(admin, target, role_id).status_code == 201
    assert _assign(admin, target, role_id).status_code == 409
    scoped = _assign(admin, target, role_id, college)
    assert scoped.status_code == 201
    assignments = scoped.json()["assignments"]
    assert {a["node_id"] for a in assignments} == {None, str(college)}
    scoped_row = next(a for a in assignments if a["node_id"])
    assert scoped_row["node_name"] == "Original"

    with SessionLocal() as session:
        audited = session.query(AuditLog).filter_by(
            action="iam.role.assigned", entity_id=str(target["id"])
        )
        assert audited.count() == 2

    removed = admin.delete(f"{USERS}/{target['id']}/roles/{scoped_row['id']}")
    assert removed.status_code == 200
    remaining = removed.json()["assignments"]
    assert [a["node_id"] for a in remaining] == [None]

    other = make_user()
    wrong_user = admin.delete(f"{USERS}/{other['id']}/roles/{remaining[0]['id']}")
    assert wrong_user.status_code == 404


def test_assigners_can_only_assign_what_they_hold(
    role_name, signed_in, make_user, grant
):
    admin = signed_in(is_superuser=True)
    holder = signed_in()
    grant(holder.user, "iam.user.assign_role")
    grant(holder.user, "org.node.view")
    target = make_user()
    allowed = _role(admin, role_name(), ["org.node.view"])
    too_much = _role(admin, role_name(), ["org.node.update"])
    super_admin = {r["name"]: r["id"] for r in admin.get(ROLES).json()}["Super Admin"]

    assert _assign(holder, target, too_much).status_code == 403
    assert _assign(holder, target, super_admin).status_code == 403
    assert _assign(holder, target, allowed).status_code == 201


def test_assigning_roles_needs_the_assign_permission(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    role_id = _role(admin, role_name())
    assert _assign(signed_in(), make_user(), role_id).status_code == 403


def test_node_scoped_assigners_are_limited_to_their_subtree(
    role_name, two_nodes, signed_in, make_user, grant
):
    first, second = two_nodes
    admin = signed_in(is_superuser=True)
    delegate = signed_in()
    grant(delegate.user, "iam.user.assign_role", node_id=first)
    grant(delegate.user, "org.node.view", node_id=first)
    target = make_user()
    role_id = _role(admin, role_name(), ["org.node.view"])

    created = _assign(delegate, target, role_id, first)
    assert created.status_code == 201
    assert _assign(delegate, target, role_id, second).status_code == 403
    assert _assign(delegate, target, role_id).status_code == 403

    row = next(a for a in created.json()["assignments"] if a["node_id"] == str(first))
    elsewhere = _assign(admin, target, role_id, second).json()
    elsewhere_row = next(
        a for a in elsewhere["assignments"] if a["node_id"] == str(second)
    )
    base = f"{USERS}/{target['id']}/roles"
    assert delegate.delete(f"{base}/{elsewhere_row['id']}").status_code == 403
    assert delegate.delete(f"{base}/{row['id']}").status_code == 200