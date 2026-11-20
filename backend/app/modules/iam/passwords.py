from pwdlib import PasswordHash

# Argon2id with the library's recommended parameters.
_hasher = PasswordHash.recommended()

# Temporary constants: these become configurable in Settings later.
MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128  # also stops people sending huge inputs to the hasher


class WeakPasswordError(ValueError):
    """The password does not satisfy the password policy."""


def validate_password(password: str, *, email: str | None = None) -> None:
    """Raise WeakPasswordError if the password breaks the policy."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise WeakPasswordError(
            f"Password must be at most {MAX_PASSWORD_LENGTH} characters long."
        )
    if email and password.lower() == email.lower():
        raise WeakPasswordError("Password must not be the same as the email address.")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Check a password.

    Returns (is_valid, new_hash). If new_hash is not None, the stored hash
    uses outdated settings and should be replaced with new_hash.
    """
    return _hasher.verify_and_update(password, password_hash)