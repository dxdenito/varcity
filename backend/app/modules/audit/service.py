import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog

# Any key containing one of these fragments has its value hidden.
SENSITIVE_FRAGMENTS = ("password", "secret", "token", "otp", "api_key", "private_key")


def redact(value: Any) -> Any:
    """Return a copy of value with sensitive fields replaced by a marker."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if any(fragment in str(key).lower() for fragment in SENSITIVE_FRAGMENTS)
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def record(
    db: Session,
    *,
    action: str,
    module: str,
    actor_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    old_values: Any | None = None,
    new_values: Any | None = None,
    reason: str | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
) -> AuditLog:
    """Add an audit entry to the caller's transaction.

    This function never commits. The audit row is saved or rolled back
    together with the business change it describes.
    """
    entry = AuditLog(
        action=action,
        module=module,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=redact(old_values) if old_values is not None else None,
        new_values=redact(new_values) if new_values is not None else None,
        reason=reason,
        ip_address=ip_address,
        request_id=request_id,
    )
    db.add(entry)
    return entry