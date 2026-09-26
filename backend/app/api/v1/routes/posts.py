import uuid
from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status

from app.api.deps import (
    AppSettings,
    CurrentUser,
    DbSession,
    OptionalUser,
    Pagination,
    StorageDep,
)
from app.core.exceptions import FileTooLargeError
from app.schemas.pagination import Page
from app.schemas.post import PostCreate, PostDetail, PostRead, PostSummary, PostUpdate
from app.services.like_service import LikeService
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("")
async def list_posts(
    db: DbSession,
    params: Pagination,
    q: Annotated[
        str | None,
        Query(max_length=200, description='Search words. Supports "phrases", or, -exclude'),
    ] = None,
    author: Annotated[str | None, Query(max_length=50, description="A username")] = None,
) -> Page[PostSummary]:
    """The public feed: published posts, newest first. With `q`, best matches first."""
    posts, total = await PostService(db).list_published(params, q, author)
    return Page(
        items=[PostSummary.model_validate(p) for p in posts],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get("/{slug}")
async def read_post(slug: str, db: DbSession, viewer: OptionalUser) -> PostDetail:
    """Anyone can read a published post. Drafts are visible only to their author."""
    post = await PostService(db).get_by_slug(slug, viewer)
    liked = await LikeService(db).has_liked(viewer, post)
    return PostDetail(**PostRead.model_validate(post).model_dump(), liked_by_me=liked)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_post(data: PostCreate, db: DbSession, user: CurrentUser) -> PostRead:
    """Creates a draft. Publish it with POST /posts/{id}/publish."""
    return PostRead.model_validate(await PostService(db).create(user, data))


@router.patch("/{post_id}")
async def update_post(
    post_id: uuid.UUID, data: PostUpdate, db: DbSession, user: CurrentUser
) -> PostRead:
    return PostRead.model_validate(await PostService(db).update(user, post_id, data))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    await PostService(db).delete(user, post_id)


@router.post("/{post_id}/publish")
async def publish_post(post_id: uuid.UUID, db: DbSession, user: CurrentUser) -> PostRead:
    return PostRead.model_validate(await PostService(db).publish(user, post_id))


@router.post("/{post_id}/unpublish")
async def unpublish_post(post_id: uuid.UUID, db: DbSession, user: CurrentUser) -> PostRead:
    return PostRead.model_validate(await PostService(db).unpublish(user, post_id))


@router.post("/{post_id}/cover")
async def upload_cover(
    post_id: uuid.UUID,
    file: Annotated[UploadFile, File(description="A JPEG, PNG or WebP image, at most 5 MB")],
    db: DbSession,
    user: CurrentUser,
    storage: StorageDep,
    settings: AppSettings,
) -> PostRead:
    """Sets or replaces the post's cover image. Send it as multipart form field `file`."""
    # Read one byte past the limit: enough to know a file is too big without reading all of it
    data = await file.read(settings.max_cover_bytes + 1)
    if len(data) > settings.max_cover_bytes:
        limit_mb = settings.max_cover_bytes // (1024 * 1024)
        raise FileTooLargeError(f"The cover must be at most {limit_mb} MB")
    return PostRead.model_validate(await PostService(db).set_cover(user, post_id, data, storage))


@router.delete("/{post_id}/cover")
async def delete_cover(
    post_id: uuid.UUID, db: DbSession, user: CurrentUser, storage: StorageDep
) -> PostRead:
    return PostRead.model_validate(await PostService(db).remove_cover(user, post_id, storage))
