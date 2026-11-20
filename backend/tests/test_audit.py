import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.db import SessionLocal
from app.modules.audit import service as audit
from app.modules.audit.models import AuditLog
from app.modules.audit.service import redact
from app.modules.settings.models import AppSetting


def _unique() -> str:
    return f"test.{uuid.uuid4()}"


def _audit_count(entity_id: str) -> int:
    """Count audit rows using a brand-new session (sees only committed data)."""
    with SessionLocal() as session:
        rows = session.scalars(select(AuditLog).where(AuditLog.entity_id == entity_id))
        return len(rows.all())


def _setting_exists(key: str) -> bool:
    with SessionLocal() as session:
        return session.get(AppSetting, key) is not None


def test_business_change_and_audit_are_committed_together(db):
    key = _unique()
    db.add(AppSetting(key=key, value={"theme": "blue"}))
    audit.record(
        db,
        action="settings.create",
        module="settings",
        entity_type="app_setting",
        entity_id=key,
        new_values={"theme": "blue"},
    )
    db.commit()

    assert _setting_exists(key)
    assert _audit_count(key) == 1


def test_rollback_discards_both_the_change_and_its_audit(db):
    key = _unique()
    db.add(AppSetting(key=key, value={"theme": "blue"}))
    audit.record(
        db,
        action="settings.create",
        module="settings",
        entity_type="app_setting",
        entity_id=key,
    )
    db.flush()  # written inside the transaction, but not committed
    db.rollback()

    assert not _setting_exists(key)
    assert _audit_count(key) == 0


def test_secrets_are_redacted_before_storage(db):
    marker = _unique()
    audit.record(
        db,
        action="user.create",
        module="iam",
        entity_id=marker,
        new_values={"username": "alice", "password": "hunter2"},
    )
    db.flush()

    stored = db.execute(
        select(AuditLog.new_values).where(AuditLog.entity_id == marker)
    ).scalar_one()
    assert stored == {"username": "alice", "password": "[REDACTED]"}


def test_redact_hides_sensitive_keys_at_any_depth_without_mutating_input():
    original = {
        "username": "alice",
        "Password": "x",
        "profile": {"api_token": "t"},
        "items": [{"otp_code": "123456"}],
    }
    result = redact(original)

    assert result == {
        "username": "alice",
        "Password": "[REDACTED]",
        "profile": {"api_token": "[REDACTED]"},
        "items": [{"otp_code": "[REDACTED]"}],
    }
    assert original["Password"] == "x"  # the caller's data is untouched


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit.audit_log SET module = 'changed'",
        "DELETE FROM audit.audit_log",
    ],
)
def test_audit_log_is_append_only(db, statement):
    audit.record(db, action="test.action", module="test", entity_id=_unique())
    db.flush()

    with pytest.raises(DBAPIError, match="append-only"):
        db.execute(text(statement))