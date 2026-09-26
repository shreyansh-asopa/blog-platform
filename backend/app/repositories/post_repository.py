import uuid
from collections.abc import AsyncIterator

from sqlalchemy import Select, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, PostStatus, User
from app.repositories.pagination import paginate
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

    async def list_published(
        self, params: PageParams, search: str | None = None, author: str | None = None
    ) -> tuple[list[Post], int]:
        """Newest first, or best match first when searching.

        `search` takes what people type into search boxes: `"exact phrase"`, `or`, and
        `-word` to exclude. `author` is a username; an unknown one just matches nothing.
        """
        query = _visible().where(Post.status == PostStatus.PUBLISHED)
        order_by = [Post.published_at.desc(), Post.id]
        if author:
            query = query.where(Post.author_id.in_(select(User.id).where(User.username == author)))
        if search := (search or "").strip():
            # websearch_to_tsquery never fails on odd input, unlike to_tsquery
            terms = func.websearch_to_tsquery("english", search)
            query = query.where(Post.search_vector.bool_op("@@")(terms))
            # ts_rank scores how often and where (title or body) the words appear
            order_by.insert(0, func.ts_rank(Post.search_vector, terms).desc())
        return await paginate(self.session, query, params, *order_by)

    async def count_published_by(self, author_id: uuid.UUID) -> int:
        query = _visible().where(Post.author_id == author_id, Post.status == PostStatus.PUBLISHED)
        return await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0

    async def list_by_author(
        self, author_id: uuid.UUID, params: PageParams, status: PostStatus | None = None
    ) -> tuple[list[Post], int]:
        query = _visible().where(Post.author_id == author_id)
        if status is not None:
            query = query.where(Post.status == status)
        return await paginate(self.session, query, params, Post.updated_at.desc(), Post.id)

    async def stream_by_author(
        self, author_id: uuid.UUID, status: PostStatus | None = None, batch_size: int = 500
    ) -> AsyncIterator[Post]:
        """All of an author's posts, oldest first, fetched from the database in batches.

        Unlike a list, this never holds every post in memory at once.
        """
        query = _visible().where(Post.author_id == author_id).order_by(Post.created_at, Post.id)
        if status is not None:
            query = query.where(Post.status == status)
        result = await self.session.stream_scalars(query.execution_options(yield_per=batch_size))
        async for post in result:
            yield post

    async def add(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.flush()
        return post
