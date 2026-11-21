import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.db import SessionLocal
from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.iam.models import UserAccount
from app.modules.iam.passwords import hash_password

PASSWORD = "a-long-test-passphrase"
LOGIN = "/api/v1/auth/login"
UNLOCK = "/api/v1/admin/users/{}/unlock"


@pytest.fixture
def make_user():
    created = []

    def _make(*, is_superuser=False, locked=False):
        email = f"{uuid.uuid4()}@example.com"
        locked_until = datetime.now(UTC) + timedelta(minutes=15) if locked else None
        with SessionLocal() as session:
            account = UserAccount(
                email=email,
                password_hash=hash_password(PASSWORD),
                full_name="Test User",
                is_superuser=is_superuser,
                locked_until=locked_until,
            )
            session.add(account)
            session.commit()
            created.append(account.id)
            return {"id": account.id, "email": email}

    yield _make
    with SessionLocal() as session:
        session.execute(delete(UserAccount).where(UserAccount.id.in_(created)))
        session.commit()


@pytest.fixture
def client():
    return TestClient(app)


def _login(client, email):
    return client.post(LOGIN, json={"email": email, "password": PASSWORD})


def test_superuser_can_unlock_a_locked_account(client, make_user):
    admin = make_user(is_superuser=True)
    target = make_user(locked=True)
    assert _login(TestClient(app), target["email"]).status_code == 401

    csrf = _login(client, admin["email"]).json()["csrf_token"]
    response = client.post(UNLOCK.format(target["id"]), headers={"X-CSRF-Token": csrf})

    assert response.status_code == 204
    assert _login(TestClient(app), target["email"]).status_code == 200
    with SessionLocal() as session:
        actions = session.scalars(
            select(AuditLog.action).where(AuditLog.entity_id == str(target["id"]))
        ).all()
    assert "auth.account.unlocked" in actions


def test_regular_user_cannot_unlock(client, make_user):
    regular = make_user()
    target = make_user(locked=True)
    csrf = _login(client, regular["email"]).json()["csrf_token"]

    response = client.post(UNLOCK.format(target["id"]), headers={"X-CSRF-Token": csrf})

    assert response.status_code == 403
    with SessionLocal() as session:
        assert session.get(UserAccount, target["id"]).locked_until is not None


def test_unlock_requires_login_and_csrf(client, make_user):
    target = make_user(locked=True)
    url = UNLOCK.format(target["id"])
    assert client.post(url).status_code == 401

    _login(client, make_user(is_superuser=True)["email"])
    assert client.post(url).status_code == 403


def test_unlocking_an_unknown_account_returns_404(client, make_user):
    admin = make_user(is_superuser=True)
    csrf = _login(client, admin["email"]).json()["csrf_token"]

    response = client.post(UNLOCK.format(uuid.uuid4()), headers={"X-CSRF-Token": csrf})
    assert response.status_code == 404