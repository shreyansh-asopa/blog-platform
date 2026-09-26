# Import every model here so Alembic autogenerate can see all tables
from app.models.audit_log import AuditAction, AuditLog
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post, PostStatus
from app.models.user import User, UserRole

__all__ = ["AuditAction", "AuditLog", "Comment", "Like", "Post", "PostStatus", "User", "UserRole"]
