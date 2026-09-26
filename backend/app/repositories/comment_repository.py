import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment
from app.repositories.pagination import paginate
from app.schemas.pagination import PageParams


def _visible() -> Select[tuple[Comment]]:
    return select(Comment).where(Comment.deleted_at.is_(None))


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        return await self.session.scalar(_visible().where(Comment.id == comment_id))

    async def list_for_post(
        self, post_id: uuid.UUID, params: PageParams
    ) -> tuple[list[Comment], int]:
        query = _visible().where(Comment.post_id == post_id)
        # Oldest first, so a thread reads like a conversation
        return await paginate(self.session, query, params, Comment.created_at, Comment.id)

    async def add(self, comment: Comment) -> Comment:
        self.session.add(comment)
        await self.session.flush()
        return comment
