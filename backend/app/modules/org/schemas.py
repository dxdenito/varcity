import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

CODE_PATTERN = r"^[A-Za-z0-9]{1,20}$"

NodeName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class InitializeRequest(BaseModel):
    template: Literal["college", "faculty"]
    institution_code: str = Field(pattern=CODE_PATTERN)


class NodeTypeOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    plural_name: str
    is_campus: bool
    allowed_parent_type_ids: list[uuid.UUID]


class NodeCreate(BaseModel):
    type_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    code: str | None = Field(default=None, pattern=CODE_PATTERN)
    name: NodeName


class NodeUpdate(BaseModel):
    code: str | None = Field(default=None, pattern=CODE_PATTERN)
    name: NodeName | None = None


class NodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type_id: uuid.UUID
    parent_id: uuid.UUID | None
    code: str | None
    name: str
    status: str
    code_locked: bool

class NodeMove(BaseModel):
    new_parent_id: uuid.UUID