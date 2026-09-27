from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession, Pagination, SessionMaker
from app.models import PostStatus
from app.repositories.post_repository import Sort
from app.schemas.pagination import Page
from app.schemas.post import PostSummary
from app.services.export_service import ExportFormat, export_posts
from app.services.post_service import PostService

router = APIRouter(prefix="/me", tags=["me"])

SearchQuery = Annotated[
    str | None,
    Query(max_length=200, description='Search your posts. Supports "phrases", or, -exclude'),
]

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("/posts")
async def my_posts(
    db: DbSession,
    user: CurrentUser,
    params: Pagination,
    status: PostStatus | None = None,
    q: SearchQuery = None,
    sort: Sort = "newest",
) -> Page[PostSummary]:
    """Your own posts. Filter with ?status=draft, search with ?q=, and sort with ?sort=oldest."""
    posts, total = await PostService(db).list_mine(user, params, status, q, sort)
    return Page(
        items=[PostSummary.model_validate(p) for p in posts],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get(
    "/posts/export",
    responses={
        200: {
            "content": dict.fromkeys(_MEDIA_TYPES.values(), {}),
            "description": "A PDF or Word file download",
        }
    },
)
async def export_my_posts(
    sessionmaker: SessionMaker,
    user: CurrentUser,
    format: ExportFormat = "pdf",
    status: PostStatus | None = None,
    q: SearchQuery = None,
) -> Response:
    """Download all your posts, drafts included, as a PDF or Word document.

    Filter with ?status= and ?q=, as in GET /me/posts.
    """
    body = await export_posts(sessionmaker, user, format, status, q)
    suffix = f"-{status.value}" if status else ""
    filename = f"lumen-posts{suffix}-{datetime.now(UTC):%Y-%m-%d}.{format}"
    return Response(
        content=body,
        media_type=_MEDIA_TYPES[format],
        # "attachment" makes browsers save the file instead of showing it
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
