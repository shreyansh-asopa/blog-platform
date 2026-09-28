from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.topic_repository import TopicRepository
from app.schemas.topic import TopicDetail

# How far back likes and comments count towards a topic trending
TRENDING_WINDOW = timedelta(days=7)


def _detail(topic, count: int) -> TopicDetail:
    return TopicDetail(
        slug=topic.slug, name=topic.name, description=topic.description, post_count=count
    )


class TopicService:
    def __init__(self, session: AsyncSession):
        self.topics = TopicRepository(session)

    async def trending(self, limit: int) -> list[TopicDetail]:
        since = datetime.now(UTC) - TRENDING_WINDOW
        return [_detail(topic, count) for topic, count in await self.topics.trending(since, limit)]

    async def list(self) -> list[TopicDetail]:
        return [_detail(topic, count) for topic, count in await self.topics.list_with_counts()]

    async def get(self, slug: str) -> TopicDetail:
        found = await self.topics.get_with_count(slug.lower())
        if found is None:
            raise NotFoundError("Topic not found")
        return _detail(*found)
