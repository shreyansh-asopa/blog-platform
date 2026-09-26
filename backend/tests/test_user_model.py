import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import create_engine, create_sessionmaker
from app.models import User, UserRole

pytestmark = pytest.mark.anyio


@pytest.fixture
async def db(settings) -> AsyncIterator[AsyncSession]:
    engine = create_engine(settings)
    async with create_sessionmaker(engine)() as session:
        yield session
        # Leave the table empty for the next test
        await session.rollback()
        await session.execute(delete(User))
        await session.commit()
    await engine.dispose()


def make_user(**overrides) -> User:
    fields = {
        "email": "ada@example.com",
        "username": "ada",
        "hashed_password": "not-a-real-hash",
    } | overrides
    return User(**fields)


async def test_new_user_gets_defaults(db: AsyncSession):
    user = make_user()
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.role is UserRole.USER
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.parametrize("field", ["email", "username"])
async def test_email_and_username_must_be_unique(db: AsyncSession, field: str):
    db.add(make_user())
    await db.commit()

    # Same value for `field`, different value for the other one
    other = {"email": "grace@example.com", "username": "grace"}
    other.pop(field)
    db.add(make_user(**other))

    with pytest.raises(IntegrityError, match=f"uq_users_{field}"):
        await db.commit()
