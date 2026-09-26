import uuid

from pydantic import BaseModel


class LikeStatus(BaseModel):
    """Returned after liking or unliking, so the page can update the heart and the count."""

    post_id: uuid.UUID
    liked: bool
    like_count: int
