import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update

from app.core.db import SessionLocal
from app.main import app
from app.modules.org.models import Node, NodeType, NodeTypeParent

INITIALIZE, TYPES, NODES = "/api/v1/org/initialize", "/api/v1/org/node-types", "/api/v1/org/nodes"


def _wipe():
    with SessionLocal() as session:
        session.execute(delete(Node))
        session.execute(delete(NodeTypeParent))
        session.execute(delete(NodeType))
        session.commit()


@pytest.fixture
def clean_org():
    _wipe()
    yield
    _wipe()


@pytest.fixture
def admin(signed_in):
    return signed_in(is_superuser=True)


def _initialize(client, template="college", code="ku"):
    return client.post(INITIALIZE, json={"template": template, "institution_code": code})


def _tree(client):
    types = {t["code"]: t["id"] for t in client.get(TYPES).json()}
    root = client.get(NODES).json()[0]
    return types, root


def _create(client, types, type_code, parent, code, name="Test"):
    return client.post(
        NODES,
        json={
            "type_id": types[type_code],
            "parent_id": parent["id"] if parent else None,
            "code": code,
            "name": name,
        },
    )


def test_initialize_creates_the_levels_and_the_top_entry(clean_org, admin):
    assert _initialize(admin).status_code == 201

    types, root = _tree(admin)
    assert set(types) == {"university", "campus", "college", "school", "department"}
    assert root["code"] == "KU"
    assert root["parent_id"] is None
    assert _initialize(admin).status_code == 409


def test_faculty_template_uses_faculty_as_the_level_name(clean_org, admin):
    _initialize(admin, template="faculty")
    names = {t["code"]: t["name"] for t in admin.get(TYPES).json()}
    assert names["faculty"] == "Faculty"
    assert "college" not in names


def test_entries_follow_the_allowed_levels(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)

    campus = _create(admin, types, "campus", root, "main").json()
    college = _create(admin, types, "college", campus, "eng").json()
    assert _create(admin, types, "department", college, "cs").status_code == 201
    assert _create(admin, types, "department", campus, "bad").status_code == 422


def test_only_one_top_level_entry_is_allowed(clean_org, admin):
    _initialize(admin)
    types, _ = _tree(admin)
    assert _create(admin, types, "university", None, "other").status_code == 422


def test_codes_are_unique_per_level_ignoring_case(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)
    assert _create(admin, types, "campus", root, "c001").status_code == 201
    assert _create(admin, types, "campus", root, "C001").status_code == 409


def test_code_can_change_until_it_is_locked(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)
    campus = _create(admin, types, "campus", root, "c001").json()

    response = admin.patch(f"{NODES}/{campus['id']}", json={"code": "c002", "name": "Nairobi"})
    assert response.status_code == 200
    assert response.json()["code"] == "C002"

    with SessionLocal() as session:
        session.execute(update(Node).where(Node.code == "C002").values(code_locked=True))
        session.commit()
    assert admin.patch(f"{NODES}/{campus['id']}", json={"code": "c003"}).status_code == 409
    assert admin.patch(f"{NODES}/{campus['id']}", json={"name": "Renamed"}).status_code == 200


def test_delete_is_refused_while_something_depends_on_the_entry(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)
    campus = _create(admin, types, "campus", root, "c001").json()
    college = _create(admin, types, "college", campus, "eng").json()

    blocked = admin.delete(f"{NODES}/{campus['id']}")
    assert blocked.status_code == 409
    assert "still contains" in blocked.json()["detail"]
    assert admin.delete(f"{NODES}/{root['id']}").status_code == 409

    assert admin.delete(f"{NODES}/{college['id']}").status_code == 204
    assert admin.delete(f"{NODES}/{campus['id']}").status_code == 204


