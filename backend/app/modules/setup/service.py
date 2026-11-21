import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.net import clean_ip
from app.modules.audit import service as audit
from app.modules.iam.models import UserAccount
from app.modules.iam.passwords import hash_password, validate_password
from app.modules.settings.models import AppSetting
from app.modules.settings.schemas import BrandingConfig
from app.modules.setup.code import expected_setup_code, verify_setup_code
from app.modules.setup.schemas import SetupRequest

logger = logging.getLogger(__name__)

SETUP_KEY = "setup"
BRANDING_KEY = "branding"


class SetupAlreadyDone(Exception):
    pass


class InvalidSetupCode(Exception):
    pass


class AccountAlreadyExists(Exception):
    pass


def is_setup_required(db: Session) -> bool:
    return db.get(AppSetting, SETUP_KEY) is None


def complete_setup(db: Session, payload: SetupRequest, ip_address: str | None) -> None:
    """Do the whole first-time setup. Never commits; the caller does.

    Raises SetupAlreadyDone, InvalidSetupCode, AccountAlreadyExists or
    WeakPasswordError. An IntegrityError means a concurrent setup won the race.
    """
    ip = clean_ip(ip_address)

    if not is_setup_required(db):
        raise SetupAlreadyDone

    if not verify_setup_code(payload.setup_code):
        audit.record(db, action="setup.code.invalid", module="setup", ip_address=ip)
        raise InvalidSetupCode

    email = str(payload.admin_email).strip().lower()
    validate_password(payload.admin_password, email=email)

    now = datetime.now(UTC)

    # Claim the setup row first. If another request is running setup right now,
    # this blocks until it finishes and then fails: setup can only succeed once.
    db.add(
        AppSetting(
            key=SETUP_KEY,
            value={"completed_at": now.isoformat(), "app_version": settings.version},
        )
    )
    db.flush()

    if db.scalar(select(UserAccount.id).where(UserAccount.email == email)):
        raise AccountAlreadyExists

    admin = UserAccount(
        full_name=payload.admin_full_name,
        email=email,
        password_hash=hash_password(payload.admin_password),
        status="active",
        is_superuser=True,
        password_changed_at=now,
    )
    db.add(admin)
    db.flush()

    branding = BrandingConfig(
        university_name=payload.university_name.strip(),
        short_name=payload.short_name.strip(),
        primary_color=payload.primary_color,
        sidebar_color=payload.sidebar_color,
    )
    db.merge(
        AppSetting(key=BRANDING_KEY, value=branding.model_dump(), updated_by=admin.id)
    )

    audit.record(
        db,
        action="setup.complete",
        module="setup",
        actor_id=admin.id,
        entity_type="installation",
        new_values={"branding": branding.model_dump(), "admin_email": email},
        ip_address=ip,
    )


def announce_setup_code_if_needed() -> None:
    """At startup: if setup is still pending, print the setup code to the console."""
    try:
        with SessionLocal() as db:
            required = is_setup_required(db)
    except Exception:
        logger.warning("Could not check the setup state at startup", exc_info=True)
        return

    if not required:
        return

    line = "=" * 64
    print(
        f"\n{line}\n"
        " VARCITY FIRST-RUN SETUP REQUIRED\n"
        " Open the application in your browser and enter this setup code:\n\n"
        f"     {expected_setup_code()}\n\n"
        " The code stops working as soon as setup is complete.\n"
        f"{line}\n",
        flush=True,
    )