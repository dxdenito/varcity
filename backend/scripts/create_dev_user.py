"""Development helper: create a super administrator account.

Temporary. The first-run setup wizard replaces this.
"""

import getpass
import sys
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.db import SessionLocal
from app.modules.audit import service as audit
from app.modules.iam.models import UserAccount
from app.modules.iam.passwords import WeakPasswordError, hash_password, validate_password


def main() -> None:
    email = input("Email: ").strip().lower()
    password = getpass.getpass("Password (hidden while typing): ")
    try:
        validate_password(password, email=email)
    except WeakPasswordError as error:
        sys.exit(str(error))

    with SessionLocal() as db:
        if db.scalar(select(UserAccount).where(UserAccount.email == email)):
            sys.exit("An account with that email already exists.")
        user = UserAccount(
            email=email,
            password_hash=hash_password(password),
            is_superuser=True,
            password_changed_at=datetime.now(UTC),
        )
        db.add(user)
        db.flush()
        audit.record(
            db,
            action="user.create",
            module="iam",
            entity_type="user_account",
            entity_id=str(user.id),
            new_values={"email": email, "is_superuser": True},
            reason="development helper script",
        )
        db.commit()
    print(f"Created {email}")


if __name__ == "__main__":
    main()