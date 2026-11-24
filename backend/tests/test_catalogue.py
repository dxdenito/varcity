import pytest

from app.modules.iam import registry
from app.modules.iam.rbac_models import Permission

TREE = "/api/v1/admin/permission-tree"


def test_tree_needs_the_view_permission(signed_in, grant):
    client = signed_in()
    assert client.get(TREE).status_code == 403
    grant(client.user, "iam.role.view")
    assert client.get(TREE).status_code == 200


def test_tree_groups_permissions_with_labels_and_risk(signed_in):
    admin = signed_in(is_superuser=True)
    groups = {group["module"]: group for group in admin.get(TREE).json()}

    org = groups["org"]
    assert org["label"] == "Organization"
    node = next(r for r in org["resources"] if r["resource"] == "node")
    assert node["label"] == "Organization structure"
    permissions = {p["code"]: p for p in node["permissions"]}
    assert permissions["org.node.view"]["action"] == "view"
    assert permissions["org.node.delete"]["risk"] == "sensitive"

    codes = {
        p["code"]: p
        for resource in groups["iam"]["resources"]
        for p in resource["permissions"]
    }
    assert codes["iam.role.manage"]["risk"] == "critical"


def test_risk_is_stored_with_the_permission(db):
    assert db.get(Permission, "iam.user.assign_role").risk == "critical"
    assert db.get(Permission, "org.node.view").risk == "normal"


@pytest.fixture
def empty_registry(monkeypatch):
    monkeypatch.setattr(registry, "_registry", {})


def test_unknown_actions_and_risks_are_rejected(empty_registry):
    with pytest.raises(ValueError):
        registry.declare(registry.Permission("test.item.edit", "Edit"))
    with pytest.raises(ValueError):
        registry.declare(
            registry.Permission("test.item.update", "Update", risk="severe")
        )
    registry.declare(registry.Permission("test.item.update", "Update", risk="critical"))