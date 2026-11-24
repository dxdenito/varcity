"""user types and session elevation

Revision ID: a9c3d5e7f102
Revises: f2a7c4d1e8b3
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a9c3d5e7f102"
down_revision: Union[str, Sequence[str], None] = "f2a7c4d1e8b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("role", sa.Column("category", sa.Text(), nullable=True), schema="iam")
    op.add_column(
        "role",
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        schema="iam",
    )
    op.add_column(
        "user_session",
        sa.Column("elevated_until", sa.DateTime(timezone=True), nullable=True),
        schema="iam",
    )


def downgrade() -> None:
    op.drop_column("user_session", "elevated_until", schema="iam")
    op.drop_column("role", "is_active", schema="iam")
    op.drop_column("role", "category", schema="iam")