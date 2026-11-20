from pydantic import BaseModel, Field

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


class BrandingConfig(BaseModel):
    """What is stored in the database under the key 'branding'."""

    university_name: str = Field("Your University", min_length=1, max_length=120)
    short_name: str = Field("University", min_length=1, max_length=40)
    primary_color: str = Field("#1d4ed8", pattern=HEX_COLOR)
    sidebar_color: str = Field("#0f2557", pattern=HEX_COLOR)
    logo_url: str | None = None
    show_powered_by: bool = True


class BrandingColors(BaseModel):
    primary: dict[str, str]  # shades "50" ... "950"
    on_primary: str  # readable text colour on the primary colour
    sidebar: str
    on_sidebar: str


class BrandingPublic(BaseModel):
    """What the public endpoint returns."""

    university_name: str
    short_name: str
    logo_url: str | None
    show_powered_by: bool
    colors: BrandingColors