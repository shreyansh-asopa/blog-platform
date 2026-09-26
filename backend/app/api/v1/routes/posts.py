import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession, OptionalUser, Pagination
from app.schemas.pagination import Page
from app.schemas.post import PostCreate, PostRead, PostSummary, PostUpdate
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("")
async def list_posts(db: DbSession, params: Pagination) -> Page[PostSummary]:
    """The public feed: published posts, newest first."""
    posts, total = await PostService(db).list_published(params)
    return Page(
        items=[PostSummary.model_validate(p) for p in posts],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get("/{slug}")
async def read_post(slug: str, db: DbSession, viewer: OptionalUser) -> PostRead:
    """Anyone can read a published post. Drafts are visible only to their author."""
    return PostRead.model_validate(await PostService(db).get_by_slug(slug, viewer))


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
