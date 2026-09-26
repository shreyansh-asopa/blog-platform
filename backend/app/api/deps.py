from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Annotated

import jwt
from fastapi import Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, PermissionDeniedError, RateLimitedError
from app.core.rate_limit import RateLimiter
from app.core.security import decode_access_token
from app.integrations.moderation import Moderator
from app.integrations.storage import Storage
from app.models import User
from app.permissions import Permission, has_permission
from app.repositories.user_repository import UserRepository
from app.schemas.pagination import PageParams

# Reads "Authorization: Bearer <token>"; tokenUrl makes the /docs "Authorize" button work
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_sessionmaker(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.sessionmaker


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """One database session per request, closed when the request ends."""
    async with request.app.state.sessionmaker() as session:
        yield session


async def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    """The logged-in user, or None for a guest. A token that is sent but invalid is still a 401."""
    if token is None:
        return None
    try:
        user_id = decode_access_token(token, settings)
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid token") from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Invalid token")
    return user


async def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise AuthenticationError("Not authenticated")
    return user


def require_permission(
    permission: Permission,
) -> Callable[[User], Coroutine[None, None, User]]:
    """A dependency that lets a request through only if the user has `permission`.

    Usage: admin: Annotated[User, Depends(require_permission(Permission.MANAGE_USERS))]
    The role is read from the database on every request, not from the token, so a
    demoted admin loses access at once, even with a token issued before the change.
    """

    async def check(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not has_permission(user, permission):
            raise PermissionDeniedError("You don't have permission to do this")
        return user

    return check


def _enforce(request: Request, key: str, per_minute: int, message: str) -> None:
    limiter: RateLimiter = request.app.state.rate_limiter
    wait = limiter.hit(key, limit=per_minute, window=60)
    if wait is not None:
        raise RateLimitedError(message, retry_after=wait)


async def limit_login_attempts(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Slows down password guessing: a few attempts per minute per IP address and username.

    Keyed on both, so one person guessing can't lock others on the same network out.
    """
    ip = request.client.host if request.client else "unknown"
    _enforce(
        request,
        f"login:{ip}:{form.username.lower()}",
        settings.login_attempts_per_minute,
        "Too many login attempts, please wait a minute",
    )


async def limit_comments(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    _enforce(
        request,
        f"comment:{user.id}",
        settings.comments_per_minute,
        "You're commenting too fast, please wait a moment",
    )


def get_moderator(request: Request) -> Moderator:
    return request.app.state.moderator


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


def get_page_params(
    page: Annotated[int, Query(ge=1, description="Page number, starting at 1")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PageParams:
    return PageParams(page=page, size=size)


DbSession = Annotated[AsyncSession, Depends(get_db)]
SessionMaker = Annotated[async_sessionmaker[AsyncSession], Depends(get_sessionmaker)]
AppSettings = Annotated[Settings, Depends(get_settings)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
Pagination = Annotated[PageParams, Depends(get_page_params)]
ModeratorDep = Annotated[Moderator, Depends(get_moderator)]
StorageDep = Annotated[Storage, Depends(get_storage)]
