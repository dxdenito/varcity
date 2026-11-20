import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.iam.models import UserAccount


def test_new_account_gets_safe_defaults(db):
    user = UserAccount(email="new.user@example.com")
    db.add(user)
    db.flush()
    db.refresh(user)

    assert user.id is not None
    assert user.status == "active"
    assert user.is_superuser is False
    assert user.failed_login_count == 0
    assert user.password_hash is None


def test_duplicate_email_is_rejected(db):
    db.add(UserAccount(email="same@example.com"))
    db.flush()
    db.add(UserAccount(email="same@example.com"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_email_must_be_stored_lowercase(db):
    db.add(UserAccount(email="Mixed.Case@Example.com"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_invalid_status_is_rejected(db):
    db.add(UserAccount(email="status@example.com", status="banana"))
    with pytest.raises(IntegrityError):
        db.flush()