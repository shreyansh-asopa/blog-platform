import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ContentRejectedError, NotFoundError, PermissionDeniedError
from app.integrations.moderation import ModerationUnavailableError, Moderator
from app.models import AuditAction, Comment, Post, PostStatus, User
from app.permissions import Permission, has_permission
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.post_repository import PostRepository
from app.schemas.comment import CommentCreate
from app.schemas.pagination import PageParams
from app.services.post_service import can_manage

logger = logging.getLogger(__name__)


def can_delete(user: User, comment: Comment, post: Post) -> bool:
    return (
        comment.author_id == user.id
        or post.author_id == user.id
        or has_permission(user, Permission.DELETE_ANY_COMMENT)
    )


class CommentService:
    def __init__(self, session: AsyncSession, moderator: Moderator):
        self.session = session
        self.moderator = moderator
        self.comments = CommentRepository(session)
        self.posts = PostRepository(session)
        self.audit = AuditLogRepository(session)

    async def list_for_post(
        self, post_id: uuid.UUID, viewer: User | None, params: PageParams
    ) -> tuple[list[Comment], int]:
        post = await self._get_visible_post(post_id, viewer)
        return await self.comments.list_for_post(post.id, params)

    async def create(self, user: User, post_id: uuid.UUID, data: CommentCreate) -> Comment:
        post = await self.posts.get_by_id(post_id)
        if post is None or post.status is not PostStatus.PUBLISHED:
            raise NotFoundError("Post not found")
        # End the read transaction first, so no database connection sits idle
        # while we wait on the moderation service over the network
        await self.session.commit()
        await self._moderate(data.content)

        comment = Comment(post_id=post.id, author=user, content=data.content)
        await self.comments.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def delete(self, user: User, comment_id: uuid.UUID) -> None:
        comment = await self.comments.get_by_id(comment_id)
        if comment is None:
            raise NotFoundError("Comment not found")
        # A comment under a post you can't see is hidden too
        post = await self._get_visible_post(comment.post_id, user, not_found="Comment not found")
        if not can_delete(user, comment, post):
            raise PermissionDeniedError("You can only delete your own comments")
        comment.deleted_at = datetime.now(UTC)
        self.audit.record(
            user,
            AuditAction.COMMENT_DELETED,
            "comment",
            comment.id,
            {"post_id": str(post.id), "author_id": str(comment.author_id)},
        )
        await self.session.commit()

    async def _moderate(self, text: str) -> None:
        try:
            result = await self.moderator.check(text)
        except ModerationUnavailableError as exc:
            # Fail open: a moderation outage must not stop people from commenting.
            # Anything that slips through can still be deleted by the post author or an admin
            logger.warning("Moderation unavailable, accepting comment unchecked: %s", exc)
            return
        if not result.allowed:
            raise ContentRejectedError(
                f"Comment was rejected by moderation ({result.reason or 'no reason given'})"
            )

    async def _get_visible_post(
        self, post_id: uuid.UUID, viewer: User | None, *, not_found: str = "Post not found"
    ) -> Post:
        post = await self.posts.get_by_id(post_id)
        if post is None or (
            post.status is PostStatus.DRAFT and (viewer is None or not can_manage(viewer, post))
        ):
            raise NotFoundError(not_found)
        return post
