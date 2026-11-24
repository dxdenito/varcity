import uuid

import pytest

from app.core.ids import new_id
from app.modules.iam import registry
from app.modules.iam.access import Access, sync_registry
from app.modules.iam.rbac_models import (
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
)
from app.modules.iam.models import UserAccount
from app.modules.org.models import Node, NodeType

VIEW = "test.item.view"
EDIT = "test.item.update"


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    monkeypatch.setattr(registry, "_registry", {})
    registry.declare(
        registry.Permission(VIEW, "View items", roles=("dean", "lecturer")),
        registry.Permission(EDIT, "Edit items", roles=("dean",)),
    )


def role_named(db, key):
    return db.query(Role).filter(Role.system_key == key).one()


def load(db, user):
    return Access.load(db, db.get(UserAccount, user["id"]))


def assign(db, user, role, node=None):
    db.add(
        RoleAssignment(
            user_id=user["id"], role_id=role.id, node_id=node.id if node else None
        )
    )
    db.flush()


@pytest.fixture
def make_node(db):
    node_type = NodeType(
        code=f"t{uuid.uuid4().hex[:8]}", name="Level", plural_name="Levels"
    )
    db.add(node_type)
    db.flush()

    def _make(parent=None):
        node_id = new_id()
        prefix = parent.path if parent else "/"
        node = Node(
            id=node_id,
            type_id=node_type.id,
            parent_id=parent.id if parent else None,
            name="Node",
            path=f"{prefix}{node_id}/",
        )
        db.add(node)
        db.flush()
        return node

    return _make


def test_sync_creates_starter_roles_and_default_grants(db):
    sync_registry(db)
    dean_codes = {
        rp.permission_code
        for rp in db.query(RolePermission).filter_by(role_id=role_named(db, "dean").id)
    }
    lecturer_codes = {
        rp.permission_code
        for rp in db.query(RolePermission).filter_by(
            role_id=role_named(db, "lecturer").id
        )
    }
    assert {VIEW, EDIT} <= dean_codes
    assert VIEW in lecturer_codes and EDIT not in lecturer_codes
    assert role_named(db, "super_admin").grants_all is True
    assert role_named(db, "auditor").grants_all is False


def test_sync_does_not_regrant_a_permission_an_admin_removed(db):
    sync_registry(db)
    dean = role_named(db, "dean")
    db.query(RolePermission).filter_by(role_id=dean.id, permission_code=EDIT).delete()
    db.flush()
    sync_registry(db)
    assert (
        db.query(RolePermission)
        .filter_by(role_id=dean.id, permission_code=EDIT)
        .count()
        == 0
    )


def test_sync_updates_changed_description(db):
    sync_registry(db)
    registry._registry[VIEW] = registry.Permission(VIEW, "Changed", roles=("dean",))
    sync_registry(db)
    assert db.get(Permission, VIEW).description == "Changed"


def test_no_assignment_means_no_access(db, make_user):
    sync_registry(db)
    access = load(db, make_user())
    assert not access.can(VIEW)
    assert not access.can_anywhere(VIEW)
    assert access.scope(VIEW).everywhere is False
    assert access.scope(VIEW).paths == ()


def test_university_wide_assignment_covers_everything(db, make_user, make_node):
    sync_registry(db)
    user = make_user()
    assign(db, user, role_named(db, "dean"))
    access = load(db, user)
    node = make_node()
    assert access.can(VIEW)
    assert access.can(VIEW, node.path)
    assert access.can_on_node(EDIT, node.id)
    assert access.scope(VIEW).everywhere is True


def test_node_assignment_covers_only_its_subtree(db, make_user, make_node):
    sync_registry(db)
    user = make_user()
    college = make_node()
    department = make_node(college)
    other_college = make_node()
    assign(db, user, role_named(db, "dean"), college)
    access = load(db, user)
    assert access.can(VIEW, college.path)
    assert access.can(EDIT, department.path)
    assert access.can_on_node(EDIT, department.id)
    assert not access.can(EDIT, other_college.path)
    assert not access.can_on_node(EDIT, other_college.id)
    assert not access.can(EDIT)
    assert access.can_anywhere(EDIT)
    scope = access.scope(EDIT)
    assert scope.everywhere is False and scope.paths == (college.path,)


def test_role_without_the_permission_is_denied(db, make_user, make_node):
    sync_registry(db)
    user = make_user()
    college = make_node()
    assign(db, user, role_named(db, "lecturer"), college)
    access = load(db, user)
    assert access.can(VIEW, college.path)
    assert not access.can(EDIT, college.path)
    assert not access.can_anywhere(EDIT)


def test_permissions_from_several_assignments_combine(db, make_user, make_node):
    sync_registry(db)
    user = make_user()
    first = make_node()
    second = make_node()
    assign(db, user, role_named(db, "dean"), first)
    assign(db, user, role_named(db, "lecturer"), second)
    access = load(db, user)
    assert access.can(EDIT, first.path)
    assert access.can(VIEW, second.path)
    assert not access.can(EDIT, second.path)
    assert set(access.scope(VIEW).paths) == {first.path, second.path}


def test_grants_all_role_includes_unlisted_permissions(db, make_user):
    sync_registry(db)
    user = make_user()
    assign(db, user, role_named(db, "super_admin"))
    assert load(db, user).can("anything.at.all")


def test_superuser_flag_bypasses_checks(db, make_user):
    access = load(db, make_user(is_superuser=True))
    assert access.can("anything.at.all")
    assert access.scope("anything.at.all").everywhere is True