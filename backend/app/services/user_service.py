from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import ProfileRead


class UserService:
    def __init__(self, session: AsyncSession):
        self.users = UserRepository(session)
        self.posts = PostRepository(session)

    async def get_profile(self, username: str) -> ProfileRead:
        user = await self.users.get_by_username(username)
        # A deactivated account gets the same answer as a missing one
        if user is None or not user.is_active:
            raise NotFoundError("User not found")
        return ProfileRead(
            id=user.id,
            username=user.username,
            created_at=user.created_at,
            post_count=await self.posts.count_published_by(user.id),
        )
