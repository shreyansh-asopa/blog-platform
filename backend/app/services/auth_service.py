from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token
from app.schemas.user import UserCreate

# Same message for "no such user" and "wrong password", so attackers can't probe for accounts
INVALID_CREDENTIALS = "Incorrect email/username or password"


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)

    async def register(self, data: UserCreate) -> User:
        email_taken, username_taken = await self.users.email_or_username_taken(
            data.email, data.username
        )
        if email_taken:
            raise ConflictError("Email is already registered")
        if username_taken:
            raise ConflictError("Username is already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        try:
            await self.users.add(user)
            await self.session.commit()
        except IntegrityError as exc:
            # Two sign-ups with the same email at the same moment: the database has the final say
            await self.session.rollback()
            raise ConflictError("Email or username is already taken") from exc
        await self.session.refresh(user)
        return user

    async def login(self, identifier: str, password: str) -> Token:
        user = await self.users.get_by_email_or_username(identifier)
        if user is None:
            verify_password(password, DUMMY_HASH)
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        token = create_access_token(user.id, user.role.value, self.settings)
        return Token(access_token=token)
