"""add lifestyle topics

Revision ID: b7d2e4f19a60
Revises: 5ca3699f3588
Create Date: 2026-09-27 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d2e4f19a60"
down_revision: str | Sequence[str] | None = "5ca3699f3588"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Non-technical subjects, listed after the eight tech topics (positions 1 to 8)
TOPICS = [
    ("lifestyle", "Lifestyle", "Habits, homes and the small things that make a good day."),
    ("travel", "Travel", "Places, journeys and what we learn on the way."),
    ("food", "Food & Cooking", "Recipes, kitchens and the stories behind a good meal."),
    ("health-wellness", "Health & Wellness", "Sleep, movement, calm and looking after yourself."),
    ("personal-finance", "Personal Finance", "Budgets, saving and money decisions made simple."),
    ("books", "Books & Reading", "Reviews, reading lists and the joy of a good book."),
]

topics = sa.table(
    "topics",
    sa.column("slug", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("position", sa.SmallInteger),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(
        topics,
        [
            {"slug": slug, "name": name, "description": description, "position": position}
            for position, (slug, name, description) in enumerate(TOPICS, start=9)
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # post_topics rows go with them (ON DELETE CASCADE); the posts themselves stay
    op.execute(topics.delete().where(topics.c.slug.in_([slug for slug, _, _ in TOPICS])))
