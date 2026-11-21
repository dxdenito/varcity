"""optional node code and settings asset table

Revision ID: 93a84b4065bf
Revises: 86e9b22e2dd8
Create Date: 2026-11-21 21:09:21.746302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93a84b4065bf'
down_revision: Union[str, Sequence[str], None] = '86e9b22e2dd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("node", "code", existing_type=sa.Text(), nullable=True, schema="org")
    op.create_table(
        "asset",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_asset")),
        schema="settings",
    )


def downgrade() -> None:
    op.drop_table("asset", schema="settings")
    op.execute(
        "UPDATE org.node SET code = 'N' || substr(replace(id::text, '-', ''), 1, 12) "
        "WHERE code IS NULL"
    )
    op.alter_column("node", "code", existing_type=sa.Text(), nullable=False, schema="org")