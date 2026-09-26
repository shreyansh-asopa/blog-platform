import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models import PostStatus

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Content = Annotated[str, StringConstraints(min_length=1, max_length=100_000)]
Excerpt = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]


class PostCreate(BaseModel):
    title: Title
    content: Content
    # Left out: generated from the content
    excerpt: Excerpt | None = None


class PostUpdate(BaseModel):
    """Only the fields sent are changed. Send "excerpt": null to go back to the generated one."""

    title: Title | None = None
    content: Content | None = None
    excerpt: Excerpt | None = None

    @model_validator(mode="after")
    def title_and_content_cannot_be_null(self) -> Self:
        for field in ("title", "content"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str


class PostSummary(BaseModel):
    """A post in a list: everything except the full content, to keep list responses small."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    excerpt: str
    status: PostStatus
    cover_image: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    author: AuthorRead
    like_count: int
    comment_count: int


class PostRead(PostSummary):
    content: str = Field(description="Full post body")


class PostDetail(PostRead):
    """A single post as a reader sees it, including whether they have liked it."""

    liked_by_me: bool = Field(description="Always false when not logged in")
