import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Text, Uuid, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.core.ids import new_id


class AuditLog(Base):
    """One immutable record of something that happened in the system.

    The table is partitioned by month on occurred_at. Rows can never be
    updated or deleted (enforced by a database trigger).
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        # "Show me the history of this record"
        Index("ix_audit_log_entity", "entity_type", "entity_id", "occurred_at"),
        # "Show me what this user did"
        Index("ix_audit_log_actor", "actor_id", "occurred_at"),
        {"schema": "audit", "postgresql_partition_by": "RANGE (occurred_at)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    # Part of the primary key because it is the partition key.
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, server_default=func.now()
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_values: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    request_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)