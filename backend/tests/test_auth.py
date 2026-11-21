import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update

from app.core.db import SessionLocal
from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.iam.models import UserAccount, UserSession
from app.modules.iam.passwords import hash_password
from app.modules.iam.tokens import csrf_for, hash_token

PASSWORD = "a-long-test-passphrase"
COOKIE = "varcity_session"
LOGIN, ME, LOGOUT = "/api/v1/auth/login", "/api/v1/auth/me", "/api/v1/auth/logout"


@pytest.fixture
def user():
    """A committed test account, removed afterwards (its sessions go with it)."""
    email = f"{uuid.uuid4()}@example.com"
    with SessionLocal() as session:
        account = UserAccount(
            email=email, password_hash=hash_password(PASSWORD), full_name="Test User"
        )
        session.add(account)
        session.commit()
        user_id = account.id
    yield {"id": user_id, "email": email}
    with SessionLocal() as session:
        session.execute(delete(UserAccount).where(UserAccount.id == user_id))
        session.commit()


@pytest.fixture
def client():
    return TestClient(app)  # each test gets its own cookie jar


def _login(client, email, password=PASSWORD):
    return client.post(LOGIN, json={"email": email, "password": password})


def _update_user(user_id, **values):
    with SessionLocal() as session:
        session.execute(update(UserAccount).where(UserAccount.id == user_id).values(**values))
        session.commit()


def test_login_sets_an_httponly_cookie_and_returns_a_csrf_token(client, user):
    response = _login(client, user["email"])
    assert response.status_code == 200

    body = response.json()
    assert body["user"]["email"] == user["email"]
    assert body["user"]["full_name"] == "Test User"
    assert body["csrf_token"]
    assert "password" not in response.text.lower()

    cookie_header = response.headers["set-cookie"].lower()
    assert COOKIE in cookie_header
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header


def test_session_token_is_not_stored_in_plain_text(client, user):
    _login(client, user["email"])
    token = client.cookies.get(COOKIE)

    with SessionLocal() as session:
        stored = session.scalars(
            select(UserSession.token_hash).where(UserSession.user_id == user["id"])
        ).all()
    assert token not in stored
    assert hash_token(token) in stored


def test_wrong_password_and_unknown_email_look_identical(client, user):
    wrong_password = _login(client, user["email"], "not-the-right-password")
    unknown_email = _login(client, "nobody@example.com", "not-the-right-password")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_failed_login_is_counted_and_audited(client, user):
    _login(client, user["email"], "not-the-right-password")

    with SessionLocal() as session:
        account = session.get(UserAccount, user["id"])
        assert account.failed_login_count == 1
        actions = session.scalars(
            select(AuditLog.action).where(AuditLog.entity_id == str(user["id"]))
        ).all()
    assert "auth.login.failed" in actions


def test_account_locks_after_repeated_failures_and_recovers(client, user):
    for _ in range(5):
        assert _login(client, user["email"], "not-the-right-password").status_code == 401

    # Even the correct password is refused while the account is locked.
    assert _login(client, user["email"]).status_code == 401
    with SessionLocal() as session:
        assert session.get(UserAccount, user["id"]).locked_until is not None

    _update_user(user["id"], locked_until=None)  # simulate the lock expiring
    assert _login(client, user["email"]).status_code == 200


def test_suspended_account_cannot_log_in(client, user):
    _update_user(user["id"], status="suspended")
    assert _login(client, user["email"]).status_code == 401


def test_me_needs_a_session(client, user):
    assert client.get(ME).status_code == 401

    login_body = _login(client, user["email"]).json()
    response = client.get(ME)
    assert response.status_code == 200
    assert response.json()["user"]["email"] == user["email"]
    assert response.json()["csrf_token"] == login_body["csrf_token"]


def test_logout_needs_csrf_and_really_ends_the_session(client, user):
    csrf = _login(client, user["email"]).json()["csrf_token"]
    token = client.cookies.get(COOKIE)

    assert client.post(LOGOUT).status_code == 403  # no CSRF header
    assert client.post(LOGOUT, headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get(ME).status_code == 401

    # Replaying the old cookie must fail too: the session is revoked on the server.
    replay = TestClient(app).get(ME, headers={"Cookie": f"{COOKIE}={token}"})
    assert replay.status_code == 401


@pytest.mark.parametrize(
    "column, offset",
    [
        ("expires_at", timedelta(minutes=-1)),  # absolute lifetime passed
        ("last_seen_at", timedelta(hours=-1)),  # idle for longer than 30 minutes
    ],
)
def test_expired_or_idle_sessions_are_rejected(client, user, column, offset):
    _login(client, user["email"])
    assert client.get(ME).status_code == 200

    with SessionLocal() as session:
        session.execute(
            update(UserSession)
            .where(UserSession.user_id == user["id"])
            .values({column: datetime.now(UTC) + offset})
        )
        session.commit()

    assert client.get(ME).status_code == 401


def test_csrf_token_is_stable_but_different_for_each_session():
    assert csrf_for("session-a") == csrf_for("session-a")
    assert csrf_for("session-a") != csrf_for("session-b")