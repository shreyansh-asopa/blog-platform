import uuid

from sqlalchemy import delete, exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Like


class LikeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: uuid.UUID, post_id: uuid.UUID) -> None:
        # ON CONFLICT DO NOTHING: liking twice (even two requests at the same moment)
        # leaves exactly one row instead of raising an error
        await self.session.execute(
            insert(Like).values(user_id=user_id, post_id=post_id).on_conflict_do_nothing()
        )

    async def remove(self, user_id: uuid.UUID, post_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )

    async def exists(self, user_id: uuid.UUID, post_id: uuid.UUID) -> bool:
        query = select(exists().where(Like.user_id == user_id, Like.post_id == post_id))
        return bool(await self.session.scalar(query))

    async def count_for_post(self, post_id: uuid.UUID) -> int:
        query = select(func.count()).where(Like.post_id == post_id)
        return await self.session.scalar(query) or 0
