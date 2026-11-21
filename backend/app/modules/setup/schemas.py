from pydantic import BaseModel, EmailStr, Field

from app.modules.iam.passwords import MAX_PASSWORD_LENGTH
from app.modules.settings.schemas import HEX_COLOR


class SetupStatus(BaseModel):
    setup_required: bool


class SetupRequest(BaseModel):
    setup_code: str = Field(max_length=64)
    university_name: str = Field(min_length=1, max_length=120)
    short_name: str = Field(min_length=1, max_length=40)
    primary_color: str = Field(pattern=HEX_COLOR)
    sidebar_color: str = Field(pattern=HEX_COLOR)
    admin_email: EmailStr
    admin_password: str = Field(max_length=MAX_PASSWORD_LENGTH + 100)