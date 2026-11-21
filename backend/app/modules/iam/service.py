import uuid
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.audit import service as audit
from app.modules.iam.models import UserAccount, UserSession
from app.modules.iam.passwords import hash_password, verify_password
from app.modules.iam.tokens import csrf_for, generate_token, hash_token
from app.core.net import clean_ip

logger = logging.getLogger(__name__)

# Temporary constants: these become configurable in Settings later.
MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION = timedelta(minutes=15)
LAST_SEEN_UPDATE_INTERVAL = timedelta(seconds=60)

_dummy_hash: str | None = None


def _get_dummy_hash() -> str:
    """A throwaway hash, so unknown emails take as long to check as real ones."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("dummy-password-for-timing-only")
    return _dummy_hash


@dataclass
class LoginSuccess:
    user: UserAccount
    token: str


@dataclass
class AuthContext:
    user: UserAccount
    session: UserSession
    csrf_token: str


def login(
    db: Session,
    *,
    email: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
) -> LoginSuccess | None:
    """Try to log in. Returns None on any failure.

    This function never commits. The caller must commit in BOTH cases:
    failures also need to be saved (failure counter and audit record).
    """
    now = datetime.now(UTC)
    email = email.strip().lower()
    ip = clean_ip(ip_address)
    user = db.scalar(select(UserAccount).where(UserAccount.email == email))

    # Always do one password check, so timing doesn't reveal if the email exists.
    if user is None or user.password_hash is None:
        verify_password(password, _get_dummy_hash())
        password_ok, new_hash = False, None
    else:
        password_ok, new_hash = verify_password(password, user.password_hash)

    locked = user is not None and user.locked_until is not None and user.locked_until > now

    if user is None:
        reason = "unknown_account"
    elif locked:
        reason = "locked"
    elif not password_ok:
        reason = "wrong_password"
    elif user.status != "active":
        reason = "account_not_active"
    else:
        reason = None

    if reason is not None:
        if reason == "wrong_password":
            _count_failure(db, user, now)
        audit.record(
            db,
            action="auth.login.failed",
            module="iam",
            actor_id=user.id if user else None,
            entity_type="user_account",
            entity_id=str(user.id) if user else None,
            new_values={"email": email},
            reason=reason,
            ip_address=ip,
        )
        return None

    # Success
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    if new_hash:  # the stored hash used outdated settings: upgrade it
        user.password_hash = new_hash

    token = generate_token()
    db.add(
        UserSession(
            token_hash=hash_token(token),
            user_id=user.id,
            last_seen_at=now,
            expires_at=now + timedelta(hours=settings.session_absolute_hours),
            ip_address=ip,
            user_agent=(user_agent or "")[:300] or None,
        )
    )
    audit.record(
        db,
        action="auth.login.success",
        module="iam",
        actor_id=user.id,
        entity_type="user_account",
        entity_id=str(user.id),
        ip_address=ip,
    )
    return LoginSuccess(user=user, token=token)


def _count_failure(db: Session, user: UserAccount, now: datetime) -> None:
    """Add one failed attempt (atomically) and lock the account at the limit."""
    count = db.execute(
        update(UserAccount)
        .where(UserAccount.id == user.id)
        .values(failed_login_count=UserAccount.failed_login_count + 1)
        .returning(UserAccount.failed_login_count)
    ).scalar_one()

    if count >= MAX_FAILED_LOGINS:
        db.execute(
            update(UserAccount)
            .where(UserAccount.id == user.id)
            .values(failed_login_count=0, locked_until=now + LOCKOUT_DURATION)
        )
        audit.record(
            db,
            action="auth.account.locked",
            module="iam",
            actor_id=user.id,
            entity_type="user_account",
            entity_id=str(user.id),
            reason="too_many_failed_logins",
        )


def resolve_session(db: Session, token: str) -> AuthContext | None:
    """Find the live session and active user for a cookie token."""
    now = datetime.now(UTC)
    row = db.execute(
        select(UserSession, UserAccount)
        .join(UserAccount, UserAccount.id == UserSession.user_id)
        .where(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
            UserSession.last_seen_at > now - timedelta(minutes=settings.session_idle_minutes),
            UserAccount.status == "active",
        )
    ).first()
    if row is None:
        return None

    session, user = row
    if now - session.last_seen_at > LAST_SEEN_UPDATE_INTERVAL:
        session.last_seen_at = now
        db.commit()
    return AuthContext(user=user, session=session, csrf_token=csrf_for(token))


def logout(db: Session, ctx: AuthContext, ip_address: str | None) -> None:
    """End the session. Does not commit."""
    ctx.session.revoked_at = datetime.now(UTC)
    audit.record(
        db,
        action="auth.logout",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="user_account",
        entity_id=str(ctx.user.id),
        ip_address=clean_ip(ip_address),
    )

class AccountNotFound(Exception):
    pass


def unlock_account(
    db: Session, ctx: AuthContext, user_id: uuid.UUID, ip_address: str | None
) -> None:
    user = db.get(UserAccount, user_id)
    if user is None:
        raise AccountNotFound

    was_locked = user.locked_until is not None and user.locked_until > datetime.now(UTC)
    user.locked_until = None
    user.failed_login_count = 0
    audit.record(
        db,
        action="auth.account.unlocked",
        module="iam",
        actor_id=ctx.user.id,
        entity_type="user_account",
        entity_id=str(user.id),
        new_values={"was_locked": was_locked},
        ip_address=clean_ip(ip_address),
    )