def test_an_entry_with_a_used_code_cannot_be_deleted(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)
    campus = _create(admin, types, "campus", root, "c001").json()
    with SessionLocal() as session:
        session.execute(update(Node).where(Node.code == "C001").values(code_locked=True))
        session.commit()

    response = admin.delete(f"{NODES}/{campus['id']}")
    assert response.status_code == 409
    assert "already been used" in response.json()["detail"]


def test_structure_access_follows_permissions(clean_org, admin, signed_in, grant):
    _initialize(admin)
    types, root = _tree(admin)
    regular = signed_in()
    body = {"type_id": types["campus"], "parent_id": root["id"], "code": "x1", "name": "X"}

    assert regular.get(NODES).status_code == 403
    grant(regular.user, "org.node.view")
    assert regular.get(NODES).status_code == 200
    assert regular.post(NODES, json=body).status_code == 403
    assert TestClient(app).get(NODES).status_code == 401

def _paths():
    with SessionLocal() as session:
        return {n.code: n.path for n in session.scalars(select(Node))}


def test_moving_an_entry_moves_everything_under_it(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)
    main = _create(admin, types, "campus", root, "main").json()
    other = _create(admin, types, "campus", root, "other").json()
    college = _create(admin, types, "college", main, "eng").json()
    _create(admin, types, "department", college, "cs")

    response = admin.post(f"{NODES}/{college['id']}/move", json={"new_parent_id": other["id"]})
    assert response.status_code == 200
    assert response.json()["parent_id"] == other["id"]

    paths = _paths()
    assert paths["ENG"].startswith(paths["OTHER"])
    assert paths["CS"].startswith(paths["ENG"])
    assert not paths["CS"].startswith(paths["MAIN"])


def test_invalid_moves_are_refused(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)
    main = _create(admin, types, "campus", root, "main").json()
    college = _create(admin, types, "college", main, "eng").json()
    dept = _create(admin, types, "department", college, "cs").json()
    other = _create(admin, types, "campus", root, "other").json()

    def move(node, parent):
        return admin.post(f"{NODES}/{node['id']}/move", json={"new_parent_id": parent["id"]})

    assert move(college, dept).status_code == 422  # inside its own subtree
    assert move(dept, other).status_code == 422  # a department cannot sit under a campus
    assert move(root, other).status_code == 422  # the top-level entry never moves
    assert move(college, main).status_code == 422  # already there


def test_archive_needs_dependents_dealt_with_first(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)
    campus = _create(admin, types, "campus", root, "main").json()
    college = _create(admin, types, "college", campus, "eng").json()

    blocked = admin.post(f"{NODES}/{campus['id']}/archive")
    assert blocked.status_code == 409
    assert "still contains" in blocked.json()["detail"]

    assert admin.post(f"{NODES}/{college['id']}/archive").json()["status"] == "archived"
    assert admin.post(f"{NODES}/{campus['id']}/archive").json()["status"] == "archived"
    assert admin.post(f"{NODES}/{college['id']}/unarchive").status_code == 409

    assert admin.post(f"{NODES}/{campus['id']}/unarchive").json()["status"] == "active"
    assert admin.post(f"{NODES}/{college['id']}/unarchive").json()["status"] == "active"
    assert admin.post(f"{NODES}/{root['id']}/archive").status_code == 422

def test_codes_are_optional_and_can_be_cleared(clean_org, admin):
    _initialize(admin)
    types, root = _tree(admin)

    first = _create(admin, types, "campus", root, None, "Main Campus").json()
    second = _create(admin, types, "campus", root, None, "Satellite").json()
    assert first["code"] is None and second["code"] is None

    url = f"{NODES}/{second['id']}"
    assert admin.patch(url, json={"code": "c001"}).json()["code"] == "C001"
    assert admin.patch(url, json={"code": None}).json()["code"] is None

    admin.patch(url, json={"code": "c001"})
    with SessionLocal() as session:
        session.execute(update(Node).where(Node.code == "C001").values(code_locked=True))
        session.commit()
    assert admin.patch(url, json={"code": None}).status_code == 409