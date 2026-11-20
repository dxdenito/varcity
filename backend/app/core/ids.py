import uuid


def new_id() -> uuid.UUID:
    """Generate a new time-ordered (version 7) UUID for primary keys."""
    return uuid.uuid7()