from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment, Like, Post, PostStatus, Topic, post_topics


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


def _live_posts_of_topic():
    """The outer Topic row's live, published post ids."""
    return (
        select(post_topics.c.post_id)
        .join(Post, Post.id == post_topics.c.post_id)
        .where(
            post_topics.c.topic_slug == Topic.slug,
            Post.status == PostStatus.PUBLISHED,
            Post.deleted_at.is_(None),
        )
        .correlate(Topic)
    )


def _engagement_since(since: datetime):
    """Likes plus comments that the topic's posts received since `since`."""
    posts = _live_posts_of_topic()
    likes = (
        select(func.count())
        .select_from(Like)
        .where(Like.post_id.in_(posts), Like.created_at >= since)
        .correlate(Topic)
        .scalar_subquery()
    )
    comments = (
        select(func.count())
        .select_from(Comment)
        .where(
            Comment.post_id.in_(posts),
            Comment.created_at >= since,
            Comment.deleted_at.is_(None),
        )
        .correlate(Topic)
        .scalar_subquery()
    )
    return likes + comments


class TopicRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_with_counts(self) -> list[tuple[Topic, int]]:
        query = select(Topic, _published_count()).order_by(Topic.position)
        return [(topic, count) for topic, count in await self.session.execute(query)]

    async def trending(self, since: datetime, limit: int) -> list[tuple[Topic, int]]:
        """The topics whose posts got the most likes and comments since `since`. Ties go to
        the topic with more posts, then to display order."""
        count = _published_count()
        query = (
            select(Topic, count)
            .order_by(_engagement_since(since).desc(), count.desc(), Topic.position)
            .limit(limit)
        )
        return [(topic, count) for topic, count in await self.session.execute(query)]

    async def get_with_count(self, slug: str) -> tuple[Topic, int] | None:
        row = (
            await self.session.execute(select(Topic, _published_count()).where(Topic.slug == slug))
        ).first()
        return (row[0], row[1]) if row else None

    async def get_many(self, slugs: Sequence[str]) -> list[Topic]:
        result = await self.session.scalars(select(Topic).where(Topic.slug.in_(slugs)))
        return list(result)
