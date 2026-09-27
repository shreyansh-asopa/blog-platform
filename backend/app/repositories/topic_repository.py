from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, PostStatus, Topic, post_topics


def _published_count():
    """How many live, published posts a topic has, as a subquery on the outer Topic row."""
    return (
        select(func.count())
        .select_from(post_topics)
        .join(Post, Post.id == post_topics.c.post_id)
        .where(
            post_topics.c.topic_slug == Topic.slug,
            Post.status == PostStatus.PUBLISHED,
            Post.deleted_at.is_(None),
        )
        .correlate(Topic)
        .scalar_subquery()
    )


class TopicRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_with_counts(self) -> list[tuple[Topic, int]]:
        query = select(Topic, _published_count()).order_by(Topic.position)
        return [(topic, count) for topic, count in await self.session.execute(query)]

    async def get_with_count(self, slug: str) -> tuple[Topic, int] | None:
        row = (
            await self.session.execute(select(Topic, _published_count()).where(Topic.slug == slug))
        ).first()
        return (row[0], row[1]) if row else None

    async def get_many(self, slugs: Sequence[str]) -> list[Topic]:
        result = await self.session.scalars(select(Topic).where(Topic.slug.in_(slugs)))
        return list(result)
