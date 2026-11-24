PASSWORD = "a-long-test-passphrase"
REAUTH = "/api/v1/auth/reauth"
ROLES = "/api/v1/admin/roles"
USERS = "/api/v1/admin/users"


def test_editing_user_types_needs_a_recent_password_confirmation(role_name, signed_in):
    client = signed_in(is_superuser=True, elevated=False)
    body = {"name": role_name(), "permissions": []}
    assert client.post(ROLES, json=body).status_code == 428
    assert client.post(REAUTH, json={"password": PASSWORD}).status_code == 200
    assert client.post(ROLES, json=body).status_code == 201


def test_a_wrong_password_does_not_confirm(role_name, signed_in):
    client = signed_in(is_superuser=True, elevated=False)
    assert client.post(REAUTH, json={"password": "not-the-password-1"}).status_code == 403
    body = {"name": role_name(), "permissions": []}
    assert client.post(ROLES, json=body).status_code == 428


def test_repeated_wrong_passwords_block_confirmation(signed_in):
    client = signed_in(elevated=False)
    for _ in range(5):
        assert client.post(REAUTH, json={"password": "not-the-password-1"}).status_code == 403
    assert client.post(REAUTH, json={"password": PASSWORD}).status_code == 403


def test_individual_grants_need_confirmation(signed_in, make_user):
    client = signed_in(is_superuser=True, elevated=False)
    url = f"{USERS}/{make_user()['id']}/permissions"
    assert client.post(url, json={"permission": "org.node.view"}).status_code == 428
    client.post(REAUTH, json={"password": PASSWORD})
    assert client.post(url, json={"permission": "org.node.view"}).status_code == 201


def test_assigning_a_role_with_critical_permissions_needs_confirmation(
    role_name, signed_in, make_user
):
    admin = signed_in(is_superuser=True)
    plain = signed_in(is_superuser=True, elevated=False)
    target = make_user()
    critical = admin.post(
        ROLES, json={"name": role_name(), "permissions": ["iam.role.manage"]}
    ).json()["id"]
    harmless = admin.post(
        ROLES, json={"name": role_name(), "permissions": ["org.node.view"]}
    ).json()["id"]

    url = f"{USERS}/{target['id']}/roles"
    assert plain.post(url, json={"role_id": critical}).status_code == 428
    assert plain.post(url, json={"role_id": harmless}).status_code == 201


def test_reading_and_removing_access_does_not_need_confirmation(signed_in, make_user):
    admin = signed_in(is_superuser=True)
    plain = signed_in(is_superuser=True, elevated=False)
    target = make_user()
    granted = admin.post(
        f"{USERS}/{target['id']}/permissions", json={"permission": "org.node.view"}
    ).json()

    assert plain.get(ROLES).status_code == 200
    removed = plain.delete(f"{USERS}/{target['id']}/permissions/{granted['grants'][0]['id']}")
    assert removed.status_code == 200