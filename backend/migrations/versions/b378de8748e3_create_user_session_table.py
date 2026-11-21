"""create user_session table

Revision ID: b378de8748e3
Revises: f9b92ad52841
Create Date: 2026-11-21 09:46:26.829489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b378de8748e3'
down_revision: Union[str, Sequence[str], None] = 'f9b92ad52841'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["iam.user_account.id"],
            name=op.f("fk_user_session_user_id_user_account"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_session")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_user_session_token_hash")),
        schema="iam",
    )
    op.create_index("ix_user_session_user_id", "user_session", ["user_id"], schema="iam")
    op.create_index("ix_user_session_expires_at", "user_session", ["expires_at"], schema="iam")


def downgrade() -> None:
    op.drop_table("user_session", schema="iam")