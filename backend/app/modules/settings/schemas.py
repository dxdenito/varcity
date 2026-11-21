from pydantic import BaseModel, Field

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


class BrandingConfig(BaseModel):
    """The university profile as stored under the key 'branding'."""

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


class BrandingColors(BaseModel):
    primary: dict[str, str]
    on_primary: str
    sidebar: str
    on_sidebar: str


class BrandingPublic(BaseModel):
    """What the public endpoint returns."""

    university_name: str
    short_name: str
    motto: str | None
    logo_url: str | None
    show_powered_by: bool
    colors: BrandingColors