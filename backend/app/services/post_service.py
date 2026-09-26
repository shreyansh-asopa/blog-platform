import logging
import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    UnsupportedFileTypeError,
)
from app.core.text import make_excerpt, slugify
from app.integrations.storage import Storage, detect_image_type
from app.models import AuditAction, Post, PostStatus, User
from app.permissions import Permission, has_permission
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.post_repository import PostRepository
from app.schemas.pagination import PageParams
from app.schemas.post import PostCreate, PostUpdate

logger = logging.getLogger(__name__)


def can_manage(user: User, post: Post) -> bool:
    return post.author_id == user.id or has_permission(user, Permission.MANAGE_ANY_POST)


class PostService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.posts = PostRepository(session)
        self.audit = AuditLogRepository(session)

    # --- Reading ---

    async def list_published(self, params: PageParams) -> tuple[list[Post], int]:
        return await self.posts.list_published(params)

    async def list_mine(
        self, user: User, params: PageParams, status: PostStatus | None
    ) -> tuple[list[Post], int]:
        return await self.posts.list_by_author(user.id, params, status)

    async def get_by_slug(self, slug: str, viewer: User | None) -> Post:
        post = await self.posts.get_by_slug(slug)
        # A draft is a 404 for everyone who can't manage it, so drafts can't be discovered
        if post is None or (
            post.status is PostStatus.DRAFT and (viewer is None or not can_manage(viewer, post))
        ):
            raise NotFoundError("Post not found")
        return post

    # --- Writing ---

    async def create(self, user: User, data: PostCreate) -> Post:
        post = Post(
            author=user,
            title=data.title,
            slug=await self._unique_slug(data.title),
            content=data.content,
            excerpt=data.excerpt or make_excerpt(data.content),
        )
        await self.posts.add(post)
        return await self._save(post)

    async def update(self, user: User, post_id: uuid.UUID, data: PostUpdate) -> Post:
        post = await self._get_managed(user, post_id)
        changes = data.model_dump(exclude_unset=True)

        if "title" in changes and changes["title"] != post.title:
            post.title = changes["title"]
            # A draft's URL follows its title; once published, links in the wild must keep working
            if post.status is PostStatus.DRAFT and slugify(post.title) != post.slug:
                post.slug = await self._unique_slug(post.title)

        if "content" in changes:
            # Keep a generated excerpt in step with the content, but never touch a custom one
            excerpt_was_generated = post.excerpt == make_excerpt(post.content)
            post.content = changes["content"]
            if excerpt_was_generated and "excerpt" not in changes:
                post.excerpt = make_excerpt(post.content)

        if "excerpt" in changes:
            post.excerpt = changes["excerpt"] or make_excerpt(post.content)

        self._audit_if_not_author(user, AuditAction.POST_UPDATED, post, fields=sorted(changes))
        return await self._save(post)

    async def publish(self, user: User, post_id: uuid.UUID) -> Post:
        post = await self._get_managed(user, post_id)
        post.status = PostStatus.PUBLISHED
        post.published_at = post.published_at or datetime.now(UTC)
        self._audit_if_not_author(user, AuditAction.POST_PUBLISHED, post)
        return await self._save(post)

    async def unpublish(self, user: User, post_id: uuid.UUID) -> Post:
        post = await self._get_managed(user, post_id)
        post.status = PostStatus.DRAFT
        self._audit_if_not_author(user, AuditAction.POST_UNPUBLISHED, post)
        return await self._save(post)

    async def delete(self, user: User, post_id: uuid.UUID) -> None:
        post = await self._get_managed(user, post_id)
        post.deleted_at = datetime.now(UTC)
        # Every delete is recorded, so a post can be found and restored later
        self.audit.record(
            user,
            AuditAction.POST_DELETED,
            "post",
            post.id,
            {"title": post.title, "author_id": str(post.author_id)},
        )
        await self.session.commit()

    # --- Cover image ---

    async def set_cover(
        self, user: User, post_id: uuid.UUID, data: bytes, storage: Storage
    ) -> Post:
        post = await self._get_managed(user, post_id)
        extension = detect_image_type(data)
        if extension is None:
            raise UnsupportedFileTypeError("The cover must be a JPEG, PNG or WebP image")

        old_url = post.cover_image
        # File first, then the database: if saving the post fails we remove the new file,
        # so the post never points at a file that doesn't exist
        new_url = await storage.save("covers", data, extension)
        post.cover_image = new_url
        self._audit_if_not_author(user, AuditAction.POST_UPDATED, post, fields=["cover_image"])
        try:
            post = await self._save(post)
        except Exception:
            await storage.delete(new_url)
            raise

        await self._delete_file(storage, old_url)
        return post

    async def remove_cover(self, user: User, post_id: uuid.UUID, storage: Storage) -> Post:
        post = await self._get_managed(user, post_id)
        old_url = post.cover_image
        if old_url is None:
            return post
        post.cover_image = None
        self._audit_if_not_author(user, AuditAction.POST_UPDATED, post, fields=["cover_image"])
        post = await self._save(post)
        await self._delete_file(storage, old_url)
        return post

    # --- Helpers ---

    @staticmethod
    async def _delete_file(storage: Storage, url: str | None) -> None:
        # Only after the database change is saved. If this fails, the cost is an unused
        # file on disk, which is harmless, so it is logged rather than failing the request
        if url is None:
            return
        try:
            await storage.delete(url)
        except OSError:
            logger.warning("Could not delete old cover %s", url, exc_info=True)

    def _audit_if_not_author(self, user: User, action: AuditAction, post: Post, **details) -> None:
        # Authors editing their own posts is everyday use; an admin changing
        # someone else's post is worth a record
        if user.id != post.author_id:
            details["author_id"] = str(post.author_id)
            self.audit.record(user, action, "post", post.id, details)

    async def _get_managed(self, user: User, post_id: uuid.UUID) -> Post:
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")
        if not can_manage(user, post):
            # Another user's draft: 404, so its existence stays private. Published: 403
            if post.status is PostStatus.DRAFT:
                raise NotFoundError("Post not found")
            raise PermissionDeniedError("You can only change your own posts")
        return post

    async def _unique_slug(self, title: str) -> str:
        slug = slugify(title)
        while await self.posts.slug_exists(slug):
            # "my-post" is taken: try "my-post-3f9a2c"
            slug = f"{slugify(title)[:193]}-{secrets.token_hex(3)}"
        return slug

    async def _save(self, post: Post) -> Post:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            # Two posts grabbed the same slug at the same moment
            await self.session.rollback()
            raise ConflictError("Could not save the post, please try again") from exc
        # Reload what the database set (updated_at) along with the author
        await self.session.refresh(post)
        return post
