"""create rbac tables

Revision ID: c4d1a7e92b60
Revises: 93a84b4065bf
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d1a7e92b60"
down_revision: Union[str, Sequence[str], None] = "93a84b4065bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permission",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("module", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("code", name="pk_permission"),
        schema="iam",
    )
    op.create_table(
        "role",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("system_key", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "grants_all", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_role"),
        sa.UniqueConstraint("system_key", name="uq_role_system_key"),
        sa.UniqueConstraint("name", name="uq_role_name"),
        schema="iam",
    )
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_code", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["iam.role.id"],
            name="fk_role_permission_role_id_role",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_code"],
            ["iam.permission.code"],
            name="fk_role_permission_permission_code_permission",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_code", name="pk_role_permission"),
        schema="iam",
    )
    op.create_table(
        "role_assignment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.Uuid(), nullable=True),
        sa.Column("granted_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["iam.user_account.id"],
            name="fk_role_assignment_user_id_user_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["iam.role.id"], name="fk_role_assignment_role_id_role"
        ),
        sa.ForeignKeyConstraint(
            ["node_id"], ["org.node.id"], name="fk_role_assignment_node_id_node"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_id"],
            ["iam.user_account.id"],
            name="fk_role_assignment_granted_by_id_user_account",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_role_assignment"),
        sa.UniqueConstraint(
            "user_id",
            "role_id",
            "node_id",
            name="uq_role_assignment_scope",
            postgresql_nulls_not_distinct=True,
        ),
        schema="iam",
    )
    op.create_index(
        "ix_role_assignment_user_id", "role_assignment", ["user_id"], schema="iam"
    )
    op.create_index(
        "ix_role_assignment_node_id", "role_assignment", ["node_id"], schema="iam"
    )


def downgrade() -> None:
    op.drop_table("role_assignment", schema="iam")
    op.drop_table("role_permission", schema="iam")
    op.drop_table("role", schema="iam")
    op.drop_table("permission", schema="iam")