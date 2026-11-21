import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Point the whole application at the TEST database, before anything from
# the app is imported. Environment variables take priority over .env.
_test_url = os.environ.get("VARCITY_TEST_DATABASE_URL") or dotenv_values(
    BACKEND_DIR / ".env"
).get("VARCITY_TEST_DATABASE_URL")

if not _test_url:
    raise RuntimeError("Set VARCITY_TEST_DATABASE_URL in backend/.env")

# Safety guard: the test run wipes and rebuilds this database.
if not _test_url.rsplit("/", 1)[-1].split("?")[0].endswith("_test"):
    raise RuntimeError("The test database name must end with '_test'")

os.environ["VARCITY_DATABASE_URL"] = _test_url
os.environ["VARCITY_SECRET_KEY"] = "test-only-secret-key-not-for-real-use-0123456789"


@pytest.fixture(scope="session", autouse=True)
def database():
    """Rebuild the test database from migrations once per test run."""
    from alembic import command
    from alembic.config import Config

    from app.core.db import engine

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield
    engine.dispose()


@pytest.fixture
def db():
    """A database session. Anything not committed is rolled back after the test."""
    from app.core.db import SessionLocal

    with SessionLocal() as session:
        yield session
        session.rollback()

@pytest.fixture
def make_user():
    import uuid

    from sqlalchemy import delete

    from app.core.db import SessionLocal
    from app.modules.iam.models import UserAccount
    from app.modules.iam.passwords import hash_password

    created = []

    def _make(*, is_superuser=False):
        email = f"{uuid.uuid4()}@example.com"
        with SessionLocal() as session:
            account = UserAccount(
                email=email,
                password_hash=hash_password("a-long-test-passphrase"),
                full_name="Test User",
                is_superuser=is_superuser,
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
def signed_in(make_user):
    from fastapi.testclient import TestClient

    from app.main import app

    def _sign_in(*, is_superuser=False):
        user = make_user(is_superuser=is_superuser)
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": "a-long-test-passphrase"},
        )
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        return client

    return _sign_in