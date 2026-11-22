from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


class BrandingConfig(BaseModel):
    university_name: str = Field("Your University", min_length=1, max_length=120)
    short_name: str = Field("University", min_length=1, max_length=40)
    motto: str | None = Field(None, max_length=200)
    address: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=200, pattern=r"^https?://\S+$")
    primary_color: str = Field("#1d4ed8", pattern=HEX_COLOR)
    sidebar_color: str = Field("#0f2557", pattern=HEX_COLOR)
    show_powered_by: bool = True


class UniversityProfile(BrandingConfig):
    logo_url: str | None = None


class GeneralConfig(BaseModel):
    timezone: str = "Africa/Nairobi"
    date_format: Literal["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD", "D MMM YYYY"] = "DD/MM/YYYY"

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Unknown time zone.")
        return value


class BrandingColors(BaseModel):
    primary: dict[str, str]
    on_primary: str
    sidebar: str
    on_sidebar: str


class BrandingPublic(BaseModel):
    university_name: str
    short_name: str
    motto: str | None
    logo_url: str | None
    show_powered_by: bool
    timezone: str
    date_format: str
    colors: BrandingColors