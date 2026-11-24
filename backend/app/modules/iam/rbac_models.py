import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.core.ids import new_id

WINDOW_RULE = "valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from"


class Permission(Base):
    """A permission declared in code and synced to the database at startup."""

    __tablename__ = "permission"
    __table_args__ = (
        CheckConstraint(
            "risk IN ('normal', 'sensitive', 'critical')", name="risk_valid"
        ),
        {"schema": "iam"},
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    module: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'normal'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Role(Base):
    """A named set of permissions. Starter roles carry a stable system_key."""

    __tablename__ = "role"
    __table_args__ = {"schema": "iam"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    system_key: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    grants_all: Mapped[bool] = mapped_column(
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


class RolePermission(Base):
    __tablename__ = "role_permission"
    __table_args__ = {"schema": "iam"}

    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("iam.role.id", ondelete="CASCADE"), primary_key=True
    )
    permission_code: Mapped[str] = mapped_column(
        Text, ForeignKey("iam.permission.code", ondelete="CASCADE"), primary_key=True
    )


class RoleAssignment(Base):
    """A user holding a role, university-wide (node_id empty) or at a node, within a window."""

    __tablename__ = "role_assignment"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "node_id",
            name="uq_role_assignment_scope",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(WINDOW_RULE, name="window_valid"),
        Index("ix_role_assignment_user_id", "user_id"),
        Index("ix_role_assignment_node_id", "node_id"),
        {"schema": "iam"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("iam.user_account.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("iam.role.id"), nullable=False
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("org.node.id"), nullable=True
    )
    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    granted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserPermission(Base):
    """A permission granted to one user directly, at a scope, within a window."""

    __tablename__ = "user_permission"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "permission_code",
            "node_id",
            name="uq_user_permission_scope",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(WINDOW_RULE, name="window_valid"),
        Index("ix_user_permission_user_id", "user_id"),
        Index("ix_user_permission_node_id", "node_id"),
        {"schema": "iam"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("iam.user_account.id", ondelete="CASCADE"), nullable=False
    )
    permission_code: Mapped[str] = mapped_column(
        Text, ForeignKey("iam.permission.code", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("org.node.id"), nullable=True
    )
    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    granted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )