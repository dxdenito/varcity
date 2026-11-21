import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.core.ids import new_id


class NodeType(Base):
    """A level of the organization tree, named by the university (College, Campus...)."""

    __tablename__ = "node_type"
    __table_args__ = {"schema": "org"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    plural_name: Mapped[str] = mapped_column(Text, nullable=False)
    is_campus: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )


class NodeTypeParent(Base):
    """Which level types may sit directly under which."""

    __tablename__ = "node_type_parent"
    __table_args__ = {"schema": "org"}

    type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("org.node_type.id", ondelete="CASCADE"), primary_key=True
    )
    parent_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("org.node_type.id", ondelete="CASCADE"), primary_key=True
    )


class Node(Base):
    """An actual entry of the tree, such as Main Campus or School of Computing."""

    __tablename__ = "node"
    __table_args__ = (
        UniqueConstraint("type_id", "code", name="uq_node_type_id_code"),
        CheckConstraint("status IN ('active', 'archived')", name="status_valid"),
        Index("ix_node_parent_id", "parent_id"),
        Index("ix_node_path", "path", postgresql_ops={"path": "text_pattern_ops"}),
        {"schema": "org"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("org.node_type.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("org.node.id"), nullable=True
    )
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    code_locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )