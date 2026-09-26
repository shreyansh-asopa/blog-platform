import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.like import LikeStatus
from app.services.like_service import LikeService

router = APIRouter(prefix="/posts", tags=["likes"])


# PUT and DELETE rather than POST: both are idempotent, so repeating a request
# (a double click, a retry after a timeout) never changes the result
@router.put("/{post_id}/like")
async def like_post(post_id: uuid.UUID, db: DbSession, user: CurrentUser) -> LikeStatus:
    return await LikeService(db).like(user, post_id)


@router.delete("/{post_id}/like")
async def unlike_post(post_id: uuid.UUID, db: DbSession, user: CurrentUser) -> LikeStatus:
    return await LikeService(db).unlike(user, post_id)
