"""create settings schema and app_setting table

Revision ID: 42fe81fc941f
Revises: 
Create Date: 2026-11-20 16:04:01.970626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '42fe81fc941f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS settings")
    op.create_table(
        "app_setting",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_app_setting")),
        schema="settings",
    )


def downgrade() -> None:
    op.drop_table("app_setting", schema="settings")
    op.execute("DROP SCHEMA IF EXISTS settings")