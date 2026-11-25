import uuid
from datetime import UTC, datetime, timedelta

USERS = "/api/v1/admin/users"
ROLES = "/api/v1/admin/roles"


def _in(**delta):
    return (datetime.now(UTC) + timedelta(**delta)).isoformat()


def _role(admin, name, permissions=()):
    response = admin.post(ROLES, json={"name": name, "permissions": list(permissions)})
    assert response.status_code == 201
    return response.json()["id"]


def _post(client, user, action, **body):
    return client.post(f"{USERS}/{user['id']}/access/{action}", json=body)


def _detail(client, user):
    return client.get(f"{USERS}/{user['id']}/access").json()


def test_changes_are_applied_together(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _role(admin, role_name(), ["org.node.view"])

    response = _post(
        admin,
        target,
        "apply",
        add_assignments=[{"role_id": role_id, "reason": "Joined the team"}],
        add_grants=[{"permission": "settings.general.view"}],
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["assignments"]) == 1 and len(body["grants"]) == 1
    assert "settings.general.view" in body["permissions"]


def test_changes_can_update_and_remove(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    target = make_user()
    role_id = _role(admin, role_name(), ["org.node.view"])
    first = _post(
        admin,
        target,
        "apply",
        add_assignments=[{"role_id": role_id}],
        add_grants=[{"permission": "settings.general.view"}],
    ).json()
    assignment_id = first["assignments"][0]["id"]
    grant_id = first["grants"][0]["id"]

    second = _post(
        admin,
        target,
        "apply",
        update_assignments=[
            {"id": assignment_id, "valid_until": _in(days=5), "reason": "Extended"}
        ],
        remove_grants=[grant_id],
    ).json()
    assert second["assignments"][0]["valid_until"] is not None
    assert second["assignments"][0]["reason"] == "Extended"
    assert second["grants"] == []

    third = _post(admin, target, "apply", remove_assignments=[assignment_id]).json()
    assert third["assignments"] == []


def test_one_failing_change_applies_nothing(role_name, signed_in, make_user, grant):
    admin = signed_in(is_superuser=True)
    holder = signed_in()
    grant(holder.user, "iam.user.assign_role")
    grant(holder.user, "org.node.view")
    target = make_user()
    role_id = _role(admin, role_name(), ["org.node.view"])

    response = _post(
        holder,
        target,
        "apply",
        add_assignments=[{"role_id": role_id}],
        add_grants=[{"permission": "org.node.update"}],
    )
    assert response.status_code == 403
    assert _detail(admin, target)["assignments"] == []


def test_node_scoped_assigners_cannot_stray_outside_their_scope(
    role_name, two_nodes, signed_in, make_user, grant
):
    first, second = two_nodes
    admin = signed_in(is_superuser=True)
    delegate = signed_in()
    grant(delegate.user, "iam.user.assign_role", node_id=first)
    grant(delegate.user, "org.node.view", node_id=first)
    target = make_user()
    role_id = _role(admin, role_name(), ["org.node.view"])

    response = _post(
        delegate,
        target,
        "apply",
        add_assignments=[
            {"role_id": role_id, "node_id": str(first)},
            {"role_id": role_id, "node_id": str(second)},
        ],
    )
    assert response.status_code == 403
    assert _detail(admin, target)["assignments"] == []


def test_review_describes_changes_without_applying_them(role_name, signed_in, make_user):
    admin = signed_in(is_superuser=True)
    plain = signed_in(is_superuser=True, elevated=False)
    target = make_user()
    critical_role = _role(admin, role_name(), ["iam.role.manage"])

    review = _post(
        plain,
        target,
        "review",
        add_assignments=[{"role_id": critical_role}],
        add_grants=[{"permission": "org.node.delete", "reason": "Cleanup duty"}],
    )
    assert review.status_code == 200
    body = review.json()
    assert body["requires_confirmation"] is True
    assert body["critical"] == ["iam.role.manage"]
    assert body["sensitive"] == ["org.node.delete"]
    assert {item["kind"] for item in body["items"]} == {"assignment", "grant"}
    assert _detail(admin, target)["assignments"] == []
    assert _detail(admin, target)["grants"] == []


def test_review_does_not_ask_again_when_already_confirmed(signed_in, make_user):
    admin = signed_in(is_superuser=True)
    review = _post(
        admin,
        make_user(),
        "review",
        add_grants=[{"permission": "settings.general.view"}],
    )
    assert review.json()["requires_confirmation"] is False


def test_apply_needs_confirmation_and_changes_nothing_without_it(signed_in, make_user):
    admin = signed_in(is_superuser=True)
    plain = signed_in(is_superuser=True, elevated=False)
    target = make_user()
    response = _post(
        plain, target, "apply", add_grants=[{"permission": "settings.general.view"}]
    )
    assert response.status_code == 428
    assert _detail(admin, target)["grants"] == []


def test_removing_an_unknown_assignment_is_not_found(signed_in, make_user):
    admin = signed_in(is_superuser=True)
    response = _post(
        admin, make_user(), "apply", remove_assignments=[str(uuid.uuid4())]
    )
    assert response.status_code == 404