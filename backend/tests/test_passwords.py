import pytest

from app.modules.iam.passwords import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    WeakPasswordError,
    hash_password,
    validate_password,
    verify_password,
)


def test_hash_uses_argon2id_and_is_salted():
    first = hash_password("correct horse battery")
    second = hash_password("correct horse battery")
    assert first.startswith("$argon2id$")
    assert first != second  # a random salt makes every hash different


def test_verify_accepts_the_right_password_and_rejects_the_wrong_one():
    stored = hash_password("correct horse battery")

    valid, _ = verify_password("correct horse battery", stored)
    assert valid is True

    valid, _ = verify_password("wrong password!!", stored)
    assert valid is False


def test_a_good_password_passes_the_policy():
    validate_password("a-long-enough-passphrase", email="user@example.com")


@pytest.mark.parametrize(
    "password",
    [
        "x" * (MIN_PASSWORD_LENGTH - 1),
        "x" * (MAX_PASSWORD_LENGTH + 1),
    ],
)
def test_length_limits_are_enforced(password):
    with pytest.raises(WeakPasswordError):
        validate_password(password)


def test_password_may_not_equal_the_email():
    with pytest.raises(WeakPasswordError):
        validate_password("Admin@University.ac.ke", email="admin@university.ac.ke")