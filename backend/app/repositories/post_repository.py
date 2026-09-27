import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal

from sqlalchemy import Select, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, PostStatus, User, post_topics
from app.repositories.pagination import paginate
from app.repositories.user_repository import username_is
from app.schemas.pagination import PageParams

Sort = Literal["newest", "oldest"]


def _visible() -> Select[tuple[Post]]:
    """Every query starts here, so soft-deleted posts can't leak into any result."""
    return select(Post).where(Post.deleted_at.is_(None))


def _searched(query: Select[tuple[Post]], search: str | None) -> tuple[Select[tuple[Post]], Any]:
    """Filters `query` to rows matching `search`; also returns a ts_rank expression to
    order by, or None when there was nothing to search for.

    `search` takes what people type into search boxes: `"exact phrase"`, `or`, and
    `-word` to exclude.
    """
    if not (search := (search or "").strip()):
        return query, None
    # websearch_to_tsquery never fails on odd input, unlike to_tsquery
    terms = func.websearch_to_tsquery("english", search)
    query = query.where(Post.search_vector.bool_op("@@")(terms))
    # ts_rank scores how often and where (title or body) the words appear
    return query, func.ts_rank(Post.search_vector, terms)


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
        self,
        params: PageParams,
        search: str | None = None,
        author: str | None = None,
        topic: str | None = None,
        sort: Sort | None = None,
    ) -> tuple[list[Post], int]:
        """Newest first, or oldest first with sort="oldest".

        `search` takes what people type into search boxes: `"exact phrase"`, `or`, and
        `-word` to exclude. `author` is a username and `topic` a topic slug; an unknown
        one just matches nothing. While searching, results rank best match first instead
        -- unless `sort` is given, which then means exactly what it says.
        """
        query = _visible().where(Post.status == PostStatus.PUBLISHED)
        if author:
            query = query.where(Post.author_id.in_(select(User.id).where(username_is(author))))
        if topic:
            tagged = select(post_topics.c.post_id).where(post_topics.c.topic_slug == topic.lower())
            query = query.where(Post.id.in_(tagged))
        query, rank = _searched(query, search)
        chronological = [
            Post.published_at.asc() if sort == "oldest" else Post.published_at.desc(),
            Post.id,
        ]
        order_by = chronological if sort or rank is None else [rank.desc(), *chronological]
        return await paginate(self.session, query, params, *order_by)

    async def count_published_by(self, author_id: uuid.UUID) -> int:
        query = _visible().where(Post.author_id == author_id, Post.status == PostStatus.PUBLISHED)
        return await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0

    async def list_by_author(
        self,
        author_id: uuid.UUID,
        params: PageParams,
        status: PostStatus | None = None,
        search: str | None = None,
        sort: Sort = "newest",
    ) -> tuple[list[Post], int]:
        """Most recently edited first, or oldest first with `sort="oldest"`."""
        query = _visible().where(Post.author_id == author_id)
        if status is not None:
            query = query.where(Post.status == status)
        query, _ = _searched(query, search)
        updated = Post.updated_at.asc() if sort == "oldest" else Post.updated_at.desc()
        return await paginate(self.session, query, params, updated, Post.id)

    async def stream_by_author(
        self,
        author_id: uuid.UUID,
        status: PostStatus | None = None,
        search: str | None = None,
        batch_size: int = 500,
    ) -> AsyncIterator[Post]:
        """All of an author's posts, oldest first, fetched from the database in batches.

        Unlike a list, this never holds every post in memory at once.
        """
        query = _visible().where(Post.author_id == author_id).order_by(Post.created_at, Post.id)
        if status is not None:
            query = query.where(Post.status == status)
        query, _ = _searched(query, search)
        result = await self.session.stream_scalars(query.execution_options(yield_per=batch_size))
        async for post in result:
            yield post

    async def add(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.flush()
        return post
