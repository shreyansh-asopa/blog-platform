import uuid

from sqlalchemy import Select, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, PostStatus
from app.schemas.pagination import PageParams


def _visible() -> Select[tuple[Post]]:
    """Every query starts here, so soft-deleted posts can't leak into any result."""
    return select(Post).where(Post.deleted_at.is_(None))


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, post_id: uuid.UUID) -> Post | None:
        return await self.session.scalar(_visible().where(Post.id == post_id))

    async def get_by_slug(self, slug: str) -> Post | None:
        return await self.session.scalar(_visible().where(Post.slug == slug))

    async def slug_exists(self, slug: str) -> bool:
        # Deliberately includes deleted posts: slugs are never reused
        return bool(await self.session.scalar(select(exists().where(Post.slug == slug))))

    async def list_published(self, params: PageParams) -> tuple[list[Post], int]:
        query = _visible().where(Post.status == PostStatus.PUBLISHED)
        return await self._paginate(query, params, Post.published_at.desc())

    async def list_by_author(
        self, author_id: uuid.UUID, params: PageParams, status: PostStatus | None = None
    ) -> tuple[list[Post], int]:
        query = _visible().where(Post.author_id == author_id)
        if status is not None:
            query = query.where(Post.status == status)
        return await self._paginate(query, params, Post.updated_at.desc())

    async def add(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.flush()
        return post

    async def _paginate(self, query, params: PageParams, order_by) -> tuple[list[Post], int]:
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        # id as a tie-breaker keeps the order stable when timestamps are equal
        page = query.order_by(order_by, Post.id).offset(params.offset).limit(params.size)
        items = list(await self.session.scalars(page))
        return items, total or 0
