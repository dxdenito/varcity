import base64
import hashlib
import hmac

from app.core.config import settings


def _expected_raw() -> str:
    digest = hmac.new(
        settings.secret_key.encode(), b"varcity-setup-code", hashlib.sha256
    ).digest()
    return base64.b32encode(digest)[:12].decode()  # letters A-Z and digits 2-7


def expected_setup_code() -> str:
    """The code shown in the server console, e.g. ABCD-EFGH-IJKL."""
    raw = _expected_raw()
    return "-".join(raw[i : i + 4] for i in range(0, 12, 4))


def verify_setup_code(candidate: str) -> bool:
    normalized = candidate.replace("-", "").replace(" ", "").upper()
    return hmac.compare_digest(normalized.encode(), _expected_raw().encode())