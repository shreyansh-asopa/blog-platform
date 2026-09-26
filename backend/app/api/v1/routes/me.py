from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession, Pagination, SessionMaker
from app.models import PostStatus
from app.schemas.pagination import Page
from app.schemas.post import PostSummary
from app.services.export_service import export_posts_csv
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


@router.get(
    "/posts/export",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/csv": {}}, "description": "A CSV file download"}},
)
async def export_my_posts(
    sessionmaker: SessionMaker,
    user: CurrentUser,
    format: Literal["csv"] = "csv",
    status: PostStatus | None = None,
) -> StreamingResponse:
    """Download all your posts, drafts included, as a spreadsheet file. Filter with ?status=."""
    filename = f"lumen-posts-{datetime.now(UTC):%Y-%m-%d}.csv"
    return StreamingResponse(
        export_posts_csv(sessionmaker, user, status),
        media_type="text/csv; charset=utf-8",
        # "attachment" makes browsers save the file instead of showing it
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
