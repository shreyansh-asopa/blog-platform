import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.user import User


class PostStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Post(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (
        # The public feed: published posts, newest first (Postgres reads the index backwards)
        Index("ix_posts_status_published_at", "status", "published_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    # URL-friendly title, e.g. "my-first-post". Unique even across deleted posts,
    # so an old link never starts pointing at someone else's post
    slug: Mapped[str] = mapped_column(String(220), unique=True)
    content: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(String(300))
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status", values_callable=lambda e: [m.value for m in e]),
        default=PostStatus.DRAFT,
        server_default=PostStatus.DRAFT.value,
    )
    cover_image: Mapped[str | None] = mapped_column(String(255))
    # Set on first publish and kept afterwards, so unpublish/republish doesn't bump a post
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Loaded in the same query as the post (a JOIN), so listing posts never
    # fires one extra query per post to fetch its author (the "N+1" problem)
    author: Mapped[User] = relationship(lazy="joined")
