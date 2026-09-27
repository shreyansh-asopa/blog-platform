"""Fill a local database with sample authors, posts, likes and comments.

    uv run python -m app.seed                     # on your machine
    docker compose exec api python -m app.seed    # inside the API container

Run it inside the container when the API runs in Docker: covers are saved to the uploads
folder, and only the container's one is served.

Safe to run again: posts are matched by author and title, so nothing is added twice. An
existing sample post that has no topics or cover yet gets them. New accounts get a random
password, printed once, so the public repo holds no working login.
"""

import asyncio
import secrets
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.core.config import Settings
from app.db.session import create_engine, create_sessionmaker
from app.integrations.moderation import WordListModerator
from app.integrations.storage import LocalStorage
from app.models import Post, User
from app.repositories.user_repository import UserRepository
from app.schemas.comment import CommentCreate
from app.schemas.post import PostCreate, PostUpdate
from app.schemas.user import UserCreate
from app.seed_data import AUTHORS, POSTS
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.like_service import LikeService
from app.services.post_service import PostService

COVERS = Path(__file__).parent / "seed_covers"
# How many covers scripts/draw_sample_art.py draws per topic
COVER_VARIANTS = 3


async def seed(settings: Settings | None = None) -> None:
    settings = settings or Settings()
    engine = create_engine(settings)
    sessionmaker = create_sessionmaker(engine)
    storage = LocalStorage(settings.upload_dir)
    password = secrets.token_urlsafe(12)

    async with sessionmaker() as session:
        users = UserRepository(session)
        authors: dict[str, User] = {}
        created: set[str] = set()
        for username in AUTHORS:
            existing = await users.get_by_email_or_username(username)
            if existing:
                authors[username] = existing
                continue
            data = UserCreate(email=f"{username}@example.com", username=username, password=password)
            authors[username] = await AuthService(session, settings).register(data)
            created.add(username)

        posts = PostService(session)
        likes = LikeService(session)
        comments = CommentService(session, WordListModerator())
        now = datetime.now(UTC)
        # Posts on the same topic take turns through its covers
        covers_used: Counter[str] = Counter()
        added = tagged = covered = 0

        for sample in POSTS:
            author = authors[sample.author]
            topic = sample.topics[0]
            cover = COVERS / f"{topic}-{covers_used[topic] % COVER_VARIANTS + 1}.webp"
            covers_used[topic] += 1

            post = await session.scalar(
                select(Post).where(
                    Post.author_id == author.id,
                    Post.title == sample.title,
                    Post.deleted_at.is_(None),
                )
            )
            if post is None:
                data = PostCreate(title=sample.title, content=sample.content, topics=sample.topics)
                post = await posts.create(author, data)
                post = await posts.publish(author, post.id)
                # Spread the posts out over the last two weeks, so the feed looks lived in
                post.published_at = now - timedelta(days=sample.days_ago, hours=len(sample.title))
                await session.commit()
                added += 1

                for username in sample.liked_by:
                    await likes.like(authors[username], post.id)
                for username, text in sample.comments:
                    await comments.create(authors[username], post.id, CommentCreate(content=text))
            elif not post.topics:
                # A sample post from before topics existed
                await posts.update(author, post.id, PostUpdate(topics=sample.topics))
                tagged += 1

            if post.cover_image is None:
                await posts.set_cover(author, post.id, cover.read_bytes(), storage)
                covered += 1

    await engine.dispose()

    if not (created or added or tagged or covered):
        print("Sample data already exists, nothing to do.")
        return
    print(f"Added {added} posts, filed {tagged} older ones under topics, added {covered} covers.")
    if created:
        print(f"Log in as any of {', '.join(sorted(created))} with password: {password}")


if __name__ == "__main__":
    asyncio.run(seed())
