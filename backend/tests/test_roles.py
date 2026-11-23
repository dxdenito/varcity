import uuid

import pytest
from sqlalchemy import delete

from app.core.db import SessionLocal
from app.modules.audit.models import AuditLog
from app.modules.iam.rbac_models import Role, RoleAssignment

ROLES = "/api/v1/admin/roles"
PERMISSIONS = "/api/v1/admin/permissions"


@pytest.fixture
def role_name():
    names = []

    def _name():
        name = f"Test {uuid.uuid4().hex[:10]}"
        names.append(name)
        return name

    yield _name
    with SessionLocal() as session:
        session.execute(delete(Role).where(Role.name.in_(names)))
        session.commit()


def _create(client, name, permissions=()):
    return client.post(ROLES, json={"name": name, "permissions": list(permissions)})


def test_roles_need_the_view_permission(signed_in, grant):
    client = signed_in()
    assert client.get(ROLES).status_code == 403
    assert client.get(PERMISSIONS).status_code == 403

    grant(client.user, "iam.role.view")
    roles = {role["name"]: role for role in client.get(ROLES).json()}
    assert roles["Dean"]["is_system"] is True
    assert roles["Super Admin"]["grants_all"] is True
    catalogue = {p["code"]: p for p in client.get(PERMISSIONS).json()}
    assert catalogue["org.node.view"]["module"] == "org"


def test_creating_a_role_adds_the_matching_view_permission(role_name, signed_in):
    admin = signed_in(is_superuser=True)
    response = _create(admin, role_name(), ["org.node.update"])
    assert response.status_code == 201
    body = response.json()
    assert body["permissions"] == ["org.node.update", "org.node.view"]
    assert body["is_system"] is False and body["assignment_count"] == 0
    with SessionLocal() as session:
        audited = session.query(AuditLog).filter_by(
            action="iam.role.created", entity_id=body["id"]
        )
        assert audited.count() == 1


def test_unknown_permission_and_duplicate_name_are_rejected(role_name, signed_in):
    admin = signed_in(is_superuser=True)
    name = role_name()
    assert _create(admin, name, ["not.a.permission"]).status_code == 422
    assert _create(admin, name).status_code == 201
    assert _create(admin, name.upper()).status_code == 409


def test_a_role_manager_can_only_grant_what_they_hold(role_name, signed_in, grant):
    client = signed_in()
    grant(client.user, "iam.role.manage")
    grant(client.user, "org.node.view")
    assert _create(client, role_name(), ["org.node.update"]).status_code == 403
    assert _create(client, role_name(), ["org.node.view"]).status_code == 201


def test_updating_a_role_replaces_its_permissions(role_name, signed_in):
    admin = signed_in(is_superuser=True)
    created = _create(admin, role_name(), ["org.node.update"]).json()
    new_name = role_name()
    response = admin.put(
        f"{ROLES}/{created['id']}",
        json={
            "name": new_name,
            "description": "Changed",
            "permissions": ["settings.general.update"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == new_name and body["description"] == "Changed"
    assert body["permissions"] == ["settings.general.update", "settings.general.view"]


def test_changing_roles_needs_the_manage_permission(role_name, signed_in, grant):
    admin = signed_in(is_superuser=True)
    created = _create(admin, role_name()).json()
    client = signed_in()
    grant(client.user, "iam.role.view")
    change = {"name": role_name(), "permissions": []}
    assert client.put(f"{ROLES}/{created['id']}", json=change).status_code == 403
    assert client.delete(f"{ROLES}/{created['id']}").status_code == 403


def test_starter_roles_are_protected(signed_in):
    admin = signed_in(is_superuser=True)
    roles = {role["name"]: role for role in admin.get(ROLES).json()}
    super_admin, dean = roles["Super Admin"], roles["Dean"]
    change = {"name": "Boss", "permissions": []}
    assert admin.put(f"{ROLES}/{super_admin['id']}", json=change).status_code == 403
    assert admin.delete(f"{ROLES}/{super_admin['id']}").status_code == 403
    assert admin.delete(f"{ROLES}/{dean['id']}").status_code == 403
    assert admin.get(f"{ROLES}/{uuid.uuid4()}").status_code == 404


def test_a_role_in_use_cannot_be_deleted(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    created = _create(admin, role_name()).json()
    member = make_user()
    with SessionLocal() as session:
        session.add(
            RoleAssignment(user_id=member["id"], role_id=uuid.UUID(created["id"]))
        )
        session.commit()
    assert admin.delete(f"{ROLES}/{created['id']}").status_code == 409

    with SessionLocal() as session:
        session.execute(
            delete(RoleAssignment).where(RoleAssignment.user_id == member["id"])
        )
        session.commit()
    assert admin.delete(f"{ROLES}/{created['id']}").status_code == 204