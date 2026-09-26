from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import ProfileRead, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


# After /me, so "me" is never looked up as a username (usernames are 3+ characters anyway)
@router.get("/{username}")
async def read_profile(username: str, db: DbSession) -> ProfileRead:
    """An author's public profile. Their posts: GET /posts?author={username}."""
    return await UserService(db).get_profile(username)
