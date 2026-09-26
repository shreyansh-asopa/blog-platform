import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email_or_username(self, identifier: str) -> User | None:
        """Look up a user by either field, as typed into the login form."""
        query = select(User).where(
            or_(User.email == identifier.lower(), User.username == identifier)
        )
        return await self.session.scalar(query)

    async def email_or_username_taken(self, email: str, username: str) -> tuple[bool, bool]:
        query = select(User.email, User.username).where(
            or_(User.email == email, User.username == username)
        )
        rows = (await self.session.execute(query)).all()
        return (
            any(row.email == email for row in rows),
            any(row.username == username for row in rows),
        )

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
