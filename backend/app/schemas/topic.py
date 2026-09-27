from pydantic import BaseModel, ConfigDict


class TopicRead(BaseModel):
    """A topic as shown on a post."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str


class TopicDetail(TopicRead):
    """A topic in the topic list, with how many published posts it has."""

    description: str
    post_count: int
