import uuid

from pydantic import BaseModel, ConfigDict, Field


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    module: str
    description: str


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_system: bool
    grants_all: bool
    permissions: list[str]
    assignment_count: int


class RoleIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=300)
    permissions: list[str] = Field(default_factory=list, max_length=500)