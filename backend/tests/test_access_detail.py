import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.core.db import SessionLocal
from app.modules.iam.access import Access
from app.modules.iam.models import UserAccount
from app.modules.iam.rbac_models import Role, RoleAssignment

USERS = "/api/v1/admin/users"
ROLES = "/api/v1/admin/roles"


def _in(**delta):
    return (datetime.now(UTC) + timedelta(**delta)).isoformat()


def _role_id(admin, name):
    return {r["name"]: r["id"] for r in admin.get(ROLES).json()}[name]


def _make_role(admin, name, permissions=()):
    response = admin.post(ROLES, json={"name": name, "permissions": list(permissions)})
    assert response.status_code == 201
    return response.json()["id"]


def _assign(client, user, role_id, node_id=None, **window):
    return client.post(
        f"{USERS}/{user['id']}/roles",
        json={"role_id": role_id, "node_id": str(node_id) if node_id else None, **window},
    )


def _grant(client, user, permission, node_id=None, **extra):
    return client.post(
        f"{USERS}/{user['id']}/permissions",
        json={"permission": permission, "node_id": str(node_id) if node_id else None, **extra},
    )


def _access_of(db, user):
    return Access.load(db, db.get(UserAccount, user["id"]))


def test_windows_are_stored_and_reported(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _make_role(admin, role_name(), ["org.node.view"])

    response = _assign(
        admin, target, role_id, valid_until=_in(days=30), reason="Acting COD"
    )
    assert response.status_code == 201
    row = response.json()["assignments"][0]
    assert row["state"] == "active"
    assert row["reason"] == "Acting COD"
    assert row["valid_until"] is not None


def test_scheduled_assignments_are_reported_as_scheduled(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _make_role(admin, role_name())
    response = _assign(admin, target, role_id, valid_from=_in(days=2))
    assert response.json()["assignments"][0]["state"] == "scheduled"


def test_bad_windows_are_rejected(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _make_role(admin, role_name())
    assert _assign(admin, target, role_id, valid_until=_in(days=-1)).status_code == 422
    backwards = _assign(admin, target, role_id, valid_from=_in(days=5), valid_until=_in(days=2))
    assert backwards.status_code == 422
    naive = _assign(admin, target, role_id, valid_until="2099-01-01T00:00:00")
    assert naive.status_code == 422


def test_expired_and_scheduled_assignments_grant_nothing(db, make_user):
    registrar = db.query(Role).filter_by(system_key="registrar").one()
    now = datetime.now(UTC)
    windows = {
        "expired": dict(valid_from=now - timedelta(hours=2), valid_until=now - timedelta(hours=1)),
        "scheduled": dict(valid_from=now + timedelta(hours=1), valid_until=None),
        "current": dict(valid_from=now - timedelta(hours=1), valid_until=now + timedelta(hours=1)),
    }
    results = {}
    for name, window in windows.items():
        user = make_user()
        db.add(RoleAssignment(user_id=user["id"], role_id=registrar.id, **window))
        db.flush()
        results[name] = _access_of(db, user).can("org.node.update")
    assert results == {"expired": False, "scheduled": False, "current": True}


def test_an_expired_assignment_can_be_renewed(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _make_role(admin, role_name())
    assert _assign(admin, target, role_id, valid_until=_in(days=1)).status_code == 201
    assert _assign(admin, target, role_id).status_code == 409

    with SessionLocal() as session:
        session.execute(
            update(RoleAssignment)
            .where(RoleAssignment.user_id == target["id"])
            .values(valid_from=None, valid_until=datetime.now(UTC) - timedelta(hours=1))
        )
        session.commit()

    renewed = _assign(admin, target, role_id, valid_until=_in(days=10))
    assert renewed.status_code == 201
    assert renewed.json()["assignments"][0]["state"] == "active"


def test_individual_grant_gives_access_and_can_be_revoked(db, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    assert not _access_of(db, target).can("org.node.view")
    db.rollback()

    response = _grant(admin, target, "org.node.view")
    assert response.status_code == 201
    body = response.json()
    assert len(body["grants"]) == 1
    source = body["permissions"]["org.node.view"][0]
    assert source["kind"] == "individual"
    assert _access_of(db, target).can("org.node.view")
    db.rollback()

    assert _grant(admin, target, "org.node.view").status_code == 409

    revoked = admin.delete(f"{USERS}/{target['id']}/permissions/{body['grants'][0]['id']}")
    assert revoked.status_code == 200
    assert revoked.json()["grants"] == []
    assert "org.node.view" not in revoked.json()["permissions"]


def test_sensitive_grants_need_a_reason(signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    assert _grant(admin, target, "org.node.delete").status_code == 422
    assert _grant(admin, target, "org.node.delete", reason="Cleanup duty").status_code == 201
    assert _grant(admin, target, "not.a.permission").status_code == 422


def test_granters_can_only_grant_what_they_hold(signed_in, make_user, grant):
    holder = signed_in()
    grant(holder.user, "iam.user.assign_role")
    grant(holder.user, "org.node.view")
    target = make_user()
    assert _grant(holder, target, "org.node.update").status_code == 403
    assert _grant(holder, target, "org.node.view").status_code == 201


def test_access_detail_lists_role_sources(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _make_role(admin, role_name(), ["org.node.update"])
    _assign(admin, target, role_id)
    detail = admin.get(f"{USERS}/{target['id']}/access").json()
    sources = detail["permissions"]["org.node.update"]
    assert [s["kind"] for s in sources] == ["role"]
    assert "org.node.view" in detail["permissions"]


def test_explain_names_where_access_comes_from(two_nodes, signed_in, make_user):
    first, second = two_nodes
    admin = signed_in(is_superuser=True)
    target = make_user()
    assert _assign(admin, target, _role_id(admin, "Dean"), first).status_code == 201

    def explain(node):
        return admin.get(
            f"{USERS}/{target['id']}/explain",
            params={"permission": "org.node.update", "node_id": str(node)},
        ).json()

    allowed = explain(first)
    assert allowed["allowed"] is True
    assert allowed["granted_by"][0]["label"] == "Dean"

    denied = explain(second)
    assert denied["allowed"] is False
    assert denied["held_elsewhere"][0]["label"] == "Dean"


def test_explain_reports_expired_assignments(signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    now = datetime.now(UTC)
    with SessionLocal() as session:
        registrar = session.query(Role).filter_by(system_key="registrar").one()
        session.add(
            RoleAssignment(
                user_id=target["id"],
                role_id=registrar.id,
                valid_from=now - timedelta(days=3),
                valid_until=now - timedelta(days=1),
            )
        )
        session.commit()

    result = admin.get(
        f"{USERS}/{target['id']}/explain", params={"permission": "org.node.update"}
    ).json()
    assert result["allowed"] is False
    assert result["inactive"][0]["state"] == "expired"
    assert result["inactive"][0]["label"] == "Registrar"
    assert admin.get(
        f"{USERS}/{uuid.uuid4()}/explain", params={"permission": "org.node.update"}
    ).status_code == 404