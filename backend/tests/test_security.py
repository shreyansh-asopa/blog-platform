from app.core.security import hash_password, verify_password


def test_hash_is_argon2_and_not_the_password():
    hashed = hash_password("correct-horse-battery")

    assert hashed.startswith("$argon2id$")
    assert "correct-horse-battery" not in hashed


def test_same_password_hashes_differently_each_time():
    # A random salt per hash: identical passwords don't produce identical hashes
    assert hash_password("same") != hash_password("same")


def test_verify_password():
    hashed = hash_password("correct-horse-battery")

    assert verify_password("correct-horse-battery", hashed) is True
    assert verify_password("wrong", hashed) is False
