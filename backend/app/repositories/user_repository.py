import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.repositories.pagination import paginate
from app.schemas.pagination import PageParams


def username_is(username: str):
    """Usernames match ignoring case. Written as lower(username) so it uses the unique index."""
    return func.lower(User.username) == username.lower()


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        return await self.session.scalar(select(User).where(username_is(username)))

    async def get_by_email_or_username(self, identifier: str) -> User | None:
        """Look up a user by either field, as typed into the login form."""
        query = select(User).where(or_(User.email == identifier.lower(), username_is(identifier)))
        return await self.session.scalar(query)

    async def email_or_username_taken(self, email: str, username: str) -> tuple[bool, bool]:
        query = select(User.email, User.username).where(
            or_(User.email == email, username_is(username))
        )
        rows = (await self.session.execute(query)).all()
        return (
            any(row.email == email for row in rows),
            any(row.username.lower() == username.lower() for row in rows),
        )

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def list(
        self, params: PageParams, search: str | None = None, role: UserRole | None = None
    ) -> tuple[list[User], int]:
        """Newest accounts first. `search` matches part of a username or email, any case."""
        query = select(User)
        if search := (search or "").strip():
            # % and _ are wildcards in LIKE; escaped, so "a_b" finds exactly "a_b"
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            query = query.where(
                or_(
                    User.username.ilike(pattern, escape="\\"),
                    User.email.ilike(pattern, escape="\\"),
                )
            )
        if role is not None:
            query = query.where(User.role == role)
        return await paginate(self.session, query, params, User.created_at.desc(), User.id)
