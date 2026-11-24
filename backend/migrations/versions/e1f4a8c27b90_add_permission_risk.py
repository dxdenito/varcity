"""add permission risk

Revision ID: e1f4a8c27b90
Revises: c4d1a7e92b60
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f4a8c27b90"
down_revision: Union[str, Sequence[str], None] = "c4d1a7e92b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "permission",
        sa.Column(
            "risk", sa.Text(), server_default=sa.text("'normal'"), nullable=False
        ),
        schema="iam",
    )
    op.create_check_constraint(
        op.f("ck_permission_risk_valid"),
        "permission",
        "risk IN ('normal', 'sensitive', 'critical')",
        schema="iam",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_permission_risk_valid"), "permission", schema="iam", type_="check"
    )
    op.drop_column("permission", "risk", schema="iam")