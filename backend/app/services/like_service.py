import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models import Post, PostStatus, User
from app.repositories.like_repository import LikeRepository
from app.repositories.post_repository import PostRepository
from app.schemas.like import LikeStatus


class LikeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.likes = LikeRepository(session)
        self.posts = PostRepository(session)

    async def like(self, user: User, post_id: uuid.UUID) -> LikeStatus:
        post = await self._get_likeable(post_id)
        if post.author_id == user.id:
            raise PermissionDeniedError("You can't like your own post")
        await self.likes.add(user.id, post.id)
        return await self._status(post, liked=True)

    async def unlike(self, user: User, post_id: uuid.UUID) -> LikeStatus:
        post = await self._get_likeable(post_id)
        await self.likes.remove(user.id, post.id)
        return await self._status(post, liked=False)

    async def has_liked(self, user: User | None, post: Post) -> bool:
        return user is not None and await self.likes.exists(user.id, post.id)

    async def _get_likeable(self, post_id: uuid.UUID) -> Post:
        post = await self.posts.get_by_id(post_id)
        # Only published posts can be liked; drafts stay a 404 like everywhere else
        if post is None or post.status is not PostStatus.PUBLISHED:
            raise NotFoundError("Post not found")
        return post

    async def _status(self, post: Post, *, liked: bool) -> LikeStatus:
        await self.session.commit()
        return LikeStatus(
            post_id=post.id, liked=liked, like_count=await self.likes.count_for_post(post.id)
        )
