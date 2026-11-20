"""create audit schema and audit_log table

Revision ID: 44ed731c486d
Revises: 42fe81fc941f
Create Date: 2026-11-20 16:12:29.196925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import date


# revision identifiers, used by Alembic.
revision: str = '44ed731c486d'
down_revision: Union[str, Sequence[str], None] = '42fe81fc941f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    op.execute(
        """
        CREATE TABLE audit.audit_log (
            id uuid NOT NULL,
            occurred_at timestamptz NOT NULL DEFAULT now(),
            actor_id uuid,
            action text NOT NULL,
            module text NOT NULL,
            entity_type text,
            entity_id text,
            old_values jsonb,
            new_values jsonb,
            ip_address inet,
            request_id text,
            reason text,
            CONSTRAINT pk_audit_log PRIMARY KEY (id, occurred_at)
        ) PARTITION BY RANGE (occurred_at)
        """
    )

    # Safety net: catches any row that has no monthly partition.
    op.execute("CREATE TABLE audit.audit_log_default PARTITION OF audit.audit_log DEFAULT")

    # Monthly partitions: the current month and the next 23.
    today = date.today()
    year, month = today.year, today.month
    for _ in range(24):
        next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
        op.execute(
            f"CREATE TABLE audit.audit_log_y{year}m{month:02d} "
            f"PARTITION OF audit.audit_log "
            f"FOR VALUES FROM ('{year}-{month:02d}-01 00:00:00+00') "
            f"TO ('{next_year}-{next_month:02d}-01 00:00:00+00')"
        )
        year, month = next_year, next_month

    op.execute(
        "CREATE INDEX ix_audit_log_entity "
        "ON audit.audit_log (entity_type, entity_id, occurred_at)"
    )
    op.execute(
        "CREATE INDEX ix_audit_log_actor ON audit.audit_log (actor_id, occurred_at)"
    )

    # Append-only: reject every UPDATE and DELETE.
    op.execute(
        """
        CREATE FUNCTION audit.forbid_change() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_append_only
        BEFORE UPDATE OR DELETE ON audit.audit_log
        FOR EACH ROW EXECUTE FUNCTION audit.forbid_change()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE audit.audit_log")  # also drops all partitions
    op.execute("DROP FUNCTION audit.forbid_change()")
    op.execute("DROP SCHEMA audit")
