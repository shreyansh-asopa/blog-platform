from sqlalchemy import Column, ForeignKey, SmallInteger, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Topic(Base):
    """A fixed list of subjects a post can be filed under, e.g. "AI" or "Data Engineering".

    The list is curated (the migration adds it), not typed by authors, so there are
    no near-duplicates like "genai" and "Gen AI".
    """

    __tablename__ = "topics"

    # The slug is the key: short, stable, and what URLs use (/t/data-engineering)
    slug: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(200))
    # Where it sits in lists like the sidebar
    position: Mapped[int] = mapped_column(SmallInteger)


# Which posts are filed under which topics. A plain table rather than a model: it holds
# nothing but the two keys. The primary key stops a post getting the same topic twice
post_topics = Table(
    "post_topics",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    # Own index for "every post in this topic"; the primary key only helps lookups by post
    Column(
        "topic_slug",
        ForeignKey("topics.slug", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
