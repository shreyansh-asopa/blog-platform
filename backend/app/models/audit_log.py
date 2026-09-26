import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class AuditAction(enum.StrEnum):
    ROLE_CHANGED = "user.role_changed"
    POST_UPDATED = "post.updated"
    POST_PUBLISHED = "post.published"
    POST_UNPUBLISHED = "post.unpublished"
    POST_DELETED = "post.deleted"
    COMMENT_DELETED = "comment.deleted"


class AuditLog(Base):
    """An append-only record of who did what. Rows are written, never changed."""

    __tablename__ = "audit_logs"

    # A growing number rather than a UUID: cheap, and it also shows the order of events
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    # SET NULL, not CASCADE: deleting a user must not erase the history of what they did
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Plain strings, not a Postgres enum, so adding a new action needs no migration
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(64))
    # "metadata" is reserved by SQLAlchemy, so the attribute is `details` on the same column
    details: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    actor: Mapped[User | None] = relationship(lazy="joined")
