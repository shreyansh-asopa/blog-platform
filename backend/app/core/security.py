import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import Settings

password_hash = PasswordHash((Argon2Hasher(),))

# Checked against when a login names an unknown user, so that request takes as long
# as a real one and response timing doesn't reveal which accounts exist
DUMMY_HASH = password_hash.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expires = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    claims = {"sub": str(user_id), "role": role, "iat": now, "exp": expires}
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> uuid.UUID:
    """Return the user id from a valid token. Raises jwt.InvalidTokenError otherwise."""
    claims = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "exp"]},
    )
    try:
        return uuid.UUID(claims["sub"])
    except ValueError as exc:
        raise jwt.InvalidTokenError("sub is not a user id") from exc
