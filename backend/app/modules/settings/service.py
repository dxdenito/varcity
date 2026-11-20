import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.modules.settings.branding import build_palette, readable_text_color
from app.modules.settings.models import AppSetting
from app.modules.settings.schemas import BrandingColors, BrandingConfig, BrandingPublic

logger = logging.getLogger(__name__)

BRANDING_KEY = "branding"


def get_branding(db: Session) -> BrandingPublic:
    """Return the public branding, falling back to defaults if needed."""
    config = BrandingConfig()
    row = db.get(AppSetting, BRANDING_KEY)
    if row is not None:
        try:
            config = BrandingConfig.model_validate(row.value)
        except ValidationError:
            logger.warning("Stored branding is invalid; using defaults")

    return BrandingPublic(
        university_name=config.university_name,
        short_name=config.short_name,
        logo_url=config.logo_url,
        show_powered_by=config.show_powered_by,
        colors=BrandingColors(
            primary=build_palette(config.primary_color),
            on_primary=readable_text_color(config.primary_color),
            sidebar=config.sidebar_color.lower(),
            on_sidebar=readable_text_color(config.sidebar_color),
        ),
    )