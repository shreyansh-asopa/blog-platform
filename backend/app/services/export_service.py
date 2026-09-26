"""Exporting a user's posts as a CSV file."""

import csv
import io
from collections.abc import AsyncIterator
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Post, PostStatus, User
from app.repositories.post_repository import PostRepository

COLUMNS = [
    "id",
    "title",
    "slug",
    "status",
    "excerpt",
    "content",
    "cover_image",
    "like_count",
    "comment_count",
    "created_at",
    "published_at",
    "updated_at",
]

# Spreadsheet apps run a cell that starts with one of these as a formula, so a post
# titled "=HYPERLINK(...)" could do things when the file is opened ("CSV injection")
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value: object) -> str:
    """A value as CSV text that a spreadsheet will show, never run."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    text = str(value)
    return f"'{text}" if text.startswith(_FORMULA_STARTS) else text


def _row(post: Post) -> list[str]:
    return [safe_cell(getattr(post, column)) for column in COLUMNS]


async def export_posts_csv(
    sessionmaker: async_sessionmaker[AsyncSession], user: User, status: PostStatus | None
) -> AsyncIterator[str]:
    """The user's posts as CSV text, produced a row at a time while it is being downloaded.

    It opens its own database session: the download can outlast the request's own
    session, which closes when the endpoint function returns.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    def flush() -> str:
        text = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate()
        return text

    # The byte-order mark tells Excel the file is UTF-8, so "é" doesn't turn into "Ã©"
    yield "﻿"
    writer.writerow(COLUMNS)
    yield flush()

    async with sessionmaker() as session:
        async for post in PostRepository(session).stream_by_author(user.id, status):
            writer.writerow(_row(post))
            yield flush()
