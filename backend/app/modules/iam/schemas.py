import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=1000)


class ReauthRequest(BaseModel):
    password: str = Field(max_length=1000)


class ReauthResponse(BaseModel):
    elevated_until: datetime


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    is_superuser: bool


class PermissionSummary(BaseModel):
    all: bool
    everywhere: list[str]
    scoped: dict[str, list[uuid.UUID]]


class AuthResponse(BaseModel):
    user: UserPublic
    csrf_token: str
    permissions: PermissionSummary