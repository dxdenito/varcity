"""assignment windows and user permissions

Revision ID: f2a7c4d1e8b3
Revises: e1f4a8c27b90
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2a7c4d1e8b3"
down_revision: Union[str, Sequence[str], None] = "e1f4a8c27b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

WINDOW_RULE = "valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from"


def upgrade() -> None:
    op.add_column(
        "role_assignment",
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        schema="iam",
    )
    op.add_column(
        "role_assignment",
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        schema="iam",
    )
    op.add_column(
        "role_assignment",
        sa.Column("reason", sa.Text(), nullable=True),
        schema="iam",
    )
    op.create_check_constraint(
        op.f("ck_role_assignment_window_valid"),
        "role_assignment",
        WINDOW_RULE,
        schema="iam",
    )

    op.create_table(
        "user_permission",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("permission_code", sa.Text(), nullable=False),
        sa.Column("node_id", sa.Uuid(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
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
            name="fk_user_permission_user_id_user_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_code"],
            ["iam.permission.code"],
            name="fk_user_permission_permission_code_permission",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["node_id"], ["org.node.id"], name="fk_user_permission_node_id_node"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_id"],
            ["iam.user_account.id"],
            name="fk_user_permission_granted_by_id_user_account",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_permission"),
        sa.UniqueConstraint(
            "user_id",
            "permission_code",
            "node_id",
            name="uq_user_permission_scope",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint(WINDOW_RULE, name=op.f("ck_user_permission_window_valid")),
        schema="iam",
    )
    op.create_index(
        "ix_user_permission_user_id", "user_permission", ["user_id"], schema="iam"
    )
    op.create_index(
        "ix_user_permission_node_id", "user_permission", ["node_id"], schema="iam"
    )


def downgrade() -> None:
    op.drop_table("user_permission", schema="iam")
    op.drop_constraint(
        op.f("ck_role_assignment_window_valid"),
        "role_assignment",
        schema="iam",
        type_="check",
    )
    op.drop_column("role_assignment", "reason", schema="iam")
    op.drop_column("role_assignment", "valid_until", schema="iam")
    op.drop_column("role_assignment", "valid_from", schema="iam")