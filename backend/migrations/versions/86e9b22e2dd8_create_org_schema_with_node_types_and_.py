"""create org schema with node types and nodes

Revision ID: 86e9b22e2dd8
Revises: 21a88a3328e5
Create Date: 2026-11-21 15:12:30.262361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86e9b22e2dd8'
down_revision: Union[str, Sequence[str], None] = '21a88a3328e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS org")

    op.create_table(
        "node_type",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("plural_name", sa.Text(), nullable=False),
        sa.Column("is_campus", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_node_type")),
        sa.UniqueConstraint("code", name=op.f("uq_node_type_code")),
        schema="org",
    )

    op.create_table(
        "node_type_parent",
        sa.Column("type_id", sa.Uuid(), nullable=False),
        sa.Column("parent_type_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["org.node_type.id"],
            name=op.f("fk_node_type_parent_type_id_node_type"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_type_id"],
            ["org.node_type.id"],
            name=op.f("fk_node_type_parent_parent_type_id_node_type"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("type_id", "parent_type_id", name=op.f("pk_node_type_parent")),
        schema="org",
    )

    op.create_table(
        "node",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("code_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('active', 'archived')", name=op.f("ck_node_status_valid")),
        sa.ForeignKeyConstraint(["type_id"], ["org.node_type.id"], name=op.f("fk_node_type_id_node_type")),
        sa.ForeignKeyConstraint(["parent_id"], ["org.node.id"], name=op.f("fk_node_parent_id_node")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_node")),
        sa.UniqueConstraint("type_id", "code", name="uq_node_type_id_code"),
        schema="org",
    )
    op.create_index("ix_node_parent_id", "node", ["parent_id"], schema="org")
    op.create_index(
        "ix_node_path", "node", ["path"], schema="org", postgresql_ops={"path": "text_pattern_ops"}
    )


def downgrade() -> None:
    op.drop_table("node", schema="org")
    op.drop_table("node_type_parent", schema="org")
    op.drop_table("node_type", schema="org")
    op.execute("DROP SCHEMA IF EXISTS org")