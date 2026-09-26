import uuid

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.user import User


class Comment(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (
        # A post's thread, oldest first: the rows are already in order in the index
        Index("ix_comments_post_id_created_at", "post_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)

    author: Mapped[User] = relationship(lazy="joined")
