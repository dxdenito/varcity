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
os.environ["VARCITY_SESSION_IDLE_MINUTES"] = "30"
os.environ["VARCITY_SESSION_ABSOLUTE_HOURS"] = "12"


@pytest.fixture(scope="session", autouse=True)
def database():
    """Rebuild the test database from migrations once per test run."""
    from alembic import command
    from alembic.config import Config

    import app.modules.all_permissions  # noqa: F401
    from app.core.db import SessionLocal, engine
    from app.modules.iam.access import sync_registry

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    with SessionLocal() as session:
        sync_registry(session)
        session.commit()
    yield
    engine.dispose()


@pytest.fixture
def db(make_user):
    """A database session. Anything not committed is rolled back after the test.

    Requesting make_user makes this session roll back before test users are deleted.
    """
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

    def _sign_in(*, is_superuser=False, elevated=True):
        user = make_user(is_superuser=is_superuser)
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": "a-long-test-passphrase"},
        )
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        client.user = user
        if elevated:
            client.post(
                "/api/v1/auth/reauth", json={"password": "a-long-test-passphrase"}
            )
        return client

    return _sign_in


@pytest.fixture
def grant():
    """Give a user a throwaway role holding one permission, optionally at a node."""
    import uuid

    from sqlalchemy import delete

    from app.core.db import SessionLocal
    from app.modules.iam.rbac_models import Role, RoleAssignment, RolePermission

    role_ids = []

    def _grant(user, code, node_id=None):
        with SessionLocal() as session:
            role = Role(name=f"Test role {uuid.uuid4()}")
            session.add(role)
            session.flush()
            session.add(RolePermission(role_id=role.id, permission_code=code))
            session.add(
                RoleAssignment(user_id=user["id"], role_id=role.id, node_id=node_id)
            )
            session.commit()
            role_ids.append(role.id)

    yield _grant
    with SessionLocal() as session:
        session.execute(
            delete(RoleAssignment).where(RoleAssignment.role_id.in_(role_ids))
        )
        session.execute(delete(Role).where(Role.id.in_(role_ids)))
        session.commit()


@pytest.fixture
def role_name():
    import uuid

    from sqlalchemy import delete

    from app.core.db import SessionLocal
    from app.modules.iam.rbac_models import Role

    names = []

    def _name():
        name = f"Test {uuid.uuid4().hex[:10]}"
        names.append(name)
        return name

    yield _name
    with SessionLocal() as session:
        session.execute(delete(Role).where(Role.name.in_(names)))
        session.commit()


@pytest.fixture
def two_nodes():
    import uuid

    from sqlalchemy import delete

    from app.core.db import SessionLocal
    from app.core.ids import new_id
    from app.modules.org.models import Node, NodeType

    with SessionLocal() as session:
        node_type = NodeType(
            code=f"t{uuid.uuid4().hex[:8]}", name="Level", plural_name="Levels"
        )
        session.add(node_type)
        session.flush()
        ids = []
        for _ in range(2):
            node_id = new_id()
            session.add(
                Node(
                    id=node_id,
                    type_id=node_type.id,
                    name="Original",
                    path=f"/{node_id}/",
                )
            )
            ids.append(node_id)
        type_id = node_type.id
        session.commit()
    yield ids
    with SessionLocal() as session:
        session.execute(delete(Node).where(Node.id.in_(ids)))
        session.execute(delete(NodeType).where(NodeType.id == type_id))
        session.commit()