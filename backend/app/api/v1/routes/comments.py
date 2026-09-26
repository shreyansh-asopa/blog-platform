import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    ModeratorDep,
    OptionalUser,
    Pagination,
    limit_comments,
)
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.pagination import Page
from app.services.comment_service import CommentService

router = APIRouter(tags=["comments"])


@router.get("/posts/{post_id}/comments")
async def list_comments(
    post_id: uuid.UUID,
    db: DbSession,
    viewer: OptionalUser,
    moderator: ModeratorDep,
    params: Pagination,
) -> Page[CommentRead]:
    """A post's comments, oldest first."""
    comments, total = await CommentService(db, moderator).list_for_post(post_id, viewer, params)
    return Page(
        items=[CommentRead.model_validate(c) for c in comments],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.post(
    "/posts/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_comments)],
)
async def create_comment(
    post_id: uuid.UUID,
    data: CommentCreate,
    db: DbSession,
    user: CurrentUser,
    moderator: ModeratorDep,
) -> CommentRead:
    """Comment on a published post. The text is checked by moderation first (422 if rejected)."""
    comment = await CommentService(db, moderator).create(user, post_id, data)
    return CommentRead.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: uuid.UUID, db: DbSession, user: CurrentUser, moderator: ModeratorDep
) -> None:
    """Allowed for the comment's author, the post's author, and admins."""
    await CommentService(db, moderator).delete(user, comment_id)
