import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, LargeBinary, Text, Uuid, func
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
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class Asset(Base):
    """A small uploaded file, such as the university logo."""

    __tablename__ = "asset"
    __table_args__ = {"schema": "settings"}

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)