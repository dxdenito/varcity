import uuid
from datetime import datetime

from pydantic import BaseModel


class AssignmentOut(BaseModel):
    id: uuid.UUID
    role_id: uuid.UUID
    role_name: str
    node_id: uuid.UUID | None
    node_name: str | None


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