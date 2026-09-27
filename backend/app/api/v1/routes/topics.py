from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.topic import TopicDetail
from app.services.topic_service import TopicService

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("")
async def list_topics(db: DbSession) -> list[TopicDetail]:
    """Every topic, in display order, with its number of published posts."""
    return await TopicService(db).list()


@router.get("/{slug}")
async def read_topic(slug: str, db: DbSession) -> TopicDetail:
    """One topic. Its posts: GET /posts?topic={slug}."""
    return await TopicService(db).get(slug)
