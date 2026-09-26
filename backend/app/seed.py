"""Fill a local database with sample authors, posts, likes and comments.

    uv run python -m app.seed                     # on your machine
    docker compose exec api python -m app.seed    # inside the API container

Safe to run twice: authors that already exist are skipped, along with their posts.
The accounts get a random password, printed once, so the public repo holds no working login.
"""

import asyncio
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.db.session import create_engine, create_sessionmaker
from app.integrations.moderation import WordListModerator
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.comment import CommentCreate
from app.schemas.post import PostCreate
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.like_service import LikeService
from app.services.post_service import PostService

AUTHORS = ["ada_writes", "grace_codes", "linus_notes"]


@dataclass
class SamplePost:
    author: str
    title: str
    content: str
    days_ago: int
    liked_by: list[str] = field(default_factory=list)
    # (commenter, text), oldest first
    comments: list[tuple[str, str]] = field(default_factory=list)


POSTS = [
    SamplePost(
        author="ada_writes",
        title="Welcome to Lumen",
        days_ago=0,
        liked_by=["grace_codes", "linus_notes"],
        comments=[
            ("grace_codes", "Congrats on the launch! The reading view is lovely."),
            ("linus_notes", "Dark mode by default, my eyes thank you."),
        ],
        content="""Lumen is a small, fast place to **write to think** and **publish to connect**.

## What you can do today

- Read posts from every author in one feed
- Like the ones that teach you something
- Join the discussion in the comments

## What's coming next

1. A Markdown editor with a live preview
2. Drafts, cover images and CSV export
3. Search across every post

> Good writing is clear thinking made visible.

Thanks for being one of the first readers.""",
    ),
    SamplePost(
        author="grace_codes",
        title="Async SQLAlchemy in five minutes",
        days_ago=1,
        liked_by=["ada_writes"],
        comments=[("ada_writes", "The table makes the case better than any paragraph could.")],
        content="""Async database access lets one worker serve **many requests**
while it waits on Postgres.

## The session

```python
async with sessionmaker() as session:
    session.add(post)
    await session.commit()
```

## Why bother?

| Mode  | Requests/s |
|-------|-----------:|
| sync  |        900 |
| async |       2400 |

The numbers are illustrative; measure your own app before you optimise.

Read more in [the SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html).""",
    ),
    SamplePost(
        author="linus_notes",
        title="Writing Git commit messages people can read",
        days_ago=2,
        liked_by=["ada_writes", "grace_codes"],
        comments=[
            ("grace_codes", "The 50/72 rule changed my life."),
            ("ada_writes", "Saving this for the next code review."),
            ("linus_notes", "Glad it helps! Imperative mood is the hardest habit to build."),
        ],
        content="""A commit message is a letter to the next person who runs `git blame`, often you.

## The shape

```text
Add rate limiting to the login endpoint

Five attempts per minute per IP and username. Stops password
guessing without locking real users out for long.
```

## Three rules

- **Subject in the imperative:** "Add", not "Added"
- **Keep it under ~50 characters**, wrap the body at 72
- **Explain why**, the diff already shows what

That's it. Small habit, big payoff.""",
    ),
    SamplePost(
        author="ada_writes",
        title="CSS variables make dark mode easy",
        days_ago=4,
        liked_by=["linus_notes"],
        content="""Define your colours once as tokens, then swap them for dark mode.

```css
:root {
  --bg: #ffffff;
  --text: #1a1a1a;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1115;
    --text: #e6e6e6;
  }
}

body {
  background: var(--bg);
  color: var(--text);
}
```

Every component reads `var(--bg)`, so none of them needs to know which theme is active.""",
    ),
    SamplePost(
        author="grace_codes",
        title="Optimistic updates with TanStack Query",
        days_ago=6,
        liked_by=["ada_writes", "linus_notes"],
        comments=[("linus_notes", "The rollback part is what most tutorials skip. Nice.")],
        content="""When someone taps **Like**, show the heart straight away
and talk to the server afterwards.

## The recipe

1. `onMutate`: cancel queries in flight, save the old data, write the new data
2. `onError`: put the old data back
3. `onSettled`: refetch so the cache matches the server

```ts
onMutate: async () => {
  await queryClient.cancelQueries({ queryKey })
  const previous = queryClient.getQueryData(queryKey)
  queryClient.setQueryData(queryKey, (post) => ({ ...post, liked_by_me: true }))
  return { previous }
}
```

The app feels instant, and it stays correct when the network fails.""",
    ),
    SamplePost(
        author="linus_notes",
        title="Why your API errors deserve a schema",
        days_ago=9,
        liked_by=["grace_codes"],
        content="""Every error from the API should look the same:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Some fields are invalid",
    "request_id": "7f3c…",
    "details": [{ "field": "email", "message": "Not a valid email" }]
  }
}
```

- `code` is for **programs**: the frontend switches on it
- `message` is for **people**
- `request_id` lets support find the exact log line

One shape means one error component in the frontend, not twenty.""",
    ),
    SamplePost(
        author="ada_writes",
        title="Notes on learning in public",
        days_ago=13,
        liked_by=["grace_codes", "linus_notes"],
        comments=[("grace_codes", "Point three is the one I needed to hear.")],
        content="""Some things I've learned from writing about what I'm learning:

1. **You understand it better** once you've explained it
2. **Mistakes get corrected fast**: readers are generous
3. **Nobody expects perfection**, only honesty
4. **Your future self** is your most grateful reader

Start small. One paragraph about one thing you figured out today is enough.""",
    ),
]


async def seed() -> None:
    settings = Settings()
    engine = create_engine(settings)
    sessionmaker = create_sessionmaker(engine)
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

        for sample in POSTS:
            if sample.author not in created:
                continue
            author = authors[sample.author]
            data = PostCreate(title=sample.title, content=sample.content)
            post = await posts.create(author, data)
            post = await posts.publish(author, post.id)
            # Spread the posts out over the last two weeks, so the feed looks lived in
            post.published_at = now - timedelta(days=sample.days_ago, hours=len(sample.title))
            await session.commit()

            for username in sample.liked_by:
                await likes.like(authors[username], post.id)
            for username, text in sample.comments:
                await comments.create(authors[username], post.id, CommentCreate(content=text))

    await engine.dispose()

    if created:
        count = sum(post.author in created for post in POSTS)
        print(f"Created {len(created)} authors and {count} posts.")
        print(f"Log in as any of {', '.join(sorted(created))} with password: {password}")
    else:
        print("Sample data already exists, nothing to do.")


if __name__ == "__main__":
    asyncio.run(seed())
