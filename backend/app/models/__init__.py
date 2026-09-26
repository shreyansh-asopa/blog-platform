# Import every model here so Alembic autogenerate can see all tables
from app.models.post import Post, PostStatus
from app.models.user import User, UserRole

__all__ = ["Post", "PostStatus", "User", "UserRole"]
