import uuid

import pytest
from sqlalchemy import delete

from app.core.db import SessionLocal
from app.core.ids import new_id
from app.modules.org.models import Node, NodeType


@pytest.fixture
def two_nodes():
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


def test_listing_the_tree_needs_the_view_permission(signed_in, grant):
    client = signed_in()
    assert client.get("/api/v1/org/nodes").status_code == 403
    grant(client.user, "org.node.view")
    assert client.get("/api/v1/org/nodes").status_code == 200


def test_node_scoped_grant_limits_updates_to_its_subtree(signed_in, two_nodes, grant):
    first, second = two_nodes
    client = signed_in()
    grant(client.user, "org.node.update", node_id=first)
    renamed = {"name": "Renamed"}
    assert client.patch(f"/api/v1/org/nodes/{first}", json=renamed).status_code == 200
    assert client.patch(f"/api/v1/org/nodes/{second}", json=renamed).status_code == 403


def test_settings_view_does_not_allow_changes(signed_in, grant):
    client = signed_in()
    grant(client.user, "settings.general.view")
    current = client.get("/api/v1/settings/general")
    assert current.status_code == 200
    assert client.put("/api/v1/settings/general", json=current.json()).status_code == 403