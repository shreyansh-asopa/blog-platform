from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.integrations.moderation import Moderator
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.pagination import PageParams

# Reads "Authorization: Bearer <token>"; tokenUrl makes the /docs "Authorize" button work
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


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


def get_moderator(request: Request) -> Moderator:
    return request.app.state.moderator


def get_page_params(
    page: Annotated[int, Query(ge=1, description="Page number, starting at 1")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PageParams:
    return PageParams(page=page, size=size)


DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
Pagination = Annotated[PageParams, Depends(get_page_params)]
ModeratorDep = Annotated[Moderator, Depends(get_moderator)]
