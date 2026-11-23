from fastapi.testclient import TestClient

from app.main import app

UNLOCK = "iam.user.unlock"


def unlock_url(user):
    return f"/api/v1/admin/users/{user['id']}/unlock"


def test_unauthenticated_request_is_rejected(make_user):
    target = make_user()
    assert TestClient(app).post(unlock_url(target)).status_code == 401


def test_signed_in_user_without_permission_is_forbidden(signed_in, make_user):
    client = signed_in()
    assert client.post(unlock_url(make_user())).status_code == 403


def test_user_with_permission_is_allowed(signed_in, make_user, grant):
    client = signed_in()
    grant(client.user, UNLOCK)
    assert client.post(unlock_url(make_user())).status_code == 204


def test_permission_alone_is_not_enough_without_csrf(signed_in, make_user, grant):
    client = signed_in()
    grant(client.user, UNLOCK)
    client.headers.pop("X-CSRF-Token")
    assert client.post(unlock_url(make_user())).status_code == 403


def test_superuser_still_allowed(signed_in, make_user):
    client = signed_in(is_superuser=True)
    assert client.post(unlock_url(make_user())).status_code == 204