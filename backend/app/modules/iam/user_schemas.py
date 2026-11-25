import uuid
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, Field


class AssignmentOut(BaseModel):
    id: uuid.UUID
    role_id: uuid.UUID
    role_name: str
    node_id: uuid.UUID | None
    node_name: str | None
    valid_from: datetime | None
    valid_until: datetime | None
    reason: str | None
    state: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    status: str
    is_superuser: bool
    is_locked: bool
    last_login_at: datetime | None
    assignments: list[AssignmentOut]


class UserPage(BaseModel):
    items: list[UserOut]
    total: int


class AssignIn(BaseModel):
    role_id: uuid.UUID
    node_id: uuid.UUID | None = None
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    reason: str | None = Field(default=None, max_length=300)


class GrantIn(BaseModel):
    permission: str = Field(min_length=1, max_length=100)
    node_id: uuid.UUID | None = None
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    reason: str | None = Field(default=None, max_length=300)


class GrantOut(BaseModel):
    id: uuid.UUID
    permission: str
    node_id: uuid.UUID | None
    node_name: str | None
    valid_from: datetime | None
    valid_until: datetime | None
    reason: str | None
    state: str


class SourceOut(BaseModel):
    kind: str
    label: str
    node_id: uuid.UUID | None
    node_name: str | None


class AccessOut(BaseModel):
    assignments: list[AssignmentOut]
    grants: list[GrantOut]
    permissions: dict[str, list[SourceOut]]


class ExplainSource(BaseModel):
    kind: str
    label: str
    scope: str
    state: str
    valid_until: datetime | None


class ExplainOut(BaseModel):
    permission: str
    scope: str
    allowed: bool
    granted_by: list[ExplainSource]
    held_elsewhere: list[ExplainSource]
    inactive: list[ExplainSource]



class AssignmentAdd(BaseModel):
    role_id: uuid.UUID
    node_id: uuid.UUID | None = None
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    reason: str | None = Field(default=None, max_length=300)


class AssignmentChange(BaseModel):
    id: uuid.UUID
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    reason: str | None = Field(default=None, max_length=300)


class AccessChanges(BaseModel):
    add_assignments: list[AssignmentAdd] = Field(default_factory=list, max_length=100)
    update_assignments: list[AssignmentChange] = Field(default_factory=list, max_length=100)
    remove_assignments: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    add_grants: list[GrantIn] = Field(default_factory=list, max_length=200)
    remove_grants: list[uuid.UUID] = Field(default_factory=list, max_length=200)


class ReviewItem(BaseModel):
    kind: str
    action: str
    label: str
    scope: str


class ReviewOut(BaseModel):
    items: list[ReviewItem]
    sensitive: list[str]
    critical: list[str]
    requires_confirmation: bool