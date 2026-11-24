from app.modules.iam.access import sync_registry
from app.modules.iam.rbac_models import Role, RolePermission

ROLES = "/api/v1/admin/roles"
USERS = "/api/v1/admin/users"


def _roles(client):
    return {role["name"]: role for role in client.get(ROLES).json()}


def test_the_catalogue_is_seeded_with_categories(signed_in):
    roles = _roles(signed_in(is_superuser=True))
    assert len(roles) >= 100
    assert roles["Data Protection Officer"]["category"] == "Audit and compliance"
    assert roles["Chair of Department (COD)"]["category"] == "Academic leadership"
    assert roles["Cashier"]["permissions"] == []
    assert roles["Staff Member"]["permissions"] == ["org.node.view"]
    categories = {r["category"] for r in roles.values() if r["is_system"]}
    assert len(categories) >= 12


def test_custom_types_can_have_a_category(role_name, signed_in):
    admin = signed_in(is_superuser=True)
    response = admin.post(
        ROLES, json={"name": role_name(), "category": "Pilot team", "permissions": []}
    )
    assert response.status_code == 201
    assert response.json()["category"] == "Pilot team"
    assert response.json()["is_active"] is True


def test_deactivated_types_cannot_be_assigned_but_existing_assignments_stay(
    role_name, signed_in, make_user
):
    admin = signed_in(is_superuser=True)
    target, other = make_user(), make_user()
    created = admin.post(
        ROLES, json={"name": role_name(), "permissions": ["org.node.view"]}
    ).json()
    assigned = admin.post(
        f"{USERS}/{target['id']}/roles", json={"role_id": created["id"]}
    )
    assert assigned.status_code == 201

    update = admin.put(
        f"{ROLES}/{created['id']}",
        json={"name": created["name"], "permissions": ["org.node.view"], "is_active": False},
    )
    assert update.status_code == 200 and update.json()["is_active"] is False

    refused = admin.post(f"{USERS}/{other['id']}/roles", json={"role_id": created["id"]})
    assert refused.status_code == 422
    kept = admin.get(f"{USERS}/{target['id']}").json()["assignments"]
    assert [a["role_id"] for a in kept] == [created["id"]]


def test_duplicating_copies_permissions_and_is_not_a_system_type(role_name, signed_in):
    admin = signed_in(is_superuser=True)
    roles = _roles(admin)
    lecturer = roles["Lecturer"]
    response = admin.post(
        f"{ROLES}/{lecturer['id']}/duplicate", json={"name": role_name()}
    )
    assert response.status_code == 201
    copy = response.json()
    assert copy["permissions"] == lecturer["permissions"]
    assert copy["category"] == lecturer["category"]
    assert copy["is_system"] is False

    super_admin = roles["Super Admin"]
    blocked = admin.post(
        f"{ROLES}/{super_admin['id']}/duplicate", json={"name": role_name()}
    )
    assert blocked.status_code == 403


def test_duplicating_cannot_hand_out_permissions_you_lack(role_name, signed_in, grant):
    admin = signed_in(is_superuser=True)
    dean = _roles(admin)["Dean"]
    manager = signed_in()
    grant(manager.user, "iam.role.manage")
    response = manager.post(
        f"{ROLES}/{dean['id']}/duplicate", json={"name": role_name()}
    )
    assert response.status_code == 403


def test_a_custom_type_with_a_starter_name_is_adopted(db):
    starter = db.query(Role).filter_by(system_key="cashier").one()
    db.delete(starter)
    db.flush()
    db.add(Role(name="Cashier", description="Mine"))
    db.flush()

    sync_registry(db)

    adopted = db.query(Role).filter_by(name="Cashier").one()
    assert adopted.system_key == "cashier"
    assert adopted.description == "Mine"
    assert adopted.category == "Finance"


def test_a_new_starter_type_receives_defaults_for_existing_permissions(db):
    staff = db.query(Role).filter_by(system_key="staff_member").one()
    db.delete(staff)
    db.flush()

    sync_registry(db)

    recreated = db.query(Role).filter_by(system_key="staff_member").one()
    codes = {
        rp.permission_code
        for rp in db.query(RolePermission).filter_by(role_id=recreated.id)
    }
    assert codes == {"org.node.view"}