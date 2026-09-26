from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AppSettings, DbSession, limit_login_attempts
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DbSession, settings: AppSettings) -> UserRead:
    user = await AuthService(db, settings).register(data)
    return UserRead.model_validate(user)


@router.post("/login", dependencies=[Depends(limit_login_attempts)])
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
    settings: AppSettings,
) -> Token:
    """Standard OAuth2 password form. The `username` field accepts a username or an email."""
    return await AuthService(db, settings).login(form.username, form.password)
