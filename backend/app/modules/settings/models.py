import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class AppSetting(Base):
    """A single configuration value, identified by a unique key."""

    __tablename__ = "app_setting"
    __table_args__ = {"schema": "settings"}

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Will reference the users table once it exists.
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)