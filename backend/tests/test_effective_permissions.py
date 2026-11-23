import uuid

from fastapi.testclient import TestClient

from app.core.ids import new_id
from app.main import app
from app.modules.iam.access import Access
from app.modules.iam.models import UserAccount
from app.modules.iam.rbac_models import Role, RoleAssignment
from app.modules.org.models import Node, NodeType

ME = "/api/v1/auth/me"


def test_user_without_roles_has_no_permissions(signed_in):
    permissions = signed_in().get(ME).json()["permissions"]
    assert permissions == {"all": False, "everywhere": [], "scoped": {}}


def test_university_wide_grant_is_listed_as_everywhere(signed_in, grant):
    client = signed_in()
    grant(client.user, "org.node.view")
    permissions = client.get(ME).json()["permissions"]
    assert permissions["all"] is False
    assert permissions["everywhere"] == ["org.node.view"]


def test_superuser_has_all_permissions(signed_in):
    assert signed_in(is_superuser=True).get(ME).json()["permissions"]["all"] is True


def test_login_response_includes_permissions(make_user):
    user = make_user(is_superuser=True)
    response = TestClient(app).post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "a-long-test-passphrase"},
    )
    assert response.json()["permissions"]["all"] is True


def _node(db):
    node_type = NodeType(
        code=f"t{uuid.uuid4().hex[:8]}", name="Level", plural_name="Levels"
    )
    db.add(node_type)
    db.flush()
    node_id = new_id()
    node = Node(
        id=node_id, type_id=node_type.id, name="Node", path=f"/{node_id}/"
    )
    db.add(node)
    db.flush()
    return node


def _assign(db, user, system_key, node=None):
    role = db.query(Role).filter(Role.system_key == system_key).one()
    db.add(
        RoleAssignment(
            user_id=user["id"], role_id=role.id, node_id=node.id if node else None
        )
    )
    db.flush()


def _effective(db, user):
    return Access.load(db, db.get(UserAccount, user["id"])).effective()


def test_node_scoped_grants_are_listed_by_permission(db, make_user):
    user = make_user()
    college = _node(db)
    _assign(db, user, "dean", college)
    summary = _effective(db, user)
    assert summary["all"] is False
    assert summary["everywhere"] == []
    assert summary["scoped"]["org.node.update"] == [college.id]
    assert "org.node.move" not in summary["scoped"]


def test_super_admin_role_at_a_node_lists_every_permission_there(db, make_user):
    user = make_user()
    college = _node(db)
    _assign(db, user, "super_admin", college)
    summary = _effective(db, user)
    assert summary["all"] is False
    assert summary["scoped"]["org.node.move"] == [college.id]


def test_super_admin_role_university_wide_means_all(db, make_user):
    user = make_user()
    _assign(db, user, "super_admin")
    assert _effective(db, user)["all"] is True