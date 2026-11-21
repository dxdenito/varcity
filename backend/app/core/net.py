import ipaddress


def clean_ip(value: str | None) -> str | None:
    """Return a valid IP address string, or None (safe to store in an INET column)."""
    try:
        return str(ipaddress.ip_address(value)) if value else None
    except ValueError:
        return None