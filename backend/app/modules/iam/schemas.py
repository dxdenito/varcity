import uuid

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=1000)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    is_superuser: bool


class AuthResponse(BaseModel):
    user: UserPublic
    csrf_token: str