from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.modules.iam.passwords import MAX_PASSWORD_LENGTH
from app.modules.settings.schemas import HEX_COLOR


def _text(max_length: int):
    """Text that is trimmed and must not be empty."""
    return Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=max_length)
    ]


class SetupStatus(BaseModel):
    setup_required: bool


class SetupRequest(BaseModel):
    setup_code: str = Field(max_length=64)
    university_name: _text(120)
    short_name: _text(40)
    primary_color: str = Field(pattern=HEX_COLOR)
    sidebar_color: str = Field(pattern=HEX_COLOR)
    admin_full_name: _text(200)
    admin_email: EmailStr
    admin_password: str = Field(max_length=MAX_PASSWORD_LENGTH + 100)