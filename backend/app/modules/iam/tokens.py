import hashlib
import hmac
import secrets

from app.core.config import settings


def generate_token() -> str:
    """A random 256-bit session token (this is what goes in the cookie)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """What we store in the database instead of the token itself."""
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_for(token: str) -> str:
    """CSRF token for a session: an HMAC of the session token with our secret.

    It cannot be guessed without the secret, and it is tied to one session.
    """
    return hmac.new(settings.secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()