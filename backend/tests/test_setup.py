import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.db import SessionLocal
from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.iam.models import UserAccount
from app.modules.settings.models import AppSetting
from app.modules.setup.code import expected_setup_code, verify_setup_code

STATUS, COMPLETE = "/api/v1/setup/status", "/api/v1/setup/complete"
ADMIN_EMAIL = "first.admin@example.com"
ADMIN_PASSWORD = "a-long-test-passphrase"


def _reset() -> None:
    with SessionLocal() as session:
        session.execute(delete(AppSetting).where(AppSetting.key.in_(["setup", "branding"])))
        session.execute(delete(UserAccount).where(UserAccount.email == ADMIN_EMAIL))
        session.commit()


@pytest.fixture
def fresh_install():
    """Make the test database look like a brand-new installation."""
    _reset()
    yield
    _reset()


@pytest.fixture
def client():
    return TestClient(app)


def _payload(**overrides):
    payload = {
        "setup_code": expected_setup_code(),
        "university_name": "Test University",
        "short_name": "TU",
        "primary_color": "#047857",
        "sidebar_color": "#022c22",
        "admin_full_name": "First Administrator",
        "admin_email": ADMIN_EMAIL,
        "admin_password": ADMIN_PASSWORD,
    }
    payload.update(overrides)
    return payload


def _nothing_was_created() -> bool:
    with SessionLocal() as session:
        setup_row = session.get(AppSetting, "setup")
        admin = session.scalar(select(UserAccount).where(UserAccount.email == ADMIN_EMAIL))
    return setup_row is None and admin is None


def test_wrong_setup_code_is_rejected_and_creates_nothing(fresh_install, client):
    response = client.post(COMPLETE, json=_payload(setup_code="AAAA-BBBB-CCCC"))
    assert response.status_code == 403
    assert _nothing_was_created()
    assert client.get(STATUS).json() == {"setup_required": True}


def test_successful_setup_creates_branding_and_a_working_admin(fresh_install, client):
    assert client.get(STATUS).json() == {"setup_required": True}

    response = client.post(COMPLETE, json=_payload())
    assert response.status_code == 201
    assert client.get(STATUS).json() == {"setup_required": False}

    # Branding is live
    branding = client.get("/api/v1/public/branding").json()
    assert branding["university_name"] == "Test University"
    assert branding["colors"]["primary"]["600"] == "#047857"

    # The admin exists with a hashed password and can log in
    with SessionLocal() as session:
        admin = session.scalar(select(UserAccount).where(UserAccount.email == ADMIN_EMAIL))
        assert admin.is_superuser is True
        assert admin.password_hash.startswith("$argon2id$")
        audit_values = session.scalars(
            select(AuditLog.new_values).where(AuditLog.action == "setup.complete")
        ).all()
    assert audit_values  # setup was audited...
    assert ADMIN_PASSWORD not in str(audit_values)  # ...without the password

    login = client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert login.status_code == 200


def test_setup_cannot_run_twice(fresh_install, client):
    assert client.post(COMPLETE, json=_payload()).status_code == 201
    second = client.post(
        COMPLETE, json=_payload(university_name="Hijacked", admin_email="attacker@example.com")
    )
    assert second.status_code == 409
    assert client.get("/api/v1/public/branding").json()["university_name"] == "Test University"


def test_weak_password_is_rejected_and_creates_nothing(fresh_install, client):
    response = client.post(COMPLETE, json=_payload(admin_password="short"))
    assert response.status_code == 422
    assert _nothing_was_created()


def test_invalid_colour_is_rejected(fresh_install, client):
    response = client.post(COMPLETE, json=_payload(primary_color="green"))
    assert response.status_code == 422
    assert _nothing_was_created()


def test_setup_code_format_and_tolerant_matching():
    code = expected_setup_code()
    assert re.fullmatch(r"[A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4}", code)
    assert verify_setup_code(code.lower())  # case does not matter
    assert verify_setup_code(code.replace("-", " "))  # dashes or spaces both fine
    assert not verify_setup_code("AAAA-BBBB-CCCC")

def test_blank_name_is_rejected(fresh_install, client):
    response = client.post(COMPLETE, json=_payload(admin_full_name="   "))
    assert response.status_code == 422
    assert _nothing_was_created()