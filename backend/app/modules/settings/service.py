import hashlib
import logging
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam.service import AuthContext
from app.modules.settings.branding import build_palette, readable_text_color
from app.modules.settings.models import AppSetting, Asset
from app.modules.settings.schemas import (
    BrandingColors,
    BrandingConfig,
    BrandingPublic,
    UniversityProfile,
    GeneralConfig,
)

logger = logging.getLogger(__name__)

BRANDING_KEY = "branding"
LOGO_KEY = "logo"
GENERAL_KEY = "general"
MAX_LOGO_BYTES = 512 * 1024


class InvalidLogo(ValueError):
    pass


def _load_config(db: Session) -> BrandingConfig:
    row = db.get(AppSetting, BRANDING_KEY)
    if row is not None:
        try:
            return BrandingConfig.model_validate(row.value)
        except ValidationError:
            logger.warning("Stored branding is invalid; using defaults")
    return BrandingConfig()

def _load_general(db: Session) -> GeneralConfig:
    row = db.get(AppSetting, GENERAL_KEY)
    if row is not None:
        try:
            return GeneralConfig.model_validate(row.value)
        except ValidationError:
            logger.warning("Stored general settings are invalid; using defaults")
    return GeneralConfig()


def get_general(db: Session) -> GeneralConfig:
    return _load_general(db)


def update_general(
    db: Session, ctx: AuthContext, config: GeneralConfig, ip_address: str | None
) -> None:
    old = _load_general(db)
    row = db.get(AppSetting, GENERAL_KEY)
    if row is None:
        db.add(AppSetting(key=GENERAL_KEY, value=config.model_dump(), updated_by=ctx.user.id))
    else:
        row.value = config.model_dump()
        row.updated_by = ctx.user.id
        row.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action="settings.general.update",
        module="settings",
        actor_id=ctx.user.id,
        entity_type="app_setting",
        entity_id=GENERAL_KEY,
        old_values=old.model_dump(),
        new_values=config.model_dump(),
        ip_address=clean_ip(ip_address),
    )

def _logo_url(db: Session) -> str | None:
    digest = db.scalar(select(Asset.sha256).where(Asset.key == LOGO_KEY))
    return f"/api/v1/public/branding/logo?v={digest[:12]}" if digest else None


def get_branding(db: Session) -> BrandingPublic:
    config = _load_config(db)
    general = _load_general(db)
    return BrandingPublic(
        university_name=config.university_name,
        short_name=config.short_name,
        motto=config.motto,
        logo_url=_logo_url(db),
        show_powered_by=config.show_powered_by,
        timezone=general.timezone,
        date_format=general.date_format,
        colors=BrandingColors(
            primary=build_palette(config.primary_color),
            on_primary=readable_text_color(config.primary_color),
            sidebar=config.sidebar_color.lower(),
            on_sidebar=readable_text_color(config.sidebar_color),
        ),
    )


def get_university_profile(db: Session) -> UniversityProfile:
    return UniversityProfile(**_load_config(db).model_dump(), logo_url=_logo_url(db))


def update_university_profile(
    db: Session, ctx: AuthContext, config: BrandingConfig, ip_address: str | None
) -> None:
    old = _load_config(db)
    row = db.get(AppSetting, BRANDING_KEY)
    if row is None:
        db.add(AppSetting(key=BRANDING_KEY, value=config.model_dump(), updated_by=ctx.user.id))
    else:
        row.value = config.model_dump()
        row.updated_by = ctx.user.id
        row.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action="settings.university.update",
        module="settings",
        actor_id=ctx.user.id,
        entity_type="app_setting",
        entity_id=BRANDING_KEY,
        old_values=old.model_dump(),
        new_values=config.model_dump(),
        ip_address=clean_ip(ip_address),
    )


def _detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def set_logo(db: Session, ctx: AuthContext, data: bytes, ip_address: str | None) -> None:
    if not data:
        raise InvalidLogo("The file is empty.")
    if len(data) > MAX_LOGO_BYTES:
        raise InvalidLogo("The logo must be 512 KB or smaller.")
    content_type = _detect_image_type(data)
    if content_type is None:
        raise InvalidLogo("The logo must be a PNG, JPEG or WebP image.")

    digest = hashlib.sha256(data).hexdigest()
    asset = db.get(Asset, LOGO_KEY)
    if asset is None:
        db.add(
            Asset(
                key=LOGO_KEY,
                content_type=content_type,
                data=data,
                sha256=digest,
                updated_by=ctx.user.id,
            )
        )
    else:
        asset.content_type = content_type
        asset.data = data
        asset.sha256 = digest
        asset.updated_by = ctx.user.id
        asset.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action="settings.logo.update",
        module="settings",
        actor_id=ctx.user.id,
        entity_type="asset",
        entity_id=LOGO_KEY,
        new_values={"content_type": content_type, "size": len(data), "sha256": digest},
        ip_address=clean_ip(ip_address),
    )


def remove_logo(db: Session, ctx: AuthContext, ip_address: str | None) -> None:
    asset = db.get(Asset, LOGO_KEY)
    if asset is None:
        return
    db.delete(asset)
    audit.record(
        db,
        action="settings.logo.remove",
        module="settings",
        actor_id=ctx.user.id,
        entity_type="asset",
        entity_id=LOGO_KEY,
        ip_address=clean_ip(ip_address),
    )


def get_logo(db: Session) -> Asset | None:
    return db.get(Asset, LOGO_KEY)