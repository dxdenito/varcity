import uuid

from pydantic import BaseModel, ConfigDict, Field


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    module: str
    description: str
    risk: str


class PermissionLeaf(BaseModel):
    code: str
    action: str
    description: str
    risk: str


class ResourceNode(BaseModel):
    resource: str
    label: str
    permissions: list[PermissionLeaf]


class GroupNode(BaseModel):
    module: str
    label: str
    resources: list[ResourceNode]


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: str | None
    is_system: bool
    is_active: bool
    grants_all: bool
    permissions: list[str]
    assignment_count: int


class RoleIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=300)
    category: str | None = Field(default=None, max_length=80)
    is_active: bool = True
    permissions: list[str] = Field(default_factory=list, max_length=500)


class DuplicateIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)