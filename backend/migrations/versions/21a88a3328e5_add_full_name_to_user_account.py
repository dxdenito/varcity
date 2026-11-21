"""add full_name to user_account

Revision ID: 21a88a3328e5
Revises: b378de8748e3
Create Date: 2026-11-21 11:21:10.129175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21a88a3328e5'
down_revision: Union[str, Sequence[str], None] = 'b378de8748e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_account", sa.Column("full_name", sa.Text(), nullable=True), schema="iam")


def downgrade() -> None:
    op.drop_column("user_account", "full_name", schema="iam")
