# Import every model here so Alembic autogenerate can see all tables
from app.models.audit_log import AuditAction, AuditLog
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import ContentFormat, Post, PostStatus
from app.models.topic import Topic, post_topics
from app.models.user import User, UserRole

__all__ = [
    "AuditAction",
    "AuditLog",
    "Comment",
    "ContentFormat",
    "Like",
    "Post",
    "PostStatus",
    "Topic",
    "User",
    "UserRole",
    "post_topics",
]
