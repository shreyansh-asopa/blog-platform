from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, Pagination
from app.models import PostStatus
from app.schemas.pagination import Page
from app.schemas.post import PostSummary
from app.services.post_service import PostService

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/posts")
async def my_posts(
    db: DbSession, user: CurrentUser, params: Pagination, status: PostStatus | None = None
) -> Page[PostSummary]:
    """Your own posts, drafts included, most recently edited first. Filter with ?status=draft."""
    posts, total = await PostService(db).list_mine(user, params, status)
    return Page(
        items=[PostSummary.model_validate(p) for p in posts],
        total=total,
        page=params.page,
        size=params.size,
    )
